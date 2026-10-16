# ADR 0002 · Come l'agente trova e scrive le difformità

- **Stato:** proposta, in attesa delle misure con Claude e Ollama
- **Data:** 16/10/2026

## Contesto

Dopo l'estrazione (ADR 0001) ogni documento della pratica è una scheda di dati: titolo edilizio con i locali dell'elaborato grafico, visura, planimetria catastale, rilievo dello stato di fatto. Il valore per il tecnico sta nel passo dopo: confrontare le schede e dire cosa non torna, con l'entità, la norma e la fonte.

Vincoli:
- **Il tecnico firma.** Un esito sbagliato ha conseguenze legali. Deve poter capire perché l'agente dice "non conforme".
- **Le difformità perse costano più di quelle false.** Una falsa la scarta il tecnico in revisione, una persa finisce nella relazione firmata.
- **Ripetibilità.** La stessa pratica deve dare lo stesso esito a ogni esecuzione.

## Opzioni

| | A. Tutto all'LLM | B. Regole + LLM per il testo | C. Solo regole |
|---|---|---|---|
| Chi decide le difformità | il modello, leggendo le schede | codice: locali, destinazioni, tolleranze | codice |
| Chi scrive descrizione e valutazione | il modello | il modello, con i passaggi normativi trovati | testo fisso per tipo |
| Ripetibile | no | sì sull'esito, il testo varia | sì |
| Casi nuovi | generalizza, ma può inventare | serve una regola per ogni nuovo tipo | serve una regola per ogni nuovo tipo |
| Spiegabile | poco | sì: ogni difformità ha i fatti che l'hanno generata | sì |

## Decisione

**B.** Il modello non decide l'esito. Il grafo (`backend/app/agente/grafo.py`, LangGraph):

```
estrai ─► controlla_documenti ─┬─► confronta ─┬─► cerca_norme ─► redigi ─► concludi
                               │              └──(nessuna difformità)──────────┘
                               └──(documenti mancanti)─────────────────────────► concludi
```

- **confronta** (`confronto.py`) confronta i locali del titolo legittimo (l'ultimo titolo con l'elaborato, es. la CILA) con quelli del rilievo e della planimetria. Riconosce: spazio esterno chiuso, accessorio trasformato in abitativo, diversa distribuzione, ampliamento, piscina, scostamento oltre la tolleranza dell'art. 34-bis (graduata per superficie dal DL 69/2024), planimetria non aggiornata, catasto aggiornato senza titolo. In area vincolata (titolo o distanza dalla costa sotto i 300 m) le opere esterne diventano edilizio-paesaggistiche, gravità alta.
- **cerca_norme** (`norme.py`) è la parte RAG: per ogni difformità cerca 4 passaggi in `norme.json` con embedding multilingue (fastembed) o, come ripiego, per parole.
- **redigi** (`redazione.py`) fa scrivere al modello (Claude o Ollama via LangChain, output strutturato) descrizione e valutazione, citando solo i passaggi trovati. Le citazioni fuori dai passaggi vengono scartate e annotate.
- **controlla_documenti** ferma la verifica se mancano titolo con elaborato o rilievo: l'esito è "documentazione incompleta", mai "conforme".
- La **revisione umana** resta nella pagina della pratica: il tecnico conferma o scarta ogni difformità prima della relazione.

Perché non un vector DB: il corpus sono 12 articoli. Qdrant entra quando arrivano regolamenti edilizi comunali e leggi regionali.

## Come la misuriamo

`backend/scripts/valuta_agente.py` confronta le difformità trovate con le `difformita_attese` dei `ground_truth.json`, per tipo:

- **precisione** (difformità vere tra quelle trovate) e **richiamo** (attese trovate): il richiamo conta di più
- **esito**, **ambito**, **gravità** corretti
- **articoli citati**: articoli del riferimento atteso presenti in quello dell'agente
- **ricerca norme**: articoli previsti per il tipo presenti tra i passaggi trovati (qualità del RAG)

| Estrattore + redattore | Set | Esiti | Precisione | Richiamo | Articoli | Ricerca norme |
|---|---|---|---|---|---|---|
| regole + testo di base, ricerca per parole | PDF digitali | 5/5 | 100% | 100% | 100% | 69% |
| regole + testo di base, ricerca per parole | scansioni | 0/5 (documentazione incompleta) | — | 0% | — | — |
| Claude + Claude | scansioni | da misurare | | | | |
| Ollama + Ollama | scansioni | da misurare | | | | |

Come per l'ADR 0001, il 100% con le regole non dimostra la qualità: estrattore e confronto sono stati scritti guardando queste 5 pratiche. Dice solo che il confronto funziona quando i dati estratti sono giusti. Il numero che conta è **Claude o Ollama sulle scansioni**, dove gli errori di estrazione si propagano al confronto. Sulle scansioni le regole non leggono i locali e l'agente si ferma invece di inventare: è il comportamento voluto.

## Conseguenze

- Ogni nuovo tipo di difformità è una regola in `confronto.py` più una voce in `catalogo.py`, con un caso nel golden set.
- Le sintesi in `norme.json` e le valutazioni del catalogo sono una prima stesura: vanno riviste da un tecnico, come i `ground_truth.json`.
- Le pratiche demo sono troppo pulite. Servono pratiche reali anonimizzate e casi difficili (documenti in contraddizione, elaborati senza tabella dei locali) prima di fidarsi dei numeri.
- Con `LANGSMITH_TRACING=true` e `LANGSMITH_API_KEY` ogni esecuzione del grafo è tracciata su LangSmith (passi, prompt, token).
