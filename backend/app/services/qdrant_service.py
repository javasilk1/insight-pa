from qdrant_client import QdrantClient
from qdrant_client.http import models
from services.embedding_service import embedding_service
from core.config import settings
import uuid


class QdrantService:
    def __init__(self, pool=None):
        self.client = QdrantClient(url=settings.QDRANT_URL)
        self.pool = pool

    def create_collection(self, collection_name: str = "quartu_documents"):
        collections = self.client.get_collections().collections
        existing = {c.name for c in collections}
        if collection_name in existing:
            return
        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
        )

    async def upsert_document(self, document_id: str, text: str, metadata: dict, collection_name: str = "quartu_documents"):
        self.create_collection(collection_name)
        vector = embedding_service.encode(text)
        point_id = str(uuid.uuid4())

        payload = {"document_id": document_id, **(metadata or {})}
        self.client.upsert(
            collection_name=collection_name,
            points=[models.PointStruct(id=point_id, vector=vector, payload=payload)],
        )

        if self.pool:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO document_embeddings (document_id, qdrant_point_id)
                    VALUES ($1, $2)
                    ON CONFLICT DO NOTHING
                    """,
                    document_id,
                    point_id,
                )

        return point_id

    def search(self, query: str, limit: int = 10, collection_name: str = "quartu_documents"):
        self.create_collection(collection_name)
        vector = embedding_service.encode(query)
        return self.client.search(
            collection_name=collection_name,
            query_vector=vector,
            limit=limit,
        )

    def search_by_building(self, building_id: str, query: str, limit: int = 10, collection_name: str = "quartu_documents"):
        self.create_collection(collection_name)
        vector = embedding_service.encode(query)
        building_filter = models.Filter(
            must=[models.FieldCondition(key="building_id", match=models.MatchValue(value=str(building_id)))]
        )
        return self.client.search(
            collection_name=collection_name,
            query_vector=vector,
            limit=limit,
            query_filter=building_filter,
        )

    async def find_similar_cases(self, building_id: str, limit: int = 5, collection_name: str = "quartu_documents"):
        if not self.pool:
            return []

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT d.id, d.extracted_text, d.file_name
                FROM documents d
                WHERE d.building_id = $1
                ORDER BY d.upload_date DESC
                LIMIT 1
                """,
                building_id,
            )

        if not row:
            return []

        query_text = row["extracted_text"] or row["file_name"] or ""
        building_filter = models.Filter(
            must_not=[models.FieldCondition(key="building_id", match=models.MatchValue(value=str(building_id)))]
        )

        self.create_collection(collection_name)
        vector = embedding_service.encode(query_text)
        return self.client.search(
            collection_name=collection_name,
            query_vector=vector,
            limit=limit,
            query_filter=building_filter,
        )


qdrant_service = QdrantService()
