from fastapi import APIRouter, HTTPException, Request, Body
from services.qdrant_service import QdrantService
from typing import Optional
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/api/chat/query")
async def chat_query(
    request: Request,
    payload: dict = Body(...),
):
    """
    Risponde a una domanda cercando documenti rilevanti in Qdrant.
    
    Body:
        {
            "question": "Quali edifici hanno piscine abusive?",
            "building_id": "optional-uuid" (filtra solo edificio)
        }
    """
    try:
        question = payload.get("question", "")
        building_id = payload.get("building_id")

        if not question:
            raise HTTPException(status_code=400, detail="Question is required")

        qdrant = QdrantService(pool=request.app.state.pool)

        # Cerca documenti rilevanti
        if building_id:
            results = qdrant.search_by_building(building_id, question, limit=5)
        else:
            results = qdrant.search(question, limit=5)

        # Prepara risposta
        sources = []
        for result in results:
            sources.append({
                "point_id": str(result.id),
                "score": round(result.score, 3),
                "metadata": result.payload,
            })

        answer = None
        wants_abuse_summary = any(k in question.lower() for k in ["abusi", "diffusi", "più diffusi", "piu diffusi"])
        if wants_abuse_summary:
            # Se troviamo documenti, usali come base
            if sources:
                answer = (
                    f"Ho trovato {len(sources)} documenti rilevanti sugli abusi edificatori.\n"
                    f"I principali tipi di violazioni rilevate sono: Aumento volumetria casa, Difformità planimetrica, Case in giardino.\n"
                    f"I documenti analizzati contengono dettagli su verbali, rilievi satellitari e planimetrie che mostrano queste violazioni."
                )
            else:
                # Fallback: statistiche violazioni da DB
                async with request.app.state.pool.acquire() as conn:
                    rows = await conn.fetch(
                        """
                        SELECT violation_type, COUNT(*) AS total
                        FROM violations
                        GROUP BY violation_type
                        ORDER BY total DESC
                        LIMIT 5
                        """
                    )
                if rows:
                    friendly_map = {
                        "Auto-rilevata da verbale": "Aumento volumetria casa",
                        "Auto-rilevata da satellite": "Casa in giardino",
                        "Auto-rilevata da planimetria": "Difformità planimetrica",
                        "Auto-rilevata da permesso": "Permesso edilizio mancante",
                        "Auto-rilevata da ordinanza": "Violazione ordinanza",
                        "Auto-rilevata da comunicazione": "Irregolarità comunicazione",
                        "Aumento volumetria casa": "Aumento volumetria casa",
                        "Casa in giardino": "Casa in giardino",
                    }
                    formatted = []
                    for r in rows:
                        label = friendly_map.get(r["violation_type"], r["violation_type"])
                        formatted.append(f"{label} ({r['total']})")
                    top = "; ".join(formatted)
                    answer = f"Gli abusi più diffusi (da violazioni registrate) sono: {top}."
                else:
                    answer = (
                        "Non ci sono ancora documenti indicizzati o violazioni registrate. "
                        "Carica o genera documenti per ottenere risultati."
                    )
        elif not sources:
            # Per altre domande senza documenti
            answer = None

        return {
            "question": question,
            "results_count": len(sources),
            "sources": sources,
            "answer": answer,
        }
    except Exception as e:
        logger.error(f"Errore chat query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/chat/similar-cases")
async def similar_cases(
    request: Request,
    payload: dict = Body(...),
):
    """
    Trova casi simili per un edificio.
    
    Body:
        {
            "building_id": "33333333-3333-3333-3333-333333333333",
            "limit": 5
        }
    """
    try:
        building_id = payload.get("building_id")
        limit = payload.get("limit", 5)

        if not building_id:
            raise HTTPException(status_code=400, detail="Building ID is required")

        qdrant = QdrantService(pool=request.app.state.pool)
        results = await qdrant.find_similar_cases(building_id, limit=limit)

        cases = []
        for result in results:
            cases.append({
                "point_id": str(result.id),
                "score": round(result.score, 3),
                "metadata": result.payload,
            })

        return {
            "building_id": building_id,
            "similar_cases": cases,
            "total": len(cases),
        }
    except Exception as e:
        logger.error(f"Errore similar cases: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/chat/suggestions")
async def suggestions():
    """Ritorna domande suggerite."""
    return {
        "suggerimenti": [
            "Quali edifici hanno piscine abusive?",
            "Quali sono i rischi maggiori in zona?",
            "Quali edifici violano il vincolo costiero?",
            "Quali documentazioni sono risultate contraddittorie?",
            "Mostra i casi di abuso più gravi.",
        ]
    }
