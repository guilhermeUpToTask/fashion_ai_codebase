# Build stage
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN apt-get update && apt-get install -y \
    build-essential \
    g++ \
    gcc \
    libgl1 \
    libglib2.0-0 \
    libssl-dev \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    libpng-dev \
    cmake \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --user --cache-dir /tmp/pip-cache -r requirements.txt

# Runtime stage
FROM python:3.12-slim
WORKDIR /app

COPY --from=builder /root/.local /root/.local

COPY app ./app

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app

#Change cmd for run in prod
CMD ["fastapi", "dev", "--host", "0.0.0.0", "--port", "8000"]