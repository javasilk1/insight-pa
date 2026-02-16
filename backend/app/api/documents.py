from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from services.minio_service import minio_service
from services.qdrant_service import QdrantService
from services.risk_engine import risk_engine
import uuid
from datetime import datetime
import json

router = APIRouter()


@router.post("/api/documents/upload")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    building_id: str = Form(...),
    document_type: str = Form("generale"),
):
    """Carica un documento e genera embedding + calcola rischio."""
    try:
        file_data = await file.read()
        filename = f"{document_type}_{datetime.now().timestamp()}_{file.filename}"

        # Salva in MinIO
        file_url = minio_service.upload_file(file_data, filename, building_id)

        # Inserisci record in documents
        doc_id = str(uuid.uuid4())
        async with request.app.state.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO documents (id, building_id, file_name, file_url, document_type, extracted_text, upload_date)
                VALUES ($1, $2, $3, $4, $5, $6, NOW())
                """,
                doc_id,
                building_id,
                file.filename,
                file_url,
                document_type,
                f"Documento {document_type} caricato",
            )

            # Genera embedding e carica in Qdrant
            qdrant = QdrantService(pool=request.app.state.pool)
            await qdrant.upsert_document(
                doc_id,
                f"Documento {document_type}: {file.filename}",
                {"building_id": building_id, "document_type": document_type},
            )

            # Ricalcola rischio edificio
            building = await conn.fetchrow(
                "SELECT cadastral_data FROM buildings WHERE id = $1",
                building_id,
            )

            risk_result = {"risk_score": 0}
            if building:
                cadastral_data = building["cadastral_data"]
                if isinstance(cadastral_data, str):
                    cadastral = json.loads(cadastral_data)
                else:
                    cadastral = cadastral_data or {}

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

                # Aggiorna risk_score in building
                await conn.execute(
                    "UPDATE buildings SET risk_score = $1 WHERE id = $2",
                    risk_result["risk_score"],
                    building_id,
                )

                # Se rischio > 70%, crea violazione automatica
                if risk_result["risk_score"] > 70:
                    await conn.execute(
                        """
                        INSERT INTO violations (building_id, violation_type, description, status, severity, detected_date)
                        VALUES ($1, $2, $3, $4, $5, NOW()::date)
                        ON CONFLICT DO NOTHING
                        """,
                        building_id,
                        f"Rilevata da documento: {document_type}",
                        f"Risk score automatico: {risk_result['risk_score']}%",
                        "open",
                        "high",
                    )

        return {
            "document_id": doc_id,
            "file_url": file_url,
            "building_id": building_id,
            "risk_score": risk_result["risk_score"],
            "message": "Documento caricato con successo",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/documents/building/{building_id}")
async def get_building_documents(request: Request, building_id: str):
    """Restituisci tutti i documenti di un edificio."""
    async with request.app.state.pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, file_name, file_url, document_type, upload_date FROM documents WHERE building_id = $1 ORDER BY upload_date DESC",
            building_id,
        )
    return [dict(r) for r in rows]


@router.delete("/api/documents/{document_id}")
async def delete_document(request: Request, document_id: str):
    """Elimina un documento."""
    async with request.app.state.pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT file_url FROM documents WHERE id = $1",
            document_id,
        )
        if not row:
            raise HTTPException(status_code=404, detail="Document not found")

        # Elimina da MinIO
        minio_service.delete_file(row["file_url"])

        # Elimina da DB e Qdrant
        await conn.execute("DELETE FROM document_embeddings WHERE document_id = $1", document_id)
        await conn.execute("DELETE FROM documents WHERE id = $1", document_id)

    return {"message": "Documento eliminato"}


@router.get("/api/documents/{document_id}/download")
async def download_document(document_id: str):
    """Scarica un documento."""
    return {"message": "Download endpoint da implementare con streaming"}
