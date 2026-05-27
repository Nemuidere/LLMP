FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps: build tools needed by some Python wheels (e.g. razdel).
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (better layer caching).
COPY pyproject.toml ./
RUN pip install --upgrade pip \
    && pip install .

# Project source.
COPY app ./app
COPY scripts ./scripts

# SQLite file + kaikki dictionary live here; volume-mount in compose.
RUN mkdir -p /app/data

ENV DATABASE_URL=sqlite:////app/data/llmp.db

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
