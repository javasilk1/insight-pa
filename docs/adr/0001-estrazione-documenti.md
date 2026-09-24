# ADR 0001 · Come estrarre i dati dai documenti di una pratica

- **Stato:** proposta, in attesa delle misure
- **Data:** 24/09/2026

## Contesto

La verifica dello stato legittimo parte da documenti eterogenei: titoli edilizi dagli anni '70 a oggi, visure, planimetrie catastali, rilievi. Molti arrivano dall'accesso agli atti come **scansioni** senza testo selezionabile, spesso storte o sbiadite.

Da ogni documento servono pochi campi precisi (numero e data del titolo, superfici, categoria catastale, locali), perché su quei campi lavorano il confronto e le regole di tolleranza. Un errore di estrazione diventa una difformità falsa o, peggio, una difformità non vista.

Vincoli:
- **GDPR.** I documenti contengono dati personali (nomi, codici fiscali, indirizzi) e i clienti sono studi professionali italiani.
- **Costo.** Il prezzo previsto è per pratica, quindi il costo di estrazione per pratica deve stare molto sotto quel prezzo.
- **Affidabilità misurabile.** Il tecnico firma la relazione: dobbiamo poter dire quanto sbaglia l'estrazione, non solo che funziona.

## Opzioni

| | A. Regole (regex) | B. Claude via API | C. Modello locale (Ollama) |
|---|---|---|---|
| Input | testo del PDF | PDF originale, anche scansionato | testo del PDF + OCR (tesseract) |
| Scansioni | non funziona | le legge direttamente | dipende dalla qualità dell'OCR |
| Documenti nuovi | va riscritta per ogni formato | generalizza | generalizza, meno bene su testi lunghi |
| Dati personali | restano sul server | escono verso un fornitore: servono DPA e hosting UE | restano sul server |
| Costo | zero | a token, per pratica | hardware (GPU) o lentezza su CPU |
| Manutenzione | alta | bassa | media: modelli e OCR da aggiornare |

Tutte e tre implementano la stessa interfaccia (`backend/app/estrazione/estrattori.py`) e producono gli stessi schemi Pydantic (`schema.py`), quindi sono intercambiabili e confrontabili.

## Come decidiamo

Con numeri e non con opinioni. `backend/scripts/valuta_estrazione.py` confronta ogni campo estratto con i `ground_truth.json` e riporta accuratezza, tempo, token e costo, su due set:

- `demo_data/pratiche`: PDF digitali
- `demo_data/pratiche_scansionate`: gli stessi documenti come scansioni senza testo

| Estrattore | PDF digitali | Scansioni | Tempo | Costo per pratica |
|---|---|---|---|---|
| Regole | 54/54 (100%) | 0/54 (0%) | 0,1 s | 0 |
| Claude (`claude-opus-5`) | da misurare | da misurare | | |
| Ollama (`qwen2.5:7b`) + OCR | da misurare | da misurare | | |

Il 100% delle regole sui PDF digitali non dice nulla sulla qualità: le regole sono scritte sul formato esatto delle pratiche demo. Il loro 0% sulle scansioni mostra invece perché servono i modelli.

## Decisione provvisoria

- Default **Claude via API** per la qualità sulle scansioni, con la chiave e il DPA dello studio pilota, e se possibile inferenza in UE.
- **Ollama come alternativa** per chi non vuole che i documenti escano dal server, se le misure lo rendono accettabile.
- Le **regole restano** come test veloce del harness in CI.

La decisione diventa definitiva quando la tabella è compilata anche su pratiche reali anonimizzate. Le pratiche demo sono generate e troppo pulite.

## Conseguenze

- Ogni modifica a prompt, schema o modello si valuta rilanciando lo script: la tabella sopra è il registro.
- Il costo per pratica calcolato dallo script alimenta il prezzo del piano.
- Da valutare dopo: modelli più piccoli per la classificazione, cache del prompt, batch notturni per le pratiche non urgenti.
