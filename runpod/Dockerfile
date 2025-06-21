FROM nvidia/cuda:12.1.0-devel-ubuntu22.04

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=${CUDA_HOME}/bin:${PATH}
ENV LD_LIBRARY_PATH=${CUDA_HOME}/lib64:${LD_LIBRARY_PATH}

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-dev \
    python3-pip \
    git \
    wget \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3.10 as default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1

# Upgrade pip
RUN python -m pip install --upgrade pip

# Install PyTorch with CUDA support
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install flash-attn (requires CUDA)
RUN pip install ninja
RUN pip install flash-attn --no-build-isolation

# Install apex
RUN git clone https://github.com/NVIDIA/apex
RUN cd apex && pip install -v --disable-pip-version-check --no-cache-dir --no-build-isolation --config-settings "--build-option=--cpp_ext" --config-settings "--build-option=--cuda_ext" ./

# Install other dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# Install RunPod
RUN pip install runpod

# Copy model download script
COPY download_model.py /app/download_model.py

# Download SeedVR2-7B model
RUN python /app/download_model.py

# Copy inference script from SeedVR2 repo
RUN git clone https://github.com/ByteDance-Seed/SeedVR.git /seedvr
RUN cp /seedvr/projects/inference_seedvr2_*.py /app/

# Copy handler
COPY handler.py /app/handler.py

# Set working directory
WORKDIR /app

# Run handler
CMD ["python", "-m", "runpod.serverless.start", "handler.py"]