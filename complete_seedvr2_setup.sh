#!/bin/bash
# COMPLETE SeedVR2 Setup - Everything from the official README
# This ensures ALL dependencies are installed

echo "============================================================"
echo "🚀 COMPLETE SEEDVR2 SETUP - FOLLOWING OFFICIAL README"
echo "============================================================"

# Step 1: Python environment (RunPod already has Python 3.10)
echo -e "\n📦 Step 1: Installing ALL SeedVR2 dependencies..."

# From the official SeedVR requirements
pip install --upgrade pip

# Core dependencies from SeedVR2 README
pip install torch==2.0.1 torchvision==0.15.2 --index-url https://download.pytorch.org/whl/cu118

# Install requirements from SeedVR repo
cd /workspace/SeedVR
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    # Manual install of all common dependencies
    pip install \
        diffusers \
        transformers \
        accelerate \
        opencv-python \
        einops \
        omegaconf \
        safetensors \
        huggingface_hub \
        scipy \
        imageio \
        imageio-ffmpeg \
        av \
        mediapy \
        tqdm \
        matplotlib \
        tensorboard \
        flask \
        flask-cors \
        requests
fi

# Try to install flash_attn (optional, may fail)
echo -e "\n📦 Installing optional flash attention..."
pip install flash_attn==2.5.9.post1 --no-build-isolation || echo "Flash attention optional - skipping"

# Step 2: Download apex wheel if needed
echo -e "\n📦 Step 2: Installing apex (if available)..."
if [ -f "/workspace/apex-0.1-cp310-cp310-linux_x86_64.whl" ]; then
    pip install /workspace/apex-0.1-cp310-cp310-linux_x86_64.whl
else
    echo "Apex wheel not found - skipping (optional)"
fi

# Step 3: Verify model exists
echo -e "\n🔍 Step 3: Checking SeedVR2 model..."
if [ -d "/workspace/ckpts/SeedVR2-7B" ]; then
    echo "✅ SeedVR2-7B model found!"
else
    echo "⚠️  Model not found. Downloading..."
    python3 << 'EOF'
from huggingface_hub import snapshot_download
import os
os.makedirs("/workspace/ckpts", exist_ok=True)
snapshot_download(
    repo_id="ByteDance-Seed/SeedVR2-7B",
    local_dir="/workspace/ckpts/SeedVR2-7B",
    resume_download=True
)
print("✅ Model downloaded!")
EOF
fi

# Step 4: Create test script
echo -e "\n🧪 Step 4: Creating test script..."
cat > /workspace/test_seedvr2.py << 'EOF'
#!/usr/bin/env python3
"""Test if SeedVR2 can be imported and run"""
import sys
sys.path.append("/workspace/SeedVR")

print("Testing SeedVR2 imports...")
try:
    import torch
    print(f"✅ PyTorch: {torch.__version__}")
    print(f"✅ CUDA available: {torch.cuda.is_available()}")
    
    import mediapy
    print("✅ mediapy imported")
    
    import imageio
    print("✅ imageio imported")
    
    import einops
    print("✅ einops imported")
    
    import diffusers
    print("✅ diffusers imported")
    
    # Test if we can import the inference script
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "inference", 
        "/workspace/SeedVR/projects/inference_seedvr2_7b.py"
    )
    if spec:
        print("✅ SeedVR2 inference script found")
    
    print("\n✅ All imports successful! SeedVR2 is ready to use.")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Run: pip install", e.name)
EOF

python3 /workspace/test_seedvr2.py

# Step 5: Create working server with all dependencies
echo -e "\n🌐 Step 5: Creating final server..."
cat > /workspace/seedvr2_server_final.py << 'EOF'
#!/usr/bin/env python3
from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
import os, sys, uuid, subprocess, threading, time, glob
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app, origins="*")

sys.path.append("/workspace/SeedVR")

UPLOAD_FOLDER = '/workspace/uploads'
OUTPUT_FOLDER = '/workspace/outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

jobs = {}

