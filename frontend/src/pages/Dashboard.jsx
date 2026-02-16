import React, { useEffect, useState } from 'react';
import {
  Box,
  Paper,
  TextField,
  FormGroup,
  FormControlLabel,
  Checkbox,
  Typography,
  LinearProgress,
  CircularProgress,
  Card,
  CardContent,
  Button,
  Divider,
  List,
  ListItem,
  ListItemText,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import { useNavigate } from 'react-router-dom';

export default function Dashboard() {
  const navigate = useNavigate();
  const [buildings, setBuildings] = useState([]);
  const [filteredBuildings, setFilteredBuildings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedBuilding, setSelectedBuilding] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [docType, setDocType] = useState('verbale');
  const [uploadFile, setUploadFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [chatInput, setChatInput] = useState('');
  const [chatMessages, setChatMessages] = useState([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({
    all: true,
    verde: false,
    giallo: false,
    rosso: false,
  });
  const [frazioni, setFrazioni] = useState({
    all: true,
    centro: false,
    flumini: false,
    geremeas: false,
    poetto: false,
    mare_pintau: false,
  });

  useEffect(() => {
    fetchBuildings();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [buildings, searchTerm, filters, frazioni]);

  const fetchBuildings = async () => {
    try {
      const response = await fetch('/api/buildings');
      const data = await response.json();
      setBuildings(data);
      if (data?.length) {
        setSelectedBuilding(data[0]);
        fetchDocuments(data[0].id);
      }
    } catch (error) {
      console.error('Errore caricamento edifici:', error);
      setError('Impossibile caricare gli edifici. Verifica il backend.');
    } finally {
      setLoading(false);
    }
  };

  const fetchDocuments = async (buildingId) => {
    try {
      const response = await fetch(`/api/documents/building/${buildingId}`);
      const data = await response.json();
      setDocuments(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Errore caricamento documenti:', err);
      setDocuments([]);
    }
  };

  const getRiskLevel = (score) => {
    if (score < 30) return 'verde';
    if (score < 70) return 'giallo';
    return 'rosso';
  };

  const applyFilters = () => {
    let result = buildings;

    // Filtro rischio
    if (!filters.all) {
      result = result.filter((b) => {
        const level = getRiskLevel(b.risk_score);
        return filters[level];
      });
    }

    // Filtro frazioni
    if (!frazioni.all) {
      result = result.filter((b) => frazioni[b.quartu_frazione]);
    }

    // Filtro ricerca
    if (searchTerm) {
      result = result.filter((b) =>
        b.address.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    setFilteredBuildings(result);
  };

  const stats = {
    verde: buildings.filter((b) => getRiskLevel(b.risk_score) === 'verde').length,
    giallo: buildings.filter((b) => getRiskLevel(b.risk_score) === 'giallo').length,
    rosso: buildings.filter((b) => getRiskLevel(b.risk_score) === 'rosso').length,
    total: buildings.length,
  };

  const pct = (value) => (stats.total ? (value / stats.total) * 100 : 0);

  const handleFilterChange = (e) => {
    const { name, checked } = e.target;
    if (name === 'all') {
      setFilters({
        all: checked,
        verde: false,
        giallo: false,
        rosso: false,
      });
    } else {
      setFilters({
        ...filters,
        all: false,
        [name]: checked,
      });
    }
  };

  const handleFrazioniChange = (e) => {
    const { name, checked } = e.target;
    if (name === 'all') {
      setFrazioni({
        all: checked,
        centro: false,
        flumini: false,
        geremeas: false,
        poetto: false,
        mare_pintau: false,
      });
    } else {
      setFrazioni({
        ...frazioni,
        all: false,
        [name]: checked,
      });
    }
  };

  const handleSelectBuilding = (building) => {
    setSelectedBuilding(building);
    fetchDocuments(building.id);
  };

  const handleUpload = async () => {
    if (!selectedBuilding || !uploadFile) {
      setError('Seleziona un edificio e un file da caricare.');
      return;
    }
    setUploading(true);
    setError('');
    try {
      const formData = new FormData();
      formData.append('file', uploadFile);
      formData.append('building_id', selectedBuilding.id);
      formData.append('document_type', docType);

      const response = await fetch('/api/documents/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Upload fallito');
      }

      await fetchDocuments(selectedBuilding.id);
      setUploadFile(null);
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
        body: JSON.stringify({
          question,
          building_id: selectedBuilding?.id || null,
        }),
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

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      {/* Header */}
      <Paper sx={{ p: 2, backgroundColor: '#1565C0', color: 'white' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
            🏛️ INSIGHTPA · Rilevamento Abusivismo Edilizio
          </Typography>
          <Typography variant="h6">
            🧑‍⚖️ Comune di Quartu S.E.
          </Typography>
        </Box>
      </Paper>

      {/* Main Content */}
      <Box sx={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Sidebar */}
        <Paper
          sx={{
            width: 250,
            p: 2,
            borderRadius: 0,
            display: 'flex',
            flexDirection: 'column',
            gap: 3,
            overflowY: 'auto',
            backgroundColor: '#f5f5f5',
            borderRight: '1px solid #ddd',
          }}
        >
          {/* Ricerca */}
          <Box>
            <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              🔍 RICERCA
            </Typography>
            <TextField
              fullWidth
              size="small"
              placeholder="Cerca indirizzo"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              variant="outlined"
              InputProps={{
                startAdornment: <SearchIcon sx={{ mr: 1, color: 'action.active' }} />,
              }}
            />
          </Box>

          {/* Filtri Rischio */}
          <Box>
            <Typography variant="h6" sx={{ mb: 1 }}>
              📋 FILTRI RISCHIO
            </Typography>
            <FormGroup>
              <FormControlLabel
                control={
                  <Checkbox
                    name="all"
                    checked={filters.all}
                    onChange={handleFilterChange}
                  />
                }
                label={`☑ Tutti (${stats.total})`}
              />
              <FormControlLabel
                control={
                  <Checkbox
                    name="verde"
                    checked={filters.verde}
                    onChange={handleFilterChange}
                    disabled={filters.all}
                  />
                }
                label={`🟢 Verde (${stats.verde})`}
              />
              <FormControlLabel
                control={
                  <Checkbox
                    name="giallo"
                    checked={filters.giallo}
                    onChange={handleFilterChange}
                    disabled={filters.all}
                  />
                }
                label={`🟡 Giallo (${stats.giallo})`}
              />
              <FormControlLabel
                control={
                  <Checkbox
                    name="rosso"
                    checked={filters.rosso}
                    onChange={handleFilterChange}
                    disabled={filters.all}
                  />
                }
                label={`🔴 Rosso (${stats.rosso})`}
              />
            </FormGroup>
          </Box>

          {/* Filtri Frazioni */}
          <Box>
            <Typography variant="h6" sx={{ mb: 1 }}>
              🏘️ FRAZIONI
            </Typography>
            <FormGroup>
              <FormControlLabel
                control={
                  <Checkbox
                    name="all"
                    checked={frazioni.all}
                    onChange={handleFrazioniChange}
                  />
                }
                label="☑ Tutte"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    name="centro"
                    checked={frazioni.centro}
                    onChange={handleFrazioniChange}
                    disabled={frazioni.all}
                  />
                }
                label="⚫ Centro"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    name="flumini"
                    checked={frazioni.flumini}
                    onChange={handleFrazioniChange}
                    disabled={frazioni.all}
                  />
                }
                label="⚫ Flumini"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    name="geremeas"
                    checked={frazioni.geremeas}
                    onChange={handleFrazioniChange}
                    disabled={frazioni.all}
                  />
                }
                label="⚫ Geremeas"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    name="poetto"
                    checked={frazioni.poetto}
                    onChange={handleFrazioniChange}
                    disabled={frazioni.all}
                  />
                }
                label="⚫ Poetto"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    name="mare_pintau"
                    checked={frazioni.mare_pintau}
                    onChange={handleFrazioniChange}
                    disabled={frazioni.all}
                  />
                }
                label="⚫ Mare Pintau"
              />
            </FormGroup>
          </Box>
        </Paper>

        {/* Dashboard Content */}
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <Box sx={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 2, p: 2, overflow: 'auto' }}>
            {/* Lista edifici */}
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  🗂️ Edifici filtrati ({filteredBuildings.length})
                </Typography>
                {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
                {loading ? (
                  <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                    <CircularProgress />
                  </Box>
                ) : (
                  <List dense sx={{ maxHeight: 350, overflow: 'auto' }}>
                    {filteredBuildings.map((b) => (
                      <ListItem
                        key={b.id}
                        button
                        selected={selectedBuilding?.id === b.id}
                        onClick={() => handleSelectBuilding(b)}
                      >
                        <ListItemText
                          primary={b.address}
                          secondary={`Rischio: ${b.risk_score?.toFixed?.(1) || b.risk_score}% · ${b.quartu_frazione}`}
                        />
                        <Button size="small" onClick={() => navigate(`/edificio/${b.id}`)}>
                          Dettaglio
                        </Button>
                      </ListItem>
                    ))}
                  </List>
                )}
              </CardContent>
            </Card>

            {/* Dettaglio + Documenti */}
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  📁 Documenti collegati
                </Typography>
                {!selectedBuilding ? (
                  <Typography color="textSecondary">Seleziona un edificio.</Typography>
                ) : (
                  <>
                    <Typography variant="subtitle2" gutterBottom>
                      {selectedBuilding.address}
                    </Typography>
                    <Divider sx={{ mb: 2 }} />
                    <Box sx={{ mb: 2 }}>
                      <FormControl fullWidth size="small" sx={{ mb: 1 }}>
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
                      <Button
                        variant="contained"
                        fullWidth
                        sx={{ mt: 1 }}
                        disabled={uploading}
                        onClick={handleUpload}
                      >
                        {uploading ? 'Caricamento...' : 'Carica documento'}
                      </Button>
                    </Box>
                    <Divider sx={{ mb: 2 }} />
                    {documents.length === 0 ? (
                      <Typography color="textSecondary">Nessun documento trovato.</Typography>
                    ) : (
                      <List dense sx={{ maxHeight: 220, overflow: 'auto' }}>
                        {documents.map((doc) => (
                          <ListItem key={doc.id}>
                            <ListItemText
                              primary={doc.file_name}
                              secondary={`${doc.document_type} · ${new Date(doc.upload_date).toLocaleDateString('it-IT')}`}
                            />
                          </ListItem>
                        ))}
                      </List>
                    )}
                  </>
                )}
              </CardContent>
            </Card>

            {/* Chat */}
            <Card sx={{ gridColumn: '1 / span 2' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  💬 Chat investigativa
                </Typography>
                <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                  Usa la chat per interrogare i documenti (filtra automaticamente sull'edificio selezionato).
                </Typography>
                <Box sx={{ maxHeight: 200, overflow: 'auto', mb: 2, p: 1, backgroundColor: '#fafafa', borderRadius: 1 }}>
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
          </Box>

          {/* Statistiche */}
          <Paper
            sx={{
              p: 2,
              backgroundColor: '#fff',
              borderTop: '2px solid #1565C0',
            }}
          >
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                📊 STATISTICHE IN TEMPO REALE
              </Typography>
              <Typography variant="caption" color="textSecondary">
                🕐 Aggiornato: {new Date().toLocaleTimeString('it-IT')}
              </Typography>
            </Box>

            <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 2 }}>
              {/* Verde */}
              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                  <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                    🟢 {stats.verde} edifici conformi
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    {pct(stats.verde).toFixed(0)}%
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={pct(stats.verde)}
                  sx={{
                    backgroundColor: '#e0e0e0',
                    '& .MuiLinearProgress-bar': { backgroundColor: '#4CAF50' },
                  }}
                />
              </Box>

              {/* Giallo */}
              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                  <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                    🟡 {stats.giallo} sotto verifica
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    {pct(stats.giallo).toFixed(0)}%
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={pct(stats.giallo)}
                  sx={{
                    backgroundColor: '#e0e0e0',
                    '& .MuiLinearProgress-bar': { backgroundColor: '#FFC107' },
                  }}
                />
              </Box>

              {/* Rosso */}
              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                  <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                    🔴 {stats.rosso} abusi accertati
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    {pct(stats.rosso).toFixed(0)}%
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={pct(stats.rosso)}
                  sx={{
                    backgroundColor: '#e0e0e0',
                    '& .MuiLinearProgress-bar': { backgroundColor: '#F44336' },
                  }}
                />
              </Box>
            </Box>

            <Box sx={{ mt: 2, textAlign: 'center' }}>
              <Typography variant="body2" color="textSecondary">
                TOTALE: {stats.total} edifici monitorati a Quartu Sant'Elena
              </Typography>
            </Box>
          </Paper>
        </Box>
      </Box>
    </Box>
  );
}
