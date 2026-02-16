from fastapi import APIRouter, HTTPException, Request
from services.risk_engine import risk_engine
from uuid import UUID
import json

router = APIRouter()


@router.post("/api/risk/calculate")
async def calculate_risk(building_data: dict):
    """Calcola il rischio in base ai dati forniti nel body."""
    result = risk_engine.calculate(building_data)
    return result


@router.post("/api/risk/calculate-from-db/{building_id}")
async def calculate_risk_from_db(building_id: UUID, request: Request):
    """Calcola il rischio in tempo reale recuperando i dati dal DB."""
    async with request.app.state.pool.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT id, address, quartu_frazione, risk_score, status,
                      cadastral_data
               FROM buildings WHERE id = $1""",
            str(building_id),
        )
        if not row:
            raise HTTPException(status_code=404, detail="Building not found")

        building = dict(row)
        raw_cadastral = building.get("cadastral_data") or "{}"
        cadastral = json.loads(raw_cadastral) if isinstance(raw_cadastral, str) else (raw_cadastral or {})

        # Costruisci building_data dal DB + cadastral_data JSONB
        building_data = {
            "superficie_catastale": cadastral.get("superficie_catastale", 0),
            "superficie_autorizzata": cadastral.get("superficie_autorizzata", 0),
            "distanza_mare": cadastral.get("distanza_mare"),
            "has_permesso": cadastral.get("has_permesso", True),
            "has_piscina": cadastral.get("has_piscina", False),
            "has_permesso_piscina": cadastral.get("has_permesso_piscina", True),
            "satellite_change_pct": cadastral.get("satellite_change_pct", 0),
            "documenti_contrastanti": cadastral.get("documenti_contrastanti", False),
        }

        result = risk_engine.calculate(building_data)
        result["building_id"] = str(building["id"])
        result["address"] = building["address"]
        result["quartu_frazione"] = building["quartu_frazione"]
        return result
