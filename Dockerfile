# GPU-enabled Dockerfile for Face Swap GPU Node
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# Set working directory
WORKDIR /app

# Install system dependencies (runtime + build tools)
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    python3-dev \
    python3.10-venv \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    pkg-config \
    ffmpeg \
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavutil-dev \
    libswscale-dev \
    libswresample-dev \
    libavfilter-dev \
    gcc \
    g++ \
    make \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set Python path
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Create and activate virtual environment
# This avoids pip root user warnings and provides better isolation
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies in virtual environment
RUN pip install --upgrade pip --no-cache-dir && \
    pip install -r requirements.txt --no-cache-dir

# Copy application code
COPY src/ /app/src/
COPY models/ /app/models/

# Copy download script
COPY scripts/download_models.sh /app/scripts/download_models.sh
RUN chmod +x /app/scripts/download_models.sh

# Create models directory if it doesn't exist
RUN mkdir -p /app/models

# Expose ports
# 8080: Health API
# 8081: WebRTC (if needed)
EXPOSE 8080 8081

# Set environment variables
ENV HOST=0.0.0.0
ENV PORT=8080
ENV MODEL_PATH=/app/models
ENV MODEL_TYPE=insightface
ENV GPU_ID=0

# Run the application (venv python is already in PATH)
# Download models before starting the application
CMD ["bash", "-c", "/app/scripts/download_models.sh && python -m src.main"]

