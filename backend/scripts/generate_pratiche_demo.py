"""
Genera 5 pratiche edilizie FITTIZIE per la demo di verifica dello stato legittimo.

Ogni pratica contiene i documenti che un geometra confronta a mano
(titolo edilizio con tavola di progetto, eventuale titolo successivo,
visura e planimetria catastale, rilievo dello stato di fatto) e un file
ground_truth.json con le difformità inserite apposta. Il ground truth serve
sia per la demo sia come golden set per valutare estrazione e agente.

Tutti i dati sono inventati: comune, persone, protocolli e immobili.
Ogni pagina porta la filigrana "DATI FITTIZI".

Uso:
    python backend/scripts/generate_pratiche_demo.py [cartella_output]
"""
import json
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas

COMUNE = "Comune di Villanova Marina"
PROVINCIA = "Provincia di Cagliari (comune fittizio)"
CATASTO = "Agenzia delle Entrate - Ufficio Provinciale Territorio (simulazione)"
WATERMARK = "DATI FITTIZI - DEMO InsightPA"
W, H = A4


# ---------------------------------------------------------------------------
# Primitive di disegno
# ---------------------------------------------------------------------------

def new_page(c: canvas.Canvas, ente: str, sottotitolo: str):
    c.saveState()
    c.setFont("Helvetica-Bold", 44)
    c.setFillColor(colors.Color(0.85, 0.85, 0.85, alpha=0.35))
    c.translate(W / 2, H / 2)
    c.rotate(35)
    c.drawCentredString(0, 0, WATERMARK)
    c.restoreState()

    c.setStrokeColor(colors.HexColor("#1d3d5c"))
    c.circle(2.4 * cm, H - 2.1 * cm, 0.8 * cm)
    c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(2.4 * cm, H - 2.2 * cm, "STEMMA")
    c.setFillColor(colors.HexColor("#1d3d5c"))
    c.setFont("Helvetica-Bold", 13)
    c.drawString(3.6 * cm, H - 1.8 * cm, ente)
    c.setFont("Helvetica", 9)
    c.drawString(3.6 * cm, H - 2.35 * cm, sottotitolo)
    c.line(1.5 * cm, H - 3.1 * cm, W - 1.5 * cm, H - 3.1 * cm)
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 7)
    c.drawCentredString(W / 2, 1 * cm, WATERMARK + " - nessun riferimento a persone o immobili reali")
    return H - 4 * cm


def text(c, y, s, size=10, bold=False, x=2 * cm, width=None):
    width = width or (W - x - 2 * cm)
    font = "Helvetica-Bold" if bold else "Helvetica"
    c.setFont(font, size)
    for line in simpleSplit(s, font, size, width):
        c.drawString(x, y, line)
        y -= size * 1.35
    return y - 2


def table(c, y, headers, rows, col_w, x=2 * cm, size=9):
    c.setFont("Helvetica-Bold", size)
    cx = x
    for h, w in zip(headers, col_w):
        c.drawString(cx + 2, y, h)
        cx += w
    y -= 4
    c.line(x, y, x + sum(col_w), y)
    y -= size * 1.4
    c.setFont("Helvetica", size)
    for r in rows:
        cx = x
        for v, w in zip(r, col_w):
            c.drawString(cx + 2, y, str(v))
            cx += w
        y -= size * 1.5
    c.line(x, y + size, x + sum(col_w), y + size)
    return y - 6


def fmt(v: float) -> str:
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def area(r) -> float:
    return round(r.get("area", r["w"] * r["h"]), 2)


def draw_plan(c, rooms, titolo, y_top, scala=100, note=None):
    """Pianta con un rettangolo per locale. 1 m = (100/scala) cm sulla carta."""
    k = cm * 100 / scala
    max_x = max(r["x"] + r["w"] for r in rooms)
    max_y = max(r["y"] + r["h"] for r in rooms)
    ox = (W - max_x * k) / 2
    oy = y_top - 1.2 * cm - max_y * k

    c.setFont("Helvetica-Bold", 11)
    c.drawString(2 * cm, y_top, titolo)
    c.setFont("Helvetica", 8)
    c.drawString(2 * cm, y_top - 0.45 * cm, f"Scala 1:{scala} - misure in metri, superfici utili nette")

    for r in rooms:
        g = r.get("draw", r)  # geometria disegnata (le quote rilevate possono differire di pochi cm)
        x, y = ox + g["x"] * k, oy + (max_y - g["y"] - g["h"]) * k
        kind = r.get("kind", "vano")
        c.setLineWidth(0.6 if kind != "vano" else 1.4)
        if kind in ("balcone", "portico"):
            c.setDash(4, 3)
        elif kind == "piscina":
            c.setFillColor(colors.HexColor("#d7ebf5"))
            c.rect(x, y, g["w"] * k, g["h"] * k, stroke=0, fill=1)
            c.setFillColor(colors.black)
        c.rect(x, y, g["w"] * k, g["h"] * k)
        c.setDash()
        cx, cy = x + g["w"] * k / 2, y + g["h"] * k / 2
        lato = min(g["w"], g["h"]) * k  # lato minore sulla carta
        fs = 8 if lato >= 2.2 * cm else 7 if lato >= 1.6 * cm else 5.5
        c.setFont("Helvetica-Bold", fs)
        c.drawCentredString(cx, cy + 2, r["nome"].upper())
        c.setFont("Helvetica", fs)
        c.drawCentredString(cx, cy - fs, f"{fmt(area(r))} m²")

    # scala grafica e nord
    c.setLineWidth(1)
    c.line(ox, oy - 0.8 * cm, ox + 5 * k, oy - 0.8 * cm)
    for i in range(6):
        c.line(ox + i * k, oy - 0.9 * cm, ox + i * k, oy - 0.7 * cm)
    c.setFont("Helvetica", 7)
    c.drawString(ox + 5 * k + 4, oy - 0.85 * cm, "5 m")
    nx = W - 2.5 * cm
    c.line(nx, y_top - 1.8 * cm, nx, y_top - 0.8 * cm)
    c.drawCentredString(nx, y_top - 0.7 * cm, "N")
    y = oy - 1.6 * cm
    if note:
        y = text(c, y, note, size=8)
    return y


