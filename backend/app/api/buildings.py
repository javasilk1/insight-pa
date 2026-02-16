from fastapi import APIRouter, HTTPException, Request
from models.schemas import Building
from services.risk_engine import risk_engine
from uuid import UUID
from typing import List, Optional
import json

router = APIRouter()

def get_recommendation(risk_score: float, violations: list) -> dict:
    """Genera raccomandazione automatica basata su severity"""
    if risk_score >= 80:
        return {
            "action": "ORDINANZA IMMEDIATA",
            "priority": "CRITICA",
            "description": "Violare il vincolo senza autorizzazione costituisce abuso edilizio. Ordinanza immediata per demolizione o messa in conformità.",
            "timeline": "24-48 ore",
        }
    elif risk_score >= 50:
        return {
            "action": "COMUNICAZIONE FORMALE",
            "priority": "ALTA",
            "description": "Possibili irregolarità catastali. Richiesta chiarimenti e documentazione.",
            "timeline": "7-14 giorni",
        }
    elif risk_score >= 30:
        return {
            "action": "VERIFICA DOCUMENTALE",
            "priority": "MEDIA",
            "description": "Segnalazioni minori. Richiedere conferma della conformità tramite documenti.",
            "timeline": "30 giorni",
        }
    else:
        return {
            "action": "MONITORAGGIO",
            "priority": "BASSA",
            "description": "Edificio conforme. Monitoring periodico raccomandfato.",
            "timeline": "Semestrale",
        }

@router.get("/api/buildings", response_model=List[Building])
async def get_buildings(request: Request):
    async with request.app.state.pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, address, area_name, risk_score, status FROM buildings")
        return [dict(row) for row in rows]

@router.get("/api/buildings/nearby", response_model=List[Building])
async def get_buildings_nearby(lat: float, lon: float, distance: float, request: Request):
    async with request.app.state.pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, address, area_name, risk_score, status FROM get_buildings_within_distance($1, $2, $3)",
            lat, lon, distance
        )
        return [dict(row) for row in rows]

@router.get("/api/buildings/{id}")
async def get_building(id: UUID, request: Request):
    async with request.app.state.pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, address, area_name, risk_score, status, cadastral_data, coordinates FROM buildings WHERE id = $1",
            str(id),
        )
        if not row:
            raise HTTPException(status_code=404, detail="Building not found")

        building = dict(row)
        raw_cadastral = building.get("cadastral_data") or "{}"
        cadastral = json.loads(raw_cadastral) if isinstance(raw_cadastral, str) else (raw_cadastral or {})

        # Calcolo rischio in tempo reale (fallback se dati catastali mancanti)
        if cadastral:
            risk_data = {
                "superficie_catastale": cadastral.get("superficie_catastale", 0),
                "superficie_autorizzata": cadastral.get("superficie_autorizzata", 0),
                "distanza_mare": cadastral.get("distanza_mare"),
                "has_permesso": cadastral.get("has_permesso", True),
                "has_piscina": cadastral.get("has_piscina", False),
                "has_permesso_piscina": cadastral.get("has_permesso_piscina", True),
                "satellite_change_pct": cadastral.get("satellite_change_pct", 0),
                "documenti_contrastanti": cadastral.get("documenti_contrastanti", False),
            }
            risk_result = risk_engine.calculate(risk_data)
        else:
            stored_score = float(building.get("risk_score") or 0)
            risk_result = {
                "risk_score": stored_score,
                "color": risk_engine.get_color(stored_score),
                "level": risk_engine.get_level(stored_score),
                "triggered_rules": [],
                "total_rules": len(risk_engine.rules),
                "rules_triggered": 0,
            }

        # Ottieni documenti
        documents = await conn.fetch(
            """
            SELECT id, file_name, file_url, document_type, upload_date
            FROM documents
            WHERE building_id = $1
            ORDER BY upload_date DESC
            """,
            str(id),
        )

        # Ottieni violazioni
        violations = await conn.fetch(
            """
            SELECT id, violation_type, severity, description, detected_date, unauthorized_area_m2
            FROM violations
            WHERE building_id = $1
            ORDER BY detected_date DESC
            """,
            str(id),
        )

        # Calcola raccomandazione
        recommendation = get_recommendation(risk_result["risk_score"], violations)

        # Estrai coordinate per distanza dal mare
        coords_text = building.get("coordinates", "")
        latitude = None
        longitude = None
        if coords_text:
            try:
                # Formato: "0101000020E6100000..." ma useremo il JSONB output
                latitude = cadastral.get("latitude")
                longitude = cadastral.get("longitude")
            except:
                pass

        return {
            "id": str(building["id"]),
            "address": building["address"],
            "area_name": building["area_name"],
            "risk_score": risk_result["risk_score"],
            "status": building["status"],
            "cadastral_data": cadastral,
            "risk_detail": risk_result,
            "documents": [
                {
                    "id": str(doc["id"]),
                    "file_name": doc["file_name"],
                    "file_url": doc["file_url"],
                    "document_type": doc["document_type"],
                    "upload_date": doc["upload_date"].isoformat() if doc["upload_date"] else None,
                }
                for doc in documents
            ],
            "violations": [
                {
                    "id": str(v["id"]),
                    "type": v["violation_type"],
                    "severity": v["severity"],
                    "description": v["description"],
                    "detected_date": v["detected_date"].isoformat() if v["detected_date"] else None,
                    "unauthorized_area_m2": float(v["unauthorized_area_m2"]) if v["unauthorized_area_m2"] else None,
                }
                for v in violations
            ],
            "recommendation": recommendation,
        }
