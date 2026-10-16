"""
Cosa estraiamo da ogni tipo di documento.

Gli stessi modelli servono a tre cose: istruire il modello di linguaggio
(output strutturato), validarne la risposta, confrontarla con i ground truth.
"""
from typing import Literal, Optional

from pydantic import BaseModel, Field

TipoDocumento = Literal["titolo_edilizio", "visura", "planimetria", "rilievo", "altro"]


class TitoloEdilizio(BaseModel):
    tipo: Optional[str] = Field(None, description="Tipo di titolo in minuscolo: licenza edilizia, concessione edilizia, permesso di costruire, CILA, SCIA, condono")
    numero: Optional[str] = Field(None, description="Numero del titolo nel formato del documento, es. 45/2001")
    protocollo: Optional[str] = Field(None, description="Numero di protocollo, solo cifre")
    data: Optional[str] = Field(None, description="Data di rilascio o di presentazione, formato YYYY-MM-DD")
    oggetto: Optional[str] = Field(None, description="Oggetto dei lavori autorizzati o comunicati")
    destinazione: Optional[str] = Field(None, description="Destinazione d'uso principale in minuscolo, es. residenziale")
    destinazione_sottotetto: Optional[str] = Field(None, description="Destinazione del sottotetto se indicata, es. accessorio non abitabile")
    sup_utile_m2: Optional[float] = Field(None, description="Superficie utile residenziale autorizzata in m²")
    sup_non_residenziale_m2: Optional[float] = Field(None, description="Superficie non residenziale (balconi, portici, accessori) in m²")
    volume_m3: Optional[float] = Field(None, description="Volume autorizzato in m³")
    altezza_media_m: Optional[float] = Field(None, description="Altezza media interna in metri, se indicata")
    vincolo_paesaggistico: Optional[bool] = Field(None, description="True se il titolo cita un vincolo paesaggistico o la fascia costiera")
    prescrizioni: list[str] = Field(default_factory=list, description="Prescrizioni e condizioni del titolo, una per voce")


class Visura(BaseModel):
    categoria: Optional[str] = Field(None, description="Categoria catastale, es. A/2")
    classe: Optional[str] = Field(None, description="Classe catastale")
    consistenza_vani: Optional[float] = Field(None, description="Consistenza in vani, es. 5.5")
    sup_catastale_m2: Optional[float] = Field(None, description="Superficie catastale totale in m²")
    rendita_euro: Optional[float] = Field(None, description="Rendita catastale in euro")


class Locale(BaseModel):
    nome: str
    destinazione: Optional[str] = Field(None, description="residenziale, non residenziale, accessorio, pertinenza, collegamento")
    superficie_m2: Optional[float] = None


class Rilievo(BaseModel):
    data_sopralluogo: Optional[str] = Field(None, description="Formato YYYY-MM-DD")
    sup_utile_m2: Optional[float] = Field(None, description="Superficie utile totale rilevata in m²")
    distanza_mare_m: Optional[float] = Field(None, description="Distanza dalla linea di costa in metri, se indicata")
    locali: list[Locale] = Field(default_factory=list, description="Tutti i locali e le pertinenze rilevati")

    def derivati(self) -> dict:
        """Campi calcolati dai locali, confrontabili con i ground truth."""
        return {
            "locali_abitativi": [l.nome for l in self.locali if (l.destinazione or "").lower() == "residenziale"],
            "piscina": any("piscina" in l.nome.lower() for l in self.locali),
        }


class Classificazione(BaseModel):
    tipo: TipoDocumento


SCHEMI: dict[str, type[BaseModel]] = {"titolo_edilizio": TitoloEdilizio, "visura": Visura, "rilievo": Rilievo}


def classifica(testo: str) -> TipoDocumento:
    """Riconosce il tipo di documento dal testo della prima pagina."""
    t = testo.lower()
    if "visura per immobile" in t or "catasto fabbricati" in t:
        return "visura"
    if "planimetria di u.i.u" in t or "planimetria catastale" in t:
        return "planimetria"
    if "rilievo dello stato di fatto" in t:
        return "rilievo"
    if any(k in t for k in ("licenza edilizia", "concessione edilizia", "permesso di costruire", "(cila)", "scia")):
        return "titolo_edilizio"
    return "altro"


def come_dict(dati: BaseModel) -> dict:
    out = dati.model_dump(exclude_none=True)
    if isinstance(dati, Rilievo):
        out.update(dati.derivati())
    return out