def rooms_table(c, y, rooms):
    rows = [
        (r["nome"], r.get("dest", "residenziale"), f"{fmt(r['w'])} x {fmt(r['h'])}", fmt(area(r)))
        for r in rooms
    ]
    sup_utile = sum(area(r) for r in rooms if r.get("kind", "vano") == "vano")
    y = table(c, y, ["Locale", "Destinazione", "Dimensioni (m)", "Sup. (m²)"], rows,
              [4.5 * cm, 4.5 * cm, 4 * cm, 3 * cm])
    return text(c, y, f"Superficie utile totale (esclusi balconi, portici e piscine): {fmt(sup_utile)} m²", bold=True)


def signature(c, y, ruolo, nome):
    c.setFont("Helvetica", 9)
    c.drawString(W - 8 * cm, y, ruolo)
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(W - 8 * cm, y - 0.5 * cm, nome)
    c.line(W - 8 * cm, y - 0.7 * cm, W - 2.5 * cm, y - 0.7 * cm)


# ---------------------------------------------------------------------------
# Documenti
# ---------------------------------------------------------------------------

def doc_titolo(path, p, t):
    c = canvas.Canvas(str(path), pagesize=A4)
    y = new_page(c, COMUNE, "Area Tecnica - Servizio Edilizia Privata - " + PROVINCIA)
    y = text(c, y, t["tipo_esteso"].upper(), 14, bold=True)
    y = text(c, y, f"N. {t['numero']} del {t['data']} - Prot. {t['protocollo']}", 10)
    y -= 8
    y = text(c, y, "IL DIRIGENTE", 10, bold=True)
    y = text(c, y, f"Vista la domanda presentata in data {t['data_domanda']} da {p['intestatario']}, "
                   f"codice fiscale {p['cf']}, intesa ad ottenere il titolo per: {t['oggetto']};")
    y = text(c, y, "Visti gli elaborati progettuali a firma del tecnico incaricato, allegati quale parte "
                   "integrante del presente provvedimento;")
    y = text(c, y, "Visto il parere favorevole della Commissione Edilizia e verificata la conformità "
                   "urbanistica dell'intervento;")
    y -= 4
    y = text(c, y, "RILASCIA", 11, bold=True)
    y = text(c, y, f"a {p['intestatario']} il titolo in oggetto per l'immobile sito in {p['indirizzo']}, "
                   f"distinto in catasto al Foglio {p['foglio']}, Particella {p['particella']}"
                   f"{', Sub. ' + p['sub'] if p.get('sub') else ''}.")
    y -= 4
    y = text(c, y, "Dati dell'intervento autorizzato", 10, bold=True)
    y = table(c, y, ["Parametro", "Valore"], [
        ("Destinazione d'uso", t["destinazione"]),
        ("Superficie utile residenziale", f"{fmt(t['sup_utile'])} m²"),
        ("Superficie non residenziale", f"{fmt(t.get('sup_non_res', 0))} m²"),
        ("Volume", f"{fmt(t['volume'])} m³"),
        ("Altezza interna", t["altezza"]),
    ], [7 * cm, 8 * cm])
    for pr in t.get("prescrizioni", []):
        y = text(c, y, "- " + pr, 9)
    signature(c, 5 * cm, "Il Dirigente dell'Area Tecnica", "Ing. Dirigente Fittizio")
    c.showPage()

    y = new_page(c, COMUNE, f"Allegato al titolo n. {t['numero']} - Elaborato grafico approvato")
    y = draw_plan(c, t["rooms"], t["tavola"], y, scala=t.get("scala", 100))
    rooms_table(c, y, t["rooms"])
    c.showPage()
    c.save()


