"""Test del modulo di estrazione e del confronto con i ground truth (senza chiamate a modelli reali)."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend" / "app"))
sys.path.insert(0, str(ROOT / "backend" / "scripts"))

from estrazione import estrattori  # noqa: E402
from estrazione.estrattori import ClaudeEstrattore, OllamaEstrattore, RegoleEstrattore  # noqa: E402
from estrazione.pdf_testo import estrai_pagine  # noqa: E402
from estrazione.schema import Classificazione, Rilievo, TitoloEdilizio  # noqa: E402
from estrazione.valutazione import corrisponde  # noqa: E402
from valuta_estrazione import valuta  # noqa: E402

PRATICHE = ROOT / "demo_data" / "pratiche"
SCANSIONI = ROOT / "demo_data" / "pratiche_scansionate"


def test_baseline_regole_estrae_tutti_i_campi_dei_pdf_digitali():
    report = valuta("regole", PRATICHE)
    sbagliati = [r for r in report["campi"] if not r["ok"]]
    assert report["campi_totali"] == 54
    assert sbagliati == []


def test_le_scansioni_non_hanno_testo_selezionabile():
    pagine = estrai_pagine(SCANSIONI / "P-002" / "01_licenza_edilizia.pdf")
    assert len(pagine) == 2
    assert all(p["metodo"] in ("ocr", "illeggibile") for p in pagine)


@pytest.mark.parametrize("campo,atteso,estratto,ok", [
    ("sup_utile_m2", 80.0, "80", True),
    ("sup_utile_m2", 80.0, 81.95, False),
    ("data", "2019-05-06", "06/05/2019", True),
    ("categoria", "A/2", "a/2", True),
    ("vincolo_paesaggistico", True, None, False),
    ("locali_abitativi", ["Camera", "Bagno"], ["bagno", "camera"], True),
    ("oggetto", "demolizione tramezzo cucina-soggiorno e rifacimento bagno",
     "demolizione del tramezzo tra cucina e soggiorno e rifacimento del bagno", True),
    ("oggetto", "demolizione tramezzo cucina-soggiorno e rifacimento bagno", "rifacimento del bagno", False),
])
def test_confronto_campi(campo, atteso, estratto, ok):
    assert corrisponde(campo, atteso, estratto) is ok


class FintoClaude:
    """Registra le chiamate e risponde come l'SDK, senza rete."""

    def __init__(self, risposte):
        self.chiamate, self.risposte = [], list(risposte)
        self.beta = SimpleNamespace(messages=SimpleNamespace(parse=self.parse))

    def parse(self, **kwargs):
        self.chiamate.append(kwargs)
        return SimpleNamespace(parsed_output=self.risposte.pop(0), stop_reason="end_turn",
                               usage=SimpleNamespace(input_tokens=1200, output_tokens=150))


def _claude(risposte):
    e = ClaudeEstrattore.__new__(ClaudeEstrattore)
    e.client, e.model = FintoClaude(risposte), "claude-opus-5"
    return e


def test_claude_riceve_il_pdf_e_usa_lo_schema_giusto():
    e = _claude([TitoloEdilizio(tipo="licenza edilizia", numero="212/1979", sup_non_residenziale_m2=8)])
    r = e.estrai(PRATICHE / "P-002" / "01_licenza_edilizia.pdf")
    chiamata = e.client.chiamate[0]
    assert chiamata["output_format"] is TitoloEdilizio
    assert chiamata["fallbacks"] == "default"
    assert chiamata["messages"][0]["content"][0]["type"] == "document"
    assert r.dati["numero"] == "212/1979" and r.token_input == 1200


def test_claude_classifica_le_scansioni_senza_testo():
    e = _claude([Classificazione(tipo="rilievo"), Rilievo(sup_utile_m2=88, locali=[])])
    r = e.estrai(SCANSIONI / "P-002" / "04_rilievo_stato_di_fatto.pdf")
    if r.note and any("ocr" in n for n in r.note):
        pytest.skip("OCR installato: la classificazione avviene sul testo")
    assert [c["output_format"] for c in e.client.chiamate] == [Classificazione, Rilievo]
    assert r.tipo == "rilievo" and r.dati["sup_utile_m2"] == 88


def test_ollama_vincola_la_risposta_allo_schema(monkeypatch):
    inviato = {}

    def finto_post(url, json, timeout):
        inviato.update(json)
        contenuto = '{"categoria": "A/2", "classe": "2", "consistenza_vani": 5.5, "sup_catastale_m2": 88}'
        return SimpleNamespace(raise_for_status=lambda: None,
                               json=lambda: {"message": {"content": contenuto}, "prompt_eval_count": 900, "eval_count": 40})

    import httpx
    monkeypatch.setattr(httpx, "post", finto_post)
    r = OllamaEstrattore(model="qwen2.5:7b").estrai(PRATICHE / "P-002" / "02_visura_catastale.pdf")
    assert inviato["format"]["title"] == "Visura"
    assert "Visura per immobile" in inviato["messages"][1]["content"]
    assert r.dati["sup_catastale_m2"] == 88 and r.token_output == 40
