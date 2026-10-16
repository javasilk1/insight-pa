import React, { useEffect, useState } from 'react';
import {
  Alert, Box, Button, LinearProgress, Link, MenuItem, Paper, Stack, Table, TableBody, TableCell, TableHead,
  TableRow, TextField, Typography,
} from '@mui/material';
import CheckIcon from '@mui/icons-material/Check';
import CloseIcon from '@mui/icons-material/Close';
import { avviaEstrazione, getEstrattori, getEstrazione } from '../services/pratiche';

const label = (s) => s.replaceAll('_', ' ').replace(/^./, (c) => c.toUpperCase());

const valore = (v) => {
  if (v === null || v === undefined || v === '') return '—';
  if (Array.isArray(v)) return v.length ? v.map((x) => (typeof x === 'object' ? x.nome : x)).join(', ') : '—';
  if (typeof v === 'boolean') return v ? 'sì' : 'no';
  return String(v);
};

function DocumentoEstratto({ doc, onOpen }) {
  const attesi = new Set(doc.confronto.map((c) => c.campo));
  const altri = Object.entries(doc.dati).filter(([k]) => !attesi.has(k));
  return (
    <Box>
      <Stack direction="row" spacing={1} alignItems="baseline" flexWrap="wrap" useFlexGap>
        <Link component="button" variant="subtitle2" onClick={() => onOpen(doc.file)}>{doc.file}</Link>
        <Typography variant="caption" color="text.secondary">
          {doc.tipo ? label(doc.tipo) : 'tipo non riconosciuto'} · {doc.secondi} s
        </Typography>
      </Stack>
      {doc.note.map((n) => <Typography key={n} variant="caption" color="text.secondary" component="div">{n}</Typography>)}
      {doc.confronto.length > 0 && (
        <Table size="small" sx={{ mt: 0.5 }}>
          <TableHead>
            <TableRow>
              <TableCell>Campo</TableCell>
              <TableCell>Estratto</TableCell>
              <TableCell>Atteso</TableCell>
              <TableCell padding="checkbox" />
            </TableRow>
          </TableHead>
          <TableBody>
            {doc.confronto.map((c) => (
              <TableRow key={c.campo}>
                <TableCell>{label(c.campo)}</TableCell>
                <TableCell>{valore(c.estratto)}</TableCell>
                <TableCell sx={{ color: 'text.secondary' }}>{valore(c.atteso)}</TableCell>
                <TableCell padding="checkbox">
                  {c.ok ? <CheckIcon fontSize="small" color="success" /> : <CloseIcon fontSize="small" color="error" />}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
      {altri.length > 0 && (
        <Box sx={{ mt: 1 }}>
          {altri.map(([k, v]) => (
            <Typography variant="body2" key={k}>
              <Box component="span" color="text.secondary">{label(k)}:</Box> {valore(v)}
            </Typography>
          ))}
        </Box>
      )}
    </Box>
  );
}

export default function EstrazionePanel({ praticaId, onOpen }) {
  const [estrattori, setEstrattori] = useState([]);
  const [scelto, setScelto] = useState('');
  const [stato, setStato] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    getEstrattori()
      .then((lista) => {
        setEstrattori(lista);
        setScelto((s) => s || lista.find((e) => e.disponibile)?.nome || '');
      })
      .catch(() => setError('Backend non raggiungibile.'));
    getEstrazione(praticaId).then(setStato).catch(() => {});
  }, [praticaId]);

  const inCorso = stato?.stato === 'in_corso';

  useEffect(() => {
    if (!inCorso) return undefined;
    const t = setInterval(() => getEstrazione(praticaId).then(setStato).catch(() => {}), 2000);
    return () => clearInterval(t);
  }, [praticaId, inCorso]);

  const avvia = async () => {
    setError('');
    try {
      setStato(await avviaEstrazione(praticaId, scelto));
    } catch (e) {
      setError(e.response?.data?.detail || 'Estrazione non avviata.');
    }
  };

  const info = estrattori.find((e) => e.nome === scelto);

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Typography variant="subtitle1">Estrazione con l'AI</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
        Il modello legge i PDF della pratica e compila i dati di ogni documento. Li confrontiamo con i valori attesi
        della pratica demo.
      </Typography>
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} alignItems={{ sm: 'center' }}>
        <TextField select size="small" label="Modello" value={scelto} onChange={(e) => setScelto(e.target.value)}
          sx={{ minWidth: 200 }} disabled={inCorso}>
          {estrattori.map((e) => (
            <MenuItem key={e.nome} value={e.nome} disabled={!e.disponibile}>{e.etichetta}</MenuItem>
          ))}
        </TextField>
        <Button variant="contained" onClick={avvia} disabled={!info?.disponibile || inCorso}>
          {inCorso ? 'Estrazione in corso…' : stato ? 'Estrai di nuovo' : 'Estrai i dati'}
        </Button>
      </Stack>
      {info && <Typography variant="caption" color="text.secondary">{info.nota}</Typography>}
      {estrattori.filter((e) => !e.disponibile).map((e) => (
        <Typography key={e.nome} variant="caption" color="text.secondary" component="div">
          {e.etichetta} non disponibile: {e.nota}
        </Typography>
      ))}
      {error && <Alert severity="error" sx={{ mt: 1.5 }}>{error}</Alert>}

      {stato && (
        <Box sx={{ mt: 2 }}>
          {inCorso && (
            <>
              <Typography variant="body2">Documento {Math.min(stato.completati + 1, stato.totali)} di {stato.totali}…</Typography>
              <LinearProgress variant="determinate" value={(100 * stato.completati) / stato.totali} sx={{ my: 1 }} />
            </>
          )}
          {stato.stato === 'errore' && <Alert severity="error">{stato.errore}</Alert>}
          {stato.stato === 'completata' && (
            <Alert severity={stato.campi_corretti === stato.campi_totali ? 'success' : 'warning'} sx={{ mb: 1.5 }}>
              {label(stato.estrattore)}{stato.modello ? ` (${stato.modello})` : ''}: {stato.campi_corretti} campi corretti
              su {stato.campi_totali} in {stato.secondi_totali} s
              {stato.token_input ? `, ${stato.token_input} token in / ${stato.token_output} out` : ''}.
            </Alert>
          )}
          <Stack spacing={2}>
            {stato.documenti.map((d) => <DocumentoEstratto key={d.file} doc={d} onOpen={onOpen} />)}
          </Stack>
        </Box>
      )}
    </Paper>
  );
}
