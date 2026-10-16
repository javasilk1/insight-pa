"""
Valuta un estrattore sulle pratiche demo confrontando i dati estratti con i ground_truth.json.

Uso:
    python backend/scripts/valuta_estrazione.py regole
    python backend/scripts/valuta_estrazione.py claude            # richiede ANTHROPIC_API_KEY
    python backend/scripts/valuta_estrazione.py ollama            # richiede Ollama in esecuzione
    python backend/scripts/valuta_estrazione.py claude --cartella demo_data/pratiche_scansionate
    python backend/scripts/valuta_estrazione.py claude --json report.json

Nel container: docker-compose exec backend python scripts/valuta_estrazione.py claude
"""
import argparse
import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=DeprecationWarning)
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend" / "app"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # nel container il codice è in /app

from estrazione.estrattori import ESTRATTORI  # noqa: E402
from estrazione.valutazione import confronta  # noqa: E402

# $ per milione di token (input, output). Aggiornare se cambiano i listini.
PREZZI = {"claude-opus-5": (5.0, 25.0), "claude-sonnet-5": (2.0, 10.0), "claude-haiku-4-5": (1.0, 5.0)}


def valuta(nome: str, cartella: Path) -> dict:
    estrattore = ESTRATTORI[nome]()
    righe, documenti = [], []
    for gt_path in sorted(cartella.glob("P-*/ground_truth.json")):
        gt = json.loads(gt_path.read_text(encoding="utf-8"))
        for file, attesi in gt.get("dati_estratti_attesi", {}).items():
            r = estrattore.estrai(gt_path.parent / file)
            campi = confronta(attesi, r.dati)
            righe += [{"pratica": gt["id"], "file": file, **c} for c in campi]
            documenti.append({"pratica": gt["id"], "file": file, "tipo": r.tipo, "secondi": round(r.secondi, 2),
                              "token_input": r.token_input, "token_output": r.token_output, "note": r.note})
    ok = sum(r["ok"] for r in righe)
    tin, tout = sum(d["token_input"] for d in documenti), sum(d["token_output"] for d in documenti)
    model = getattr(estrattore, "model", None)
    costo = None
    if model in PREZZI:
        pin, pout = PREZZI[model]
        costo = round((tin * pin + tout * pout) / 1e6, 4)
    return {
        "estrattore": nome, "modello": model,
        "campi_corretti": ok, "campi_totali": len(righe), "accuratezza": round(ok / len(righe), 3) if righe else None,
        "secondi_totali": round(sum(d["secondi"] for d in documenti), 1),
        "token_input": tin, "token_output": tout, "costo_usd": costo,
        "documenti": documenti, "campi": righe,
    }


def stampa(report: dict):
    for r in report["campi"]:
        if not r["ok"]:
            print(f"  ✗ {r['pratica']} {r['file']} · {r['campo']}: atteso {r['atteso']!r}, estratto {r['estratto']!r}")
    print(f"\n{report['estrattore']}{' (' + report['modello'] + ')' if report['modello'] else ''}: "
          f"{report['campi_corretti']}/{report['campi_totali']} campi corretti "
          f"({report['accuratezza']:.0%}) in {report['secondi_totali']} s"
          + (f", {report['token_input']} token in / {report['token_output']} out" if report["token_input"] else "")
          + (f", costo ${report['costo_usd']}" if report["costo_usd"] is not None else ""))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("estrattore", choices=list(ESTRATTORI))
    parser.add_argument("--cartella", type=Path, default=ROOT / "demo_data" / "pratiche")
    parser.add_argument("--json", type=Path, help="salva il report completo")
    args = parser.parse_args()
    report = valuta(args.estrattore, args.cartella)
    stampa(report)
    if args.json:
        args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
