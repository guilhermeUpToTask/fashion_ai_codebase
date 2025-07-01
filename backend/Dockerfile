# Build stage
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
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
