# Build stage
#later we will migrate to uv
FROM python:3.12-slim AS builder
WORKDIR /app
#will test later the mount cache volume to faster building
# RUN --mount=type=cache,target=/root/.cache/pip \
#     pip install --no-cache-dir -r requirements.txt
COPY requirements.txt .
RUN pip install --user --cache-dir /tmp/pip-cache -r requirements.txt

# Runtime stage
FROM python:3.12-slim
WORKDIR /app

COPY --from=builder /root/.local /root/.local

COPY app/ .

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app

#Change cmd for run in prod
CMD ["fastapi", "dev", "--host", "0.0.0.0", "--port", "8000"]