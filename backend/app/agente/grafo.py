"""
Il grafo dell'agente in LangGraph.

    estrai ─► controlla_documenti ─┬─► confronta ─┬─► cerca_norme ─► redigi ─► concludi
                                   │              └──────────(nessuna difformità)────────┘
                                   └──────────(documenti mancanti)──────────────────────► concludi

- estrai: legge ogni PDF con l'estrattore scelto (o riusa un'estrazione già fatta)
- controlla_documenti: senza titolo con locali e rilievo il confronto non si fa
- confronta: regole in codice, decide le difformità (confronto.py)
- cerca_norme: per ogni difformità cerca i passaggi normativi pertinenti (norme.py)
- redigi: il modello scrive descrizione e valutazione citando i passaggi (redazione.py)
- concludi: numera le difformità e calcola l'esito, che dipende solo dal confronto

La revisione umana resta nella pagina della pratica: il tecnico conferma o
scarta ogni difformità prima di esportare la relazione.
"""
import time
from pathlib import Path
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from models.pratica import Difformita

from .catalogo import esito
from .confronto import confronta
from .redazione import domanda, riferimento

PASSAGGI_PER_DIFFORMITA = 4


class Stato(TypedDict, total=False):
    cartella: str
    files: list[str]
    documenti: dict[str, dict]  # {file: {"tipo", "dati", "note"}}
    mancanti: list[str]
    riscontri: list[Any]
    verifiche: list[dict]
    passaggi: list[list[dict]]
    difformita: list[dict]
    esito: str
    sintesi: str
    note: list[str]
    passi: list[dict]  # traccia di cosa ha fatto l'agente, mostrata al tecnico


def _passo(stato: Stato, nome: str, inizio: float, dettaglio: str) -> list[dict]:
    return stato.get("passi", []) + [{"nodo": nome, "secondi": round(time.perf_counter() - inizio, 2), "dettaglio": dettaglio}]


