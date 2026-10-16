"""
Ricerca nelle norme (la parte RAG dell'agente).

Il corpus è norme.json: sintesi degli articoli citati nelle verifiche, da
rivedere con un tecnico. Sono una dozzina di passaggi, quindi l'indice sta in
memoria: Qdrant servirà quando entreranno regolamenti edilizi comunali e
leggi regionali, con migliaia di articoli.

Due modi di cercare, con la stessa interfaccia:
- RicercaParole: parole in comune pesate per rarità, senza dipendenze (test e fallback)
- RicercaSemantica: embedding multilingue di fastembed, trova "chiusura di balcone"
  anche se l'articolo parla di "vetrate panoramiche"
"""
import json
import logging
import math
import os
import re
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

CORPUS = Path(__file__).with_name("norme.json")
PAROLE_VUOTE = set("il lo la i gli le un una di del della dei delle da dal dalla in nel nella con su per tra fra e o "
                   "che non si è sono al alla ai agli all ed se come anche più".split())


@dataclass
class Passaggio:
    id: str
    citazione: str
    titolo: str
    testo: str
    punteggio: float = 0.0

    def come_dict(self) -> dict:
        return {"id": self.id, "citazione": self.citazione, "titolo": self.titolo, "testo": self.testo,
                "punteggio": round(self.punteggio, 3)}


def carica_corpus(path: Path = CORPUS) -> list[Passaggio]:
    return [Passaggio(**p) for p in json.loads(path.read_text(encoding="utf-8"))]


def _radici(testo: str) -> list[str]:
    # Radice grezza: le prime 6 lettere bastano a unire "chiusura/chiuso", "abitabile/abitativi"
    return [w[:6] for w in re.findall(r"[a-zàèéìòù0-9-]+", testo.lower()) if w not in PAROLE_VUOTE and len(w) > 2]


class RicercaParole:
    nome = "parole"

    def __init__(self, corpus: list[Passaggio] | None = None):
        self.corpus = corpus or carica_corpus()
        self._doc = [set(_radici(f"{p.titolo} {p.testo}")) for p in self.corpus]
        n = len(self.corpus)
        self._idf = {r: math.log(1 + n / sum(r in d for d in self._doc)) for d in self._doc for r in d}

    def cerca(self, domanda: str, k: int = 3) -> list[Passaggio]:
        q = set(_radici(domanda))
        punteggi = [sum(self._idf.get(r, 0) for r in q & d) for d in self._doc]
        migliori = sorted(range(len(self.corpus)), key=lambda i: -punteggi[i])[:k]
        return [Passaggio(**{**self.corpus[i].__dict__, "punteggio": punteggi[i]}) for i in migliori if punteggi[i] > 0]


class RicercaSemantica:
    nome = "semantica"

    def __init__(self, corpus: list[Passaggio] | None = None):
        import numpy as np
        from services.embedding_service import embedding_service

        self._np, self._emb = np, embedding_service
        self.corpus = corpus or carica_corpus()
        vettori = np.array([self._emb.encode(f"{p.titolo}. {p.testo}") for p in self.corpus])
        self._matrice = vettori / np.linalg.norm(vettori, axis=1, keepdims=True)

    def cerca(self, domanda: str, k: int = 3) -> list[Passaggio]:
        q = self._np.array(self._emb.encode(domanda))
        sim = self._matrice @ (q / self._np.linalg.norm(q))
        migliori = sim.argsort()[::-1][:k]
        return [Passaggio(**{**self.corpus[i].__dict__, "punteggio": float(sim[i])}) for i in migliori]


def ricerca_predefinita():
    """Semantica se il modello di embedding è disponibile, altrimenti per parole (AGENTE_RICERCA=parole la forza)."""
    if os.getenv("AGENTE_RICERCA") == "parole":
        return RicercaParole()
    try:
        return RicercaSemantica()
    except Exception as e:  # modello non scaricabile, fastembed assente...
        logger.warning("Ricerca semantica non disponibile (%s): uso la ricerca per parole", e)
        return RicercaParole()
