import asyncio
import asyncpg
from core.config import settings
from services.qdrant_service import QdrantService


async def main():
    pool = await asyncpg.create_pool(dsn=settings.DATABASE_URL)
    qdrant = QdrantService(pool=pool)

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT d.id, d.building_id, d.file_name, d.file_url, d.document_type, d.extracted_text
            FROM documents d
            LEFT JOIN document_embeddings de ON de.document_id = d.id
            WHERE de.document_id IS NULL
            """
        )

    if not rows:
        print("Nessun documento da indicizzare.")
        await pool.close()
        return

    for row in rows:
        doc_id = str(row["id"])
        text = row["extracted_text"] or row["file_name"] or ""
        metadata = {
            "building_id": str(row["building_id"]),
            "file_name": row["file_name"],
            "file_url": row["file_url"],
            "document_type": row["document_type"],
        }
        await qdrant.upsert_document(doc_id, text, metadata)

    print(f"Indicizzati {len(rows)} documenti in Qdrant.")
    await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
