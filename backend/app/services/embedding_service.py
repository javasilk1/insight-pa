from sentence_transformers import SentenceTransformer
import numpy as np


class EmbeddingService:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def encode(self, text: str) -> list[float]:
        if not text:
            text = ""
        embedding = self.model.encode(text, convert_to_numpy=True)
        if isinstance(embedding, np.ndarray):
            return embedding.astype(float).tolist()
        return list(embedding)


embedding_service = EmbeddingService()
