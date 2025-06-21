#!/bin/bash

# Interactive SeedVR2 RunPod Deployment
set -e

echo "🚀 SeedVR2 RunPod Interactive Deployment"
echo "========================================"
echo ""

# Check if RUNPOD_API_KEY is set
if [ -z "$RUNPOD_API_KEY" ]; then
    echo "⚠️  RUNPOD_API_KEY not found in environment"
    echo ""
    echo "Please enter your RunPod API key:"
    read -s RUNPOD_API_KEY
    export RUNPOD_API_KEY
    echo ""
fi

# Install runpod if not installed
if ! command -v runpod &> /dev/null; then
    echo "📦 Installing RunPod CLI..."
    pip install runpod
fi

echo "🔍 Fetching your RunPod pods..."
echo ""

# List pods
PODS_JSON=$(runpod pod list --json 2>/dev/null || echo "[]")

if [ "$PODS_JSON" = "[]" ]; then
    echo "❌ No pods found. Please check:"
    echo "   1. Your API key is correct"
    echo "   2. You have active pods on RunPod"
    echo ""
    echo "To create a pod, visit: https://www.runpod.io/console/pods"
    exit 1
fi

# Parse and display pods
echo "$PODS_JSON" | python3 -c "
import json
import sys

pods = json.load(sys.stdin)
print('Available RunPod Pods:')
print('-' * 50)
for i, pod in enumerate(pods):
    status = pod.get('desiredStatus', 'unknown')
    gpu = pod.get('machineDisplayName', 'Unknown GPU')
    name = pod.get('name', 'Unnamed')
    pod_id = pod.get('id', '')
    
    status_emoji = '🟢' if status == 'RUNNING' else '🔴'
    print(f'{i+1}. {status_emoji} {name} ({gpu})')
    print(f'   ID: {pod_id}')
    print(f'   Status: {status}')
    print()
"

echo "-" * 50
echo ""
echo "Enter the number of the pod to deploy to (or 'q' to quit):"
read POD_CHOICE

if [ "$POD_CHOICE" = "q" ]; then
    echo "Exiting..."
    exit 0
fi

# Get the pod ID
POD_ID=$(echo "$PODS_JSON" | python3 -c "
import json
import sys
pods = json.load(sys.stdin)
try:
    idx = int('$POD_CHOICE') - 1
    if 0 <= idx < len(pods):
        print(pods[idx]['id'])
except:
    pass
")

if [ -z "$POD_ID" ]; then
    echo "❌ Invalid selection"
    exit 1
fi

echo ""
echo "🎯 Selected pod: $POD_ID"
echo ""
echo "This will install:"
echo "  • SeedVR2-7B model (~15GB)"
echo "  • Required dependencies"
echo "  • API server for web interface"
echo ""
echo "Estimated time: 15-20 minutes"
echo ""
echo "Continue? (y/n)"
read CONFIRM

if [ "$CONFIRM" != "y" ]; then
    echo "Deployment cancelled"
    exit 0
fi

echo ""
echo "🚀 Starting deployment..."
echo ""

# SSH into pod and run setup
runpod ssh $POD_ID << 'ENDSSH'
#!/bin/bash
set -e

echo "🔧 Setting up SeedVR2 on RunPod..."
echo ""

# Update system
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

# Clone SeedVR repository
if [ ! -d "/app/SeedVR" ]; then
    echo "📥 Cloning SeedVR repository..."
    git clone https://github.com/bytedance-seed/SeedVR.git /app/SeedVR
fi

# Clone your repository for scripts
if [ ! -d "/app/SeedVr2Test" ]; then
    echo "📥 Cloning SeedVr2Test repository..."
    git clone https://github.com/dreamrealai/SeedVr2Test.git /app/SeedVr2Test
fi

cd /app/SeedVR

# Create conda environment
echo "🐍 Creating conda environment..."
conda create -n seedvr python=3.10 -y || true

# Activate environment
source /opt/conda/etc/profile.d/conda.sh
conda activate seedvr

# Install PyTorch
echo "🔧 Installing PyTorch with CUDA 11.8..."
pip install torch==2.3.0 torchvision==0.18.0 torchaudio==2.3.0 --index-url https://download.pytorch.org/whl/cu118

# Install requirements
echo "📚 Installing requirements..."
pip install numpy'<2' opencv-python imageio imageio-ffmpeg av decord einops \
    tensorboard tqdm omegaconf transformers diffusers accelerate xformers \
    ftfy gradio soundfile moviepy oss2 huggingface_hub fastapi uvicorn python-multipart

# Install flash attention
echo "⚡ Installing flash attention..."
pip install ninja
pip install flash_attn==2.5.9.post1 --no-build-isolation || echo "Flash attention installation failed, continuing..."

# Download model
echo "🤖 Downloading SeedVR2-7B model..."
echo "This will take 15-20 minutes depending on connection speed..."
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
    print('You may need to retry the download later')
"

# Copy API server and web UI
echo "📄 Setting up API server..."
cp /app/SeedVr2Test/runpod/seedvr2_api_server.py /app/
cp /app/SeedVr2Test/runpod/seedvr2_web_ui.html /app/

# Create test script
cat > /app/test_seedvr2.py << 'EOF'
import torch
import sys
import os
import json

print("=" * 50)
print("SeedVR2 Installation Test")
print("=" * 50)
print(f"Python: {sys.version}")
print(f"PyTorch: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA device: {torch.cuda.get_device_name(0)}")
    print(f"CUDA memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

model_path = "/models/seedvr2-7b"
if os.path.exists(model_path):
    print(f"\n✅ Model directory exists: {model_path}")
    files = os.listdir(model_path)
    print(f"   Found {len(files)} files")
    
    # Check for key model files
    key_files = ['config.json', 'model.safetensors', 'tokenizer_config.json']
    for key_file in key_files:
        if any(key_file in f for f in files):
            print(f"   ✓ {key_file} found")
else:
    print(f"\n❌ Model directory not found: {model_path}")

print("\n" + "=" * 50)
print("✅ Setup complete!")
print("=" * 50)
print("\nTo start the API server:")
print("conda run -n seedvr python /app/seedvr2_api_server.py")
print("\nTo run inference directly:")
print("conda run -n seedvr torchrun --nproc-per-node=1 /app/SeedVR/projects/inference_seedvr2_7b.py \\")
print("  --video_path input.mp4 --output_dir output/ --seed 42 --res_h 720 --res_w 1280 --sp_size 1")
EOF

# Run test
echo ""
echo "🧪 Testing installation..."
conda run -n seedvr python /app/test_seedvr2.py

# Create startup script
cat > /app/start_seedvr2_server.sh << 'EOF'
#!/bin/bash
source /opt/conda/etc/profile.d/conda.sh
conda activate seedvr
cd /app
python seedvr2_api_server.py
EOF
chmod +x /app/start_seedvr2_server.sh

echo ""
echo "🎉 SeedVR2 deployment complete!"
echo ""
echo "The API server can be started with:"
echo "/app/start_seedvr2_server.sh"
ENDSSH

echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. SSH into your pod: runpod ssh $POD_ID"
echo "2. Start the API server: /app/start_seedvr2_server.sh"
echo "3. Access the web UI at: http://<pod-ip>:8000"
echo ""
echo "Or use the one-liner to start the server:"
echo "runpod ssh $POD_ID '/app/start_seedvr2_server.sh'"
