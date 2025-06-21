#!/bin/bash
# Setup script for SeedVR2 on RunPod pod

echo "=== SeedVR2 RunPod Setup Script ==="
echo "This script will install SeedVR2 and all dependencies on your RunPod pod"
echo

# Configuration
RUNPOD_POD_ID="lh0wm9g482zr28"
MODEL_SIZE="3b"  # Using 3B model for H100

echo "1. Connecting to RunPod pod..."
runpodctl send $RUNPOD_POD_ID << 'EOSCRIPT'
#!/bin/bash
set -e

echo "=== Setting up SeedVR2 on RunPod pod ==="

# Update system
echo "Updating system packages..."
apt-get update && apt-get install -y git wget curl ffmpeg python3-pip

# Set working directory
cd /workspace

# Clone SeedVR repository
echo "Cloning SeedVR repository..."
if [ ! -d "SeedVR" ]; then
    git clone https://github.com/ByteDance-Seed/SeedVR.git
fi

# Install Python dependencies
echo "Installing Python dependencies..."
cd SeedVR
pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cu118
pip install -r requirements.txt || true

# Install additional dependencies
pip install runpod google-cloud-storage requests flask

# Download SeedVR2 3B model
echo "Downloading SeedVR2 3B model..."
mkdir -p /workspace/models
cd /workspace/models

# Download from Hugging Face
if [ ! -d "seedvr2-3b" ]; then
    echo "Downloading model weights from Hugging Face..."
    # Note: Replace with actual model download command once available
    wget -O seedvr2-3b.tar.gz "https://huggingface.co/ByteDance-Seed/SeedVR2-3B/resolve/main/model.tar.gz" || {
        echo "Model download failed - model might not be publicly available yet"
        echo "Please manually download the model from Hugging Face"
    }
fi

# Create handler script
echo "Creating RunPod handler..."
cat > /workspace/handler.py << 'EOF'
import runpod
import os
import subprocess
import requests
import tempfile
from pathlib import Path

def download_video(url, output_path):
    """Download video from URL"""
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    
    return output_path

def handler(job):
    """RunPod handler function"""
    try:
        job_input = job.get("input", {})
        video_url = job_input.get("video_url")
        
        if not video_url:
            return {"error": "No video URL provided"}
        
        # Create temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = os.path.join(temp_dir, "input.mp4")
            output_dir = os.path.join(temp_dir, "output")
            os.makedirs(output_dir, exist_ok=True)
            
            # Download input video
            download_video(video_url, input_path)
            
            # Run SeedVR2 inference
            cmd = [
                "python", "/workspace/SeedVR/projects/inference_seedvr2_3b.py",
                "--video_path", input_path,
                "--output_dir", output_dir,
                "--seed", str(job_input.get("seed", 42)),
                "--res_h", str(job_input.get("res_h", 720)),
                "--res_w", str(job_input.get("res_w", 1280))
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {"error": f"Inference failed: {result.stderr}"}
            
            # Find output video
            output_files = list(Path(output_dir).glob("*.mp4"))
            if not output_files:
                return {"error": "No output video found"}
            
            # Upload to temporary storage (implement your upload logic)
            output_url = f"https://your-storage.com/{output_files[0].name}"
            
            return {
                "status": "success",
                "result_url": output_url
            }
            
    except Exception as e:
        return {"error": str(e)}

runpod.serverless.start({"handler": handler})
EOF

# Create API server
echo "Creating API server..."
cat > /workspace/api_server.py << 'EOF'
from flask import Flask, request, jsonify
import subprocess
import json
import os

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "SeedVR2"})

@app.route('/process', methods=['POST'])
def process():
    data = request.json
    video_url = data.get('video_url')
    
    if not video_url:
        return jsonify({"error": "No video URL provided"}), 400
    
    # Run the handler
    result = subprocess.run(
        ["python", "/workspace/handler.py"],
        input=json.dumps({"input": data}),
        capture_output=True,
        text=True
    )
    
    return jsonify(json.loads(result.stdout))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
EOF

echo "=== Setup complete! ==="
echo "To start the API server: python /workspace/api_server.py"
echo "To test the handler: python /workspace/handler.py"

EOSCRIPT

echo
echo "2. Setup script sent to RunPod pod"
echo "3. To check the logs, run: runpodctl logs $RUNPOD_POD_ID"
echo
echo "Next steps:"
echo "1. SSH into the pod: runpodctl exec $RUNPOD_POD_ID python"
echo "2. Start the API server: python /workspace/api_server.py"
echo "3. Update your frontend to use the RunPod pod endpoint"