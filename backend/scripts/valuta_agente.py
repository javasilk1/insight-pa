"""
Valuta l'agente di verifica sulle pratiche demo: difformità trovate contro difformità attese.

Uso:
    python backend/scripts/valuta_agente.py                                   # regole + testo di base, senza AI
    python backend/scripts/valuta_agente.py --estrattore claude --redattore claude
    python backend/scripts/valuta_agente.py --estrattore ollama --redattore ollama --cartella demo_data/pratiche_scansionate
    python backend/scripts/valuta_agente.py --ricerca semantica --json report.json

Nel container: docker compose exec backend python scripts/valuta_agente.py --estrattore claude --redattore claude
"""
import argparse
import json
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=DeprecationWarning)
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend" / "app"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # nel container il codice è in /app

from agente.grafo import crea_grafo  # noqa: E402
from agente.norme import RicercaParole, RicercaSemantica  # noqa: E402
from agente.redazione import crea_redattore  # noqa: E402
from agente.valutazione import riepilogo, valuta_pratica  # noqa: E402
from estrazione.estrattori import ESTRATTORI  # noqa: E402


def valuta(estrattore: str, redattore: str, ricerca: str, cartella: Path) -> dict:
    red = crea_redattore(redattore)
    grafo = crea_grafo(ESTRATTORI[estrattore](), RicercaSemantica() if ricerca == "semantica" else RicercaParole(), red)
    righe, inizio = [], time.perf_counter()
    for gt_path in sorted(cartella.glob("P-*/ground_truth.json")):
        gt = json.loads(gt_path.read_text(encoding="utf-8"))
        out = grafo.invoke({"cartella": str(gt_path.parent), "files": gt["documenti"]})
        riga = valuta_pratica(gt, out)
        riga["note"] = out.get("note", [])
        riga["difformita"] = out.get("difformita", [])
        righe.append(riga)
    return {"estrattore": estrattore, "redattore": redattore, "modello_redattore": red.modello, "ricerca": ricerca,
            "cartella": cartella.name, "secondi": round(time.perf_counter() - inizio, 1),
            "riepilogo": riepilogo(righe), "pratiche": righe}


def pct(x) -> str:
    return "—" if x is None else f"{x:.0%}"


def markdown(r: dict) -> str:
    s = r["riepilogo"]
    out = [
        f"### Agente: estrattore {r['estrattore']}, redattore {r['redattore']}"
        + (f" ({r['modello_redattore']})" if r["modello_redattore"] else "") + f", ricerca {r['ricerca']}, {r['cartella']}",
        "",
        "| Esiti corretti | Precisione | Richiamo | Ambito | Gravità | Articoli citati | Ricerca norme | Verifiche | Tempo |",
        "|---|---|---|---|---|---|---|---|---|",
        f"| {s['esiti_corretti']}/{s['pratiche']} | {pct(s['precisione'])} ({s['vere']}/{s['vere'] + s['false']}) "
        f"| {pct(s['richiamo'])} ({s['vere']}/{s['difformita_attese']}) | {pct(s['ambito_ok'])} | {pct(s['gravita_ok'])} "
        f"| {pct(s['articoli'])} | {pct(s['ricerca'])} | {s['verifiche']} | {r['secondi']} s |",
        "",
        "| Pratica | Esito | Attese | Trovate | Perse | False |",
        "|---|---|---|---|---|---|",
    ]
    for p in r["pratiche"]:
        out.append(f"| {p['pratica']} | {'✅' if p['esito_ok'] else '❌'} {p['esito']} | {len(p['attese'])} | {len(p['trovate'])} "
                   f"| {', '.join(p['perse_tipi']) or '—'} | {', '.join(p['false_tipi']) or '—'} |")
    return "\n".join(out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--estrattore", choices=list(ESTRATTORI), default="regole")
    parser.add_argument("--redattore", choices=["testo", "claude", "ollama"], default="testo")
    parser.add_argument("--ricerca", choices=["parole", "semantica"], default="parole")
    parser.add_argument("--cartella", type=Path, default=ROOT / "demo_data" / "pratiche")
    parser.add_argument("--json", type=Path, help="salva il report completo")
    args = parser.parse_args()
    report = valuta(args.estrattore, args.redattore, args.ricerca, args.cartella)
    print(markdown(report))
    if args.json:
        args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
