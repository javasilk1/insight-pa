from fastapi import APIRouter, HTTPException, Request
from services.mock_document_factory import document_factory
from services.minio_service import minio_service
from services.qdrant_service import QdrantService
from services.risk_engine import risk_engine
import uuid
from datetime import datetime

router = APIRouter()


@router.post("/api/mock/generate-document")
async def generate_mock_document(
    request: Request,
    building_id: str,
    document_type: str = "verbale",
    scenario: str = "conforme",
):
    """Genera un documento finto realistico e lo carica automaticamente."""
    if document_type not in document_factory.TIPI:
        raise HTTPException(status_code=400, detail=f"Tipo documento non valido: {document_type}")
    if scenario not in document_factory.SCENARI:
        raise HTTPException(status_code=400, detail=f"Scenario non valido: {scenario}")

    try:
        # Recupera edificio dal DB
        async with request.app.state.pool.acquire() as conn:
            building = await conn.fetchrow(
                "SELECT address, cadastral_data FROM buildings WHERE id = $1",
                building_id,
            )
            if not building:
                raise HTTPException(status_code=404, detail="Building not found")

        # Genera PDF
        pdf_data = document_factory.create(
            tipo=document_type,
            scenario=scenario,
            building_address=building["address"],
            building_id=building_id,
        )

        # Carica in MinIO
        filename = f"mock_{document_type}_{scenario}_{datetime.now().timestamp()}.pdf"
        file_url = minio_service.upload_file(pdf_data, filename, building_id)

        # Registra in DB
        doc_id = str(uuid.uuid4())
        async with request.app.state.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO documents (id, building_id, file_name, file_url, document_type, extracted_text, upload_date)
                VALUES ($1, $2, $3, $4, $5, $6, NOW())
                """,
                doc_id,
                building_id,
                filename,
                file_url,
                document_type,
                f"Documento generato: {document_type} - {scenario}",
            )

            # Genera embedding
            qdrant = QdrantService(pool=request.app.state.pool)
            await qdrant.upsert_document(
                doc_id,
                f"Documento {document_type}: {scenario}",
                {
                    "building_id": building_id,
                    "document_type": document_type,
                    "scenario": scenario,
                },
            )

            # Ricalcola rischio
            cadastral = building["cadastral_data"] or {}
            if isinstance(cadastral, str):
                try:
                    import json
                    cadastral = json.loads(cadastral)
                except Exception:
                    cadastral = {}
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

            # Aggiorna risk_score
            await conn.execute(
                "UPDATE buildings SET risk_score = $1 WHERE id = $2",
                risk_result["risk_score"],
                building_id,
            )

            # Se rischio > 70%, crea violazione
            if risk_result["risk_score"] > 70 and scenario != "conforme":
                violation_type = f"Auto-rilevata da {document_type}"
                if scenario == "violazione_grave":
                    violation_type = "Aumento volumetria casa"
                elif scenario == "violazione_leggera":
                    violation_type = "Casa in giardino"
                await conn.execute(
                    """
                    INSERT INTO violations (building_id, violation_type, description, status, severity, detected_date)
                    VALUES ($1, $2, $3, $4, $5, NOW()::date)
                    ON CONFLICT DO NOTHING
                    """,
                    building_id,
                    violation_type,
                    f"Risk score: {risk_result['risk_score']}%",
                    "open",
                    "high",
                )

        return {
            "document_id": doc_id,
            "file_url": file_url,
            "building_id": building_id,
            "document_type": document_type,
            "scenario": scenario,
            "risk_score": risk_result["risk_score"],
            "risk_level": risk_result["level"],
            "message": "Documento generato e caricato con successo",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