def doc_titolo_successivo(path, p, s):
    c = canvas.Canvas(str(path), pagesize=A4)
    y = new_page(c, COMUNE, "Sportello Unico per l'Edilizia - " + PROVINCIA)
    y = text(c, y, s["tipo_esteso"].upper(), 14, bold=True)
    y = text(c, y, f"Prot. {s['protocollo']} del {s['data']}", 10)
    y -= 8
    y = text(c, y, f"Il sottoscritto {p['intestatario']}, in qualità di proprietario dell'immobile sito in "
                   f"{p['indirizzo']} (Foglio {p['foglio']}, Particella {p['particella']}"
                   f"{', Sub. ' + p['sub'] if p.get('sub') else ''}),")
    y = text(c, y, "COMUNICA", 11, bold=True)
    y = text(c, y, f"l'inizio dei lavori per: {s['oggetto']}.")
    y = text(c, y, f"Stato legittimo di riferimento: {s['stato_legittimo']}.")
    y = text(c, y, f"Tecnico asseverante: {s['tecnico']}. Data fine lavori comunicata: {s['fine_lavori']}.")
    y = text(c, y, s.get("nota_catasto", ""), 9)
    y -= 6
    y = draw_plan(c, s["rooms"], "Stato di progetto", y)
    rooms_table(c, y, s["rooms"])
    c.showPage()
    c.save()


def doc_visura(path, p, v):
    c = canvas.Canvas(str(path), pagesize=A4)
    y = new_page(c, CATASTO, "Visura per immobile - Catasto Fabbricati")
    y = text(c, y, f"Data: {v['data_visura']} - Comune di VILLANOVA MARINA (codice fittizio Z999)", 9)
    y -= 6
    y = text(c, y, "Unità immobiliare", 11, bold=True)
    y = table(c, y, ["Foglio", "Particella", "Sub", "Categoria", "Classe", "Consistenza", "Sup. catastale", "Rendita"], [
        (p["foglio"], p["particella"], p.get("sub", "-"), v["categoria"], v["classe"],
         v["consistenza"], f"{v['sup_catastale']} m²", f"Euro {v['rendita']}"),
    ], [1.4 * cm, 1.8 * cm, 1.1 * cm, 1.9 * cm, 1.4 * cm, 2.2 * cm, 2.6 * cm, 2.6 * cm], size=8)
    y = text(c, y, f"Indirizzo: {p['indirizzo'].upper()}", 9)
    y -= 6
    y = text(c, y, "Intestati", 11, bold=True)
    y = text(c, y, f"{p['intestatario'].upper()} - CF {p['cf']} - Proprietà 1/1", 9)
    y -= 6
    y = text(c, y, "Dati derivanti da", 11, bold=True)
    for d in v["storia"]:
        y = text(c, y, "- " + d, 9)
    c.showPage()
    c.save()


def doc_planimetria(path, p, pl):
    c = canvas.Canvas(str(path), pagesize=A4)
    y = new_page(c, CATASTO, "Planimetria di u.i.u. in Comune di Villanova Marina")
    y = text(c, y, f"Dichiarazione protocollo n. {pl['protocollo']} del {pl['data']} - "
                   f"Foglio {p['foglio']} Particella {p['particella']}"
                   f"{' Sub. ' + p['sub'] if p.get('sub') else ''}", 9)
    y = text(c, y, f"{p['indirizzo']} - Piano {p['piano']}", 9)
    draw_plan(c, pl["rooms"], "Planimetria catastale", y - 0.3 * cm, scala=pl.get("scala", 100),
              note="Nota: le superfici sono ricavate dal disegno a fini dimostrativi; "
                   "la planimetria catastale ha valore fiscale e non costituisce titolo edilizio.")
    c.showPage()
    c.save()


def doc_rilievo(path, p, r):
    c = canvas.Canvas(str(path), pagesize=A4)
    y = new_page(c, "Studio Tecnico Demo - Geom. Tecnico Fittizio", "Rilievo dello stato di fatto")
    y = text(c, y, "RELAZIONE DI RILIEVO DELLO STATO DI FATTO", 13, bold=True)
    y = text(c, y, f"Immobile: {p['indirizzo']}, piano {p['piano']} - "
                   f"Foglio {p['foglio']} Part. {p['particella']}"
                   f"{' Sub. ' + p['sub'] if p.get('sub') else ''}", 9)
    y = text(c, y, f"Sopralluogo del {r['data']} - strumento: distanziometro laser, "
                   f"altezza interna misurata {r['altezza']}.", 9)
    for n in r["osservazioni"]:
        y = text(c, y, "- " + n, 9)
    y -= 4
    y = draw_plan(c, r["rooms"], "Stato di fatto rilevato", y, scala=r.get("scala", 100))
    rooms_table(c, y, r["rooms"])
    signature(c, 3 * cm, "Il tecnico rilevatore", "Geom. Tecnico Fittizio")
    c.showPage()
    c.save()


# ---------------------------------------------------------------------------
# Scenari
# ---------------------------------------------------------------------------

def R(nome, x, y, w, h, dest="residenziale", kind="vano", **kw):
    return {"nome": nome, "x": x, "y": y, "w": w, "h": h, "dest": dest, "kind": kind, **kw}


APP_BASE = [
    R("Ingresso", 0, 0, 2, 2.5),
    R("Soggiorno", 2, 0, 5, 4.4),
    R("Cucina", 7, 0, 3, 4.4),
    R("Disimpegno", 0, 2.5, 2, 1.9),
    R("Camera", 0, 4.4, 4, 3.6),
    R("Camera 2", 4, 4.4, 3.2, 3.6),
    R("Bagno", 7.2, 4.4, 2.8, 2.4),
    R("Ripostiglio", 7.2, 6.8, 2.8, 1.2),
]


