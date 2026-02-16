#!/bin/bash
set -e

echo "🔨 Ricostruendo containers..."
docker-compose down -v
docker-compose up --build -d

echo "⏳ Aspettando avvio dei servizi..."
sleep 10

echo "✅ Servizi avviati!"
echo ""
echo "📊 Stato containers:"
docker-compose ps

echo ""
echo "🧪 Test Mock Document Generator:"
echo ""
echo "1️⃣ Generando documento Verbale/Violazione Grave per building 1..."
curl -X POST "http://localhost:8000/api/mock/generate-document?building_id=11111111-1111-1111-1111-111111111111&document_type=verbale&scenario=violazione_grave" -s | jq .

echo ""
echo "2️⃣ Verificando documenti registrati per building 1..."
curl -X GET "http://localhost:8000/api/documents/building/11111111-1111-1111-1111-111111111111" -s | jq .

echo ""
echo "3️⃣ Verificando edificio con nuovo risk score..."
curl -X GET "http://localhost:8000/api/buildings/11111111-1111-1111-1111-111111111111" -s | jq '.risk_score, .violations'

echo ""
echo "🌐 Frontend: http://localhost:3001"
echo "🚀 Backend: http://localhost:8000/docs"
