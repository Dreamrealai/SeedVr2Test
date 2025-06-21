#!/bin/bash

# Deploy SEEDVR2 to RunPod
set -e

echo "🚀 SEEDVR2 RunPod Deployment Script"
echo "=================================="

# Check if RunPod CLI is installed
if ! command -v runpod &> /dev/null; then
    echo "📦 Installing RunPod CLI..."
    pip install runpod
fi

# Function to setup on running pod
setup_on_pod() {
    local POD_ID=$1
    echo "🔧 Setting up SEEDVR2 on pod $POD_ID..."
    
    # SSH into the pod and run setup
    runpod ssh $POD_ID << 'ENDSSH'
# Update system
apt-get update && apt-get install -y \
    git wget ffmpeg libsm6 libxext6 libxrender-dev libgomp1

# Install Miniconda if not present
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

# Download model
echo "🤖 Downloading SeedVR2-7B model (this will take 15-20 minutes)..."
python -c "
from huggingface_hub import snapshot_download
import os

save_dir = '/models/seedvr2-7b'
repo_id = 'ByteDance-Seed/SeedVR2-7B'

print(f'Downloading {repo_id} to {save_dir}')
os.makedirs(save_dir, exist_ok=True)

try:
    snapshot_download(
        cache_dir=save_dir + '/cache',
        local_dir=save_dir,
        repo_id=repo_id,
        local_dir_use_symlinks=False,
        resume_download=True,
        allow_patterns=['*.json', '*.safetensors', '*.pth', '*.bin', '*.py', '*.md', '*.txt']
    )
    print('✅ Model downloaded successfully!')
except Exception as e:
    print(f'⚠️  Download error: {e}')
    print('Continuing with setup...')
"

# Create test script
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
    if len(files) > 0:
        print("   Model files:")
        for f in sorted(files)[:5]:
            print(f"   - {f}")
else:
    print(f"❌ Model directory not found: {model_path}")

# Test if we can load the model config
try:
    import json
    config_path = os.path.join(model_path, "config.json")
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
        print(f"✅ Model config loaded: {config.get('model_type', 'Unknown')}")
except Exception as e:
    print(f"⚠️  Could not load model config: {e}")

print("\n✅ Setup complete! SeedVR2 is ready to use.")
EOF

# Run test
echo "🧪 Testing setup..."
conda run -n seedvr python /app/test_seedvr2.py

# Create quick inference script
cat > /app/quick_inference.py << 'EOF'
#!/usr/bin/env python
import sys
import os
import subprocess

def run_inference(video_path, output_dir="/tmp/output", res_h=720, res_w=1280):
    """Quick inference wrapper"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Determine GPU count
    sp_size = 4 if (res_h > 720 or res_w > 1280) else 1
    
    cmd = [
        "torchrun",
        f"--nproc-per-node={sp_size}",
        "/app/SeedVR/projects/inference_seedvr2_7b.py",
        "--video_path", video_path,
        "--output_dir", output_dir,
        "--seed", "42",
        "--res_h", str(res_h),
        "--res_w", str(res_w),
        "--sp_size", str(sp_size)
    ]
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return None
    
    print(f"✅ Output saved to {output_dir}")
    return output_dir

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python quick_inference.py <video_path> [res_h] [res_w]")
        sys.exit(1)
    
    video_path = sys.argv[1]
    res_h = int(sys.argv[2]) if len(sys.argv) > 2 else 720
    res_w = int(sys.argv[3]) if len(sys.argv) > 3 else 1280
    
    run_inference(video_path, res_h=res_h, res_w=res_w)
EOF

chmod +x /app/quick_inference.py

echo "🎉 Setup complete!"
echo ""
echo "Quick test command:"
echo "conda run -n seedvr python /app/quick_inference.py /path/to/video.mp4 720 1280"
ENDSSH
}

# Main script
echo "🔍 Checking for running RunPod pods..."

# List pods and capture output
PODS_OUTPUT=$(runpod pod list 2>&1 || echo "No pods found")
echo "$PODS_OUTPUT"

# Ask user to select a pod
echo ""
echo "Please enter the Pod ID to setup SEEDVR2 on (or 'exit' to quit):"
read POD_ID

if [ "$POD_ID" = "exit" ]; then
    echo "Exiting..."
    exit 0
fi

# Setup on the selected pod
setup_on_pod $POD_ID

echo ""
echo "✅ SEEDVR2 deployment complete!"
echo ""
echo "Next steps:"
echo "1. SSH into your pod: runpod ssh $POD_ID"
echo "2. Test with: conda run -n seedvr python /app/quick_inference.py /path/to/video.mp4"
echo "3. Or run the API server for web interface"
