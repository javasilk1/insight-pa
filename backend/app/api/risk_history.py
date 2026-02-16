from fastapi import APIRouter, HTTPException, Request
from typing import List, Optional
from datetime import datetime, timedelta

router = APIRouter()


@router.get("/api/risk-history/{building_id}")
async def get_risk_history(
    request: Request,
    building_id: str,
    days: int = 90,
    limit: int = 100,
):
    """Ottieni storico cambamenti del rischio per un edificio"""
    
    async with request.app.state.pool.acquire() as conn:
        # Verifica che l'edificio esista
        building = await conn.fetchrow(
            "SELECT id, address, risk_score FROM buildings WHERE id = $1",
            building_id,
        )
        if not building:
            raise HTTPException(status_code=404, detail="Edificio non trovato")

        # Ottieni storico rischio
        history = await conn.fetch(
            """
            SELECT 
                id,
                old_risk_score,
                new_risk_score,
                triggered_rules,
                reason,
                recorded_at
            FROM risk_history
            WHERE building_id = $1
                AND recorded_at > NOW() - INTERVAL '1 day' * $2
            ORDER BY recorded_at DESC
            LIMIT $3
            """,
            building_id,
            days,
            limit,
        )

        # Formatta risposta
        history_items = []
        for record in history:
            history_items.append({
                "id": str(record["id"]),
                "old_risk_score": float(record["old_risk_score"]) if record["old_risk_score"] else None,
                "new_risk_score": float(record["new_risk_score"]),
                "triggered_rules": record["triggered_rules"] or [],
                "reason": record["reason"],
                "recorded_at": record["recorded_at"].isoformat() if record["recorded_at"] else None,
            })

        return {
            "building_id": building_id,
            "address": building["address"],
            "current_risk_score": float(building["risk_score"]),
            "history": history_items,
            "total_changes": len(history_items),
        }


@router.post("/api/risk-history/{building_id}")
async def record_risk_change(
    request: Request,
    building_id: str,
    old_risk_score: Optional[float] = None,
    new_risk_score: float = None,
    triggered_rules: List[str] = [],
    reason: str = "",
):
    """Registra un cambamento nel risk score (uso interno)"""
    
    async with request.app.state.pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO risk_history (
                building_id,
                old_risk_score,
                new_risk_score,
                triggered_rules,
                reason,
                recorded_at
            ) VALUES ($1, $2, $3, $4, $5, NOW())
            """,
            building_id,
            old_risk_score,
            new_risk_score,
            triggered_rules,
            reason,
        )
        
        return {"status": "ok", "message": "Risk change recorded"}


@router.get("/api/risk-history/{building_id}/summary")
async def get_risk_summary(
    request: Request,
    building_id: str,
):
    """Ottieni riassunto delle tendenze di rischio"""
    
    async with request.app.state.pool.acquire() as conn:
        # Cambamento negli ultimi 7 giorni
        week_change = await conn.fetchrow(
            """
            SELECT 
                MIN(new_risk_score) as min_score,
                MAX(new_risk_score) as max_score,
                COUNT(*) as change_count
            FROM risk_history
            WHERE building_id = $1
                AND recorded_at > NOW() - INTERVAL '7 days'
            """,
            building_id,
        )

        # Cambamento negli ultimi 30 giorni
        month_change = await conn.fetchrow(
            """
            SELECT 
                MIN(new_risk_score) as min_score,
                MAX(new_risk_score) as max_score,
                COUNT(*) as change_count
            FROM risk_history
            WHERE building_id = $1
                AND recorded_at > NOW() - INTERVAL '30 days'
            """,
            building_id,
        )

        # Règle più frequente
        top_rule = await conn.fetchrow(
            """
            SELECT unnest(triggered_rules) as rule
            FROM risk_history
            WHERE building_id = $1
            GROUP BY rule
            ORDER BY COUNT(*) DESC
            LIMIT 1
            """,
            building_id,
        )

        return {
            "building_id": building_id,
            "trend_7_days": {
                "min_score": float(week_change["min_score"]) if week_change["min_score"] else None,
                "max_score": float(week_change["max_score"]) if week_change["max_score"] else None,
                "changes": week_change["change_count"] or 0,
            },
            "trend_30_days": {
                "min_score": float(month_change["min_score"]) if month_change["min_score"] else None,
                "max_score": float(month_change["max_score"]) if month_change["max_score"] else None,
                "changes": month_change["change_count"] or 0,
            },
            "most_triggered_rule": top_rule["rule"] if top_rule else None,
        }
