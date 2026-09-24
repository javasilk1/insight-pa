import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Alert, Box, Card, CardActionArea, CardContent, Chip, CircularProgress, Grid, Stack, Typography,
} from '@mui/material';
import { ESITI, getPratiche } from '../services/pratiche';

export default function PraticheList() {
  const navigate = useNavigate();
  const [pratiche, setPratiche] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    getPratiche().then(setPratiche).catch(() => setError('Impossibile caricare le pratiche. Il backend è avviato?'));
  }, []);

  return (
    <Box sx={{ maxWidth: 1100, mx: 'auto', p: 3 }}>
      <Typography variant="h4" gutterBottom>Verifiche dello stato legittimo</Typography>
      <Typography color="text.secondary" sx={{ mb: 2 }}>
        Per ogni pratica InsightPA confronta titoli edilizi, catasto e rilievo, e propone le difformità da verificare.
      </Typography>
      <Alert severity="info" sx={{ mb: 3 }}>
        Modalità demo: pratiche con dati fittizi e risultati precompilati. L'analisi automatica dei documenti è in sviluppo.
      </Alert>
      {error && <Alert severity="error">{error}</Alert>}
      {!pratiche && !error && <CircularProgress />}
      <Grid container spacing={2}>
        {(pratiche || []).map((p) => {
          const esito = ESITI[p.esito] || { label: p.esito, color: 'default' };
          return (
            <Grid item xs={12} md={6} key={p.id}>
              <Card variant="outlined" sx={{ height: '100%' }}>
                <CardActionArea onClick={() => navigate(`/pratiche/${p.id}`)} sx={{ height: '100%' }}>
                  <CardContent>
                    <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
                      <Typography variant="overline" color="text.secondary">{p.id}</Typography>
                      <Chip size="small" label={esito.label} color={esito.color} />
                    </Stack>
                    <Typography variant="h6">{p.indirizzo}</Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>{p.intestatario}</Typography>
                    <Typography variant="body2" sx={{ mb: 1 }}>{p.scenario}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {p.n_documenti} documenti · {p.n_difformita === 0 ? 'nessuna difformità' : `${p.n_difformita} difformità da verificare`}
                    </Typography>
                  </CardContent>
                </CardActionArea>
              </Card>
            </Grid>
          );
        })}
      </Grid>
    </Box>
  );
}