def crea_grafo(estrattore, ricerca, redattore):
    """Compila il grafo con le dipendenze scelte: estrattore (estrazione/), ricerca (norme.py), redattore (redazione.py)."""

    def estrai(stato: Stato) -> Stato:
        inizio = time.perf_counter()
        if stato.get("documenti"):
            return {"passi": _passo(stato, "estrai", inizio, "riuso l'estrazione già fatta")}
        documenti = {}
        for f in stato["files"]:
            try:
                r = estrattore.estrai(Path(stato["cartella"]) / f)
                documenti[f] = {"tipo": r.tipo, "dati": r.dati, "note": r.note}
            except Exception as e:  # un documento illeggibile non deve fermare la verifica degli altri
                documenti[f] = {"tipo": None, "dati": {}, "note": [f"errore di estrazione: {e}"]}
        return {"documenti": documenti,
                "passi": _passo(stato, "estrai", inizio, f"{len(documenti)} documenti con {estrattore.nome}")}

    def controlla_documenti(stato: Stato) -> Stato:
        inizio = time.perf_counter()
        tipi = {f: d["tipo"] for f, d in stato["documenti"].items()}
        mancanti = []
        if not any(t == "titolo_edilizio" and stato["documenti"][f]["dati"].get("locali") for f, t in tipi.items()):
            mancanti.append("titolo edilizio con l'elaborato grafico dei locali")
        if not any(t == "rilievo" and stato["documenti"][f]["dati"].get("locali") for f, t in tipi.items()):
            mancanti.append("rilievo dello stato di fatto con i locali")
        if "planimetria" not in tipi.values():
            mancanti.append("planimetria catastale (solo la verifica catastale)")
        bloccanti = [m for m in mancanti if "solo la verifica" not in m]
        return {"mancanti": bloccanti, "passi": _passo(stato, "controlla_documenti", inizio,
                                                       "manca: " + "; ".join(mancanti) if mancanti else "documenti completi")}

    def confronta_documenti(stato: Stato) -> Stato:
        inizio = time.perf_counter()
        out = confronta(stato["documenti"])
        return {"riscontri": out.riscontri, "verifiche": out.verifiche, "note": out.note,
                "passi": _passo(stato, "confronta", inizio,
                                f"{len(out.riscontri)} difformità: " + ", ".join(r.tipo for r in out.riscontri)
                                if out.riscontri else "nessuna difformità")}

    def cerca_norme(stato: Stato) -> Stato:
        inizio = time.perf_counter()
        passaggi = [[p.come_dict() for p in ricerca.cerca(domanda(r), PASSAGGI_PER_DIFFORMITA)] for r in stato["riscontri"]]
        trovati = sum(len(p) for p in passaggi)
        return {"passaggi": passaggi,
                "passi": _passo(stato, "cerca_norme", inizio, f"{trovati} passaggi con la ricerca {ricerca.nome}")}

    def redigi(stato: Stato) -> Stato:
        from .norme import Passaggio

        inizio = time.perf_counter()
        difformita, note = [], list(stato.get("note", []))
        for i, (r, passaggi) in enumerate(zip(stato["riscontri"], stato["passaggi"]), 1):
            testo, avvisi = redattore.redigi(r, [Passaggio(**p) for p in passaggi])
            note += [f"D{i}: {a}" for a in avvisi]
            difformita.append(Difformita(
                id=f"D{i}", ambito=r.ambito, tipo=r.tipo, gravita=r.gravita, entita=r.entita,
                descrizione=testo.descrizione, valutazione=testo.valutazione,
                riferimento_normativo=riferimento(testo.articoli_citati), fonti=r.fonti,
                fonti_normative=[p for p in passaggi if p["id"] in testo.articoli_citati],
            ).model_dump())
        chi = f"{redattore.nome} ({redattore.modello})" if redattore.modello else redattore.nome
        return {"difformita": difformita, "note": note,
                "passi": _passo(stato, "redigi", inizio, f"{len(difformita)} testi con {chi}")}

    def concludi(stato: Stato) -> Stato:
        inizio = time.perf_counter()
        if stato.get("mancanti"):
            return {"esito": "documentazione_incompleta", "difformita": [], "verifiche": [],
                    "sintesi": "Verifica non eseguita: manca " + "; ".join(stato["mancanti"]) + ".",
                    "passi": _passo(stato, "concludi", inizio, "documentazione incompleta")}
        difformita = stato.get("difformita", [])
        risultato = esito([d["ambito"] for d in difformita])
        if difformita:
            elenco = "; ".join(f"{d['tipo'].replace('_', ' ')} ({d['ambito'].replace('_', ' ')}, gravità {d['gravita']})"
                               for d in difformita)
            sintesi = f"L'agente ha trovato {len(difformita)} difformità: {elenco}."
        else:
            sintesi = "L'agente non ha trovato difformità tra titolo, catasto e stato di fatto."
        return {"esito": risultato, "difformita": difformita, "sintesi": sintesi,
                "passi": _passo(stato, "concludi", inizio, risultato)}

    g = StateGraph(Stato)
    for nome, fn in [("estrai", estrai), ("controlla_documenti", controlla_documenti), ("confronta", confronta_documenti),
                     ("cerca_norme", cerca_norme), ("redigi", redigi), ("concludi", concludi)]:
        g.add_node(nome, fn)
    g.add_edge(START, "estrai")
    g.add_edge("estrai", "controlla_documenti")
    g.add_conditional_edges("controlla_documenti", lambda s: "concludi" if s.get("mancanti") else "confronta",
                            ["confronta", "concludi"])
    g.add_conditional_edges("confronta", lambda s: "cerca_norme" if s.get("riscontri") else "concludi",
                            ["cerca_norme", "concludi"])
    g.add_edge("cerca_norme", "redigi")
    g.add_edge("redigi", "concludi")
    g.add_edge("concludi", END)
    return g.compile()
