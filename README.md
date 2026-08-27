# 🏛️ InsightPA - Intelligent Building Compliance Analysis System

**InsightPA** is a full-stack platform that uses artificial intelligence and machine learning to analyze buildings, detect building code violations, assess regulatory risk, and manage construction-related documents.

## 🎯 Project Purpose

InsightPA helps public authorities, building professionals, and citizens to:

- **Automatically identify building violations** by analyzing documents (reports, satellite surveys, floor plans)
- **Assess the regulatory risk** of a building based on cadastral data and building compliance
- **Query documents via chat** to get intelligent answers about violations and non-conformities
- **Track risk history** over time to monitor how a situation evolves
- **Manage documents** centrally with metadata and semantic search

## 🏗️ Architecture

```
┌─────────────────┐
│   Frontend      │ React + Material-UI (Port 3001)
│   (Dashboard)   │
└────────┬────────┘
         │
         ↓
┌─────────────────────────────────────┐
│   Backend API (FastAPI)             │ Port 8000
│  ├─ /api/buildings                  │
│  ├─ /api/chat/query                 │
│  ├─ /api/documents                  │
│  ├─ /api/risk                       │
│  └─ /api/mock/generate-document     │
└────────┬────────────────────────────┘
         │
    ┌────┴──────────┬──────────────┬─────────────┐
    ↓               ↓              ↓             ↓
┌────────┐    ┌────────┐    ┌──────────┐   ┌──────────┐
│Postgres│    │ Qdrant │    │  MinIO   │   │LLM Model │
│Database│    │ Vector │    │ Storage  │   │Embeddings│
│        │    │  DB    │    │          │   │          │
└────────┘    └────────┘    └──────────┘   └──────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- macOS/Linux/Windows with WSL
- Node.js (for local frontend development)
- Python 3.9+ (for local backend development)

### Running with Docker

```bash
# Clone the repository
git clone git@github.com:javasilk1/insight-pa.git
cd insight-pa

# Start all services
docker-compose up -d

# Check that all containers are running
docker-compose ps
```

Access:
- **Frontend**: http://localhost:3001
- **Backend API**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001

## 💬 Intelligent Chat Queries

InsightPA's chat understands natural-language queries in Italian. Some examples:

### Queries about Building Violations
```
"What are the most common violations?"
→ Returns: "The most common violations are: Increased house volume (2), House in the garden (1)"

"What types of violations have been detected?"
→ Returns a list of violations with counts

"Which buildings have violations?"
→ Filters buildings by non-compliance risk
```

### Queries about Documents
```
"What documents do we have for this building?"
→ Lists reports, satellite surveys, floor plans

"Are there any conflicting documents?"
→ Indicates whether the documentation is in conflict

"Which permits are missing?"
→ Analyzes completeness of the documentation
```

### Queries about Risk
```
"What is the risk profile?"
→ Shows risk score, level (LOW/MEDIUM/HIGH/CRITICAL), factors

"How is the risk calculated?"
→ Explains the criteria used (surface area, distance from sea, permits, etc.)

"Which buildings have high risk?"
→ Filters by risk level
```

## 📊 API Endpoints

### Buildings
```bash
# Get list of buildings
GET /api/buildings

# Details for a specific building
GET /api/buildings/{building_id}

# Assess building risk
POST /api/risk
{
  "building_id": "uuid",
  "superficie_catastale": 120,
  "distanza_mare": 650,
  "has_permesso": true,
  "has_piscina": false
}
```

### Intelligent Chat
```bash
# Ask a question about documents/violations
POST /api/chat/query
{
  "question": "what are the most common violations?",
  "building_id": "uuid" (optional)
}

# Response
{
  "question": "what are the most common violations?",
  "answer": "The most common violations are: Increased house volume (2)",
  "results_count": 5,
  "sources": [...]
}
```

### Documents
```bash
# Upload a document
POST /api/documents/upload
multipart/form-data:
  - file: <PDF/JPEG>
  - building_id: uuid
  - document_type: report|satellite|floorplan|permit

# List documents for a building
GET /api/documents/building/{building_id}
```

### Demo Generation (Testing)
```bash
# Generate a mock document with violations
POST /api/mock/generate-document
Params:
  - building_id: uuid
  - document_type: report|satellite|floorplan
  - scenario: severe_violation|minor_violation|compliant
