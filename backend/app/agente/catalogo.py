"""
Catalogo dei tipi di difformità che l'agente sa riconoscere.

Il confronto (confronto.py) decide *quale* tipo si applica, con regole e numeri.
Il catalogo dice ambito, gravità di partenza, articoli da cercare tra le norme
e un testo di base, usato quando non c'è un modello di linguaggio.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class TipoDifformita:
    ambito: str  # edilizio | catastale (diventa edilizio_paesaggistico in area vincolata)
    gravita: str
    articoli: list[str]  # id in norme.json
    descrizione: str
    valutazione: str
    esterno: bool = False  # modifica l'aspetto esteriore: rileva anche per il vincolo paesaggistico
    articoli_vincolo: list[str] = field(default_factory=list)
    valutazione_vincolo: str = ""


CATALOGO: dict[str, TipoDifformita] = {
    "chiusura_balcone_veranda": TipoDifformita(
        ambito="edilizio", gravita="media", esterno=True,
        articoli=["dpr380-art6", "dpr380-art36bis"],
        descrizione="Lo spazio esterno {vecchio} ({dest_vecchia}) previsto dal titolo risulta chiuso e usato come {nuovo} ({dest_nuova}).",
        valutazione="Aumento di superficie utile senza titolo. Non è edilizia libera se la chiusura non è una vetrata amovibile e totalmente trasparente: da valutare la sanatoria.",
        articoli_vincolo=["dlgs42-art146", "dlgs42-art167"],
        valutazione_vincolo="In area vincolata la nuova superficie non è sanabile sotto il profilo paesaggistico.",
    ),
    "mutamento_destinazione_uso": TipoDifformita(
        ambito="edilizio", gravita="alta",
        articoli=["dpr380-art23ter", "dpr380-art36bis", "dm1975-altezze"],
        descrizione="{vecchio} ({dest_vecchia}) del titolo risulta trasformato in {nuovo}, con destinazione residenziale.",
        valutazione="Trasformazione in locali abitativi senza titolo: aumenta la superficie utile. Verificare altezze minime e requisiti igienici prima di valutare la sanatoria.",
    ),
    "ampliamento_senza_titolo": TipoDifformita(
        ambito="edilizio", gravita="alta", esterno=True,
        articoli=["dpr380-art31", "dpr380-art36bis"],
        descrizione="Nel rilievo ci sono locali che il titolo non prevede: {nuovo}.",
        valutazione="Nuova superficie utile realizzata senza titolo. Da verificare la sanabilità.",
        articoli_vincolo=["dlgs42-art142", "dlgs42-art167", "dpr380-art31"],
        valutazione_vincolo="In area vincolata un ampliamento con nuova superficie non è sanabile sotto il profilo paesaggistico: rischio di demolizione.",
    ),
    "piscina_senza_titolo": TipoDifformita(
        ambito="edilizio", gravita="media", esterno=True,
        articoli=["dpr380-art36bis"],
        descrizione="Nel rilievo è presente una piscina di {nuovo} che nessun titolo prevede.",
        valutazione="Opera pertinenziale realizzata senza titolo. Da verificare la sanabilità secondo le norme regionali.",
        articoli_vincolo=["dlgs42-art146", "dlgs42-art142"],
        valutazione_vincolo="In area vincolata serviva anche l'autorizzazione paesaggistica.",
    ),
    "diversa_distribuzione_interna": TipoDifformita(
        ambito="edilizio", gravita="bassa",
        articoli=["dpr380-art6bis", "dpr380-art34bis"],
        descrizione="La distribuzione dei locali è diversa dal titolo: {vecchio} nel titolo, {nuovo} nel rilievo.",
        valutazione="Modifica interna senza aumento di superficie: regolarizzabile con CILA tardiva se non tocca parti strutturali.",
    ),
    "scostamento_oltre_tolleranza": TipoDifformita(
        ambito="edilizio", gravita="media",
        articoli=["dpr380-art34bis", "dpr380-art36bis"],
        descrizione="La superficie utile dei locali presenti nel titolo è {nuovo} m² contro {vecchio} m² di progetto.",
        valutazione="Lo scostamento supera la tolleranza costruttiva applicabile.",
    ),
    "planimetria_non_aggiornata": TipoDifformita(
        ambito="catastale", gravita="media",
        articoli=["l52-art29"],
        descrizione="La planimetria catastale {vecchio} non rappresenta lo stato di fatto: {nuovo}.",
        valutazione="Serve una variazione catastale (DOCFA) prima di un atto di vendita.",
    ),
    "catasto_non_coerente_con_titolo": TipoDifformita(
        ambito="catastale", gravita="media",
        articoli=["dpr380-art9bis"],
        descrizione="La planimetria catastale riporta lo stato di fatto ({nuovo}), ma non il titolo edilizio ({vecchio}).",
        valutazione="La planimetria aggiornata non rende legittime le opere: lo stato legittimo resta quello del titolo.",
    ),
}


def esito(ambiti: list[str]) -> str:
    if not ambiti:
        return "conforme"
    if all(a == "catastale" for a in ambiti):
        return "conforme_edilizio_non_conforme_catastale"
    return "non_conforme"
