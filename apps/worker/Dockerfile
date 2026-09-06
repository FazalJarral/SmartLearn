FROM python:3.12-slim

WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*
COPY apps/worker /app/apps/worker
RUN pip install --no-cache-dir -e /app/apps/worker

CMD ["python", "-m", "worker.runner"]
