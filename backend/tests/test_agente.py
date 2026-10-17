"""Test dell'agente di verifica sulle pratiche demo (senza modelli: estrattore a regole e testo di base)."""
import json
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from agente.confronto import tolleranza  # noqa: E402
from agente.grafo import crea_grafo  # noqa: E402
from agente.norme import RicercaParole  # noqa: E402
from agente.redazione import RedattoreModello, RedattoreTesto  # noqa: E402
from agente.redazione import TestoDifformita as Testo  # noqa: E402
from agente.valutazione import articoli, riepilogo, valuta_pratica  # noqa: E402
from api import pratiche  # noqa: E402
from estrazione.estrattori import RegoleEstrattore  # noqa: E402

PRATICHE = Path(__file__).resolve().parents[2] / "demo_data" / "pratiche"


def esegui(pratica: str, redattore=None, files=None):
    gt = json.loads((PRATICHE / pratica / "ground_truth.json").read_text(encoding="utf-8"))
    grafo = crea_grafo(RegoleEstrattore(), RicercaParole(), redattore or RedattoreTesto())
    return gt, grafo.invoke({"cartella": str(PRATICHE / pratica), "files": files or gt["documenti"]})


@pytest.mark.parametrize("pratica", ["P-001", "P-002", "P-003", "P-004", "P-005"])
def test_trova_le_difformita_attese(pratica):
    gt, out = esegui(pratica)
    r = valuta_pratica(gt, out)
    assert r["esito_ok"], (r["esito"], r["esito_atteso"])
    assert r["perse_tipi"] == [] and r["false_tipi"] == []
    assert r["ambito_ok"] == r["gravita_ok"] == r["vere"]


def test_p001_entro_tolleranza_senza_inventare_difformita():
    _, out = esegui("P-001")
    assert out["difformita"] == []
    assert [v["tipo"] for v in out["verifiche"]] == ["tolleranza_costruttiva"]
    assert "+2,44%" in out["verifiche"][0]["descrizione"]


def test_p005_area_vincolata_alza_ambito_e_gravita():
    _, out = esegui("P-005")
    edilizie = [d for d in out["difformita"] if d["ambito"] != "catastale"]
    assert {d["ambito"] for d in edilizie} == {"edilizio_paesaggistico"}
    assert {d["gravita"] for d in edilizie} == {"alta"}
    assert "D.Lgs. 42/2004" in next(d for d in edilizie if d["tipo"] == "ampliamento_senza_titolo")["riferimento_normativo"]


def test_senza_rilievo_non_conclude_nulla():
    _, out = esegui("P-002", files=["01_licenza_edilizia.pdf", "02_visura_catastale.pdf"])
    assert out["esito"] == "documentazione_incompleta"
    assert out["difformita"] == []
    assert [p["nodo"] for p in out["passi"]] == ["estrai", "controlla_documenti", "concludi"]


@pytest.mark.parametrize("sup,data,attesa", [
    (80, "1987-05-14", 0.05), (59, "1987-05-14", 0.06), (150, "1999-01-01", 0.04),
    (400, "2000-01-01", 0.03), (600, "2000-01-01", 0.02), (80, "2025-01-10", 0.02),
])
def test_tolleranza_salva_casa(sup, data, attesa):
    assert tolleranza(sup, data) == attesa


class ModelloFinto:
    """Si comporta come un chat model LangChain con output strutturato."""

    def __init__(self, citati):
        self.citati, self.messaggi = citati, None

    def with_structured_output(self, schema):
        assert schema is Testo
        return self

    def invoke(self, messaggi):
        self.messaggi = messaggi
        return Testo(descrizione="Descrizione dal modello.", valutazione="Valutazione dal modello.",
                               articoli_citati=self.citati)


def test_redattore_modello_scarta_le_citazioni_inventate():
    finto = ModelloFinto(["dpr380-art6", "articolo-inventato"])
    _, out = esegui("P-002", RedattoreModello(finto, "finto"))
    d1 = out["difformita"][0]
    assert d1["descrizione"] == "Descrizione dal modello."
    assert d1["riferimento_normativo"] == "art. 6 c.1 lett. b-bis DPR 380/2001"
    assert [p["id"] for p in d1["fonti_normative"]] == ["dpr380-art6"]
    assert any("articolo-inventato" in n for n in out["note"])
    assert "Passaggi normativi" in finto.messaggi[1][1]


def test_redattore_modello_senza_citazioni_valide_usa_il_catalogo():
    _, out = esegui("P-004", RedattoreModello(ModelloFinto([]), "finto"))
    assert out["difformita"][0]["riferimento_normativo"] == "art. 29 c.1-bis L. 52/1985"


def test_metriche():
    assert articoli("art. 23-ter e art. 36-bis DPR 380/2001; DM 5/7/1975") == {"23-ter", "36-bis", "DM 5/7/1975"}
    righe = [valuta_pratica(*esegui(p)) for p in ["P-001", "P-002"]]
    s = riepilogo(righe)
    assert (s["precisione"], s["richiamo"], s["esiti_corretti"]) == (1.0, 1.0, 2)


def test_api_agente_e_relazione(monkeypatch):
    monkeypatch.setenv("AGENTE_RICERCA", "parole")
    app = FastAPI()
    app.include_router(pratiche.router)
    client = TestClient(app)
    assert client.get("/api/pratiche/P-003/agente").status_code == 404
    res = client.post("/api/pratiche/P-003/agente", json={"estrattore": "regole", "redattore": "testo"})
    assert res.status_code == 200
    body = res.json()
    assert body["origine"] == "agente" and body["esito"] == "non_conforme"
    assert [p["nodo"] for p in body["agente"]["passi"]][-1] == "concludi"
    assert client.get("/api/pratiche/P-003/agente").json()["sintesi"] == body["sintesi"]
    doc = client.post("/api/pratiche/P-003/relazione", json={"confermate": ["D1"], "origine": "agente"})
    assert doc.status_code == 200
