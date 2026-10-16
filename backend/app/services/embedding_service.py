"""Embedding dei testi con fastembed (ONNX Runtime, senza torch).

Il modello multilingue capisce l'italiano e produce vettori a 384 dimensioni,
la stessa dimensione della collezione Qdrant esistente. Viene caricato al primo
uso, non all'import, così l'avvio dell'app non scarica né carica il modello.
"""
import threading

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_DIM = 384


class EmbeddingService:
    def __init__(self, model_name: str = MODEL_NAME):
        self.model_name = model_name
        self._model = None
        self._lock = threading.Lock()

    @property
    def model(self):
        if self._model is None:
            with self._lock:
                if self._model is None:
                    from fastembed import TextEmbedding

                    self._model = TextEmbedding(model_name=self.model_name)
        return self._model

    def encode(self, text: str) -> list[float]:
        if not text:
            text = ""
        embedding = next(iter(self.model.embed([text])))
        return [float(x) for x in embedding]


embedding_service = EmbeddingService()
