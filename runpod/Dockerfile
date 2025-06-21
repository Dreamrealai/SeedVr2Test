FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-dev \
    python3-pip \
    git \
    wget \
    curl \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set python3.10 as default python
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1 && \
    update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel

# Clone SeedVR repository
RUN git clone https://github.com/ByteDance-Seed/SeedVR.git /app/SeedVR

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt /app/requirements.txt

# Install PyTorch with CUDA 12.1 support
RUN pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cu121

# Install other requirements
RUN pip install -r requirements.txt

# Install flash attention (skip for now - optional dependency)
# RUN pip install flash_attn==2.5.9.post1 --no-build-isolation

# Install apex (download pre-built wheel for Python 3.10 and CUDA 12.1)
RUN wget https://huggingface.co/ByteDance-Seed/SeedVR2-3B/resolve/main/apex-0.1-cp310-cp310-linux_x86_64.whl && \
    pip install apex-0.1-cp310-cp310-linux_x86_64.whl && \
    rm apex-0.1-cp310-cp310-linux_x86_64.whl

# Install RunPod
RUN pip install runpod

# Create models directory
RUN mkdir -p /models

# Copy handler and download script
COPY handler.py /app/handler.py
COPY download_model.py /app/download_model.py

# Download models based on build argument
ARG MODEL_SIZE=3b
ENV MODEL_SIZE=${MODEL_SIZE}
RUN python /app/download_model.py --model-size ${MODEL_SIZE}

# Set environment variables
ENV PYTHONPATH=/app/SeedVR:$PYTHONPATH
ENV MODEL_PATH=/models/seedvr2-${MODEL_SIZE}
ENV TOKENIZERS_PARALLELISM=false

# Create a startup script to handle environment variables
RUN echo '#!/bin/bash\nif [ ! -z "$GCS_KEY_JSON" ]; then\n    echo "GCS credentials provided via environment variable"\nfi\npython /app/handler.py' > /app/start.sh && \
    chmod +x /app/start.sh

# Default command
CMD ["/app/start.sh"]