```

## 🗂️ Project Structure

```
insight-pa/
├── backend/                          # FastAPI Backend
│   ├── app/
│   │   ├── api/                     # API Endpoints
│   │   │   ├── buildings.py        # Building management
│   │   │   ├── chat.py             # Intelligent chat
│   │   │   ├── documents.py        # Document management
│   │   │   ├── risk.py             # Risk calculation
│   │   │   └── mock_generator.py   # Demo generation
│   │   ├── services/               # Business Logic
│   │   │   ├── llm_service.py      # LLM integration
│   │   │   ├── embedding_service.py # Embeddings
│   │   │   ├── qdrant_service.py   # Vector search
│   │   │   ├── minio_service.py    # Storage
│   │   │   └── risk_engine.py      # Risk scoring
│   │   ├── core/
│   │   │   ├── config.py           # Configuration
│   │   │   └── database.py         # DB connection
│   │   └── main.py                 # App entry point
│   └── requirements.txt             # Dependencies
│
├── frontend/                         # React Frontend
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx       # Main page
│   │   │   ├── BuildingDetailPage.jsx # Building details
│   │   │   └── MapView.jsx         # Map
│   │   ├── components/
│   │   │   ├── Chat/               # Chat interface
│   │   │   └── Documents/          # Document management
│   │   ├── services/
│   │   │   └── api.js              # API client
│   │   └── App.jsx                 # App routing
│   ├── index.html
│   └── package.json
│
├── init-db/                         # Database initialization
│   ├── 01_init.sql                # Schema
│   └── 02_insert_buildings.sql    # Demo data (auto-generated)
│
├── docker-compose.yml               # Service orchestration
└── README.md                        # This file
```

## 🔧 Configuration

### Environment Variables (.env)
```env
# Backend
DATABASE_URL=postgresql://user:password@postgres:5432/insightpa
QDRANT_HOST=qdrant
QDRANT_PORT=6333
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
LLM_API_KEY=your_llm_key  # If using an external API

# Frontend
VITE_API_URL=http://localhost:8000
```

## 📈 Risk Metrics

The system calculates risk based on:

| Factor | Weight | Description |
|--------|--------|-------------|
| **Cadastral surface area** | High | Delta between authorized and actual |
| **Distance from the sea** | Medium | Zone E restrictions (< 300m) |
| **Building permits** | High | Presence/absence of documentation |
| **Pool/Outbuildings** | Medium | Unauthorized structures |
| **Satellite-detected changes** | Medium | Modifications detected via satellite |
| **Conflicting documents** | High | Documentation inconsistencies |

**Risk Score**: 0-100
- 0-25: LOW (🟢)
- 25-50: MEDIUM (🟡)
- 50-75: HIGH (🔴)
- 75-100: CRITICAL (⚫)

## 🧪 Testing

### API Testing with Postman
```bash
# Import the collection from test-postman/
# Run requests step by step
```

### Local Tests
```bash
# Backend
cd backend
python -m pytest

# Frontend
cd frontend
npm run test
```

## 🚢 Deployment

### Docker Production
```bash
# Build images
docker-compose build

# Deploy
docker-compose up -d

# Check service health
docker-compose ps
docker-compose logs backend --tail=50
```

### Scale-up
```bash
# Scale the backend
docker-compose up -d --scale backend=3
```

## 📝 Important Notes

- **Embeddings**: Uses `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions)
- **Vector DB**: Qdrant for semantic document search
- **Storage**: MinIO for PDF/image files
- **Database**: PostgreSQL with JSONB support for cadastral data
- **Chat**: Smart fallback from Qdrant to the violations table

## 🤝 Contributing

To contribute:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/name`)
3. Commit your changes (`git commit -m 'Add feature'`)
4. Push to the branch (`git push origin feature/name`)
5. Open a Pull Request

## 📄 License

MIT License - see LICENSE file

## 👤 Contacts

- **Repository**: https://github.com/javasilk1/insight-pa
- **Issues**: Open an issue for bugs and feature requests

---

**Built with ❤️ for building transparency and legal compliance**
