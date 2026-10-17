"""
Confronto deterministico tra titolo, catasto e rilievo.

Qui non ci sono modelli di linguaggio: le difformità le decidono numeri e regole
scritte in codice (locali presenti o mancanti, destinazioni, tolleranze di legge),
così ogni esito è ripetibile e spiegabile al tecnico che firma.
"""
import re
from datetime import date

from pydantic import BaseModel, Field

from models.pratica import Fonte

from .catalogo import CATALOGO

# DL 69/2024: per gli interventi realizzati entro il 24/05/2024 la tolleranza dipende dalla superficie utile
DATA_SALVA_CASA = date(2024, 5, 24)
SOGLIE_TOLLERANZA = [(500, 0.02), (300, 0.03), (100, 0.04), (60, 0.05), (0, 0.06)]
SPAZI_ESTERNI = ("balcone", "loggia", "terrazz", "portico", "porticato")
DISTANZA_COSTA_VINCOLO_M = 300
SIMILI = 0.05  # due superfici entro il 5% sono considerate la stessa


class Riscontro(BaseModel):
    """Una difformità trovata dal confronto, prima della redazione del testo."""
    tipo: str
    ambito: str
    gravita: str
    entita: str | None = None
    segnaposti: dict[str, str] = Field(default_factory=dict)  # per il testo di base del catalogo
    fatti: list[str] = Field(default_factory=list)  # cosa dicono i documenti, in chiaro per il modello
    fonti: list[Fonte] = Field(default_factory=list)
    articoli: list[str] = Field(default_factory=list)
    valutazione_extra: str = ""


class EsitoConfronto(BaseModel):
    riscontri: list[Riscontro]
    verifiche: list[dict]
    note: list[str]


def tolleranza(sup_utile: float, data_titolo: str | None) -> float:
    try:
        anteriore = date.fromisoformat(data_titolo or "") < DATA_SALVA_CASA
    except ValueError:
        anteriore = True  # titolo senza data: in pratica sempre un intervento non recente
    if not anteriore:
        return 0.02
    return next(t for soglia, t in SOGLIE_TOLLERANZA if sup_utile > soglia)


def _nome(n: str) -> str:
    return re.sub(r"\s+", " ", n.strip().lower())


def _abitabile(l: dict) -> bool:
    return (l.get("destinazione") or "").lower().startswith("residenziale")


def _esterno(l: dict) -> bool:
    return any(k in _nome(l["nome"]) for k in SPAZI_ESTERNI)


def _accessorio(l: dict) -> bool:
    d = (l.get("destinazione") or "").lower()
    return "accessori" in d or "non abitabile" in d


def _piscina(l: dict) -> bool:
    return "piscina" in _nome(l["nome"])


def _sup(locali) -> float:
    return round(sum(l.get("superficie_m2") or 0 for l in locali), 2)


def _simile(a: float, b: float) -> bool:
    return a > 0 and b > 0 and abs(a - b) / max(a, b) <= SIMILI


def _m2(x: float) -> str:
    return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " m²"


def _pct(x: float) -> str:
    return f"{x:+.2%}".replace(".", ",")


def _elenco(locali) -> str:
    return ", ".join(f"{l['nome']} {_m2(l.get('superficie_m2') or 0)}" for l in locali)


def _per_tipo(documenti: dict[str, dict], tipo: str) -> list[tuple[str, dict]]:
    return [(f, d["dati"]) for f, d in documenti.items() if d.get("tipo") == tipo and d.get("dati")]


