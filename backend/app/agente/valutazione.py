"""
Valutazione dell'agente sulle difformità attese dei ground_truth.json.

Per ogni pratica confronta le difformità trovate con quelle attese, per tipo:
- precisione: quante difformità trovate sono vere (le false costano tempo al tecnico)
- richiamo: quante difformità attese sono state trovate (quelle perse sono il rischio vero)
- esito, ambito e gravità corretti
- articoli: quanti articoli del riferimento atteso compaiono in quello dell'agente
- ricerca: quanti articoli previsti per il tipo sono tra i passaggi trovati (qualità del RAG)
"""
import re


def articoli(riferimento: str) -> set[str]:
    """'art. 23-ter e art. 36-bis DPR 380/2001; DM 5/7/1975' -> {'23-ter', '36-bis', 'DM 5/7/1975'}"""
    trovati = set(re.findall(r"art\.\s*(\d+(?:-[a-z]+)?)", riferimento))
    trovati |= set(re.findall(r"DM \d+/\d+/\d+", riferimento))
    return trovati


def valuta_pratica(gt: dict, out: dict) -> dict:
    attese = list(gt["difformita_attese"])
    trovate = list(out.get("difformita", []))
    coppie, perse = [], []
    for a in attese:
        t = next((t for t in trovate if t["tipo"] == a["tipo"]), None)
        if t:
            trovate.remove(t)
            coppie.append((a, t))
        else:
            perse.append(a)
    passaggi = {r.tipo: {p["id"] for p in ps} for r, ps in zip(out.get("riscontri", []), out.get("passaggi", []))}
    previsti = {r.tipo: r.articoli for r in out.get("riscontri", [])}
    art_attesi = art_ok = cerca_attesi = cerca_ok = 0
    for a, t in coppie:
        atteso = articoli(a["riferimento_normativo"])
        art_attesi += len(atteso)
        art_ok += len(atteso & articoli(t["riferimento_normativo"]))
        cerca_attesi += len(previsti.get(t["tipo"], []))
        cerca_ok += len(set(previsti.get(t["tipo"], [])) & passaggi.get(t["tipo"], set()))
    verifiche_attese = {v["tipo"] for v in gt.get("verifiche_attese", [])}
    return {
        "pratica": gt["id"],
        "esito_atteso": gt["esito_atteso"], "esito": out.get("esito"), "esito_ok": out.get("esito") == gt["esito_atteso"],
        "attese": [a["tipo"] for a in attese], "trovate": [t["tipo"] for t in out.get("difformita", [])],
        "vere": len(coppie), "false": len(trovate), "perse": len(perse),
        "false_tipi": [t["tipo"] for t in trovate], "perse_tipi": [a["tipo"] for a in perse],
        "ambito_ok": sum(a["ambito"] == t["ambito"] for a, t in coppie),
        "gravita_ok": sum(a["gravita"] == t["gravita"] for a, t in coppie),
        "articoli_ok": art_ok, "articoli_attesi": art_attesi,
        "ricerca_ok": cerca_ok, "ricerca_attesi": cerca_attesi,
        "verifiche_ok": len(verifiche_attese & {v["tipo"] for v in out.get("verifiche", [])}),
        "verifiche_attese": len(verifiche_attese),
    }


def riepilogo(righe: list[dict]) -> dict:
    s = lambda k: sum(r[k] for r in righe)  # noqa: E731
    vere, false, perse = s("vere"), s("false"), s("perse")
    q = lambda a, b: round(a / b, 3) if b else None  # noqa: E731
    return {
        "pratiche": len(righe), "esiti_corretti": s("esito_ok"),
        "difformita_attese": vere + perse, "vere": vere, "false": false, "perse": perse,
        "precisione": q(vere, vere + false), "richiamo": q(vere, vere + perse),
        "ambito_ok": q(s("ambito_ok"), vere), "gravita_ok": q(s("gravita_ok"), vere),
        "articoli": q(s("articoli_ok"), s("articoli_attesi")), "ricerca": q(s("ricerca_ok"), s("ricerca_attesi")),
        "verifiche": f"{s('verifiche_ok')}/{s('verifiche_attese')}",
    }
