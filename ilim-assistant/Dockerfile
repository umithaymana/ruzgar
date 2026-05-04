# RÜZGAR HTTP API — Railway / Fly.io / Render
# Yerel bağlam: klasör bağlamını "ilim-assistant" seçin veya kök dizinde:
#   docker build -f ilim-assistant/Dockerfile ilim-assistant

FROM python:3.11-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
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

EXPOSE 8777

# Railway PORT’u ile uyumlu: desktop_server içinde PORT okunur
CMD ["python", "desktop_server.py"]
