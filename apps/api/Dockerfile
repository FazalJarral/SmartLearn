FROM python:3.12-slim

WORKDIR /app
COPY apps/api /app/apps/api
RUN pip install --no-cache-dir -e /app/apps/api

CMD ["uvicorn", "app.main:app", "--app-dir", "apps/api", "--host", "0.0.0.0", "--port", "8000"]
