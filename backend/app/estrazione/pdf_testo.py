"""Testo di un PDF pagina per pagina, con OCR per le pagine scansionate."""
import logging
from pathlib import Path

from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)

MIN_CARATTERI = 30  # sotto questa soglia la pagina è considerata un'immagine


def _ocr(path: Path, indice: int) -> str | None:
    try:
        import pytesseract
        from pdf2image import convert_from_path
    except ImportError:
        return None
    immagini = convert_from_path(str(path), dpi=300, first_page=indice + 1, last_page=indice + 1)
    return pytesseract.image_to_string(immagini[0], lang="ita") if immagini else None


def estrai_pagine(path: Path) -> list[dict]:
    """[{"pagina": 1, "testo": "...", "metodo": "testo"|"ocr"|"illeggibile"}]"""
    pagine = []
    for i, page in enumerate(PdfReader(str(path)).pages):
        testo = (page.extract_text() or "").strip()
        metodo = "testo"
        if len(testo) < MIN_CARATTERI:
            ocr = _ocr(path, i)
            if ocr and len(ocr.strip()) >= MIN_CARATTERI:
                testo, metodo = ocr.strip(), "ocr"
            else:
                metodo = "illeggibile"
                logger.warning("Pagina %s di %s senza testo e OCR non disponibile", i + 1, path.name)
        pagine.append({"pagina": i + 1, "testo": testo, "metodo": metodo})
    return pagine


def testo_completo(pagine: list[dict]) -> str:
    return "\n\n".join(f"--- PAGINA {p['pagina']} ---\n{p['testo']}" for p in pagine)
