FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps: build tools needed by some Python wheels (e.g. razdel).
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project (source + pyproject) before install — pyproject declares
# explicit packages, so setuptools needs the source present at install time.
COPY pyproject.toml ./
COPY app ./app
COPY scripts ./scripts
RUN pip install --upgrade pip && pip install .

# SQLite file + kaikki dictionary live here; volume-mount in compose.
RUN mkdir -p /app/data

ENV DATABASE_URL=sqlite:////app/data/llmp.db

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
