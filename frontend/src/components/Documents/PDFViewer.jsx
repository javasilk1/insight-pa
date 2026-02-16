import React, { useState, useEffect } from 'react';
import { Box, CircularProgress, Typography, Button } from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';

export default function PDFViewer({ fileUrl, fileName = 'document.pdf' }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleDownload = async () => {
    try {
      setLoading(true);
      const response = await fetch(fileUrl);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(link);
    } catch (err) {
      setError('Errore download PDF');
    } finally {
      setLoading(false);
    }
  };

  if (!fileUrl) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
        <Typography color="textSecondary">Nessun file disponibile</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ mb: 2, display: 'flex', gap: 1 }}>
        <Button
          startIcon={<DownloadIcon />}
          onClick={handleDownload}
          disabled={loading}
          variant="outlined"
        >
          Download
        </Button>
      </Box>

      {error && <Typography color="error">{error}</Typography>}

      {loading && <CircularProgress />}

      <Box
        sx={{
          flex: 1,
          border: '1px solid #ccc',
          borderRadius: 1,
          overflow: 'auto',
          backgroundColor: '#f5f5f5',
        }}
      >
        <iframe
          src={`${fileUrl}#toolbar=0`}
          style={{
            width: '100%',
            height: '100%',
            border: 'none',
          }}
          title="PDF Viewer"
        />
      </Box>
    </Box>
  );
}