def with_changes(rooms, changes=None, remove=(), add=()):
    out = []
    for r in rooms:
        if r["nome"] in remove:
            continue
        r = dict(r)
        r.update((changes or {}).get(r["nome"], {}))
        out.append(r)
    return out + list(add)


def sup(rooms):
    return round(sum(area(r) for r in rooms if r.get("kind", "vano") == "vano"), 2)


def pratica_001():
    """Conforme: scostamento di superficie entro la tolleranza del Salva Casa."""
    p = dict(id="P-001", indirizzo="Via dei Gerani 14, int. 5", piano="2",
             intestatario="Laura Demo", cf="DMELRA70A41Z999X", foglio="12", particella="845", sub="9")
    progetto = APP_BASE
    rilievo = with_changes(APP_BASE, {
        "Soggiorno": {"w": 5.35, "h": 4.45, "draw": {"x": 2, "y": 0, "w": 5, "h": 4.4}},
        "Bagno": {"w": 2.80, "h": 2.45, "draw": {"x": 7.2, "y": 4.4, "w": 2.8, "h": 2.4}},
    })
    delta = round(sup(rilievo) - sup(progetto), 2)
    delta_pct = round(delta / sup(progetto) * 100, 2)
    docs = {
        "01_concessione_edilizia.pdf": (doc_titolo, dict(
            tipo_esteso="Concessione edilizia", numero="87/1987", data="14/05/1987", data_domanda="02/02/1987",
            protocollo="4412", oggetto="nuova costruzione di edificio residenziale di 4 piani, 12 alloggi",
            destinazione="Residenziale", sup_utile=sup(progetto), volume=round(sup(progetto) * 2.7, 2),
            altezza="2,70 m", tavola="Tavola 4 - Pianta piano secondo, alloggio int. 5", rooms=progetto)),
        "02_visura_catastale.pdf": (doc_visura, dict(
            data_visura="10/09/2026", categoria="A/2", classe="3", consistenza="5 vani", sup_catastale=86,
            rendita="490,63", storia=["Costituzione del 20/09/1989 prot. 8801 - planimetria in atti"])),
        "03_planimetria_catastale.pdf": (doc_planimetria, dict(
            protocollo="8801", data="20/09/1989", rooms=progetto)),
        "04_rilievo_stato_di_fatto.pdf": (doc_rilievo, dict(
            data="05/09/2026", altezza="2,70 m", rooms=rilievo,
            osservazioni=["Distribuzione interna conforme al progetto.",
                          "Soggiorno e bagno con dimensioni leggermente maggiori rispetto alla tavola.",
                          "Nessun intervento recente rilevato; finiture originali anni '80."])),
    }
    gt = dict(
        esito_atteso="conforme",
        sintesi="Stato di fatto conforme al titolo. Lo scostamento di superficie rientra nella tolleranza costruttiva.",
        difformita_attese=[],
        verifiche_attese=[dict(
            tipo="tolleranza_costruttiva",
            descrizione=f"Superficie utile rilevata {fmt(sup(rilievo))} m² contro {fmt(sup(progetto))} m² "
                        f"di progetto: +{fmt(delta)} m² (+{fmt(delta_pct)}%).",
            valutazione="Entro la tolleranza del 5% prevista per unità tra 60 e 100 m² per interventi "
                        "realizzati entro il 24/05/2024. Con la sola soglia del 2% sarebbe stata una difformità.",
            riferimento_normativo="art. 34-bis DPR 380/2001 come modificato dal DL 69/2024 (Salva Casa)",
            fonti=[dict(file="01_concessione_edilizia.pdf", pagina=2),
                   dict(file="04_rilievo_stato_di_fatto.pdf", pagina=1)],
        )],
        dati_estratti_attesi={
            "01_concessione_edilizia.pdf": dict(tipo="concessione edilizia", numero="87/1987", data="1987-05-14",
                                                sup_utile_m2=sup(progetto), destinazione="residenziale"),
            "02_visura_catastale.pdf": dict(categoria="A/2", classe="3", consistenza_vani=5, sup_catastale_m2=86),
            "04_rilievo_stato_di_fatto.pdf": dict(sup_utile_m2=sup(rilievo)),
        },
    )
    return p, docs, gt


