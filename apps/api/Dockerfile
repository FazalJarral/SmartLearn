FROM python:3.12-slim

WORKDIR /app
COPY apps/api /app/apps/api
RUN pip install --no-cache-dir -e /app/apps/api

CMD ["sh", "-c", "uvicorn app.main:app --app-dir apps/api --host 0.0.0.0 --port ${PORT:-8000}"]
