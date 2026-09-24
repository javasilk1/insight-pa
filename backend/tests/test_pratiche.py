"""Test dell'API pratiche sulle pratiche demo (non richiede Postgres né Qdrant)."""
import sys
from io import BytesIO
from pathlib import Path

from docx import Document
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from api import pratiche  # noqa: E402

app = FastAPI()
app.include_router(pratiche.router)
client = TestClient(app)


def test_lista_contiene_le_cinque_pratiche():
    res = client.get("/api/pratiche")
    assert res.status_code == 200
    ids = [p["id"] for p in res.json()]
    assert ids == ["P-001", "P-002", "P-003", "P-004", "P-005"]


def test_analisi_rispetta_il_contratto():
    res = client.get("/api/pratiche/P-002")
    assert res.status_code == 200
    body = res.json()
    assert body["origine"] == "demo_ground_truth"
    assert [d["id"] for d in body["difformita"]] == ["D1", "D2"]
    files = {d["file"]: d for d in body["documenti"]}
    assert files["01_licenza_edilizia.pdf"]["pagine"] == 2
    for dif in body["difformita"]:
        for fonte in dif["fonti"]:
            assert fonte["file"] in files
            assert 1 <= fonte["pagina"] <= files[fonte["file"]]["pagine"]


def test_fonti_valide_in_tutte_le_pratiche():
    for p in client.get("/api/pratiche").json():
        body = client.get(f"/api/pratiche/{p['id']}").json()
        pagine = {d["file"]: d["pagine"] for d in body["documenti"]}
        for item in body["difformita"] + body["verifiche"]:
            for fonte in item["fonti"]:
                assert 1 <= fonte["pagina"] <= pagine[fonte["file"]], (p["id"], fonte)


def test_documento_pdf_e_path_traversal():
    res = client.get("/api/pratiche/P-001/documenti/02_visura_catastale.pdf")
    assert res.status_code == 200
    assert res.content.startswith(b"%PDF")
    assert client.get("/api/pratiche/P-001/documenti/..%2Fground_truth.json").status_code == 404
    assert client.get("/api/pratiche/../documenti/x.pdf").status_code == 404
    assert client.get("/api/pratiche/P-999").status_code == 404


def test_relazione_include_solo_le_difformita_confermate():
    res = client.post("/api/pratiche/P-005/relazione",
                      json={"confermate": ["D1", "D3"], "note": {"D1": "Verificato in sopralluogo"}, "tecnico": "Geom. Demo"})
    assert res.status_code == 200
    text = "\n".join(p.text for p in Document(BytesIO(res.content)).paragraphs)
    assert "D1 - Ampliamento senza titolo" in text
    assert "D3 - " in text
    assert "D2 - " not in text
    assert "Nota del tecnico: Verificato in sopralluogo" in text
    assert "Geom. Demo" in text