def pratica_002():
    """Veranda: balcone chiuso senza titolo, planimetria catastale non aggiornata."""
    p = dict(id="P-002", indirizzo="Viale del Faro 112, int. 9", piano="3",
             intestatario="Paolo Esempio", cf="SMPPLA62C12Z999K", foglio="7", particella="301", sub="14")
    balcone = R("Balcone", 2, 8, 5, 1.6, dest="non residenziale", kind="balcone")
    progetto = APP_BASE + [balcone]
    veranda = R("Veranda", 2, 8, 5, 1.6, dest="residenziale (di fatto)")
    rilievo = APP_BASE + [veranda]
    docs = {
        "01_licenza_edilizia.pdf": (doc_titolo, dict(
            tipo_esteso="Licenza edilizia", numero="212/1979", data="03/10/1979", data_domanda="11/06/1979",
            protocollo="10233", oggetto="costruzione di fabbricato residenziale di 5 piani",
            destinazione="Residenziale", sup_utile=sup(progetto), sup_non_res=area(balcone),
            volume=round(sup(progetto) * 2.75, 2), altezza="2,75 m",
            tavola="Tavola 5 - Pianta piano terzo, alloggio int. 9", rooms=progetto)),
        "02_visura_catastale.pdf": (doc_visura, dict(
            data_visura="12/09/2026", categoria="A/2", classe="2", consistenza="5,5 vani", sup_catastale=88,
            rendita="468,68", storia=["Costituzione del 15/03/1981 prot. 1190 - planimetria in atti"])),
        "03_planimetria_catastale.pdf": (doc_planimetria, dict(protocollo="1190", data="15/03/1981", rooms=progetto)),
        "04_rilievo_stato_di_fatto.pdf": (doc_rilievo, dict(
            data="08/09/2026", altezza="2,75 m", rooms=rilievo,
            osservazioni=["Il balcone lato sud risulta chiuso con infissi fissi in alluminio e tamponamento "
                          "opaco nella parte bassa; il locale è arredato come zona pranzo.",
                          "La chiusura non è amovibile e non è interamente trasparente.",
                          "Il proprietario riferisce che la chiusura è stata realizzata nel 2004."])),
    }
    gt = dict(
        esito_atteso="non_conforme",
        sintesi="Balcone chiuso a veranda senza titolo: aumento di superficie utile e volume. "
                "La planimetria catastale non rappresenta lo stato di fatto.",
        difformita_attese=[
            dict(id="D1", ambito="edilizio", tipo="chiusura_balcone_veranda", gravita="media",
                 entita=f"+{fmt(area(balcone))} m² di superficie utile, circa {fmt(area(balcone) * 2.75)} m³",
                 descrizione="Il balcone approvato come superficie non residenziale è chiuso con infissi fissi "
                             "e usato come locale abitabile, senza alcun titolo edilizio.",
                 valutazione="Non rientra in tolleranza né nell'edilizia libera: la chiusura non è una vetrata "
                             "panoramica amovibile e trasparente. Da valutare la sanatoria.",
                 riferimento_normativo="art. 6 c.1 lett. b-bis e art. 36-bis DPR 380/2001",
                 fonti=[dict(file="01_licenza_edilizia.pdf", pagina=2),
                        dict(file="04_rilievo_stato_di_fatto.pdf", pagina=1)]),
            dict(id="D2", ambito="catastale", tipo="planimetria_non_aggiornata", gravita="media",
                 descrizione="La planimetria catastale del 1981 riporta il balcone aperto, non la veranda.",
                 valutazione="Dopo l'eventuale sanatoria serve una variazione DOCFA prima dell'atto di vendita.",
                 riferimento_normativo="art. 29 c.1-bis L. 52/1985",
                 fonti=[dict(file="03_planimetria_catastale.pdf", pagina=1),
                        dict(file="04_rilievo_stato_di_fatto.pdf", pagina=1)]),
        ],
        dati_estratti_attesi={
            "01_licenza_edilizia.pdf": dict(tipo="licenza edilizia", numero="212/1979", data="1979-10-03",
                                            sup_utile_m2=sup(progetto), sup_non_residenziale_m2=area(balcone)),
            "02_visura_catastale.pdf": dict(categoria="A/2", classe="2", consistenza_vani=5.5, sup_catastale_m2=88),
            "04_rilievo_stato_di_fatto.pdf": dict(sup_utile_m2=sup(rilievo)),
        },
    )
    return p, docs, gt


