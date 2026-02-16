# 🏛️ InsightPA - Sistema Intelligente di Analisi Edilizia

**InsightPA** è una piattaforma full-stack che utilizza intelligenza artificiale e machine learning per analizzare edifici, identificare abusi edilizi, valutare il rischio normativo e gestire documenti costruttivi.

## 🎯 Scopo del Progetto

InsightPA aiuta le autorità pubbliche, professionisti del settore edilizio e cittadini a:

- **Identificare abusi edificatori** automaticamente analizzando documenti (verbali, rilievi satellitari, planimetrie)
- **Valutare il rischio normativo** di un edificio basato su dati catastali e conformità edilizia
- **Interrogare documenti via chat** per ottenere risposte intelligenti su violazioni e non conformità
- **Tracciare la storia dei rischi** nel tempo per monitorare l'evoluzione della situazione
- **Gestire documenti** in modo centralizzato con metadata e ricerca semantica

## 🏗️ Architettura

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
│PostSQL │    │ Qdrant │    │  MinIO   │   │LLM Model │
│Database│    │ Vector │    │ Storage  │   │Embeddings│
│        │    │  DB    │    │          │   │          │
└────────┘    └────────┘    └──────────┘   └──────────┘
```

## 🚀 Quick Start

### Prerequisiti
- Docker & Docker Compose
- macOS/Linux/Windows con WSL
- Node.js (per sviluppo frontend locale)
- Python 3.9+ (per sviluppo backend locale)

### Avvio in Docker

```bash
# Clona il repository
git clone git@github.com:javasilk1/insight-pa.git
cd insight-pa

# Avvia tutti i servizi
docker-compose up -d

# Verifica che tutti i container siano attivi
docker-compose ps
```

Accedi a:
- **Frontend**: http://localhost:3001
- **Backend API**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001

## 💬 Query di Chat Intelligente

Il chat di InsightPA comprende query naturali in italiano. Ecco alcuni esempi:

### Query su Abusi Edificatori
```
"Quali sono gli abusi più diffusi?"
→ Restituisce: "Gli abusi più diffusi sono: Aumento volumetria casa (2), Casa in giardino (1)"

"Che tipo di violazioni sono state rilevate?"
→ Restituisce lista delle violazioni con conteggio

"Quali edifici hanno abusi?"
→ Filtra edifici con rischio non conformità
```

### Query su Documenti
```
"Quali documenti abbiamo per questo edificio?"
→ Elenca verbali, rilievi satellitari, planimetrie

"Ci sono documenti contrastanti?"
→ Indica se documentazione è in conflitto

"Quali permessi sono mancanti?"
→ Analizza completezza della documentazione
```

### Query su Rischio
```
"Qual è il profilo di rischio?"
→ Mostra score di rischio, level (BASSO/MEDIO/ALTO/CRITICO), fattori

"Come si calcola il rischio?"
→ Spiega i criteri usati (superficie, distanza mare, permessi, etc)

"Quali edifici hanno rischio alto?"
→ Filtra per livello di rischio
```

## 📊 API Endpoints

### Edifici
```bash
# Ottieni lista edifici
GET /api/buildings

# Dettagli edificio specifico
GET /api/buildings/{building_id}

# Valuta rischio edificio
POST /api/risk
{
  "building_id": "uuid",
  "superficie_catastale": 120,
  "distanza_mare": 650,
  "has_permesso": true,
  "has_piscina": false
}
```

### Chat Intelligente
```bash
# Poni una domanda sui documenti/violazioni
POST /api/chat/query
{
  "question": "quali sono gli abusi più diffusi?",
  "building_id": "uuid" (opzionale)
}

# Risposta
{
  "question": "quali sono gli abusi più diffusi?",
  "answer": "Gli abusi più diffusi sono: Aumento volumetria casa (2)",
  "results_count": 5,
  "sources": [...]
}
```

### Documenti
```bash
# Upload documento
POST /api/documents/upload
multipart/form-data:
  - file: <PDF/JPEG>
  - building_id: uuid
  - document_type: verbale|satellite|planimetria|permesso

# Lista documenti per edificio
GET /api/documents/building/{building_id}
```

### Generazione Demo (Testing)
```bash
# Genera documento mock con violazioni
POST /api/mock/generate-document
Params:
  - building_id: uuid
  - document_type: verbale|satellite|planimetria
  - scenario: violazione_grave|violazione_leggera|conforme
```

## 🗂️ Struttura del Progetto

```
insight-pa/
├── backend/                          # FastAPI Backend
│   ├── app/
│   │   ├── api/                     # API Endpoints
│   │   │   ├── buildings.py        # Gestione edifici
│   │   │   ├── chat.py             # Chat intelligente
│   │   │   ├── documents.py        # Gestione documenti
│   │   │   ├── risk.py             # Calcolo rischio
│   │   │   └── mock_generator.py   # Generazione demo
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
│   │   │   ├── Dashboard.jsx       # Pagina principale
│   │   │   ├── BuildingDetailPage.jsx # Dettagli edificio
│   │   │   └── MapView.jsx         # Mappa
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
├── docker-compose.yml               # Orchestrazione servizi
└── README.md                        # Questo file
```

## 🔧 Configurazione

### Variabili di Ambiente (.env)
```env
# Backend
DATABASE_URL=postgresql://user:password@postgres:5432/insightpa
QDRANT_HOST=qdrant
QDRANT_PORT=6333
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
LLM_API_KEY=your_llm_key  # Se usando API esterna

# Frontend
VITE_API_URL=http://localhost:8000
```

## 📈 Metriche di Rischio

Il sistema calcola il rischio in base a:

| Fattore | Peso | Descrizione |
|---------|------|-------------|
| **Superficie catastale** | Alto | Delta tra autorizzato e reale |
| **Distanza mare** | Medio | Vincoli Zone E (< 300m) |
| **Permessi edili** | Alto | Presenza/assenza documentazione |
| **Piscina/Annessi** | Medio | Strutture non autorizzate |
| **Variazioni satellitari** | Medio | Modifiche rilevate da satellite |
| **Documenti contrastanti** | Alto | Incoerenze documentazione |

**Risk Score**: 0-100
- 0-25: BASSO (🟢)
- 25-50: MEDIO (🟡)
- 50-75: ALTO (🔴)
- 75-100: CRITICO (⚫)

## 🧪 Testing

### Test API con Postman
```bash
# Importa collection da test-postman/
# Esegui requests passo per passo
```

### Test Locali
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

# Verifica salute servizi
docker-compose ps
docker-compose logs backend --tail=50
```

### Scale-up
```bash
# Scala backend
docker-compose up -d --scale backend=3
```

## 📝 Note Importanti

- **Embeddings**: Utilizza `sentence-transformers/all-MiniLM-L6-v2` (384 dimensioni)
- **Vector DB**: Qdrant per ricerca semantica documenti
- **Storage**: MinIO per file PDF/immagini
- **Database**: PostgreSQL con support JSONB per dati catastali
- **Chat**: Fallback intelligente da Qdrant a violations table

## 🤝 Contribuire

Per contribuire:
1. Fai un fork del repository
2. Crea un branch feature (`git checkout -b feature/nome`)
3. Commit changes (`git commit -m 'Add feature'`)
4. Push al branch (`git push origin feature/nome`)
5. Apri una Pull Request

## 📄 Licenza

MIT License - vedi file LICENSE

## 👤 Contatti

- **Repository**: https://github.com/javasilk1/insight-pa
- **Issues**: Apri una issue per bug e feature requests

---

**Sviluppato con ❤️ per la trasparenza edilizia e la legalità**
