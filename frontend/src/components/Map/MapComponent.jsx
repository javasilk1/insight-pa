import React from 'react';
import { useNavigate } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import { Box, Button } from '@mui/material';

const redIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

const yellowIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-yellow.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

const greenIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

export default function MapComponent({ center, buildings, zoom = 14 }) {
  const navigate = useNavigate();

  const getIcon = (riskScore) => {
    if (riskScore < 30) return greenIcon;
    if (riskScore < 70) return yellowIcon;
    return redIcon;
  };

  const getRiskLevel = (score) => {
    if (score < 30) return 'VERDE';
    if (score < 70) return 'GIALLO';
    return 'ROSSO';
  };

  return (
    <MapContainer center={center} zoom={zoom} style={{ height: '100%', width: '100%' }}>
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; OpenStreetMap contributors'
      />
      {buildings &&
        buildings.map((building) => (
          <Marker
            key={building.id}
            position={[building.latitude || 39.2414, building.longitude || 9.1837]}
            icon={getIcon(building.risk_score || 0)}
          >
            <Popup>
              <Box sx={{ minWidth: 200 }}>
                <strong>{building.address}</strong>
                <br />
                Rischio: <strong>{building.risk_score?.toFixed(1) || 0}%</strong> ({getRiskLevel(building.risk_score || 0)})
                <br />
                Area: {building.area_name}
                <br />
                <Button
                  size="small"
                  variant="contained"
                  onClick={() => navigate(`/edificio/${building.id}`)}
                  sx={{ mt: 1, width: '100%' }}
                >
                  Dettagli →
                </Button>
              </Box>
            </Popup>
          </Marker>
        ))}
    </MapContainer>
  );
}