def pratica_003():
    """Sottotetto non abitabile trasformato in camera e bagno; catasto aggiornato senza titolo."""
    p = dict(id="P-003", indirizzo="Via Sassari 7", piano="sottotetto",
             intestatario="Giulia Prova", cf="PRVGLI80M50Z999T", foglio="15", particella="1022", sub="3")
    progetto = [R("Locale di sgombero", 0, 0, 6, 5.2, dest="accessorio non abitabile"),
                R("Ripostiglio", 6, 0, 2.5, 2.4, dest="accessorio non abitabile"),
                R("Vano scala", 6, 2.4, 2.5, 2.8, dest="collegamento")]
    rilievo = [R("Camera", 0, 0, 4.2, 5.2, dest="residenziale"),
               R("Bagno", 4.2, 0, 1.8, 2.9, dest="residenziale"),
               R("Disimpegno", 4.2, 2.9, 1.8, 2.3, dest="residenziale"),
               R("Ripostiglio", 6, 0, 2.5, 2.4, dest="accessorio"),
               R("Vano scala", 6, 2.4, 2.5, 2.8, dest="collegamento")]
    docs = {
        "01_permesso_di_costruire.pdf": (doc_titolo, dict(
            tipo_esteso="Permesso di costruire", numero="45/2001", data="22/03/2001", data_domanda="15/11/2000",
            protocollo="3350", oggetto="nuova costruzione di villetta bifamiliare su due livelli con sottotetto",
            destinazione="Residenziale (piano primo); sottotetto accessorio non abitabile",
            sup_utile=0.0, sup_non_res=sup(progetto), volume=round(sup(progetto) * 1.95, 2),
            altezza="sottotetto: altezza media 1,95 m, minima 1,10 m",
            prescrizioni=["Il sottotetto non potrà essere destinato a uso abitativo.",
                          "Non sono ammessi servizi igienici al piano sottotetto."],
            tavola="Tavola 3 - Pianta piano sottotetto", rooms=progetto)),
        "02_visura_catastale.pdf": (doc_visura, dict(
            data_visura="11/09/2026", categoria="A/7", classe="2", consistenza="7 vani", sup_catastale=141,
            rendita="867,65", storia=["Costituzione del 18/06/2003 prot. 5520",
                                      "Variazione del 09/02/2016 prot. 2210 - diversa distribuzione degli spazi "
                                      "interni, planimetria in atti"])),
        "03_planimetria_catastale.pdf": (doc_planimetria, dict(protocollo="2210", data="09/02/2016", rooms=rilievo)),
        "04_rilievo_stato_di_fatto.pdf": (doc_rilievo, dict(
            data="09/09/2026", altezza="media 1,95 m, minima 1,10 m", rooms=rilievo,
            osservazioni=["Il sottotetto è suddiviso in camera da letto, bagno completo e disimpegno.",
                          "Presenti impianto di riscaldamento e finiture da abitazione.",
                          "Non è stato reperito alcun titolo edilizio successivo al permesso 45/2001."])),
    }
    gt = dict(
        esito_atteso="non_conforme",
        sintesi="Sottotetto accessorio trasformato in camera e bagno senza titolo. La planimetria catastale "
                "del 2016 riporta lo stato di fatto ma non lo rende legittimo.",
        difformita_attese=[
            dict(id="D1", ambito="edilizio", tipo="mutamento_destinazione_uso", gravita="alta",
                 entita=f"{fmt(sup(rilievo[:3]))} m² da accessorio non abitabile a residenziale",
                 descrizione="Il permesso autorizza il sottotetto come locale di sgombero non abitabile e vieta "
                             "servizi igienici; oggi contiene camera, bagno e disimpegno.",
                 valutazione="Altezza media 1,95 m inferiore ai requisiti per locali abitabili: "
                             "difficilmente sanabile come abitazione, probabile ripristino dell'uso accessorio.",
                 riferimento_normativo="art. 23-ter e art. 36-bis DPR 380/2001; DM 5/7/1975",
                 fonti=[dict(file="01_permesso_di_costruire.pdf", pagina=1),
                        dict(file="01_permesso_di_costruire.pdf", pagina=2),
                        dict(file="04_rilievo_stato_di_fatto.pdf", pagina=1)]),
            dict(id="D2", ambito="catastale", tipo="catasto_non_coerente_con_titolo", gravita="media",
                 descrizione="La variazione catastale del 2016 rappresenta camera e bagno, "
                             "ma non esiste un titolo edilizio corrispondente.",
                 valutazione="La planimetria catastale non costituisce titolo e non prova lo stato legittimo; "
                             "va allineata dopo la regolarizzazione edilizia.",
                 riferimento_normativo="art. 9-bis c.1-bis DPR 380/2001",
                 fonti=[dict(file="02_visura_catastale.pdf", pagina=1),
                        dict(file="03_planimetria_catastale.pdf", pagina=1)]),
        ],
        dati_estratti_attesi={
            "01_permesso_di_costruire.pdf": dict(tipo="permesso di costruire", numero="45/2001", data="2001-03-22",
                                                 destinazione_sottotetto="accessorio non abitabile",
                                                 altezza_media_m=1.95),
            "02_visura_catastale.pdf": dict(categoria="A/7", classe="2", consistenza_vani=7, sup_catastale_m2=141),
            "04_rilievo_stato_di_fatto.pdf": dict(locali_abitativi=["Camera", "Bagno", "Disimpegno"]),
        },
    )
    return p, docs, gt


