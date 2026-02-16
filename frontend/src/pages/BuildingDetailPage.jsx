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
  Tabs,
  Tab,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  TextField,
  Divider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import GenerateDocumentButton from '../components/Documents/GenerateDocumentButton';
import PDFViewer from '../components/Documents/PDFViewer';
import DownloadIcon from '@mui/icons-material/Download';
import WarningIcon from '@mui/icons-material/Warning';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import InsertDriveFileIcon from '@mui/icons-material/InsertDriveFile';

export default function BuildingDetailPage() {
  const { id } = useParams();
  const [building, setBuilding] = useState(null);
  const [history, setHistory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState(0);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [showPDF, setShowPDF] = useState(false);
  const [docType, setDocType] = useState('verbale');
  const [uploadFile, setUploadFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [chatInput, setChatInput] = useState('');
  const [chatMessages, setChatMessages] = useState([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchData();
  }, [id]);

  const fetchData = async () => {
    try {
      const [buildingRes, historyRes] = await Promise.all([
        fetch(`/api/buildings/${id}`),
        fetch(`/api/risk-history/${id}`),
      ]);

      const buildingData = await buildingRes.json();
      const historyData = await historyRes.json();

      setBuilding(buildingData);
      setHistory(historyData);
    } catch (error) {
      console.error('Errore caricamento dati:', error);
      setError('Impossibile caricare i dati edificio.');
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async () => {
    if (!uploadFile) {
      setError('Seleziona un file da caricare.');
      return;
    }
    setUploading(true);
    setError('');
    try {
      const formData = new FormData();
      formData.append('file', uploadFile);
      formData.append('building_id', id);
      formData.append('document_type', docType);

      const response = await fetch('/api/documents/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Upload fallito');
      }
      setUploadFile(null);
      await fetchData();
    } catch (err) {
      console.error(err);
      setError('Errore durante il caricamento del documento.');
    } finally {
      setUploading(false);
    }
  };

  const handleChatSend = async () => {
    if (!chatInput.trim()) return;
    const question = chatInput.trim();
    setChatInput('');
    setChatLoading(true);
    setChatMessages((prev) => [...prev, { role: 'user', content: question }]);

    try {
      const response = await fetch('/api/chat/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, building_id: id }),
      });
      const data = await response.json();
      const sourcesText = (data.sources || [])
        .slice(0, 3)
        .map((s) => `• ${s.metadata?.document_type || 'documento'} (score ${s.score})`)
        .join('\n');

      const content = data.answer
        ? data.answer
        : data.results_count
          ? `Trovati ${data.results_count} documenti rilevanti.\n${sourcesText}`
          : 'Nessun documento rilevante trovato.';

      setChatMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content,
        },
      ]);
    } catch (err) {
      setChatMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Errore durante la ricerca. Riprova.' },
      ]);
    } finally {
      setChatLoading(false);
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

  const getSeverityColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critica':
        return '#D32F2F';
      case 'alta':
        return '#F57C00';
      case 'media':
        return '#FBC02D';
      case 'bassa':
        return '#388E3C';
      default:
        return '#757575';
    }
  };

  const formatRuleLabel = (rule) => {
    if (!rule) return 'regola_sconosciuta';
    if (typeof rule === 'string') return rule.replace(/_/g, ' ');
    if (typeof rule === 'object') {
      const name = rule.rule || rule.name || 'regola_sconosciuta';
      return String(name).replace(/_/g, ' ');
    }
    return String(rule).replace(/_/g, ' ');
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

  // Prepara dati grafico storico
  const chartData = history?.history
    ?.slice()
    .reverse()
    .map((item, idx) => ({
      timestamp: new Date(item.recorded_at).toLocaleDateString('it-IT'),
      risk_score: item.new_risk_score,
      timestamp_full: item.recorded_at,
    })) || [];

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Paper sx={{ p: 3, mb: 3, backgroundColor: '#f5f5f5' }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={8}>
            <Typography variant="h4" gutterBottom>
              {building.address}
            </Typography>
            <Typography color="textSecondary" variant="subtitle1" gutterBottom>
              {building.quartu_frazione.toUpperCase()} • Distanza mare:{' '}
              {building.cadastral_data?.distanza_mare || 'N/A'} m
            </Typography>
          </Grid>
          <Grid item xs={12} md={4} sx={{ textAlign: 'right' }}>
            <Box sx={{ mb: 2 }}>
              <Chip
                label={`${building.risk_score?.toFixed(1) || 0}%`}
                sx={{
                  backgroundColor: getRiskColor(building.risk_score || 0),
                  color: 'white',
                  fontSize: '1.3em',
                  padding: '20px 10px',
                  mr: 1,
                }}
              />
              <Chip
                label={getRiskLevel(building.risk_score || 0)}
                variant="outlined"
                sx={{ fontSize: '1em', padding: '15px 10px' }}
              />
            </Box>
          </Grid>
        </Grid>
      </Paper>

      <Grid container spacing={3}>
        {/* Sezione Analisi Rischio */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                📊 ANALISI RISCHIO
              </Typography>

              {/* Motivazioni */}
              <Box sx={{ mb: 2, p: 2, backgroundColor: '#f9f9f9', borderRadius: 1 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Fattori di rischio attivati:
                </Typography>
                {building.risk_detail?.triggered_rules?.length > 0 ? (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {building.risk_detail.triggered_rules.map((rule, idx) => (
                      <Chip
                        key={idx}
                        label={formatRuleLabel(rule)}
                        size="small"
                        sx={{ backgroundColor: '#fff3cd' }}
                      />
                    ))}
                  </Box>
                ) : (
                  <Typography variant="body2" color="textSecondary">
                    Nessun fattore critico
                  </Typography>
                )}
              </Box>

              {/* Violazioni */}
              {building.violations?.length > 0 && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    ⚠️ Violazioni ({building.violations.length}):
                  </Typography>
                  {building.violations.map((v) => (
                    <Card key={v.id} sx={{ mb: 1, backgroundColor: '#ffebee' }}>
                      <CardContent sx={{ py: 1, px: 2 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                          <Box>
                            <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                              {v.type}
                            </Typography>
                            <Typography variant="caption" color="textSecondary">
                              {v.description}
                            </Typography>
                          </Box>
                          <Chip
                            label={v.severity}
                            size="small"
                            sx={{
                              backgroundColor: getSeverityColor(v.severity),
                              color: 'white',
                            }}
                          />
                        </Box>
                      </CardContent>
                    </Card>
                  ))}
                </Box>
              )}

              {/* Raccomandazione */}
              <Card sx={{ backgroundColor: '#e3f2fd', border: '2px solid #2196F3' }}>
                <CardContent>
                  <Typography
                    variant="subtitle2"
                    sx={{ fontWeight: 'bold', color: '#1976D2', mb: 1 }}
                  >
                    {building.recommendation?.action}
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    {building.recommendation?.description}
                  </Typography>
                  <Chip
                    label={`Priority: ${building.recommendation?.priority}`}
                    size="small"
                    sx={{ mt: 1 }}
                  />
                </CardContent>
              </Card>
            </CardContent>
          </Card>
        </Grid>

        {/* Sezione Mappa rimossa per demo */}

        {/* Sezione Documenti + Upload */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">
                  📁 DOCUMENTI ({building.documents?.length || 0})
                </Typography>
                <GenerateDocumentButton
                  buildingId={id}
                  onDocumentUploaded={() => fetchData()}
                />
              </Box>

              {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

              <Box sx={{ display: 'flex', gap: 2, mb: 2, alignItems: 'center' }}>
                <FormControl size="small" sx={{ minWidth: 180 }}>
                  <InputLabel>Tipo documento</InputLabel>
                  <Select
                    value={docType}
                    label="Tipo documento"
                    onChange={(e) => setDocType(e.target.value)}
                  >
                    <MenuItem value="verbale">Verbale</MenuItem>
                    <MenuItem value="satellite">Satellite</MenuItem>
                    <MenuItem value="planimetria">Planimetria</MenuItem>
                    <MenuItem value="permesso">Permesso</MenuItem>
                    <MenuItem value="ordinanza">Ordinanza</MenuItem>
                    <MenuItem value="comunicazione">Comunicazione</MenuItem>
                  </Select>
                </FormControl>
                <input
                  type="file"
                  onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                />
                <Button variant="contained" onClick={handleUpload} disabled={uploading}>
                  {uploading ? 'Caricamento...' : 'Carica documento'}
                </Button>
              </Box>

              {building.documents?.length === 0 ? (
                <Typography color="textSecondary">Nessun documento caricato</Typography>
              ) : (
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
                        <TableCell>Tipo</TableCell>
                        <TableCell>Nome File</TableCell>
                        <TableCell>Data Upload</TableCell>
                        <TableCell align="center">Azioni</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {building.documents.map((doc) => (
                        <TableRow key={doc.id}>
                          <TableCell>
                            <Chip label={doc.document_type} size="small" />
                          </TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <InsertDriveFileIcon sx={{ fontSize: '1.2em' }} />
                              {doc.file_name}
                            </Box>
                          </TableCell>
                          <TableCell>
                            {new Date(doc.upload_date).toLocaleDateString('it-IT')}
                          </TableCell>
                          <TableCell align="center">
                            <Button
                              size="small"
                              onClick={() => {
                                setSelectedDocument(doc);
                                setShowPDF(true);
                              }}
                            >
                              Visualizza
                            </Button>
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

        {/* Sezione Chat */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                💬 CHAT INVESTIGATIVA
              </Typography>
              <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                Interroga i documenti collegati all'edificio.
              </Typography>
              <Box sx={{ maxHeight: 220, overflow: 'auto', mb: 2, p: 1, backgroundColor: '#fafafa', borderRadius: 1 }}>
                {chatMessages.length === 0 ? (
                  <Typography color="textSecondary">Nessuna conversazione.</Typography>
                ) : (
                  chatMessages.map((m, idx) => (
                    <Box key={idx} sx={{ mb: 1 }}>
                      <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
                        {m.role === 'user' ? 'Tu' : 'Assistente'}
                      </Typography>
                      <Typography variant="body2" sx={{ whiteSpace: 'pre-line' }}>
                        {m.content}
                      </Typography>
                    </Box>
                  ))
                )}
              </Box>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <TextField
                  fullWidth
                  size="small"
                  placeholder="Fai una domanda sui documenti..."
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleChatSend()}
                />
                <Button variant="contained" onClick={handleChatSend} disabled={chatLoading}>
                  {chatLoading ? '...' : 'Invia'}
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Sezione Storico Rischio */}
        {history?.history?.length > 0 && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  📈 STORICO RISCHIO (ultimi {history.history.length} cambiamenti)
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" />
                    <YAxis domain={[0, 100]} />
                    <Tooltip
                      content={({ active, payload }) => {
                        if (active && payload && payload[0]) {
                          return (
                            <Paper sx={{ p: 1 }}>
                              <Typography variant="caption">
                                {payload[0].payload.timestamp}
                              </Typography>
                              <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                                Risk: {payload[0].value.toFixed(1)}%
                              </Typography>
                            </Paper>
                          );
                        }
                        return null;
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="risk_score"
                      stroke="#1976D2"
                      dot={{ fill: '#1976D2', r: 4 }}
                      connectNulls
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Dati Catastali */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                📋 DATI CATASTALI
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center', backgroundColor: '#f5f5f5' }}>
                    <Typography variant="caption" color="textSecondary">
                      Superficie Catastale
                    </Typography>
                    <Typography variant="h6">
                      {building.cadastral_data?.superficie_catastale} m²
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center', backgroundColor: '#f5f5f5' }}>
                    <Typography variant="caption" color="textSecondary">
                      Superficie Autorizzata
                    </Typography>
                    <Typography variant="h6">
                      {building.cadastral_data?.superficie_autorizzata} m²
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center', backgroundColor: '#f5f5f5' }}>
                    <Typography variant="caption" color="textSecondary">
                      Distanza Mare
                    </Typography>
                    <Typography variant="h6">
                      {building.cadastral_data?.distanza_mare} m
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center', backgroundColor: '#f5f5f5' }}>
                    <Typography variant="caption" color="textSecondary">
                      Variazione Satellite
                    </Typography>
                    <Typography variant="h6">
                      {building.cadastral_data?.satellite_change_pct}%
                    </Typography>
                  </Paper>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* PDF Viewer Dialog */}
      <Dialog open={showPDF} onClose={() => setShowPDF(false)} maxWidth="lg" fullWidth>
        <DialogTitle>{selectedDocument?.file_name}</DialogTitle>
        <DialogContent sx={{ height: 600 }}>
          <PDFViewer fileUrl={selectedDocument?.file_url} />
        </DialogContent>
      </Dialog>
    </Container>
  );
}
