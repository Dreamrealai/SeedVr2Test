FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    git \
    wget \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Set python3.10 as default python
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1 && \
    update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1

# Install Miniconda
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh && \
    bash miniconda.sh -b -p /opt/conda && \
    rm miniconda.sh

ENV PATH="/opt/conda/bin:${PATH}"

# Clone SeedVR repository
RUN git clone https://github.com/bytedance-seed/SeedVR.git /app/SeedVR

WORKDIR /app/SeedVR

# Create conda environment
RUN conda create -n seedvr python=3.10 -y

# Install requirements in conda environment
SHELL ["conda", "run", "-n", "seedvr", "/bin/bash", "-c"]

# Install PyTorch and basic requirements
RUN pip install torch==2.3.0 torchvision==0.18.0 torchaudio==2.3.0 --index-url https://download.pytorch.org/whl/cu118

# Copy and install requirements
COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# Install flash attention with specific version
RUN pip install flash_attn==2.5.9.post1 --no-build-isolation

# Install apex from pre-built wheel (specific to CUDA 11.8)
RUN wget https://github.com/NVIDIA/apex/releases/download/23.08/apex-23.08-cp310-cp310-linux_x86_64.whl && \
    pip install apex-23.08-cp310-cp310-linux_x86_64.whl && \
    rm apex-23.08-cp310-cp310-linux_x86_64.whl

# Install RunPod
RUN pip install runpod

# Create models directory
RUN mkdir -p /models/seedvr2-7b

# Copy download script
COPY download_model.py /app/download_model.py

# Download model weights
RUN conda run -n seedvr python /app/download_model.py

# Copy handler
COPY handler.py /app/handler.py

# Set environment variables
ENV CUDA_VISIBLE_DEVICES=0
ENV PYTHONPATH=/app/SeedVR:$PYTHONPATH
ENV MODEL_PATH=/models/seedvr2-7b

# Default to running in conda environment
ENTRYPOINT ["conda", "run", "-n", "seedvr", "python"]
CMD ["/app/handler.py"]