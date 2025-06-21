#!/bin/bash

# Setup script for RunPod pod
# This script should be run inside the RunPod pod

set -e

echo "🚀 Starting SeedVR2 setup on RunPod pod..."

# Update system
apt-get update && apt-get install -y \
    git \
    wget \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1

# Install Miniconda
if [ ! -d "/opt/conda" ]; then
    echo "📦 Installing Miniconda..."
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
    bash miniconda.sh -b -p /opt/conda
    rm miniconda.sh
fi

export PATH="/opt/conda/bin:${PATH}"

# Clone SeedVR repository
if [ ! -d "/app/SeedVR" ]; then
    echo "📥 Cloning SeedVR repository..."
    git clone https://github.com/bytedance-seed/SeedVR.git /app/SeedVR
fi

cd /app/SeedVR

# Create conda environment
conda create -n seedvr python=3.10 -y || true

# Activate environment
source /opt/conda/etc/profile.d/conda.sh
conda activate seedvr

# Install PyTorch
echo "🔧 Installing PyTorch..."
pip install torch==2.3.0 torchvision==0.18.0 torchaudio==2.3.0 --index-url https://download.pytorch.org/whl/cu118

# Install requirements
echo "📚 Installing requirements..."
pip install numpy'<2' opencv-python imageio imageio-ffmpeg av decord einops tensorboard tqdm omegaconf transformers diffusers accelerate xformers ftfy gradio soundfile moviepy oss2 huggingface_hub

# Install flash attention
echo "⚡ Installing flash attention..."
pip install flash_attn==2.5.9.post1 --no-build-isolation || echo "Flash attention installation failed, continuing..."

# Install apex
echo "🔺 Installing apex..."
wget https://github.com/NVIDIA/apex/releases/download/23.08/apex-23.08-cp310-cp310-linux_x86_64.whl
pip install apex-23.08-cp310-cp310-linux_x86_64.whl || echo "Apex installation failed, continuing..."
rm -f apex-23.08-cp310-cp310-linux_x86_64.whl

# Download model
echo "🤖 Downloading SeedVR2-7B model..."
python -c "
from huggingface_hub import snapshot_download
import os

save_dir = '/models/seedvr2-7b'
repo_id = 'ByteDance-Seed/SeedVR2-7B'

print(f'Downloading {repo_id} to {save_dir}')
os.makedirs(save_dir, exist_ok=True)

snapshot_download(
    cache_dir=save_dir + '/cache',
    local_dir=save_dir,
    repo_id=repo_id,
    local_dir_use_symlinks=False,
    resume_download=True,
    allow_patterns=['*.json', '*.safetensors', '*.pth', '*.bin', '*.py', '*.md', '*.txt']
)
print('Model downloaded successfully!')
"

# Create a simple test script
cat > /app/test_seedvr2.py << 'EOF'
import torch
import sys
import os

print("Testing SeedVR2 setup...")
print(f"Python: {sys.version}")
print(f"PyTorch: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA device: {torch.cuda.get_device_name(0)}")
    print(f"CUDA memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

model_path = "/models/seedvr2-7b"
if os.path.exists(model_path):
    print(f"✅ Model directory exists: {model_path}")
    files = os.listdir(model_path)
    print(f"   Found {len(files)} files")
else:
    print(f"❌ Model directory not found: {model_path}")

print("\n✅ Setup complete! SeedVR2 is ready to use.")
EOF

# Run test
echo "🧪 Testing setup..."
conda run -n seedvr python /app/test_seedvr2.py

echo "🎉 Setup complete! You can now run SeedVR2 inference."
echo ""
echo "Example command:"
echo "conda run -n seedvr torchrun --nproc-per-node=1 /app/SeedVR/projects/inference_seedvr2_7b.py --video_path /path/to/input.mp4 --output_dir /path/to/output --seed 42 --res_h 720 --res_w 1280 --sp_size 1"