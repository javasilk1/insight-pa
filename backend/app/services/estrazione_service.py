"""
Estrazione dei dati dai PDF di una pratica con l'estrattore scelto (Claude, Ollama o regole).

Gira in background: l'API restituisce subito e il frontend legge lo stato finché non è completata.
I risultati restano in memoria fino al riavvio del backend: diventeranno righe su Postgres
quando le pratiche passeranno al database.
"""
import os
import threading
from pathlib import Path

import httpx

from estrazione.estrattori import ESTRATTORI
from estrazione.valutazione import confronta


def _ollama_disponibile() -> tuple[bool, str]:
    url = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
    modello = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
    try:
        res = httpx.get(f"{url}/api/tags", timeout=1.5)
        res.raise_for_status()
    except httpx.HTTPError:
        return False, "Ollama non è in esecuzione (docker compose --profile locale up -d)"
    nomi = {m.get("name") for m in res.json().get("models", [])}
    if modello not in nomi:
        return False, f"modello {modello} non scaricato (ollama pull {modello})"
    return True, modello


class EstrazioneService:
    def __init__(self):
        self._stati: dict[str, dict] = {}
        self._lock = threading.Lock()

    def estrattori(self) -> list[dict]:
        claude = bool(os.getenv("ANTHROPIC_API_KEY"))
        ollama, nota_ollama = _ollama_disponibile()
        return [
            {"nome": "claude", "etichetta": "Claude (cloud)", "disponibile": claude,
             "nota": os.getenv("CLAUDE_MODEL", "claude-opus-5") if claude else "manca ANTHROPIC_API_KEY nel backend"},
            {"nome": "ollama", "etichetta": "Ollama (locale)", "disponibile": ollama, "nota": nota_ollama},
            {"nome": "regole", "etichetta": "Regole (senza AI)", "disponibile": True,
             "nota": "funziona solo sul formato delle pratiche demo"},
        ]

    def stato(self, pratica_id: str) -> dict | None:
        with self._lock:
            s = self._stati.get(pratica_id)
            return {**s, "documenti": list(s["documenti"])} if s else None

    def prenota(self, pratica_id: str, nome: str, totali: int) -> dict | None:
        """Segna l'estrazione come in corso; None se ce n'è già una per la stessa pratica."""
        with self._lock:
            if self._stati.get(pratica_id, {}).get("stato") == "in_corso":
                return None
            self._stati[pratica_id] = {
                "pratica": pratica_id, "estrattore": nome, "modello": None, "stato": "in_corso", "errore": None,
                "completati": 0, "totali": totali, "campi_corretti": 0, "campi_totali": 0,
                "secondi_totali": 0.0, "token_input": 0, "token_output": 0, "documenti": [],
            }
            return dict(self._stati[pratica_id])

    def esegui(self, pratica_id: str, nome: str, cartella: Path, files: list[str], attesi: dict[str, dict]):
        try:
            estrattore = ESTRATTORI[nome]()
        except Exception as e:  # es. chiave API mancante o non valida
            self._aggiorna(pratica_id, stato="errore", errore=str(e))
            return
        self._aggiorna(pratica_id, modello=getattr(estrattore, "model", None))
        for file in files:
            try:
                r = estrattore.estrai(cartella / file)
                doc = {"file": file, "tipo": r.tipo, "dati": r.dati, "secondi": round(r.secondi, 2),
                       "token_input": r.token_input, "token_output": r.token_output, "note": r.note}
            except Exception as e:
                doc = {"file": file, "tipo": None, "dati": {}, "secondi": 0, "token_input": 0, "token_output": 0,
                       "note": [f"errore: {e}"]}
            doc["confronto"] = confronta(attesi[file], doc["dati"]) if file in attesi else []
            with self._lock:
                s = self._stati[pratica_id]
                s["documenti"].append(doc)
                s["completati"] += 1
                s["campi_corretti"] += sum(c["ok"] for c in doc["confronto"])
                s["campi_totali"] += len(doc["confronto"])
                s["secondi_totali"] = round(s["secondi_totali"] + doc["secondi"], 1)
                s["token_input"] += doc["token_input"]
                s["token_output"] += doc["token_output"]
        self._aggiorna(pratica_id, stato="completata")

    def _aggiorna(self, pratica_id: str, **campi):
        with self._lock:
            self._stati[pratica_id].update(campi)


estrazione_service = EstrazioneService()
