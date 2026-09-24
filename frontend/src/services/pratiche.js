import api from './api';

export const ESITI = {
  conforme: { label: 'Conforme', color: 'success' },
  non_conforme: { label: 'Non conforme', color: 'error' },
  conforme_edilizio_non_conforme_catastale: { label: 'Conforme edilizio, non conforme catastale', color: 'warning' },
};

export const GRAVITA = {
  bassa: 'info',
  media: 'warning',
  alta: 'error',
};

export const getPratiche = async () => (await api.get('/pratiche')).data;

export const getPratica = async (id) => (await api.get(`/pratiche/${id}`)).data;

export const downloadRelazione = async (id, { confermate, note, tecnico }) => {
  const res = await api.post(`/pratiche/${id}/relazione`, { confermate, note, tecnico }, { responseType: 'blob' });
  const url = window.URL.createObjectURL(res.data);
  const link = document.createElement('a');
  link.href = url;
  link.download = `relazione_${id}.docx`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};
