# --- Stage 1: Builder ---
# Use a full CUDA development image to build any dependencies that need compilation.
# Pinning the exact versions of CUDA and Python is crucial for reproducibility.
FROM nvidia/cuda:12.1.1-devel-ubuntu22.04 AS builder

# Set up environment to be non-interactive
ENV TZ=Etc/UTC
ENV DEBIAN_FRONTEND=noninteractive

# Install Python and build tools
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment for clean dependency management
RUN python3.11 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install requirements.
# This leverages Docker's layer caching. This layer only rebuilds if requirements.txt changes.
COPY requirements.txt .
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cu121 -r requirements.txt

# --- Stage 2: Runtime ---
# Use the smaller CUDA runtime image for the final stage. It has the necessary libraries
# to run CUDA applications but not the full development toolkit, making it smaller.
FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

# Set up environment again
ENV TZ=Etc/UTC
ENV DEBIAN_FRONTEND=noninteractive

# Create a non-root user for better security
RUN groupadd --gid 1001 mlservice && \
    useradd --uid 1001 --gid 1001 --shell /bin/bash --create-home mlservice

# Install only necessary runtime dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy the application code
WORKDIR /app
COPY app/ .

# Set environment variables for the runtime
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app"

# Switch to the non-root user
USER mlservice

# Expose the port the service will run on
EXPOSE 8080

# The command to run the ML service application (e.g., using Gunicorn)
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8080", "main:app"]