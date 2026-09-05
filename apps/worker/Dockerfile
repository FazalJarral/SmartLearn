FROM python:3.12-slim

WORKDIR /app
COPY apps/worker /app/apps/worker
RUN pip install --no-cache-dir -e /app/apps/worker

CMD ["python", "-m", "worker.runner"]
