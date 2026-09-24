import React, { useEffect, useState } from 'react';
import { Link as RouterLink, useParams } from 'react-router-dom';
import {
  Accordion, AccordionDetails, AccordionSummary, Alert, Box, Button, Card, CardContent, Chip, CircularProgress,
  Divider, Grid, Link, Paper, Stack, Tab, Tabs, TextField, ToggleButton, ToggleButtonGroup, Typography,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import DescriptionIcon from '@mui/icons-material/Description';
import { ESITI, GRAVITA, downloadRelazione, getPratica } from '../services/pratiche';

// La revisione del tecnico resta nel browser finché non esiste un backend multi-utente.
const loadReview = (id) => {
  try {
    return JSON.parse(localStorage.getItem(`revisione-${id}`)) || { stato: {}, note: {} };
  } catch {
    return { stato: {}, note: {} };
  }
};

const label = (s) => s.replaceAll('_', ' ').replace(/^./, (c) => c.toUpperCase());

function FonteChips({ fonti, onOpen }) {
  return (
    <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
      {fonti.map((f) => (
        <Chip
          key={`${f.file}-${f.pagina}`}
          size="small"
          variant="outlined"
          icon={<DescriptionIcon />}
          label={`${f.file.replace(/^\d+_|\.pdf$/g, '').replaceAll('_', ' ')} · pag. ${f.pagina}`}
          onClick={() => onOpen(f.file, f.pagina)}
        />
      ))}
    </Stack>
  );
}

function DifformitaCard({ d, stato, nota, onStato, onNota, onOpen }) {
  const border = stato === 'confermata' ? 'success.main' : stato === 'scartata' ? 'grey.400' : 'divider';
  return (
    <Card variant="outlined" sx={{ borderColor: border, opacity: stato === 'scartata' ? 0.6 : 1 }}>
      <CardContent>
        <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }} flexWrap="wrap" useFlexGap>
          <Typography variant="subtitle2">{d.id}</Typography>
          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>{label(d.tipo)}</Typography>
          <Chip size="small" label={`gravità ${d.gravita}`} color={GRAVITA[d.gravita]} />
          <Chip size="small" label={label(d.ambito)} variant="outlined" />
        </Stack>
        <Typography variant="body2" sx={{ mb: 1 }}>{d.descrizione}</Typography>
        {d.entita && <Typography variant="body2" sx={{ mb: 1 }}><b>Entità:</b> {d.entita}</Typography>}
        <Typography variant="body2" sx={{ mb: 1 }}><b>Valutazione:</b> {d.valutazione}</Typography>
        <Typography variant="caption" color="text.secondary" component="div" sx={{ mb: 1.5 }}>
          {d.riferimento_normativo}
        </Typography>
        <FonteChips fonti={d.fonti} onOpen={onOpen} />
        <Divider sx={{ my: 1.5 }} />
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} alignItems={{ sm: 'center' }}>
          <ToggleButtonGroup size="small" exclusive value={stato || null} onChange={(_, v) => onStato(v)}>
            <ToggleButton value="confermata" color="success">Conferma</ToggleButton>
            <ToggleButton value="scartata">Scarta</ToggleButton>
          </ToggleButtonGroup>
          <TextField
            id={`nota-${d.id}`}
            size="small"
            fullWidth
            placeholder="Nota del tecnico (finisce nella relazione)"
            value={nota || ''}
            onChange={(e) => onNota(e.target.value)}
          />
        </Stack>
      </CardContent>
    </Card>
  );
}

