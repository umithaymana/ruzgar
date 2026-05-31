# RÜZGAR HTTP API — Railway / Fly.io / Render
# Repo kökünden derle:
#   docker build -f ilim-assistant/Dockerfile .
#   docker run --rm -p 8777:8777 -e PORT=8777 -e GEMINI_API_KEY=... ruzgar-halk

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

COPY ilim-assistant/requirements-api.txt ./ilim-assistant/requirements-api.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r ilim-assistant/requirements-api.txt

COPY ilim-assistant/ilim_assistant ./ilim-assistant/ilim_assistant
COPY ilim-assistant/desktop_server.py ./ilim-assistant/desktop_server.py
COPY ilim-assistant/knowledge ./ilim-assistant/knowledge
COPY ruzgar-desktop ./ruzgar-desktop

ENV PYTHONUNBUFFERED=1
ENV RUZGAR_API_HOST=0.0.0.0
ENV RUZGAR_PUBLIC_MODE=1
ENV RUZGAR_DATA_ROOT=/app/data
ENV RUZGAR_SHARED_ROOT=/app/ilim-assistant
ENV RUZGAR_RAG_INDEX_DIR=/app/ilim-assistant/.rag_index
ENV RUZGAR_CORS_PERMISSIVE=1
ENV RUZGAR_SKIP_RAG_WARMUP=1

VOLUME ["/app/data"]

EXPOSE 8777

WORKDIR /app/ilim-assistant
CMD ["python", "desktop_server.py"]
