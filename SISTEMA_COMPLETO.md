# �️ InsightPA - Sistema di Rilevazione Abusi Edilizi

## ✅ Implementazione Completata

### Backend (FastAPI)

#### 1. Buildings API
- **GET /api/buildings** - Lista tutti gli edifici
- **GET /api/buildings/nearby** - Edifici entro una distanza
- **GET /api/buildings/{id}** - Dettagli edificio con:
  - Dati catastali
  - Risk score calcolato in tempo reale
  - Lista documenti allegati
  - Violazioni registrate
  - Raccomandazione automatica (CRITICA/ALTA/MEDIA/BASSA)

#### 2. Risk API
- **POST /api/risk/calculate** - Calcola rischio da parametri
- **POST /api/risk/calculate-from-db/{building_id}** - Calcola da dati DB

#### 3. Risk History API
- **GET /api/risk-history/{building_id}** - Storico completo con ultimi 90 giorni
- **GET /api/risk-history/{building_id}/summary** - Tendenze 7/30 giorni
- **POST /api/risk-history/{building_id}** - Registra cambamento rischio

#### 4. Chat/Search API
- **POST /api/chat/query** - Query semantica su documenti
- **POST /api/chat/search-by-building/{building_id}** - Ricerca per edificio
- **GET /api/chat/similar-cases/{building_id}** - Casi simili via embeddings

#### 5. Documents API
- **POST /api/documents/upload** - Upload documento + auto risk-recalculation
- **GET /api/documents/building/{building_id}** - Documenti per edificio
- **DELETE /api/documents/{id}** - Rimuove documento
- **GET /api/documents/{id}/download** - Download documento

#### 6. Mock Generator API
- **POST /api/mock/generate-document** - Genera PDF test realistico
  - Parametri: `building_id`, `document_type`, `scenario`
  - Document types: verbale, satellite, planimetria, permesso, ordinanza, comunicazione
  - Scenarios: conforme, violazione_leggera, violazione_grave, ricorso

### Database (PostgreSQL 15 + PostGIS)

**Tabelle:**
- `buildings` - 60+ edifici con coordinate GEOGRAPHY
- `documents` - Documenti caricati (URL MinIO)
- `violations` - Violazioni rilevate
- `document_embeddings` - Embeddings Qdrant (384-dim)
- `risk_history` - Storico cambamenti rischio

### Servizi Principali

1. **RiskEngine** - 6 regole ponderate:
   - Superficie eccedente: +40%
   - Vincolo costiero (< 500m): +30%
   - Permesso mancante: +20%
   - Piscina abusiva: +15%
   - Variazione satellite: +10%
   - Documenti contrastanti: +25%

2. **QdrantService** - Vector search su 384-dim embeddings
3. **MinioService** - S3-compatible storage per documenti
4. **EmbeddingService** - all-MiniLM-L6-v2 da sentence-transformers
5. **DocumentFactory** - PDF generation realistico

### Frontend (React + Vite)

#### Pages
- **MapView** - Mappa Leaflet con marker color-coded
- **BuildingDetailPage** - Dettaglio completo edificio con:
  - Header con indirizzo e risk badge
  - 📊 Analisi rischio (violazioni, fattori, raccomandazione)
  - 📁 Documenti (tabs, viewer, upload)
  - 📈 Grafico storico rischio (Recharts)
  - 📋 Dati catastali

#### Components
- **MapComponent** - Leaflet map con tooltip
- **GenerateDocumentButton** - Dialog per generare doc test
- **PDFViewer** - iframe viewer con download

### Infrastruttura (Docker Compose)

**Servizi:**
- insightpa-postgres (PostgreSQL 15 + PostGIS 3.3)
- insightpa-backend (FastAPI Python 3.11)
- insightpa-frontend (Nginx + React build)
- insightpa-qdrant (Qdrant vector DB)
- insightpa-minio (MinIO S3)

## 🚀 Come Avviare

```bash
# Build e avvia
docker-compose up --build -d

# Richiedi buildings
curl http://localhost:8000/api/buildings

# Visualizza Swagger
http://localhost:8000/docs

# Frontend
http://localhost:3001/mappa
```

## 📊 Dati di Test

**60 edifici generati con distribuzione:**
- Verde (conforme): 38 edifici (63%)
- Giallo (review): 15 edifici (25%)
- Rosso (violazione): 7 edifici (12%)

**5 frazioni:**
- centro (downtown)
- flumini
- poetto (coastal)
- geremeas
- mare_pintau (coastal)

## 📝 Endpoint Test (Postman)

- `step1-buildings.json` - Buildings CRUD
- `step4-risk.json` - Risk calculation
- `step5-buildings.json` - Building detail
- `step6-qdrant.json` - Chat semantico
- `step8-documents.json` - Document management
- `step9-mock.json` - Mock document generation
- `step11-building-detail.json` - Building detail + history

## 🔑 Funzionalità Key

### Risk Engine
- **Real-time calculation**: ogni GET /api/buildings/{id} ricalcola
- **Weighted rules**: 6 regole configurabili
- **Color coding**: GREEN (<30), YELLOW (30-70), RED (≥70)

### Document Management
- **PDF generation**: ReportLab con header, QR codes, firme fake
- **MinIO storage**: S3-compatible con building_id organization
- **Qdrant indexing**: embedding automatico per semantic search
- **Risk trigger**: auto-recalculate e create violations se risk > 70%

### Semantic Search
- **384-dim vectors**: all-MiniLM-L6-v2
- **COSINE distance**: Qdrant similarity
- **Building filtering**: search per edificio
- **Similar cases**: trova edifici simili

### Raccomandazioni Automatiche
- CRITICA (≥80%): Ordinanza immediata
- ALTA (≥50%): Comunicazione formale
- MEDIA (≥30%): Verifica documentale
- BASSA (<30%): Monitoraggio

## 🛠 Tech Stack

**Backend:**
- FastAPI
- asyncpg (async PostgreSQL)
- PostGIS (geographic)
- Qdrant client
- MinIO client
- sentence-transformers
- reportlab
- faker

**Frontend:**
- React 18
- Vite
- Material-UI
- Leaflet maps
- Recharts
- Axios

**Infra:**
- PostgreSQL 15 + PostGIS 3.3
- Qdrant (vector DB)
- MinIO (S3)
- Nginx (reverse proxy + SPA)
- Docker Compose

## 📈 Metriche Implementate

- **Risk Score**: 0-100%
- **Risk History**: trace ultimi 90 giorni
- **Violation Count**: per edificio
- **Document Count**: per edificio
- **Change Frequency**: pattern 7/30 giorni
- **Triggered Rules**: trace quali regole attivate

## ✨ Features Completate

✅ Multi-tier architecture (DB, Vector, Object store)
✅ Risk calculation engine (6 weighted rules)
✅ Semantic search (Qdrant + embeddings)
✅ Document upload + PDF generation
✅ Building detail page (full analytics)
✅ Risk history tracking
✅ Automatic recommendations
✅ Mock data generation (60 buildings)
✅ API documentation (Swagger)
✅ React frontend with maps
✅ Real-time risk calculation
✅ PDF viewer integration

## 🔮 Possibili Estensioni

- [ ] Ordinanza generation (LaTeX PDF)
- [ ] Email notification system
- [ ] Photo upload (satellite compare)
- [ ] Export reports (PDF/Excel)
- [ ] Webhook integrations
- [ ] ML training pipeline
- [ ] Mobile app (React Native)
- [ ] Real estate price impact calc
