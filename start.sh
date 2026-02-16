#!/bin/bash
set -e

echo "=================================="
echo "🚀 Ricostruzione Sistema Completo"
echo "=================================="

cd /Users/andreasalidu/Documents/newApp/insightPA-demo

# 1. Rimuovi container vecchi
echo ""
echo "1️⃣ Pulendo container precedenti..."
docker-compose down -v 2>/dev/null || true

# 2. Rigenera buildings
echo ""
echo "2️⃣ Generando 60 edifici di test..."
python backend/scripts/generate_buildings.py

# 3. Ricostruisci
echo ""
echo "3️⃣ Ricostruendo container con nuove dipendenze..."
docker-compose up --build -d

# 4. Aspetta avvio
echo ""
echo "4️⃣ Aspettando avvio servizi (30 secondi)..."
sleep 30

# 5. Verifica salute
echo ""
echo "5️⃣ Verificando stato container..."
docker-compose ps

# 6. Test API
echo ""
echo "6️⃣ Test API endpoint..."
echo ""
echo "   📍 GET /api/buildings (primi 3 edifici):"
curl -s http://localhost:8000/api/buildings 2>/dev/null | jq '.[0:3] | .[] | {id, address, quartu_frazione, risk_score}' || echo "⚠️ API non disponibile"

echo ""
echo "=================================="
echo "✅ Setup completato!"
echo "=================================="
echo ""
echo "🌐 Accedi ai servizi:"
echo "  Frontend:  http://localhost:3001"
echo "  Backend:   http://localhost:8000"
echo "  Swagger:   http://localhost:8000/docs"
echo "  MinIO:     http://localhost:9000"
echo "  Qdrant:    http://localhost:6333"
echo ""
echo "📝 Comandi utili:"
echo "  docker-compose logs -f backend       # Log backend"
echo "  docker-compose logs -f frontend      # Log frontend"
echo "  docker-compose ps                    # Stato container"
echo "  docker-compose down                  # Ferma tutto"
