FROM python:3.11-slim
WORKDIR /app
# OCR per le scansioni usato dall'estrattore locale (tesseract italiano + poppler per pdf2image)
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-ita poppler-utils \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./app /app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
