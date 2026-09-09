FROM python:3.12-slim

WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential python3-dev pkg-config ffmpeg fonts-dejavu-core libcairo2-dev libpango1.0-dev \
    && rm -rf /var/lib/apt/lists/*
COPY apps/api /app/apps/api
RUN pip install --no-cache-dir -e /app/apps/api

CMD ["sh", "-c", "uvicorn app.main:app --app-dir apps/api --host 0.0.0.0 --port ${PORT:-8000}"]