def pratica_004():
    """Edilizio conforme grazie a una CILA; planimetria catastale mai aggiornata."""
    p = dict(id="P-004", indirizzo="Via Roma 45, int. 3", piano="1",
             intestatario="Marco Campione", cf="CMPMRC75D10Z999W", foglio="9", particella="512", sub="6")
    progetto = APP_BASE
    open_space = R("Soggiorno-cucina", 2, 0, 8, 4.4)
    cila = with_changes(APP_BASE, remove=("Soggiorno", "Cucina"), add=[open_space])
    docs = {
        "01_concessione_edilizia.pdf": (doc_titolo, dict(
            tipo_esteso="Concessione edilizia", numero="130/1985", data="19/07/1985", data_domanda="04/03/1985",
            protocollo="7719", oggetto="nuova costruzione di edificio residenziale di 3 piani, 6 alloggi",
            destinazione="Residenziale", sup_utile=sup(progetto), volume=round(sup(progetto) * 2.7, 2),
            altezza="2,70 m", tavola="Tavola 3 - Pianta piano primo, alloggio int. 3", rooms=progetto)),
        "02_cila_2019.pdf": (doc_titolo_successivo, dict(
            tipo_esteso="Comunicazione di inizio lavori asseverata (CILA)", protocollo="15872", data="06/05/2019",
            oggetto="demolizione del tramezzo tra cucina e soggiorno e rifacimento del bagno",
            stato_legittimo="Concessione edilizia n. 130/1985", tecnico="Arch. Progettista Fittizio",
            fine_lavori="20/09/2019",
            nota_catasto="Nella comunicazione di fine lavori non risulta allegata la ricevuta di variazione catastale.",
            rooms=cila)),
        "03_visura_catastale.pdf": (doc_visura, dict(
            data_visura="10/09/2026", categoria="A/2", classe="3", consistenza="5 vani", sup_catastale=86,
            rendita="490,63", storia=["Costituzione del 02/04/1986 prot. 3104 - planimetria in atti"])),
        "04_planimetria_catastale.pdf": (doc_planimetria, dict(protocollo="3104", data="02/04/1986", rooms=progetto)),
        "05_rilievo_stato_di_fatto.pdf": (doc_rilievo, dict(
            data="06/09/2026", altezza="2,70 m", rooms=cila,
            osservazioni=["Cucina e soggiorno formano un unico ambiente open space.",
                          "Bagno con finiture recenti.",
                          "Stato di fatto corrispondente agli elaborati della CILA 2019."])),
    }
    gt = dict(
        esito_atteso="conforme_edilizio_non_conforme_catastale",
        sintesi="Lo stato di fatto è legittimato dalla CILA 2019. La planimetria catastale del 1986 "
                "mostra ancora cucina e soggiorno separati: serve una variazione DOCFA prima del rogito.",
        difformita_attese=[
            dict(id="D1", ambito="catastale", tipo="planimetria_non_aggiornata", gravita="bassa",
                 descrizione="La planimetria catastale non riporta la demolizione del tramezzo eseguita con CILA 2019.",
                 valutazione="Regolarizzabile con DOCFA; necessaria per la conformità catastale in atto.",
                 riferimento_normativo="art. 29 c.1-bis L. 52/1985",
                 fonti=[dict(file="02_cila_2019.pdf", pagina=1),
                        dict(file="04_planimetria_catastale.pdf", pagina=1),
                        dict(file="05_rilievo_stato_di_fatto.pdf", pagina=1)]),
        ],
        dati_estratti_attesi={
            "01_concessione_edilizia.pdf": dict(tipo="concessione edilizia", numero="130/1985", data="1985-07-19",
                                                sup_utile_m2=sup(progetto)),
            "02_cila_2019.pdf": dict(tipo="CILA", protocollo="15872", data="2019-05-06",
                                     oggetto="demolizione tramezzo cucina-soggiorno e rifacimento bagno"),
            "03_visura_catastale.pdf": dict(categoria="A/2", classe="3", consistenza_vani=5, sup_catastale_m2=86),
        },
    )
    return p, docs, gt


