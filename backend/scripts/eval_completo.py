"""
Lancia tutte le valutazioni e scrive i risultati in docs/eval/risultati.md.

1. Estrazione: ogni estrattore disponibile su PDF digitali e scansioni (la tabella dell'ADR 0001)
2. Agente: estrazione + confronto + norme + redazione, con lo stesso modello per estrarre e scrivere

Salta da solo Claude se manca ANTHROPIC_API_KEY e Ollama se non risponde.

Uso, con docker compose avviato:
    docker compose exec backend python scripts/eval_completo.py
    docker compose exec backend python scripts/eval_completo.py claude          # solo Claude
    # Ollama installato sul Mac invece che nel compose:
    docker compose exec -e OLLAMA_URL=http://host.docker.internal:11434 backend python scripts/eval_completo.py
"""
import argparse
import json
import sys
import warnings
from datetime import date
from pathlib import Path

warnings.filterwarnings("ignore", category=DeprecationWarning)
QUI = Path(__file__).resolve().parent
sys.path.insert(0, str(QUI.parents[0] / "app"))
sys.path.insert(0, str(QUI.parents[0]))  # nel container il codice è in /app
sys.path.insert(0, str(QUI))

from services.estrazione_service import estrazione_service  # noqa: E402
from valuta_agente import markdown as md_agente  # noqa: E402
from valuta_agente import valuta as valuta_agente  # noqa: E402
from valuta_estrazione import valuta as valuta_estrazione  # noqa: E402


def cerca(*candidati: Path) -> Path:
    return next((c for c in candidati if c.exists()), candidati[-1])


DEMO = cerca(Path("/demo_data"), QUI.parents[1] / "demo_data")
USCITA = cerca(Path("/docs"), QUI.parents[1] / "docs") / "eval"
REDATTORE = {"regole": "testo", "claude": "claude", "ollama": "ollama"}


def pct(ok, tot) -> str:
    return f"{ok}/{tot} ({ok / tot:.0%})" if tot else "—"


def main(scelti: list[str], ricerca: str):
    disponibili = {e["nome"]: e for e in estrazione_service.estrattori()}
    nomi = [n for n in (scelti or ["regole", "claude", "ollama"]) if disponibili[n]["disponibile"]]
    saltati = [f"{n}: {disponibili[n]['nota']}" for n in (scelti or ["claude", "ollama"]) if n not in nomi]
    print("Valuto:", ", ".join(nomi), "| saltati:", "; ".join(saltati) or "nessuno")
    USCITA.mkdir(parents=True, exist_ok=True)

    righe, dettagli, agenti, grezzi = [], [], [], {}
    for nome in nomi:
        print(f"\n== Estrazione {nome}")
        dig = valuta_estrazione(nome, DEMO / "pratiche")
        scan = valuta_estrazione(nome, DEMO / "pratiche_scansionate")
        n_pratiche = len({d["pratica"] for d in dig["documenti"]})
        costo = (dig["costo_usd"] + scan["costo_usd"]) / (2 * n_pratiche) if dig["costo_usd"] is not None else None
        righe.append(
            f"| {nome}{' (`' + dig['modello'] + '`)' if dig['modello'] else ''} "
            f"| {pct(dig['campi_corretti'], dig['campi_totali'])} | {pct(scan['campi_corretti'], scan['campi_totali'])} "
            f"| {dig['secondi_totali'] / n_pratiche:.1f} s / {scan['secondi_totali'] / n_pratiche:.1f} s "
            f"| {'$' + format(costo, '.3f') if costo is not None else '0'} |")
        for rep, set_ in [(dig, "digitali"), (scan, "scansioni")]:
            sbagliati = [c for c in rep["campi"] if not c["ok"]]
            if sbagliati:
                dettagli.append(f"**{nome}, {set_}**: " + "; ".join(
                    f"{c['pratica']} {c['file']} {c['campo']} (atteso {c['atteso']!r}, letto {c['estratto']!r})" for c in sbagliati))
        print(righe[-1])
        grezzi[f"estrazione_{nome}"] = {"digitali": dig, "scansioni": scan}

        print(f"== Agente {nome}")
        for cartella in ["pratiche", "pratiche_scansionate"]:
            rep = valuta_agente(nome, REDATTORE[nome], ricerca, DEMO / cartella)
            agenti.append(md_agente(rep))
            grezzi[f"agente_{nome}_{cartella}"] = rep
            print(agenti[-1].splitlines()[4])

    testo = "\n".join([
        f"# Risultati delle valutazioni ({date.today().isoformat()})",
        "",
        "Generato da `backend/scripts/eval_completo.py` sulle 5 pratiche demo. "
        "Tempo per pratica: PDF digitali / scansioni. Costo per pratica: media dei due set, prezzi di listino nello script.",
        "",
        "## Estrazione (tabella dell'ADR 0001)",
        "",
        "| Estrattore | PDF digitali | Scansioni | Tempo per pratica | Costo per pratica |",
        "|---|---|---|---|---|",
        *righe,
        "",
        *(["Non valutati: " + "; ".join(saltati), ""] if saltati else []),
        "<details><summary>Campi sbagliati</summary>", "", *([f"- {d}" for d in dettagli] or ["Nessuno."]), "", "</details>",
        "",
        "## Agente (ADR 0002)",
        "",
        *[a + "\n" for a in agenti],
    ])
    (USCITA / "risultati.md").write_text(testo, encoding="utf-8")
    (USCITA / "risultati.json").write_text(json.dumps(grezzi, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(f"\nScritto {USCITA / 'risultati.md'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("estrattori", nargs="*", choices=["regole", "claude", "ollama"])
    parser.add_argument("--ricerca", choices=["parole", "semantica"], default="semantica")
    args = parser.parse_args()
    main(args.estrattori, args.ricerca)