def confronta(documenti: dict[str, dict]) -> EsitoConfronto:
    """documenti: {file: {"tipo": ..., "dati": {...}}} come prodotto dagli estrattori."""
    note: list[str] = []
    titoli = sorted(_per_tipo(documenti, "titolo_edilizio"), key=lambda x: x[1].get("data") or "")
    rilievo_f, rilievo = (_per_tipo(documenti, "rilievo") or [(None, {})])[0]
    plan_f, plan = (_per_tipo(documenti, "planimetria") or [(None, {})])[0]

    # Stato legittimo: l'ultimo titolo che descrive i locali (es. la CILA che ha cambiato la distribuzione)
    con_locali = [(f, t) for f, t in titoli if t.get("locali")]
    if not con_locali or not rilievo.get("locali"):
        note.append("Mancano i locali del titolo o del rilievo: confronto non possibile.")
        return EsitoConfronto(riscontri=[], verifiche=[], note=note)
    titolo_f, titolo = con_locali[-1]
    nome_titolo = f"{titolo.get('tipo') or 'titolo'} {titolo.get('numero') or titolo.get('protocollo') or ''}".strip()
    pag_titolo = titolo.get("pagina_elaborato") or 1
    fonte_titolo, fonte_rilievo = Fonte(file=titolo_f, pagina=pag_titolo), Fonte(file=rilievo_f, pagina=1)

    legit = {_nome(l["nome"]): l for l in titolo["locali"]}
    stato = {_nome(l["nome"]): l for l in rilievo["locali"]}
    solo_titolo = [legit[n] for n in legit if n not in stato]
    solo_rilievo = [stato[n] for n in stato if n not in legit]

    vincolo = any(t.get("vincolo_paesaggistico") for _, t in titoli) or (
        (rilievo.get("distanza_mare_m") or 1e9) < DISTANZA_COSTA_VINCOLO_M)
    if vincolo:
        motivo = []
        if any(t.get("vincolo_paesaggistico") for _, t in titoli):
            motivo.append("il titolo cita il vincolo paesaggistico")
        if rilievo.get("distanza_mare_m"):
            motivo.append(f"distanza dalla costa {rilievo['distanza_mare_m']:.0f} m")
        note.append("Area vincolata: " + ", ".join(motivo) + ".")

    riscontri: list[Riscontro] = []

    def aggiungi(tipo: str, vecchio: str, nuovo: str, entita: str | None, fatti: list[str], **segnaposti):
        cat = CATALOGO[tipo]
        r = Riscontro(
            tipo=tipo, ambito=cat.ambito, gravita=cat.gravita, entita=entita, fatti=fatti,
            segnaposti={"vecchio": vecchio, "nuovo": nuovo, **segnaposti},
            fonti=[fonte_titolo, fonte_rilievo], articoli=list(cat.articoli),
        )
        if vincolo and cat.esterno:
            r.ambito, r.gravita = "edilizio_paesaggistico", "alta"
            r.articoli = cat.articoli_vincolo + [a for a in cat.articoli if a not in cat.articoli_vincolo]
            r.valutazione_extra = cat.valutazione_vincolo
            r.fatti.append(note[-1])
        riscontri.append(r)

    nuovi_abitabili = [l for l in solo_rilievo if _abitabile(l) and not _piscina(l)]

    # 1. Spazi esterni chiusi (balcone diventato veranda): stessa superficie, nome diverso, ora abitabile
    for vecchio in [l for l in solo_titolo if _esterno(l) and not _abitabile(l)]:
        nuovo = next((l for l in nuovi_abitabili if _simile(l.get("superficie_m2") or 0, vecchio.get("superficie_m2") or 0)), None)
        if nuovo:
            nuovi_abitabili.remove(nuovo)
            sup = nuovo.get("superficie_m2") or 0
            aggiungi("chiusura_balcone_veranda", vecchio["nome"], nuovo["nome"], f"+{_m2(sup)} di superficie utile",
                     [f"Titolo ({nome_titolo}): {vecchio['nome']}, {vecchio.get('destinazione')}, {_m2(vecchio.get('superficie_m2') or 0)}.",
                      f"Rilievo: {nuovo['nome']}, {nuovo.get('destinazione')}, {_m2(sup)}."],
                     dest_vecchia=vecchio.get("destinazione") or "", dest_nuova=nuovo.get("destinazione") or "")

    # 2. Locali accessori diventati abitativi: nel rilievo i nuovi locali abitabili ne coprono la superficie
    accessori = [l for l in solo_titolo if _accessorio(l) and not _esterno(l)]
    sup_acc = _sup(accessori)
    if accessori and _simile(_sup(nuovi_abitabili), sup_acc):
        aggiungi("mutamento_destinazione_uso", ", ".join(l["nome"] for l in accessori), ", ".join(l["nome"] for l in nuovi_abitabili),
                 f"{_m2(sup_acc)} da {accessori[0].get('destinazione')} a residenziale",
                 [f"Titolo ({nome_titolo}): {_elenco(accessori)}, {accessori[0].get('destinazione')}.",
                  f"Rilievo: {_elenco(nuovi_abitabili)}, residenziale."]
                 + [f"Prescrizione del titolo: {p}" for p in titolo.get("prescrizioni", [])],
                 dest_vecchia=accessori[0].get("destinazione") or "")
        nuovi_abitabili = []

    # 3. Locali abitabili spariti e comparsi con la stessa superficie: diversa distribuzione interna
    spariti = [l for l in solo_titolo if _abitabile(l)]
    if spariti and nuovi_abitabili and _simile(_sup(spariti), _sup(nuovi_abitabili)):
        aggiungi("diversa_distribuzione_interna", _elenco(spariti), _elenco(nuovi_abitabili), None,
                 [f"Titolo ({nome_titolo}): {_elenco(spariti)}.", f"Rilievo: {_elenco(nuovi_abitabili)}."])
        nuovi_abitabili = []

    # 4. Quello che resta di nuovo e abitabile è un ampliamento
    if nuovi_abitabili:
        sup = _sup(nuovi_abitabili)
        aggiungi("ampliamento_senza_titolo", "", _elenco(nuovi_abitabili), f"+{_m2(sup)} di superficie utile",
                 [f"Rilievo: {_elenco(nuovi_abitabili)}, assenti dall'elaborato del {nome_titolo}."])

    # 5. Piscine non previste
    for l in [l for l in solo_rilievo if _piscina(l)]:
        aggiungi("piscina_senza_titolo", "", _m2(l.get("superficie_m2") or 0), _m2(l.get("superficie_m2") or 0),
                 [f"Rilievo: {l['nome']} di {_m2(l.get('superficie_m2') or 0)}, assente dall'elaborato del {nome_titolo}."])

    # 6. Tolleranza sulle superfici dei locali presenti in entrambi
    comuni = [n for n in legit if n in stato and _abitabile(legit[n]) and _abitabile(stato[n])]
    sup_titolo, sup_rilievo = _sup(legit[n] for n in comuni), _sup(stato[n] for n in comuni)
    verifiche = []
    if sup_titolo > 0 and sup_rilievo != sup_titolo:
        sup_unita = _sup(l for l in titolo["locali"] if _abitabile(l))
        tol = tolleranza(sup_unita, titolo.get("data"))
        delta = round(sup_rilievo - sup_titolo, 2)
        pct = delta / sup_titolo
        testo = f"Superficie utile rilevata {_m2(sup_rilievo)} contro {_m2(sup_titolo)} di progetto: {'+' if delta > 0 else ''}{_m2(delta)} ({_pct(pct)})."
        if abs(pct) <= tol:
            verifiche.append({
                "tipo": "tolleranza_costruttiva", "descrizione": testo,
                "valutazione": f"Entro la tolleranza del {tol:.0%} applicabile a un'unità di {_m2(sup_unita)}.",
                "riferimento_normativo": "art. 34-bis DPR 380/2001 come modificato dal DL 69/2024 (Salva Casa)",
                "fonti": [fonte_titolo.model_dump(), fonte_rilievo.model_dump()],
            })
        else:
            aggiungi("scostamento_oltre_tolleranza", f"{sup_titolo:.2f}", f"{sup_rilievo:.2f}",
                     f"{'+' if delta > 0 else ''}{_m2(delta)} ({_pct(pct)}), tolleranza {tol:.0%}", [testo])

    # 7. Catasto: la planimetria deve rappresentare lo stato di fatto, ma non rende legittimo nulla
    edilizi = [r for r in riscontri if r.ambito != "catastale"]
    if not plan.get("locali"):
        note.append("Planimetria catastale non disponibile o senza locali: verifica catastale non eseguita.")
    else:
        nomi_plan = {_nome(l["nome"]) for l in plan["locali"]}
        fonte_plan = Fonte(file=plan_f, pagina=1)
        quando = f"del {plan['data_dichiarazione'][:4]}" if plan.get("data_dichiarazione") else ""
        if nomi_plan != set(stato):
            mancanti = sorted(set(stato) - nomi_plan)
            in_piu = sorted(nomi_plan - set(stato))
            fatti = [f"Planimetria {quando}: {_elenco(plan['locali'])}.", f"Rilievo: {_elenco(rilievo['locali'])}."]
            r = Riscontro(
                tipo="planimetria_non_aggiornata", ambito="catastale",
                gravita="media" if edilizi else "bassa", fatti=fatti,
                segnaposti={"vecchio": quando, "nuovo": "; ".join(
                    ([f"nel rilievo ci sono anche {', '.join(stato[n]['nome'] for n in mancanti)}"] if mancanti else [])
                    + ([f"in planimetria c'è ancora {', '.join(n.capitalize() for n in in_piu)}"] if in_piu else []))},
                fonti=[fonte_plan, fonte_rilievo], articoli=list(CATALOGO["planimetria_non_aggiornata"].articoli),
            )
            riscontri.append(r)
        elif edilizi and nomi_plan != set(legit):
            riscontri.append(Riscontro(
                tipo="catasto_non_coerente_con_titolo", ambito="catastale", gravita="media",
                fatti=[f"Planimetria {quando}: {_elenco(plan['locali'])}.",
                       f"Titolo ({nome_titolo}): {_elenco(titolo['locali'])}."],
                segnaposti={"vecchio": nome_titolo, "nuovo": ", ".join(sorted(nomi_plan - set(legit)))},
                fonti=[fonte_plan, fonte_titolo], articoli=list(CATALOGO["catasto_non_coerente_con_titolo"].articoli),
            ))

    return EsitoConfronto(riscontri=riscontri, verifiche=verifiche, note=note)
