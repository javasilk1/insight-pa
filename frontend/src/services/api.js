import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
});

export const getBuildings = async () => {
  const res = await api.get('/buildings');
  return res.data;
};

export const getBuildingById = async (id) => {
  const res = await api.get(`/buildings/${id}`);
  return res.data;
};

export const getViolations = async (buildingId) => {
  const res = await api.get(`/violations?building_id=${buildingId}`);
  return res.data;
};

export const getDocuments = async (buildingId) => {
  const res = await api.get(`/documents?building_id=${buildingId}`);
  return res.data;
};

export const chatQuery = async (question, buildingId = null) => {
  const res = await api.post('/chat/query', { question, building_id: buildingId });
  return res.data;
};

export const getSimilarCases = async (buildingId, limit = 5) => {
  const res = await api.post('/chat/similar-cases', { building_id: buildingId, limit });
  return res.data;
};

export const getSuggestions = async () => {
  const res = await api.get('/chat/suggestions');
  return res.data;
};

export default api;
