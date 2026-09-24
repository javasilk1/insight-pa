"""
Tre estrattori con la stessa interfaccia, confrontabili con lo stesso script di valutazione:

- RegoleEstrattore: espressioni regolari, baseline deterministica e gratuita
- ClaudeEstrattore: Claude via API, legge il PDF direttamente (anche scansioni)
- OllamaEstrattore: modello open source locale, lavora sul testo estratto (con OCR)
"""
import base64
import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import BaseModel

from .pdf_testo import estrai_pagine, testo_completo
from .schema import SCHEMI, Classificazione, Rilievo, Locale, classifica, come_dict

ISTRUZIONI = (
    "Sei l'assistente di un tecnico edilizio italiano che verifica lo stato legittimo di un immobile. "
    "Estrai i dati richiesti dal documento ({tipo}). Riporta solo valori scritti nel documento: "
    "se un dato non c'è, lascialo vuoto invece di dedurlo. Numeri con il punto decimale, date in formato YYYY-MM-DD."
)


@dataclass
class Risultato:
    file: str
    tipo: str
    dati: dict
    secondi: float
    token_input: int = 0
    token_output: int = 0
    note: list[str] = field(default_factory=list)


class Estrattore:
    nome = "base"

    def estrai(self, path: Path) -> Risultato:
        inizio = time.perf_counter()
        pagine = estrai_pagine(path)
        tipo = self._classifica(path, pagine)
        schema = SCHEMI.get(tipo)
        if not schema:
            return Risultato(path.name, tipo, {}, time.perf_counter() - inizio)
        dati, usage, note = self._estrai(path, tipo, schema, pagine)
        note += [f"pagina {p['pagina']}: {p['metodo']}" for p in pagine if p["metodo"] != "testo"]
        return Risultato(path.name, tipo, come_dict(dati), time.perf_counter() - inizio,
                         usage.get("input", 0), usage.get("output", 0), note)

    def _classifica(self, path: Path, pagine: list[dict]) -> str:
        return classifica(pagine[0]["testo"] if pagine else "")

    def _estrai(self, path: Path, tipo: str, schema: type[BaseModel], pagine: list[dict]):
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Baseline a regole
# ---------------------------------------------------------------------------

def _num(s: str | None) -> float | None:
    return float(s.replace(".", "").replace(",", ".")) if s else None


def _iso(s: str | None) -> str | None:
    if not s:
        return None
    g, m, a = s.split("/")
    return f"{a}-{m}-{g}"


def _cerca(pattern: str, testo: str, flags=re.I) -> str | None:
    m = re.search(pattern, testo, flags)
    return m.group(1).strip() if m else None


class RegoleEstrattore(Estrattore):
    """Funziona solo sul formato delle pratiche demo: serve da riferimento minimo e da test del harness."""
    nome = "regole"

    def _estrai(self, path, tipo, schema, pagine):
        t = pagine[0]["testo"]
        if tipo == "titolo_edilizio":
            titolo = _cerca(r"^(LICENZA EDILIZIA|CONCESSIONE EDILIZIA|PERMESSO DI COSTRUIRE|.*\(CILA\)|.*\(SCIA\))$", t, re.M)
            tipo_titolo = "CILA" if titolo and "(CILA)" in titolo else "SCIA" if titolo and "(SCIA)" in titolo else (titolo or "").lower() or None
            dest = _cerca(r"Destinazione d'uso\n(.+)", t)
            sotto = _cerca(r"sottotetto ([a-z ]*non abitabile)", dest or "")
            dati = schema(
                tipo=tipo_titolo,
                numero=_cerca(r"^N\. (\S+) del", t, re.M),
                protocollo=_cerca(r"Prot\. (\d+)", t),
                data=_iso(_cerca(r"(?:^N\. \S+ del|^Prot\. \d+ del) (\d{2}/\d{2}/\d{4})", t, re.M)),
                oggetto=_cerca(r"(?:inizio dei lavori per|titolo per): (.+?)[.;](?:\s|$)", t.replace("\n", " ")),
                destinazione=(dest.split(" (")[0].split(";")[0].lower() if dest else None),
                destinazione_sottotetto=sotto,
                sup_utile_m2=_num(_cerca(r"Superficie utile residenziale\n([\d.,]+) m²", t)),
                sup_non_residenziale_m2=_num(_cerca(r"Superficie non residenziale\n([\d.,]+) m²", t)),
                volume_m3=_num(_cerca(r"Volume\n([\d.,]+) m³", t)),
                altezza_media_m=_num(_cerca(r"altezza media ([\d,]+) m", t)),
                vincolo_paesaggistico=bool(re.search(r"paesaggistic|battigia|fascia costiera", t, re.I)) or None,
                prescrizioni=[l[2:] for l in t.splitlines() if l.startswith("- ")],
            )
        elif tipo == "visura":
            m = re.search(r"\n([A-F]/\d+)\n(\w+)\n([\d,]+) vani\n(\d+) m²\nEuro ([\d.,]+)", t)
            dati = schema(categoria=m.group(1), classe=m.group(2), consistenza_vani=_num(m.group(3)),
                          sup_catastale_m2=_num(m.group(4)), rendita_euro=_num(m.group(5))) if m else schema()
        else:  # rilievo
            righe = re.findall(r"^ ?([A-Z][\w -]+)\n([a-z ()]+)\n[\d,]+ x [\d,]+\n([\d,]+)$", t, re.M)
            dati = Rilievo(
                data_sopralluogo=_iso(_cerca(r"Sopralluogo del (\d{2}/\d{2}/\d{4})", t)),
                sup_utile_m2=_num(_cerca(r"Superficie utile totale[^:]*:\s*([\d.,]+) m²", t)),
                distanza_mare_m=_num(_cerca(r"battigia[^:]*: circa (\d+) m", t)),
                locali=[Locale(nome=n.strip(), destinazione=d.strip(), superficie_m2=_num(s)) for n, d, s in righe],
            )
        return dati, {}, []


