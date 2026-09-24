# Pratiche demo per la verifica dello stato legittimo

Cinque pratiche **fittizie** da usare per due cose:

1. **Demo con i geometri.** Si carica una pratica e si mostra cosa trova InsightPA, invece di raccontarlo.
2. **Golden set per gli eval.** Ogni cartella ha un `ground_truth.json` con i dati da estrarre e le difformità attese, citando documento e pagina. Così si misura la qualità di estrazione e agente a ogni modifica.

Comune, persone, codici fiscali, protocolli e immobili sono inventati. Ogni pagina porta la filigrana "DATI FITTIZI".

| Pratica | Scenario | Esito atteso | Difformità |
|---|---|---|---|
| P-001 | Appartamento con superficie +2,4% rispetto al progetto | conforme (tolleranza Salva Casa) | 0 |
| P-002 | Balcone chiuso a veranda senza titolo | non conforme | 1 edilizia, 1 catastale |
| P-003 | Sottotetto non abitabile trasformato in camera e bagno, catasto aggiornato senza titolo | non conforme | 1 edilizia, 1 catastale |
| P-004 | Tramezzo demolito con CILA regolare, planimetria catastale vecchia | conforme edilizio, non conforme catastale | 1 catastale |
| P-005 | Villa a 240 m dal mare con ampliamento e piscina senza titolo | non conforme, alto rischio | 2 edilizio-paesaggistiche, 1 catastale |

P-001 e P-004 servono a controllare che l'agente **non** inventi difformità.

## Documenti per pratica

- Titolo edilizio (licenza, concessione o permesso) con la tavola di progetto a pagina 2
- Eventuale titolo successivo (CILA in P-004)
- Visura catastale
- Planimetria catastale
- Rilievo dello stato di fatto del tecnico

## Vederle nell'app

Con `docker-compose up` la cartella è montata nel backend: la sezione **Pratiche** del frontend (http://localhost:3001/pratiche) mostra le pratiche, i PDF, le difformità da confermare o scartare e l'export della relazione in Word. Il formato dei dati è definito in `backend/app/models/pratica.py`: oggi lo riempiono i `ground_truth.json`, domani lo produrrà l'agente.

## Rigenerare

```bash
pip install reportlab
python backend/scripts/generate_pratiche_demo.py
```

## Da validare con un tecnico

I riferimenti normativi e le valutazioni nei `ground_truth.json` (tolleranze dell'art. 34-bis dopo il DL 69/2024, vetrate amovibili, sottotetti, vincolo costiero) sono una prima stesura. Vanno rivisti da un geometra prima di usarli in una demo commerciale.

## Prossimi passi possibili

- Versione "scansionata" dei PDF (immagine storta e rumorosa) per testare l'OCR
- Pratiche con documenti mancanti o in contraddizione tra loro
- Script di eval che confronta l'output dell'agente con `ground_truth.json`
