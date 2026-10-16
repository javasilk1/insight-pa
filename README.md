# InsightPA

InsightPA aiuta il tecnico (geometra, architetto) a verificare lo **stato legittimo** di un immobile: legge i documenti di una pratica (titoli edilizi, visure, planimetrie catastali, rilievi), li confronta e propone le difformità. Il tecnico le conferma o le scarta e scarica la relazione in Word.

## Avvio

```bash
docker compose up -d --build
```

- Applicazione: http://localhost:3001
- API (con pagina di prova "Try it out"): http://localhost:8000/docs
- Console MinIO: http://localhost:9001

Per usare il modello locale con Ollama al posto di Claude:

```bash
docker compose --profile locale up -d
```

Per usare Claude serve la variabile `ANTHROPIC_API_KEY` nell'ambiente (o in un file `.env` accanto al `docker-compose.yml`).

## Com'è fatto

| Pezzo | Tecnologia | A cosa serve |
|---|---|---|
| Frontend | React + MUI | lista pratiche, dettaglio, revisione delle difformità |
| Backend | Python + FastAPI | API delle pratiche, estrazione, relazione Word |
| LLM | Claude (API) oppure Ollama (locale) | leggere i documenti e compilare le schede |
| Database | Postgres + PostGIS | dove finiranno le pratiche (oggi sono file demo) |
| Agente | LangGraph + LangChain | confronto dei documenti, ricerca nelle norme, redazione delle difformità |
| Vector DB | Qdrant | ricerca semantica sui documenti caricati (le norme dell'agente stanno in memoria) |
| File | MinIO | archivio dei PDF caricati (prossimi passi) |

```
backend/app/
  api/pratiche.py         API: lista, dettaglio, documenti, relazione
  services/               logica (pratiche, MinIO, Qdrant, embedding)
  estrazione/             estrattori (regole, Claude, Ollama) e schemi dei dati
  agente/                 agente di verifica: grafo, confronto, norme, redazione
  models/                 forma dei dati delle API
backend/scripts/          generazione delle pratiche demo, valutazione di estrattori e agente
demo_data/pratiche/       5 pratiche demo con i risultati attesi (ground_truth.json)
docs/adr/                 decisioni di architettura
frontend/src/             pagine Pratiche e Dettaglio pratica
```

## API principali

- `GET /api/pratiche`: elenco delle pratiche
- `GET /api/pratiche/{id}`: analisi di una pratica (documenti, dati estratti, difformità)
- `GET /api/pratiche/{id}/documenti/{file}`: il PDF originale
- `POST /api/pratiche/{id}/relazione`: genera la relazione Word con le difformità confermate
- `GET /api/pratiche/estrattori`: quali estrattori sono disponibili (Claude, Ollama, regole)
- `POST /api/pratiche/{id}/estrazione`: avvia l'estrazione dei dati dai PDF con l'estrattore scelto
- `GET /api/pratiche/{id}/estrazione`: avanzamento e risultati, confrontati con i valori attesi
- `POST /api/pratiche/{id}/agente`: esegue l'agente di verifica e restituisce le difformità trovate

## Dove si usa l'LLM

Nella pagina di una pratica:

- **Estrazione con l'AI** fa leggere i PDF a Claude o a Ollama e mostra, campo per campo, cosa ha estratto il modello rispetto ai valori attesi.
- **Analisi con l'agente** esegue il grafo LangGraph: estrazione, confronto tra titolo, catasto e rilievo con le tolleranze di legge, ricerca nelle norme e redazione delle difformità. Il risultato si confronta con quello atteso e si rivede come le difformità demo. Le scelte sono nell'[ADR 0002](docs/adr/0002-agente-di-verifica.md).

## Valutare estrazione e agente

Tutte le misure in un colpo, con i modelli disponibili (Claude se c'è la chiave, Ollama se risponde):

```bash
docker compose exec backend python scripts/eval_completo.py
```

Scrive [docs/eval/risultati.md](docs/eval/risultati.md), che serve a chiudere l'[ADR 0001](docs/adr/0001-estrazione-documenti.md) e l'[ADR 0002](docs/adr/0002-agente-di-verifica.md). Singolarmente:

```bash
docker compose exec backend python scripts/valuta_estrazione.py claude --cartella /demo_data/pratiche_scansionate
docker compose exec backend python scripts/valuta_agente.py --estrattore claude --redattore claude --cartella /demo_data/pratiche_scansionate
```

## Test

```bash
docker compose run --rm -v "$PWD/backend:/src" -w /src backend sh -c "pip install -q pytest && python -m pytest tests -q"
```
