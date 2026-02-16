import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Box,
  LinearProgress,
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import api from '../../services/api';

export default function DocumentUploader({ buildingId, onDocumentUploaded }) {
  const [open, setOpen] = useState(false);
  const [documentType, setDocumentType] = useState('verbale');
  const [scenario, setScenario] = useState('conforme');
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleOpen = () => setOpen(true);
  const handleClose = () => setOpen(false);

  const handleGenerate = async () => {
    setLoading(true);
    setProgress(0);
    try {
      const response = await fetch(
        `/api/mock/generate-document?building_id=${buildingId}&document_type=${documentType}&scenario=${scenario}`,
        { method: 'POST' }
      );
      const data = await response.json();
      setProgress(100);
      onDocumentUploaded?.(data);
      handleClose();
    } catch (error) {
      console.error('Errore caricamento documento:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Button
        variant="contained"
        startIcon={<CloudUploadIcon />}
        onClick={handleOpen}
        sx={{ mb: 2 }}
      >
        🎲 Genera Documento Test
      </Button>

      <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
        <DialogTitle>Genera Documento Test</DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Tipo Documento</InputLabel>
            <Select
              value={documentType}
              label="Tipo Documento"
              onChange={(e) => setDocumentType(e.target.value)}
            >
              <MenuItem value="verbale">Verbale</MenuItem>
              <MenuItem value="satellite">Satellite</MenuItem>
              <MenuItem value="planimetria">Planimetria</MenuItem>
              <MenuItem value="permesso">Permesso</MenuItem>
              <MenuItem value="ordinanza">Ordinanza</MenuItem>
              <MenuItem value="comunicazione">Comunicazione</MenuItem>
            </Select>
          </FormControl>

          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Scenario</InputLabel>
            <Select
              value={scenario}
              label="Scenario"
              onChange={(e) => setScenario(e.target.value)}
            >
              <MenuItem value="conforme">Conforme</MenuItem>
              <MenuItem value="violazione_leggera">Violazione Leggera</MenuItem>
              <MenuItem value="violazione_grave">Violazione Grave</MenuItem>
              <MenuItem value="ricorso">Ricorso</MenuItem>
            </Select>
          </FormControl>

          {loading && <LinearProgress variant="determinate" value={progress} />}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Annulla</Button>
          <Button onClick={handleGenerate} variant="contained" disabled={loading}>
            Genera
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
