# NEBANK — single image: builds the Mini App, serves API + bot webhook.
# Stage 1: build the React Mini App
FROM node:22-alpine AS web
WORKDIR /web
COPY miniapp/package.json miniapp/package-lock.json* ./
RUN npm install --no-audit --no-fund
COPY miniapp/ ./
RUN npm run build

# Stage 2: python runtime
FROM python:3.11-slim AS runtime
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1 \
    MINIAPP_DIR=/app/miniapp

# Real OCR + QR (keyless): Tesseract (rus+eng) and ZBar.
RUN apt-get update && apt-get install -y --no-install-recommends \
      tesseract-ocr tesseract-ocr-rus tesseract-ocr-eng \
      libzbar0 libgl1 libglib2.0-0 curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install -r requirements.txt

COPY backend/ ./
COPY --from=web /web/dist /app/miniapp

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS http://localhost:8000/healthz || exit 1

# Single async worker: webhook + APScheduler + in-memory FSM stay coherent.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