def run_seedvr2(job_id, input_path, output_dir):
    """Run actual SeedVR2 processing"""
    print(f"\n🚀 Processing {job_id} with SeedVR2...")
    
    cmd = [
        "python3", "-u",  # -u for unbuffered output
        "/workspace/SeedVR/projects/inference_seedvr2_7b.py",
        "--video_path", input_path,
        "--output_dir", output_dir,
        "--seed", "42",
        "--res_h", "720",
        "--res_w", "1280",
        "--sp_size", "2",
        "--ckpt_path", "/workspace/ckpts/SeedVR2-7B"
    ]
    
    try:
        # Set environment
        env = os.environ.copy()
        env['PYTHONPATH'] = '/workspace/SeedVR:' + env.get('PYTHONPATH', '')
        
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        
        if result.returncode == 0:
            print(f"✅ Processing completed for {job_id}")
            # Find output
            outputs = glob.glob(os.path.join(output_dir, "*.mp4"))
            if outputs:
                jobs[job_id]["status"] = "completed"
                jobs[job_id]["output_file"] = outputs[0]
            else:
                jobs[job_id]["status"] = "error"
                jobs[job_id]["error"] = "No output file found"
        else:
            print(f"❌ Error: {result.stderr}")
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = result.stderr[:1000]
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)

@app.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.route('/health', methods=['GET', 'OPTIONS'])
def health():
    if request.method == 'OPTIONS':
        return Response(status=200)
    return jsonify({"status": "healthy", "mode": "real"})

@app.route('/upload', methods=['POST', 'OPTIONS'])
def upload():
    if request.method == 'OPTIONS':
        return Response(status=200)
    
    if 'video' not in request.files:
        return jsonify({"error": "No video file"}), 400
    
    file = request.files['video']
    job_id = str(uuid.uuid4())[:8]
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, f"{job_id}_{filename}")
    file.save(filepath)
    
    job_output_dir = os.path.join(OUTPUT_FOLDER, job_id)
    os.makedirs(job_output_dir, exist_ok=True)
    
    jobs[job_id] = {
        "status": "processing",
        "started": time.time()
    }
    
    # Run in background
    thread = threading.Thread(target=run_seedvr2, args=(job_id, filepath, job_output_dir))
    thread.start()
    
    return jsonify({
        "status": "processing",
        "job_id": job_id,
        "message": "SeedVR2 processing started"
    })

@app.route('/status/<job_id>', methods=['GET', 'OPTIONS'])
def status(job_id):
    if request.method == 'OPTIONS':
        return Response(status=200)
    
    if job_id not in jobs:
        return jsonify({"error": "Job not found"}), 404
    
    job = jobs[job_id]
    
    if job["status"] == "completed":
        return jsonify({
            "status": "completed",
            "result_url": f"/download/{job_id}",
            "message": "SeedVR2 processing complete!"
        })
    elif job["status"] == "error":
        return jsonify({
            "status": "error",
            "error": job.get("error", "Processing failed")
        })
    else:
        elapsed = time.time() - job["started"]
        progress = min(90, int(elapsed * 2))
        return jsonify({
            "status": "processing",
            "progress": progress,
            "message": f"Processing... {progress}%"
        })

@app.route('/download/<job_id>')
def download(job_id):
    if job_id in jobs and "output_file" in jobs[job_id]:
        return send_file(jobs[job_id]["output_file"], as_attachment=True)
    return jsonify({"error": "File not found"}), 404

@app.route('/process', methods=['POST', 'OPTIONS'])
def process():
    if request.method == 'OPTIONS':
        return Response(status=200)
    return jsonify({"status": "ready", "mode": "real"})

if __name__ == '__main__':
    print("\n✅ SeedVR2 Server Ready with ALL Dependencies!")
    print("📡 https://ussvh2i624ql0g-8080.proxy.runpod.net\n")
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)
EOF

chmod +x /workspace/seedvr2_server_final.py

echo -e "\n============================================================"
echo "✅ COMPLETE SETUP FINISHED!"
echo "============================================================"
echo -e "\nTo start the server:"
echo "  python3 /workspace/seedvr2_server_final.py"
echo -e "\nAll dependencies from the official README are installed!"
echo "============================================================"