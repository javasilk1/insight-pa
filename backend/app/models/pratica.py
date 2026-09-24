"""
Contratto dati della verifica di una pratica.

Oggi viene riempito dai ground_truth.json delle pratiche demo; domani lo
produrrà l'agente di verifica. Il frontend dipende solo da questo schema.
"""
from typing import Literal, Optional

from pydantic import BaseModel


class Fonte(BaseModel):
    file: str
    pagina: int


class Difformita(BaseModel):
    id: str
    ambito: str  # edilizio | catastale | edilizio_paesaggistico
    tipo: str
    gravita: Literal["bassa", "media", "alta"]
    descrizione: str
    valutazione: str
    riferimento_normativo: str
    entita: Optional[str] = None
    fonti: list[Fonte]


class Verifica(BaseModel):
    tipo: str
    descrizione: str
    valutazione: str
    riferimento_normativo: str
    fonti: list[Fonte]


class DocumentoPratica(BaseModel):
    file: str
    tipo: str
    pagine: int
    url: str


class PraticaSintesi(BaseModel):
    id: str
    indirizzo: str
    intestatario: str
    scenario: str
    esito: str
    n_difformita: int
    n_documenti: int


class AnalisiPratica(BaseModel):
    id: str
    origine: Literal["demo_ground_truth", "agente"]
    esito: str
    sintesi: str
    immobile: dict
    documenti: list[DocumentoPratica]
    dati_estratti: dict[str, dict]
    difformita: list[Difformita]
    verifiche: list[Verifica]


class RichiestaRelazione(BaseModel):
    confermate: list[str]
    note: dict[str, str] = {}
    tecnico: str = ""
