import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  Chip,
  Grid,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import MapComponent from '../components/Map/MapComponent';
import GenerateDocumentButton from '../components/Documents/GenerateDocumentButton';

export default function BuildingDetail() {
  const { id } = useParams();
  const [building, setBuilding] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBuilding();
  }, [id]);

  const fetchBuilding = async () => {
    try {
      const response = await fetch(`/api/buildings/${id}`);
      const data = await response.json();
      setBuilding(data);

      // Carica documenti dell'edificio
      const docsResponse = await fetch(`/api/documents/building/${id}`);
      const docsData = await docsResponse.json();
      setDocuments(docsData);
    } catch (error) {
      console.error('Errore caricamento edificio:', error);
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (score) => {
    if (score < 30) return '#4CAF50';
    if (score < 70) return '#FFC107';
    return '#F44336';
  };

  const getRiskLevel = (score) => {
    if (score < 30) return 'VERDE';
    if (score < 70) return 'GIALLO';
    return 'ROSSO';
  };

  if (loading) {
    return (
      <Container sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress />
      </Container>
    );
  }

  if (!building) {
    return (
      <Container>
        <Typography>Edificio non trovato</Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Grid container spacing={3}>
        {/* Mappa */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: 400 }}>
            <MapComponent
              center={[building.latitude, building.longitude]}
              buildings={[building]}
              zoom={18}
            />
          </Paper>
        </Grid>

        {/* Info edificio */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h5" gutterBottom>
                {building.address}
              </Typography>
              <Typography color="textSecondary" gutterBottom>
                {building.frazione}
              </Typography>

              <Box sx={{ mt: 2, mb: 2 }}>
                <Chip
                  label={`Risk: ${building.risk_score?.toFixed(1) || 0}%`}
                  sx={{
                    backgroundColor: getRiskColor(building.risk_score || 0),
                    color: 'white',
                    fontSize: '1.1em',
                    mr: 1,
                  }}
                />
                <Chip
                  label={getRiskLevel(building.risk_score || 0)}
                  variant="outlined"
                />
              </Box>

              <Typography variant="subtitle2">Dati Catastali:</Typography>
              <Typography variant="body2">
                Foglio: {building.cadastral_data?.foglio || 'N/A'}<br />
                Particella: {building.cadastral_data?.particella || 'N/A'}<br />
                Subalterno: {building.cadastral_data?.subalterno || 'N/A'}
              </Typography>

              <Typography variant="subtitle2" sx={{ mt: 2 }}>
                Area: {building.area || 'N/A'} m²<br />
                Data Costruzione: {building.year_built || 'N/A'}
              </Typography>

              <Box sx={{ mt: 3 }}>
                <GenerateDocumentButton
                  buildingId={id}
                  onDocumentUploaded={() => fetchBuilding()}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Documenti */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                📄 Documenti
              </Typography>
              {documents.length === 0 ? (
                <Typography color="textSecondary">Nessun documento</Typography>
              ) : (
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Tipo</TableCell>
                        <TableCell>Data Upload</TableCell>
                        <TableCell>Relevanza</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {documents.map((doc) => (
                        <TableRow key={doc.id}>
                          <TableCell>{doc.document_type}</TableCell>
                          <TableCell>
                            {new Date(doc.upload_date).toLocaleDateString('it-IT')}
                          </TableCell>
                          <TableCell>
                            {(doc.relevance_score * 100).toFixed(0)}%
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Violazioni */}
        {building.violations?.length > 0 && (
          <Grid item xs={12}>
            <Card sx={{ backgroundColor: '#ffebee' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  ⚠️ Violazioni ({building.violations.length})
                </Typography>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Tipo</TableCell>
                      <TableCell>Descrizione</TableCell>
                      <TableCell>Data</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {building.violations.map((v, i) => (
                      <TableRow key={i}>
                        <TableCell>{v.violation_type}</TableCell>
                        <TableCell>{v.description}</TableCell>
                        <TableCell>
                          {new Date(v.detection_date).toLocaleDateString('it-IT')}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Container>
  );
}
