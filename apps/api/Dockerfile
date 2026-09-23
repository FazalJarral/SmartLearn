FROM python:3.12-slim

WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential python3-dev pkg-config ffmpeg fonts-dejavu-core libcairo2-dev libpango1.0-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Piper TTS: self-hosted, no account/quota needed. Bundles its own onnxruntime,
# so no extra Python deps; the binary just needs LD_LIBRARY_PATH set to its own dir.
RUN mkdir -p /opt/piper/voices \
    && curl -fsSL https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz -o /tmp/piper.tar.gz \
    && tar -xzf /tmp/piper.tar.gz -C /opt \
    && rm /tmp/piper.tar.gz \
    && curl -fsSL https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx -o /opt/piper/voices/en_US-lessac-medium.onnx \
    && curl -fsSL https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json -o /opt/piper/voices/en_US-lessac-medium.onnx.json \
    && test -x /opt/piper/piper

COPY apps/api /app/apps/api
RUN pip install --no-cache-dir -e /app/apps/api

CMD ["sh", "-c", "uvicorn app.main:app --app-dir apps/api --host 0.0.0.0 --port ${PORT:-8000}"]