def pratica_005():
    """Villa entro 300 m dalla costa: ampliamento e piscina senza titolo in area vincolata."""
    p = dict(id="P-005", indirizzo="Località Cala Serena, Via delle Dune 3", piano="terra",
             intestatario="Anna Fittizia", cf="FTTNNA58H55Z999B", foglio="31", particella="77", sub="")
    progetto = [R("Soggiorno", 0, 0, 6, 5), R("Cucina", 6, 0, 4, 5), R("Camera", 0, 5, 4, 4),
                R("Camera 2", 4, 5, 3.5, 4), R("Bagno", 7.5, 5, 2.5, 2.4), R("Bagno 2", 7.5, 7.4, 2.5, 1.6),
                R("Disimpegno", 0, 9, 10, 1.2), R("Portico", 0, 10.2, 10, 2, dest="non residenziale", kind="portico")]
    lavanderia = R("Lavanderia", 10, 0, 3, 6)
    piscina = R("Piscina", 1, 13.2, 8, 4, dest="pertinenza", kind="piscina")
    rilievo = progetto + [lavanderia, piscina]
    docs = {
        "01_concessione_edilizia.pdf": (doc_titolo, dict(
            tipo_esteso="Concessione edilizia", numero="18/1998", data="27/02/1998", data_domanda="10/09/1997",
            protocollo="2280", oggetto="nuova costruzione di casa unifamiliare a un piano con portico",
            destinazione="Residenziale", sup_utile=sup(progetto), sup_non_res=20.0,
            volume=round(sup(progetto) * 2.8, 2), altezza="2,80 m",
            prescrizioni=["Immobile ricadente nella fascia di 300 m dalla linea di battigia: "
                          "autorizzazione paesaggistica n. 12/1997 allegata.",
                          "Ogni ulteriore intervento esterno richiede nuova autorizzazione paesaggistica."],
            tavola="Tavola 2 - Pianta piano terra", rooms=progetto, scala=200)),
        "02_visura_catastale.pdf": (doc_visura, dict(
            data_visura="13/09/2026", categoria="A/7", classe="1", consistenza="6,5 vani", sup_catastale=128,
            rendita="755,32", storia=["Costituzione del 30/11/1999 prot. 9043 - planimetria in atti"])),
        "03_planimetria_catastale.pdf": (doc_planimetria, dict(protocollo="9043", data="30/11/1999",
                                                               rooms=progetto, scala=200)),
        "04_rilievo_stato_di_fatto.pdf": (doc_rilievo, dict(
            data="10/09/2026", altezza="2,80 m", rooms=rilievo, scala=200,
            osservazioni=["Distanza dell'edificio dalla linea di battigia misurata su ortofoto: circa 240 m.",
                          "Sul lato est è presente un locale lavanderia in muratura addossato al fabbricato.",
                          "Nel giardino è presente una piscina interrata di 8 x 4 m.",
                          "Non sono stati reperiti titoli edilizi né autorizzazioni paesaggistiche successive al 1998."])),
    }
    gt = dict(
        esito_atteso="non_conforme",
        sintesi="Ampliamento e piscina realizzati senza titolo in area a vincolo paesaggistico costiero. "
                "Caso ad alto rischio, probabilmente non sanabile.",
        difformita_attese=[
            dict(id="D1", ambito="edilizio_paesaggistico", tipo="ampliamento_senza_titolo", gravita="alta",
                 entita=f"+{fmt(area(lavanderia))} m² di superficie utile, circa {fmt(area(lavanderia) * 2.8)} m³",
                 descrizione="Locale lavanderia in muratura addossato al fabbricato, assente nel progetto approvato.",
                 valutazione="Nuovo volume in area vincolata: l'accertamento di compatibilità paesaggistica "
                             "non è ammesso per nuovi volumi, quindi è probabile l'obbligo di demolizione.",
                 riferimento_normativo="art. 142 c.1 lett. a e art. 167 c.4 D.Lgs. 42/2004; art. 31 DPR 380/2001",
                 fonti=[dict(file="01_concessione_edilizia.pdf", pagina=2),
                        dict(file="04_rilievo_stato_di_fatto.pdf", pagina=1)]),
            dict(id="D2", ambito="edilizio_paesaggistico", tipo="piscina_senza_titolo", gravita="alta",
                 entita=f"{fmt(area(piscina))} m²",
                 descrizione="Piscina interrata non prevista nel titolo e priva di autorizzazione paesaggistica.",
                 valutazione="Intervento che richiede titolo edilizio e autorizzazione paesaggistica preventiva.",
                 riferimento_normativo="art. 146 D.Lgs. 42/2004; DPR 380/2001",
                 fonti=[dict(file="01_concessione_edilizia.pdf", pagina=1),
                        dict(file="04_rilievo_stato_di_fatto.pdf", pagina=1)]),
            dict(id="D3", ambito="catastale", tipo="planimetria_non_aggiornata", gravita="media",
                 descrizione="La planimetria catastale del 1999 non riporta lavanderia e piscina.",
                 valutazione="Aggiornamento catastale possibile solo dopo la definizione della posizione edilizia.",
                 riferimento_normativo="art. 29 c.1-bis L. 52/1985",
                 fonti=[dict(file="03_planimetria_catastale.pdf", pagina=1)]),
        ],
        dati_estratti_attesi={
            "01_concessione_edilizia.pdf": dict(tipo="concessione edilizia", numero="18/1998", data="1998-02-27",
                                                sup_utile_m2=sup(progetto), vincolo_paesaggistico=True),
            "02_visura_catastale.pdf": dict(categoria="A/7", classe="1", consistenza_vani=6.5, sup_catastale_m2=128),
            "04_rilievo_stato_di_fatto.pdf": dict(sup_utile_m2=sup(rilievo), distanza_mare_m=240,
                                                  piscina=True),
        },
        # Collegamento con il risk engine territoriale esistente (backend/app/services/risk_engine.py)
        input_risk_engine=dict(superficie_catastale=sup(rilievo), superficie_autorizzata=sup(progetto),
                               distanza_mare=240, has_permesso=True, has_piscina=True,
                               has_permesso_piscina=False, satellite_change_pct=25,
                               documenti_contrastanti=False),
    )
    return p, docs, gt


SCENARI = [pratica_001, pratica_002, pratica_003, pratica_004, pratica_005]


def main(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    index = []
    for build in SCENARI:
        p, docs, gt = build()
        folder = out_dir / f"{p['id']}"
        folder.mkdir(exist_ok=True)
        for name, (fn, data) in docs.items():
            fn(folder / name, p, data)
        gt = dict(id=p["id"], scenario=build.__doc__.strip(), dati_fittizi=True,
                  immobile={k: v for k, v in p.items() if k != "id"},
                  documenti=list(docs.keys()), **gt)
        (folder / "ground_truth.json").write_text(json.dumps(gt, ensure_ascii=False, indent=2), encoding="utf-8")
        index.append(dict(id=p["id"], scenario=gt["scenario"], esito_atteso=gt["esito_atteso"],
                          difformita=len(gt["difformita_attese"])))
        print(f"{p['id']}: {len(docs)} documenti, {len(gt['difformita_attese'])} difformità attese")
    (out_dir / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    default = Path(__file__).resolve().parents[2] / "demo_data" / "pratiche"
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else default)
