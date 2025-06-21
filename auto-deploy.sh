#!/bin/bash

# Automated SeedVR2 RunPod Deployment
set -e

echo "🚀 Automated SeedVR2 Deployment Starting..."
echo "=========================================="

# Set RunPod API key from .env file
export RUNPOD_API_KEY="rpa_UFDTAAMZ19E9WYJNTIPAMY4UG6DHWYZCO12RO6EUsi2hmd"

# Install runpod if needed
if ! command -v runpod &> /dev/null; then
    echo "📦 Installing RunPod CLI..."
    pip install runpod
fi

echo "🔍 Finding pods with 80GB+ VRAM..."

# Get pods and select one with 80GB+ VRAM
SELECTED_POD=$(runpod pod list --json 2>/dev/null | python3 -c "
import json
import sys

try:
    pods = json.load(sys.stdin)
    
    # Filter for running pods with 80GB+ VRAM
    suitable_pods = []
    for pod in pods:
        if pod.get('desiredStatus') == 'RUNNING':
            gpu_name = pod.get('machineDisplayName', '').lower()
            # Check for H100 80GB, A100 80GB, or similar
            if 'h100' in gpu_name or ('a100' in gpu_name and '80' in gpu_name):
                suitable_pods.append(pod)
    
    if not suitable_pods:
        print('ERROR: No running pods with 80GB+ VRAM found')
        sys.exit(1)
    
    # Select the first suitable pod
    selected = suitable_pods[0]
    print(f\"SELECTED: {selected['name']} ({selected['machineDisplayName']}) - ID: {selected['id']}\")
    print(f\"POD_ID={selected['id']}\")
    
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
")

# Extract POD_ID
POD_ID=$(echo "$SELECTED_POD" | grep "POD_ID=" | cut -d= -f2)

if [ -z "$POD_ID" ]; then
    echo "❌ No suitable pod found. Looking for any available pod..."
    
    # Fallback: get any running pod
    POD_ID=$(runpod pod list --json 2>/dev/null | python3 -c "
import json
import sys
pods = json.load(sys.stdin)
running = [p for p in pods if p.get('desiredStatus') == 'RUNNING']
if running:
    print(running[0]['id'])
")
    
    if [ -z "$POD_ID" ]; then
        echo "❌ No running pods found at all"
        exit 1
    fi
fi

echo ""
echo "✅ Selected Pod ID: $POD_ID"
echo "🚀 Starting automated deployment..."
echo ""

# SSH into pod and run complete setup
runpod ssh $POD_ID << 'ENDSSH'
#!/bin/bash
set -e

echo "🔧 Automated SeedVR2 Setup Starting..."
echo ""

# Update system without prompts
export DEBIAN_FRONTEND=noninteractive
apt-get update && apt-get install -y \
    git wget ffmpeg libsm6 libxext6 libxrender-dev libgomp1 \
    python3-pip curl

# Install Miniconda if not present
if [ ! -d "/opt/conda" ]; then
    echo "📦 Installing Miniconda..."
    wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
    bash miniconda.sh -b -p /opt/conda
    rm miniconda.sh
fi

export PATH="/opt/conda/bin:${PATH}"

# Clone repositories
if [ ! -d "/app/SeedVR" ]; then
    echo "📥 Cloning SeedVR repository..."
    git clone https://github.com/bytedance-seed/SeedVR.git /app/SeedVR
fi

if [ ! -d "/app/SeedVr2Test" ]; then
    echo "📥 Cloning SeedVr2Test repository..."
    git clone https://github.com/dreamrealai/SeedVr2Test.git /app/SeedVr2Test
fi

cd /app/SeedVR

# Create conda environment
echo "🐍 Setting up conda environment..."
conda create -n seedvr python=3.10 -y || true

# Activate environment
source /opt/conda/etc/profile.d/conda.sh
conda activate seedvr

# Install PyTorch
echo "🔧 Installing PyTorch with CUDA 11.8..."
pip install torch==2.3.0 torchvision==0.18.0 torchaudio==2.3.0 --index-url https://download.pytorch.org/whl/cu118

# Install all requirements
echo "📚 Installing all requirements..."
pip install numpy'<2' opencv-python imageio imageio-ffmpeg av decord einops \
    tensorboard tqdm omegaconf transformers diffusers accelerate xformers \
    ftfy gradio soundfile moviepy oss2 huggingface_hub fastapi uvicorn \
    python-multipart aiofiles

# Install flash attention
echo "⚡ Installing flash attention..."
pip install ninja
pip install flash_attn==2.5.9.post1 --no-build-isolation || true

# Download model with progress tracking
echo "🤖 Downloading SeedVR2-7B model (~15GB)..."
python3 << 'EOPYTHON'
from huggingface_hub import snapshot_download
import os
import sys

save_dir = '/models/seedvr2-7b'
repo_id = 'ByteDance-Seed/SeedVR2-7B'

print(f'Downloading {repo_id} to {save_dir}')
print('This will take 10-20 minutes...\n')
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
    print('\n✅ Model downloaded successfully!')
except Exception as e:
    print(f'\n⚠️  Download error: {e}')
    print('The setup will continue, but you may need to retry the download')
EOPYTHON

# Copy scripts and create server
echo "📄 Setting up API server and scripts..."
cp /app/SeedVr2Test/runpod/seedvr2_api_server.py /app/
cp /app/SeedVr2Test/runpod/seedvr2_web_ui.html /app/

# Create improved API server startup script
cat > /app/start_seedvr2_server.sh << 'EOF'
#!/bin/bash
source /opt/conda/etc/profile.d/conda.sh
conda activate seedvr
cd /app

echo "🌐 Starting SeedVR2 API Server..."
echo "================================"
echo ""
echo "Server will be available at:"
echo "  http://$(hostname -I | awk '{print $1}'):8000"
echo "  http://localhost:8000"
echo ""
echo "API Endpoints:"
echo "  POST /api/restore - Submit video for restoration"
echo "  GET  /api/status/{job_id} - Check job status"
echo "  GET  /api/download/{job_id} - Download result"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python seedvr2_api_server.py
EOF
chmod +x /app/start_seedvr2_server.sh

# Create quick test script
cat > /app/quick_test.sh << 'EOF'
#!/bin/bash
source /opt/conda/etc/profile.d/conda.sh
conda activate seedvr

echo "🧪 Quick SeedVR2 Test"
echo "===================="

# Download test video
if [ ! -f "/tmp/test_video.mp4" ]; then
    echo "📥 Downloading test video..."
    wget -q https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4 -O /tmp/test_video.mp4
fi

# Run inference
echo "🎬 Running inference on test video..."
mkdir -p /tmp/seedvr2_test_output

conda run -n seedvr torchrun --nproc-per-node=1 \
    /app/SeedVR/projects/inference_seedvr2_7b.py \
    --video_path /tmp/test_video.mp4 \
    --output_dir /tmp/seedvr2_test_output \
    --seed 42 \
    --res_h 720 \
    --res_w 1280 \
    --sp_size 1

echo ""
if [ -f "/tmp/seedvr2_test_output/*.mp4" ]; then
    echo "✅ Test successful! Output saved to /tmp/seedvr2_test_output/"
else
    echo "⚠️  Test may have issues. Check the output above."
fi
EOF
chmod +x /app/quick_test.sh

# Final test
echo ""
echo "🧪 Running final installation test..."
python3 << 'EOPYTHON'
import torch
import os
import sys

print("=" * 50)
print("SeedVR2 Installation Status")
print("=" * 50)
print(f"✅ Python: {sys.version.split()[0]}")
print(f"✅ PyTorch: {torch.__version__}")
print(f"✅ CUDA: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    gpu = torch.cuda.get_device_name(0)
    vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
    print(f"✅ GPU: {gpu} ({vram:.1f} GB)")

model_path = "/models/seedvr2-7b"
if os.path.exists(model_path):
    files = os.listdir(model_path)
    print(f"✅ Model: Found {len(files)} files")
else:
    print("⚠️  Model: Not downloaded yet")

print("=" * 50)
print("✅ Setup Complete!")
print("=" * 50)
EOPYTHON

echo ""
echo "🎉 Automated setup complete!"
echo ""
echo "📋 Quick Start Commands:"
echo "1. Start API Server: /app/start_seedvr2_server.sh"
echo "2. Run Quick Test: /app/quick_test.sh"
echo ""
echo "The server will start automatically in 5 seconds..."
sleep 5

# Auto-start the server
/app/start_seedvr2_server.sh
ENDSSH

echo ""
echo "✅ Automated deployment complete!"
echo ""
echo "The API server should now be running on your pod."
echo "Check the RunPod console for the pod's public IP address."
