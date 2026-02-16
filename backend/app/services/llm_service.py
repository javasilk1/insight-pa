from transformers import pipeline
import logging

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        try:
            self.qa_pipeline = pipeline(
                "question-answering",
                model="nickprock/bert-italian-xxl-cased-squad",
                device=-1,  # CPU
            )
            self.available = True
        except Exception as e:
            logger.warning(f"LLM non disponibile: {e}. Usero fallback.")
            self.available = False
            self.qa_pipeline = None

    def answer_question(self, question: str, context_docs: list[dict]) -> dict:
        """
        Risponde a una domanda usando il contesto fornito dai documenti.
        
        Args:
            question: Domanda in italiano
            context_docs: Lista di dict con 'text' e 'source'
        
        Returns:
            {"answer": str, "confidence": float, "source": str}
        """
        if not self.available or not self.qa_pipeline:
            return self._fallback_answer(question, context_docs)

        context = " ".join(d.get("text", "") for d in context_docs if d.get("text"))
        if not context.strip():
            return self._fallback_answer(question, context_docs)

        try:
            result = self.qa_pipeline(question=question, context=context)
            return {
                "answer": result.get("answer", "Non trovata risposta."),
                "confidence": round(result.get("score", 0), 3),
                "source": context_docs[0].get("source", "Documenti") if context_docs else "Documenti",
            }
        except Exception as e:
            logger.error(f"Errore QA pipeline: {e}")
            return self._fallback_answer(question, context_docs)

    def _fallback_answer(self, question: str, context_docs: list[dict]) -> dict:
        """Risposta template quando il modello non è disponibile."""
        if context_docs:
            context_text = " ".join(d.get("text", "")[:200] for d in context_docs[:2])
            answer = f"In base ai documenti: {context_text}..."
        else:
            answer = "Non ho trovato informazioni rilevanti per questa domanda."

        return {
            "answer": answer,
            "confidence": 0.0,
            "source": "Fallback",
        }


llm_service = LLMService()
