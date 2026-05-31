# RÜZGAR HTTP API — Railway / Fly.io / Render
# Yerel bağlam: klasör bağlamını "ilim-assistant" seçin veya kök dizinde:
#   docker build -f ilim-assistant/Dockerfile ilim-assistant

FROM python:3.11-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        curl \
        tesseract-ocr \
        tesseract-ocr-ara \
        tesseract-ocr-tur \
        tesseract-ocr-eng \
        tesseract-ocr-fas \
    && TESSDATA=/usr/share/tesseract-ocr/5/tessdata \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# API için hafifleştirilmiş bağımlılıklar (Gradio yok)
COPY requirements-api.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements-api.txt

COPY ilim_assistant ./ilim_assistant
COPY desktop_server.py .
COPY knowledge ./knowledge

ENV PYTHONUNBUFFERED=1
ENV RUZGAR_API_HOST=0.0.0.0
ENV RUZGAR_PUBLIC_MODE=1
ENV RUZGAR_DATA_ROOT=/app/data
ENV RUZGAR_SHARED_ROOT=/app
ENV RUZGAR_RAG_INDEX_DIR=/app/.rag_index
ENV RUZGAR_CORS_PERMISSIVE=1

VOLUME ["/app/data"]

EXPOSE 8777

# Railway PORT’u ile uyumlu: desktop_server içinde PORT okunur
CMD ["python", "desktop_server.py"]
