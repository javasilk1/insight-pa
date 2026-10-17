# Risultati delle valutazioni (2026-10-16)

Generato da `backend/scripts/eval_completo.py` sulle 5 pratiche demo. Tempo per pratica: PDF digitali / scansioni. Costo per pratica: media dei due set, prezzi di listino nello script.

## Estrazione (tabella dell'ADR 0001)

| Estrattore | PDF digitali | Scansioni | Tempo per pratica | Costo per pratica |
|---|---|---|---|---|
| regole | 54/54 (100%) | 22/54 (41%) | 0.0 s / 7.1 s | 0 |

<details><summary>Campi sbagliati</summary>

- **regole, scansioni**: P-001 01_concessione_edilizia.pdf sup_utile_m2 (atteso 80.0, letto None); P-001 01_concessione_edilizia.pdf destinazione (atteso 'residenziale', letto None); P-001 02_visura_catastale.pdf categoria (atteso 'A/2', letto None); P-001 02_visura_catastale.pdf classe (atteso '3', letto None); P-001 02_visura_catastale.pdf consistenza_vani (atteso 5, letto None); P-001 02_visura_catastale.pdf sup_catastale_m2 (atteso 86, letto None); P-001 04_rilievo_stato_di_fatto.pdf sup_utile_m2 (atteso 81.95, letto None); P-002 01_licenza_edilizia.pdf sup_utile_m2 (atteso 80.0, letto None); P-002 01_licenza_edilizia.pdf sup_non_residenziale_m2 (atteso 8.0, letto None); P-002 02_visura_catastale.pdf categoria (atteso 'A/2', letto None); P-002 02_visura_catastale.pdf classe (atteso '2', letto None); P-002 02_visura_catastale.pdf consistenza_vani (atteso 5.5, letto None); P-002 02_visura_catastale.pdf sup_catastale_m2 (atteso 88, letto None); P-002 04_rilievo_stato_di_fatto.pdf sup_utile_m2 (atteso 88.0, letto None); P-003 01_permesso_di_costruire.pdf destinazione_sottotetto (atteso 'accessorio non abitabile', letto None); P-003 02_visura_catastale.pdf categoria (atteso 'A/7', letto None); P-003 02_visura_catastale.pdf classe (atteso '2', letto None); P-003 02_visura_catastale.pdf consistenza_vani (atteso 7, letto None); P-003 02_visura_catastale.pdf sup_catastale_m2 (atteso 141, letto None); P-003 04_rilievo_stato_di_fatto.pdf locali_abitativi (atteso ['Camera', 'Bagno', 'Disimpegno'], letto []); P-004 01_concessione_edilizia.pdf sup_utile_m2 (atteso 80.0, letto None); P-004 03_visura_catastale.pdf categoria (atteso 'A/2', letto None); P-004 03_visura_catastale.pdf classe (atteso '3', letto None); P-004 03_visura_catastale.pdf consistenza_vani (atteso 5, letto None); P-004 03_visura_catastale.pdf sup_catastale_m2 (atteso 86, letto None); P-005 01_concessione_edilizia.pdf sup_utile_m2 (atteso 102.0, letto None); P-005 02_visura_catastale.pdf categoria (atteso 'A/7', letto None); P-005 02_visura_catastale.pdf classe (atteso '1', letto None); P-005 02_visura_catastale.pdf consistenza_vani (atteso 6.5, letto None); P-005 02_visura_catastale.pdf sup_catastale_m2 (atteso 128, letto None); P-005 04_rilievo_stato_di_fatto.pdf sup_utile_m2 (atteso 120.0, letto None); P-005 04_rilievo_stato_di_fatto.pdf piscina (atteso True, letto False)

</details>

## Agente (ADR 0002)

### Agente: estrattore regole, redattore testo, ricerca parole, pratiche

| Esiti corretti | Precisione | Richiamo | Ambito | Gravità | Articoli citati | Ricerca norme | Verifiche | Tempo |
|---|---|---|---|---|---|---|---|---|
| 5/5 | 100% (8/8) | 100% (8/8) | 100% | 100% | 100% | 69% | 1/1 | 0.2 s |

| Pratica | Esito | Attese | Trovate | Perse | False |
|---|---|---|---|---|---|
| P-001 | ✅ conforme | 0 | 0 | — | — |
| P-002 | ✅ non_conforme | 2 | 2 | — | — |
| P-003 | ✅ non_conforme | 2 | 2 | — | — |
| P-004 | ✅ conforme_edilizio_non_conforme_catastale | 1 | 1 | — | — |
| P-005 | ✅ non_conforme | 3 | 3 | — | — |

### Agente: estrattore regole, redattore testo, ricerca parole, pratiche_scansionate

| Esiti corretti | Precisione | Richiamo | Ambito | Gravità | Articoli citati | Ricerca norme | Verifiche | Tempo |
|---|---|---|---|---|---|---|---|---|
| 0/5 | — (0/0) | 0% (0/8) | — | — | — | — | 0/1 | 43.8 s |

| Pratica | Esito | Attese | Trovate | Perse | False |
|---|---|---|---|---|---|
| P-001 | ❌ documentazione_incompleta | 0 | 0 | — | — |
| P-002 | ❌ documentazione_incompleta | 2 | 0 | chiusura_balcone_veranda, planimetria_non_aggiornata | — |
| P-003 | ❌ documentazione_incompleta | 2 | 0 | mutamento_destinazione_uso, catasto_non_coerente_con_titolo | — |
| P-004 | ❌ documentazione_incompleta | 1 | 0 | planimetria_non_aggiornata | — |
| P-005 | ❌ documentazione_incompleta | 3 | 0 | ampliamento_senza_titolo, piscina_senza_titolo, planimetria_non_aggiornata | — |
