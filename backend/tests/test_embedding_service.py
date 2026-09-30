"""Test del servizio di embedding con TextEmbedding finto (nessun download del modello)."""
import sys
import types
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend" / "app"))

from services import embedding_service as modulo  # noqa: E402


class FintoTextEmbedding:
    istanze = 0

    def __init__(self, model_name):
        FintoTextEmbedding.istanze += 1
        self.model_name = model_name
        self.testi = []

    def embed(self, documents):
        for testo in documents:
            self.testi.append(testo)
            yield np.full(modulo.EMBEDDING_DIM, 0.5, dtype=np.float32)


def _installa_finto(monkeypatch):
    FintoTextEmbedding.istanze = 0
    monkeypatch.setitem(sys.modules, "fastembed", types.SimpleNamespace(TextEmbedding=FintoTextEmbedding))


def test_modello_caricato_al_primo_uso_e_una_volta_sola(monkeypatch):
    _installa_finto(monkeypatch)
    servizio = modulo.EmbeddingService()
    assert FintoTextEmbedding.istanze == 0

    servizio.encode("permesso di costruire")
    servizio.encode("SCIA")
    assert FintoTextEmbedding.istanze == 1
    assert servizio.model.model_name == "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def test_encode_restituisce_lista_di_float_a_384_dimensioni(monkeypatch):
    _installa_finto(monkeypatch)
    vettore = modulo.EmbeddingService().encode("abuso edilizio in zona vincolata")
    assert isinstance(vettore, list)
    assert len(vettore) == 384
    assert all(type(x) is float for x in vettore)


def test_testo_vuoto_o_none_diventa_stringa_vuota(monkeypatch):
    _installa_finto(monkeypatch)
    servizio = modulo.EmbeddingService()
    servizio.encode(None)
    servizio.encode("")
    assert servizio.model.testi == ["", ""]
