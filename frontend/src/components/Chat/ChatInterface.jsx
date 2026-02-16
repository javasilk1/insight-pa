import React, { useState } from 'react';
import { Box, TextField, Button, Paper, Typography, Chip, CircularProgress } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import api from '../../services/api';

export default function ChatInterface({ buildingId = null }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState([]);

  React.useEffect(() => {
    fetchSuggestions();
  }, []);

  const fetchSuggestions = async () => {
    try {
      const res = await api.get('/chat/suggestions');
      setSuggestions(res.data.suggerimenti || []);
    } catch (err) {
      console.error('Errore nel carico suggerimenti:', err);
    }
  };

  const handleSendMessage = async (text = input) => {
    if (!text.trim()) return;

    // Aggiungi messaggio utente
    setMessages(prev => [...prev, { role: 'user', text }]);
    setInput('');
    setLoading(true);

    try {
      const res = await api.post('/chat/query', {
        question: text,
        building_id: buildingId,
      });

      // Aggiungi risposta AI
      setMessages(prev => [...prev, {
        role: 'ai',
        text: res.data.risposta,
        confidenza: res.data.confidenza,
        fonti: res.data.fonti,
      }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'ai',
        text: 'Scusa, non ho potuto rispondere. Riprova più tardi.',
        confidenza: 0,
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ p: 2, display: 'flex', flexDirection: 'column', height: '100%', gap: 2 }}>
      <Typography variant="h6">Assistente InsightPA</Typography>

      {/* Cronologia messaggi */}
      <Box sx={{ flex: 1, overflow: 'auto', mb: 2 }}>
        {messages.length === 0 && (
          <Box>
            <Typography variant="body2" color="textSecondary" mb={2}>Domande suggerite:</Typography>
            {suggestions.map((sug, i) => (
              <Chip
                key={i}
                label={sug}
                onClick={() => handleSendMessage(sug)}
                sx={{ mr: 1, mb: 1 }}
              />
            ))}
          </Box>
        )}
        {messages.map((msg, i) => (
          <Paper key={i} sx={{ p: 1.5, mb: 1.5, backgroundColor: msg.role === 'user' ? '#e3f2fd' : '#f5f5f5' }}>
            <Typography variant="caption" color="primary" fontWeight="bold">
              {msg.role === 'user' ? 'Tu' : 'Assistente'}
            </Typography>
            <Typography variant="body2">{msg.text}</Typography>
            {msg.confidenza > 0 && (
              <Typography variant="caption" color="textSecondary">
                Confidenza: {(msg.confidenza * 100).toFixed(0)}%
              </Typography>
            )}
            {msg.fonti && msg.fonti.length > 0 && (
              <Box mt={1}>
                <Typography variant="caption" fontWeight="bold">Fonti:</Typography>
                {msg.fonti.map((fonte, j) => (
                  <Typography key={j} variant="caption" display="block">
                    • {fonte.titolo}
                  </Typography>
                ))}
              </Box>
            )}
          </Paper>
        ))}
      </Box>

      {/* Input */}
      <Box sx={{ display: 'flex', gap: 1 }}>
        <TextField
          fullWidth
          size="small"
          placeholder="Fai una domanda..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
          disabled={loading}
        />
        <Button
          variant="contained"
          endIcon={loading ? <CircularProgress size={20} /> : <SendIcon />}
          onClick={() => handleSendMessage()}
          disabled={loading || !input.trim()}
        >
          Invia
        </Button>
      </Box>
    </Box>
  );
}
