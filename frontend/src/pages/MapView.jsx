import React, { useEffect, useState } from 'react';
import { Box, CircularProgress } from '@mui/material';
import MapComponent from '../components/Map/MapComponent';

export default function MapView() {
  const [buildings, setBuildings] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBuildings();
  }, []);

  const fetchBuildings = async () => {
    try {
      const response = await fetch('/api/buildings');
      const data = await response.json();
      setBuildings(data);
    } catch (error) {
      console.error('Errore caricamento edifici:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100vh', width: '100%' }}>
      <MapComponent center={[39.2414, 9.1837]} buildings={buildings} zoom={14} />
    </Box>
  );
}
