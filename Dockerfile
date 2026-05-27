FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash curl ca-certificates sqlite3 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data/backups

EXPOSE 18090

CMD ["sh", "-c", "python -m scripts.seed && uvicorn app:app --host 0.0.0.0 --port ${PORT:-18090}"]
