import React, { useEffect, useState } from 'react';
import {
  Alert, Box, Button, LinearProgress, MenuItem, Paper, Stack, Step, StepContent, StepLabel, Stepper,
  TextField, Typography,
} from '@mui/material';
import { eseguiAgente, getEstrattori } from '../services/pratiche';

// Con le regole non c'è un modello per scrivere i testi: si usa il testo di base del catalogo
const MODALITA = {
  claude: { estrattore: 'claude', redattore: 'claude', etichetta: 'Claude (cloud)' },
  ollama: { estrattore: 'ollama', redattore: 'ollama', etichetta: 'Ollama (locale)' },
  regole: { estrattore: 'regole', redattore: 'testo', etichetta: 'Regole e testo di base (senza AI)' },
};

const NODI = {
  estrai: 'Lettura dei documenti',
  controlla_documenti: 'Controllo dei documenti',
  confronta: 'Confronto titolo, catasto e rilievo',
  cerca_norme: 'Ricerca nelle norme',
  redigi: 'Redazione delle difformità',
  concludi: 'Esito',
};

export default function AgentePanel({ praticaId, risultato, attese, onRisultato }) {
  const [disponibili, setDisponibili] = useState({});
  const [scelta, setScelta] = useState('');
  const [inCorso, setInCorso] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    getEstrattori()
      .then((lista) => {
        const d = Object.fromEntries(lista.map((e) => [e.nome, e]));
        setDisponibili(d);
        setScelta((s) => s || Object.keys(MODALITA).find((k) => d[k]?.disponibile) || 'regole');
      })
      .catch(() => setError('Backend non raggiungibile.'));
  }, []);

  const avvia = async () => {
    setError('');
    setInCorso(true);
    try {
      const { estrattore, redattore } = MODALITA[scelta];
      onRisultato(await eseguiAgente(praticaId, estrattore, redattore));
    } catch (e) {
      setError(e.response?.data?.detail || 'Analisi non riuscita.');
    } finally {
      setInCorso(false);
    }
  };

  const trovate = risultato?.difformita.map((d) => d.tipo) || [];
  const inComune = attese.filter((t) => trovate.includes(t)).length;

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Typography variant="subtitle1">Analisi con l'agente</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
        L'agente legge i documenti, confronta progetto, catasto e rilievo applicando le tolleranze, cerca le norme
        e scrive le difformità da confermare. Se hai già estratto i dati con lo stesso modello, li riusa.
      </Typography>
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} alignItems={{ sm: 'center' }}>
        <TextField select size="small" label="Modello" value={scelta} onChange={(e) => setScelta(e.target.value)}
          sx={{ minWidth: 220 }} disabled={inCorso}>
          {Object.entries(MODALITA).map(([k, m]) => (
            <MenuItem key={k} value={k} disabled={!disponibili[k]?.disponibile}>{m.etichetta}</MenuItem>
          ))}
        </TextField>
        <Button variant="contained" onClick={avvia} disabled={!scelta || inCorso}>
          {inCorso ? 'Analisi in corso…' : risultato ? 'Analizza di nuovo' : 'Trova le difformità'}
        </Button>
      </Stack>
      {inCorso && <LinearProgress sx={{ mt: 1.5 }} />}
      {error && <Alert severity="error" sx={{ mt: 1.5 }}>{error}</Alert>}

      {risultato?.agente && (
        <Box sx={{ mt: 2 }}>
          <Alert severity={inComune === attese.length && trovate.length === attese.length ? 'success' : 'warning'} sx={{ mb: 1.5 }}>
            Attese {attese.length}, trovate {trovate.length}, corrette {inComune}
            {' '}({MODALITA[Object.keys(MODALITA).find((k) => MODALITA[k].estrattore === risultato.agente.estrattore)]?.etichetta},
            ricerca {risultato.agente.ricerca}).
          </Alert>
          <Stepper orientation="vertical" activeStep={-1}>
            {risultato.agente.passi.map((p) => (
              <Step key={p.nodo} completed>
                <StepLabel optional={<Typography variant="caption">{p.secondi} s</Typography>}>{NODI[p.nodo] || p.nodo}</StepLabel>
                <StepContent TransitionProps={{ in: true }}>
                  <Typography variant="body2" color="text.secondary">{p.dettaglio}</Typography>
                </StepContent>
              </Step>
            ))}
          </Stepper>
          {risultato.agente.note.map((n) => (
            <Typography key={n} variant="caption" color="text.secondary" component="div">{n}</Typography>
          ))}
        </Box>
      )}
    </Paper>
  );
}