# ---------------------------------------------------------------------------
# Claude via API
# ---------------------------------------------------------------------------

class ClaudeEstrattore(Estrattore):
    """Invia il PDF originale: Claude legge testo e immagini, quindi non serve OCR."""
    nome = "claude"

    def __init__(self, model: str | None = None):
        import anthropic

        self.client = anthropic.Anthropic()  # ANTHROPIC_API_KEY dall'ambiente
        self.model = model or os.getenv("CLAUDE_MODEL", "claude-opus-5")

    def _chiedi(self, path: Path, istruzioni: str, schema: type[BaseModel]):
        pdf = base64.standard_b64encode(path.read_bytes()).decode()
        return self.client.beta.messages.parse(
            model=self.model,
            max_tokens=16000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",  # se una richiesta viene rifiutata, il server la ripete su un altro modello
            output_format=schema,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": pdf}},
                    {"type": "text", "text": istruzioni},
                ],
            }],
        )

    def _classifica(self, path, pagine):
        tipo = super()._classifica(path, pagine)
        if tipo != "altro":
            return tipo
        # Scansione senza testo: il tipo lo riconosce Claude guardando le pagine
        response = self._chiedi(path, "Che tipo di documento è? titolo_edilizio comprende licenze, concessioni, "
                                      "permessi di costruire, CILA e SCIA.", Classificazione)
        return response.parsed_output.tipo if response.parsed_output else "altro"

    def _estrai(self, path, tipo, schema, pagine):
        response = self._chiedi(path, ISTRUZIONI.format(tipo=tipo.replace("_", " ")), schema)
        if response.stop_reason == "refusal" or response.parsed_output is None:
            return schema(), _usage(response), [f"nessun output ({response.stop_reason})"]
        return response.parsed_output, _usage(response), []


def _usage(response) -> dict:
    return {"input": response.usage.input_tokens, "output": response.usage.output_tokens}


# ---------------------------------------------------------------------------
# Modello locale con Ollama
# ---------------------------------------------------------------------------

class OllamaEstrattore(Estrattore):
    """Invia il testo estratto (con OCR per le scansioni) a un modello locale con output vincolato allo schema."""
    nome = "ollama"

    def __init__(self, model: str | None = None, url: str | None = None):
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
        self.url = (url or os.getenv("OLLAMA_URL", "http://localhost:11434")).rstrip("/")

    def _estrai(self, path, tipo, schema, pagine):
        import httpx

        res = httpx.post(f"{self.url}/api/chat", timeout=300, json={
            "model": self.model,
            "stream": False,
            "format": schema.model_json_schema(),
            "options": {"temperature": 0},
            "messages": [
                {"role": "system", "content": ISTRUZIONI.format(tipo=tipo.replace("_", " "))},
                {"role": "user", "content": testo_completo(pagine)},
            ],
        })
        res.raise_for_status()
        body = res.json()
        usage = {"input": body.get("prompt_eval_count", 0), "output": body.get("eval_count", 0)}
        try:
            return schema.model_validate(json.loads(body["message"]["content"])), usage, []
        except (ValueError, KeyError) as e:
            return schema(), usage, [f"risposta non valida: {e}"]


ESTRATTORI = {"regole": RegoleEstrattore, "claude": ClaudeEstrattore, "ollama": OllamaEstrattore}