export default function PraticaDetail() {
  const { id } = useParams();
  const [pratica, setPratica] = useState(null);
  const [error, setError] = useState('');
  const [doc, setDoc] = useState({ file: null, pagina: 1, n: 0 });
  const [review, setReview] = useState(() => loadReview(id));
  const [tecnico, setTecnico] = useState('');
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    getPratica(id)
      .then((p) => {
        setPratica(p);
        setDoc({ file: p.documenti[0]?.file, pagina: 1, n: 0 });
      })
      .catch(() => setError('Pratica non trovata o backend non raggiungibile.'));
  }, [id]);

  useEffect(() => {
    try {
      localStorage.setItem(`revisione-${id}`, JSON.stringify(review));
    } catch {
      /* storage non disponibile: la revisione resta in memoria */
    }
  }, [id, review]);

  if (error) return <Box sx={{ p: 3 }}><Alert severity="error">{error}</Alert></Box>;
  if (!pratica) return <Box sx={{ p: 3 }}><CircularProgress /></Box>;

  const openDoc = (file, pagina = 1) => setDoc((d) => ({ file, pagina, n: d.n + 1 }));
  const current = pratica.documenti.find((d) => d.file === doc.file);
  const esito = ESITI[pratica.esito] || { label: pratica.esito, color: 'default' };
  const im = pratica.immobile;
  const confermate = pratica.difformita.filter((d) => review.stato[d.id] === 'confermata').map((d) => d.id);
  const daRivedere = pratica.difformita.filter((d) => !review.stato[d.id]).length;

  const setStato = (did, v) => setReview((r) => ({ ...r, stato: { ...r.stato, [did]: v } }));
  const setNota = (did, v) => setReview((r) => ({ ...r, note: { ...r.note, [did]: v } }));

  const exportDocx = async () => {
    setExporting(true);
    try {
      await downloadRelazione(id, { confermate, note: review.note, tecnico });
    } catch {
      setError('Export non riuscito: controlla che il backend sia avviato e riprova.');
    } finally {
      setExporting(false);
    }
  };

  return (
    <Box sx={{ p: { xs: 2, md: 3 } }}>
      <Link component={RouterLink} to="/pratiche" underline="hover">← Tutte le pratiche</Link>
      <Stack direction="row" spacing={2} alignItems="center" sx={{ mt: 1, mb: 0.5 }} flexWrap="wrap" useFlexGap>
        <Typography variant="h5">{im.indirizzo}</Typography>
        <Chip label={esito.label} color={esito.color} />
      </Stack>
      <Typography color="text.secondary" sx={{ mb: 2 }}>
        {pratica.id} · {im.intestatario} · Piano {im.piano} · Foglio {im.foglio}, Part. {im.particella}
        {im.sub ? `, Sub. ${im.sub}` : ''}
      </Typography>
      {pratica.origine === 'demo_ground_truth' && (
        <Alert severity="info" sx={{ mb: 2 }}>
          Pratica dimostrativa con dati fittizi: i risultati sono precompilati e mostrano cosa produrrà l'analisi automatica.
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={5}>
          <Stack spacing={2}>
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="overline" color="text.secondary">Sintesi</Typography>
              <Typography>{pratica.sintesi}</Typography>
            </Paper>

            {pratica.verifiche.map((v) => (
              <Alert key={v.tipo} severity="success" variant="outlined">
                <Typography variant="subtitle2">{label(v.tipo)}</Typography>
                <Typography variant="body2">{v.descrizione} {v.valutazione}</Typography>
                <Typography variant="caption" component="div" sx={{ my: 1 }}>{v.riferimento_normativo}</Typography>
                <FonteChips fonti={v.fonti} onOpen={openDoc} />
              </Alert>
            ))}

            <Typography variant="h6">
              Difformità ({pratica.difformita.length})
              {daRivedere > 0 && (
                <Typography component="span" color="text.secondary" sx={{ ml: 1 }}>{daRivedere} da rivedere</Typography>
              )}
            </Typography>
            {pratica.difformita.length === 0 && (
              <Typography color="text.secondary">Nessuna difformità rilevata.</Typography>
            )}
            {pratica.difformita.map((d) => (
              <DifformitaCard
                key={d.id}
                d={d}
                stato={review.stato[d.id]}
                nota={review.note[d.id]}
                onStato={(v) => setStato(d.id, v)}
                onNota={(v) => setNota(d.id, v)}
                onOpen={openDoc}
              />
            ))}

            <Accordion variant="outlined" disableGutters>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="subtitle1">Dati estratti dai documenti</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Stack spacing={1.5}>
                  {Object.entries(pratica.dati_estratti).map(([file, campi]) => (
                    <Box key={file}>
                      <Link component="button" variant="subtitle2" onClick={() => openDoc(file)}>{file}</Link>
                      {Object.entries(campi).map(([k, v]) => (
                        <Typography variant="body2" key={k}>
                          <Box component="span" color="text.secondary">{label(k)}:</Box>{' '}
                          {Array.isArray(v) ? v.join(', ') : typeof v === 'boolean' ? (v ? 'sì' : 'no') : String(v)}
                        </Typography>
                      ))}
                    </Box>
                  ))}
                </Stack>
              </AccordionDetails>
            </Accordion>

            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="subtitle1" sx={{ mb: 1 }}>Relazione</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
                La bozza in Word include solo le difformità confermate ({confermate.length}).
              </Typography>
              <Stack spacing={1.5} alignItems="flex-start">
                <TextField id="tecnico" size="small" label="Tecnico firmatario" value={tecnico}
                  onChange={(e) => setTecnico(e.target.value)} fullWidth />
                <Button variant="contained" onClick={exportDocx} disabled={exporting || daRivedere > 0}>
                  {exporting ? 'Preparazione…' : 'Esporta relazione'}
                </Button>
              </Stack>
              {daRivedere > 0 && (
                <Typography variant="caption" color="text.secondary">
                  Conferma o scarta tutte le difformità per esportare.
                </Typography>
              )}
            </Paper>
          </Stack>
        </Grid>

        <Grid item xs={12} md={7}>
          <Paper variant="outlined" sx={{ position: { md: 'sticky' }, top: 16 }}>
            <Tabs value={doc.file || false} onChange={(_, f) => openDoc(f)} variant="scrollable" scrollButtons="auto">
              {pratica.documenti.map((d) => (
                <Tab key={d.file} value={d.file} label={d.tipo} sx={{ textTransform: 'none' }} />
              ))}
            </Tabs>
            <Divider />
            {current && (
              <>
                <Typography variant="caption" color="text.secondary" sx={{ px: 2, py: 1, display: 'block' }}>
                  {current.file} · {current.pagine} {current.pagine === 1 ? 'pagina' : 'pagine'} · aperto a pagina {doc.pagina}
                </Typography>
                <Box
                  component="iframe"
                  key={`${current.file}-${doc.n}`}
                  title={current.file}
                  src={`${current.url}#page=${doc.pagina}`}
                  sx={{ width: '100%', height: { xs: 480, md: 'calc(100vh - 170px)' }, border: 0, display: 'block' }}
                />
              </>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}
