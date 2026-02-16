import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { CssBaseline, ThemeProvider, createTheme, Box } from '@mui/material';
import Dashboard from './pages/Dashboard';
import MapView from './pages/MapView';
import BuildingDetailPage from './pages/BuildingDetailPage';

const theme = createTheme({
  palette: {
    primary: { main: '#1565C0' },
    secondary: { main: '#f50057' },
  },
});

export default function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/mappa" element={<MapView />} />
          <Route path="/edificio/:id" element={<BuildingDetailPage />} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}
