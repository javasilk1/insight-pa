import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, NavLink } from 'react-router-dom';
import { AppBar, Button, CssBaseline, ThemeProvider, Toolbar, Typography, createTheme } from '@mui/material';
import Dashboard from './pages/Dashboard';
import MapView from './pages/MapView';
import BuildingDetailPage from './pages/BuildingDetailPage';
import PraticheList from './pages/PraticheList';
import PraticaDetail from './pages/PraticaDetail';

const theme = createTheme({
  palette: {
    primary: { main: '#1565C0' },
    secondary: { main: '#f50057' },
  },
});

const navStyle = ({ isActive }) => ({ opacity: isActive ? 1 : 0.75, fontWeight: isActive ? 700 : 400 });

export default function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <AppBar position="static" elevation={0}>
          <Toolbar variant="dense">
            <Typography variant="h6" sx={{ mr: 3 }}>InsightPA</Typography>
            <Button color="inherit" component={NavLink} to="/pratiche" style={navStyle}>Pratiche</Button>
            <Button color="inherit" component={NavLink} to="/dashboard" style={navStyle}>Territorio</Button>
          </Toolbar>
        </AppBar>
        <Routes>
          <Route path="/" element={<Navigate to="/pratiche" replace />} />
          <Route path="/pratiche" element={<PraticheList />} />
          <Route path="/pratiche/:id" element={<PraticaDetail />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/mappa" element={<MapView />} />
          <Route path="/edificio/:id" element={<BuildingDetailPage />} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}
