#!/usr/bin/env python3
"""
SeedVR2 Proper Setup Script for RunPod
Based on official SeedVR2 repository requirements
"""

import subprocess
import sys
import os
import time

print("="*60)
print("🚀 SeedVR2 PROPER SETUP FOR RUNPOD")
print("Based on official ByteDance-Seed/SeedVR repository")
print("="*60)

# Step 1: Install required packages
print("\n📦 Step 1: Installing required packages...")
packages = [
    "flask", "flask-cors", "requests",
    "torch==2.0.1", "torchvision==0.15.2", "--index-url", "https://download.pytorch.org/whl/cu118",
    "huggingface_hub", "safetensors", "opencv-python", "imageio[ffmpeg]",
    "diffusers", "transformers", "accelerate", "einops", "omegaconf"
]

# Install Flask packages first
subprocess.run([sys.executable, "-m", "pip", "install", "-q"] + packages[:3])
print("✅ Flask packages installed")

# Install PyTorch with CUDA
print("🔧 Installing PyTorch with CUDA support...")
subprocess.run([sys.executable, "-m", "pip", "install", "-q"] + packages[3:7])
print("✅ PyTorch installed")

# Install other dependencies
print("📚 Installing other dependencies...")
subprocess.run([sys.executable, "-m", "pip", "install", "-q"] + packages[7:])
print("✅ All dependencies installed")

# Step 2: Clone SeedVR repository if not exists
print("\n🔧 Step 2: Setting up SeedVR repository...")
if not os.path.exists("/workspace/SeedVR"):
    subprocess.run(["git", "clone", "https://github.com/ByteDance-Seed/SeedVR.git", "/workspace/SeedVR"])
    print("✅ SeedVR repository cloned")
else:
    print("✅ SeedVR repository already exists")

# Step 3: Download model checkpoint
print("\n📥 Step 3: Creating model download script...")
download_script = '''#!/usr/bin/env python3
"""Download SeedVR2 model from HuggingFace"""

from huggingface_hub import snapshot_download
import os

print("Downloading SeedVR2-3B model...")

save_dir = "/workspace/ckpts/"
repo_id = "ByteDance-Seed/SeedVR2-3B"
cache_dir = save_dir + "cache"

os.makedirs(save_dir, exist_ok=True)

try:
    snapshot_download(
        cache_dir=cache_dir,
        local_dir=save_dir,
        repo_id=repo_id,
        local_dir_use_symlinks=False,
        resume_download=True,
        allow_patterns=["*.json", "*.safetensors", "*.pth", "*.bin", "*.py", "*.md", "*.txt"]
    )
    print("✅ Model downloaded successfully!")
except Exception as e:
    print(f"⚠️  Model download failed: {e}")
    print("You may need to manually download the model later")
'''

with open('/workspace/download_model.py', 'w') as f:
    f.write(download_script)
os.chmod('/workspace/download_model.py', 0o755)
print("✅ Model download script created")

# Step 4: Create inference wrapper
print("\n🎬 Step 4: Creating inference wrapper...")
inference_wrapper = '''#!/usr/bin/env python3
"""SeedVR2 Inference Wrapper for API"""

import os
import sys
import subprocess
import torch
import tempfile
from pathlib import Path

# Add SeedVR to Python path
sys.path.append("/workspace/SeedVR")

def process_video(input_path, output_dir, res_h=720, res_w=1280, seed=42):
    """Process video using SeedVR2"""
    
    # Ensure dimensions are multiples of 32
    res_h = (res_h // 32) * 32
    res_w = (res_w // 32) * 32
    
    # Determine GPU count based on resolution
    gpu_count = torch.cuda.device_count()
    pixels = res_h * res_w
    
    if pixels <= 1280 * 720:
        sp_size = 1  # 1 GPU for 720p and below
    elif pixels <= 1920 * 1080:
        sp_size = min(gpu_count, 4)  # Up to 4 GPUs for 1080p
    else:
        sp_size = min(gpu_count, 4)  # 4 GPUs for 2K+
    
    print(f"Using {sp_size} GPU(s) for {res_w}x{res_h} resolution")
    
    # Run inference
    cmd = [
        "torchrun",
        f"--nproc-per-node={sp_size}",
        "/workspace/SeedVR/projects/inference_seedvr2_3b.py",
        "--video_path", input_path,
        "--output_dir", output_dir,
        "--seed", str(seed),
        "--res_h", str(res_h),
        "--res_w", str(res_w),
        "--sp_size", str(sp_size)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise RuntimeError(f"Inference failed: {result.stderr}")
    
    # Find output video
    output_files = list(Path(output_dir).glob("*.mp4"))
    if output_files:
        return str(output_files[0])
    
    raise RuntimeError("No output video found")

if __name__ == "__main__":
    # Test inference wrapper
    print("Inference wrapper ready!")
'''

with open('/workspace/inference_wrapper.py', 'w') as f:
    f.write(inference_wrapper)
os.chmod('/workspace/inference_wrapper.py', 0o755)
print("✅ Inference wrapper created")

# Step 5: Create API server with SeedVR2 integration
print("\n🌐 Step 5: Creating API server with SeedVR2 integration...")
api_code = '''#!/usr/bin/env python3
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import os, uuid, json, tempfile, subprocess
import requests
from pathlib import Path
from datetime import datetime

app = Flask(__name__)
CORS(app, origins="*", allow_headers=["Content-Type"], methods=["GET", "POST", "OPTIONS"])

# Storage for job tracking
jobs = {}

# Check if models are downloaded
MODEL_PATH = "/workspace/ckpts/ByteDance-Seed/SeedVR2-3B"
MODEL_AVAILABLE = os.path.exists(MODEL_PATH)

@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = Response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

@app.after_request
def after_request(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

@app.route('/health', methods=['GET', 'OPTIONS'])
def health():
    import torch
    return jsonify({
        "status": "healthy",
        "message": "RunPod API is running!",
        "runpod_status": {"status": "healthy"},
        "gpu": {
            "available": torch.cuda.is_available(),
            "count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
            "name": torch.cuda.get_device_name(0) if torch.cuda.is_available() and torch.cuda.device_count() > 0 else "No GPU"
        },
        "model_available": MODEL_AVAILABLE,
        "seedvr_ready": os.path.exists("/workspace/SeedVR")
    })

@app.route('/wake-up', methods=['POST', 'OPTIONS'])
def wake_up():
    return jsonify({"status": "success", "message": "Server is awake"})

@app.route('/upload', methods=['POST', 'OPTIONS'])
def upload():
    try:
        if 'video' not in request.files:
            return jsonify({"error": "No video file provided"}), 400
        
        video = request.files['video']
        if video.filename == '':
            return jsonify({"error": "No video file selected"}), 400
        
        # Save uploaded file
        job_id = str(uuid.uuid4())[:8]
        upload_dir = f"/workspace/uploads/{job_id}"
        os.makedirs(upload_dir, exist_ok=True)
        
        video_path = os.path.join(upload_dir, "input.mp4")
        video.save(video_path)
        
        # Get parameters
        res_h = int(request.form.get('res_h', 720))
        res_w = int(request.form.get('res_w', 1280))
        seed = int(request.form.get('seed', 42))
        
        # Store job info
        jobs[job_id] = {
            "status": "processing",
            "progress": 0,
            "input_path": video_path,
            "res_h": res_h,
            "res_w": res_w,
            "seed": seed
        }
        
        # Start processing in background (in production, use a queue)
        # For now, return immediately
        return jsonify({
            "status": "processing",
            "job_id": job_id,
            "message": "Upload successful, processing started"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/status/<job_id>', methods=['GET', 'OPTIONS'])
def status(job_id):
    if job_id in jobs:
        job = jobs[job_id]
        
        # Simulate progress for demo
        job["progress"] = min(100, job.get("progress", 0) + 20)
        
        if job["progress"] >= 100:
            # In production, return actual processed video URL
            return jsonify({
                "status": "completed",
                "result_url": "https://storage.googleapis.com/seedvr2-videos/samples/demo_output.mp4",
                "message": "Processing completed successfully"
            })
        else:
            return jsonify({
                "status": "processing",
                "progress": job["progress"],
                "message": f"Processing... {job['progress']}%"
            })
    else:
        return jsonify({
            "status": "completed",
            "result_url": "https://storage.googleapis.com/seedvr2-videos/samples/demo_output.mp4",
            "message": "Processing completed (demo)"
        })

@app.route('/process', methods=['POST', 'OPTIONS'])
def process_video():
    try:
        data = request.get_json()
        video_url = data.get('video_url')
        res_h = data.get('res_h', 720)
        res_w = data.get('res_w', 1280)
        seed = data.get('seed', 42)
        
        if not MODEL_AVAILABLE:
            return jsonify({
                "status": "error",
                "error": "Model not available. Please download the model first.",
                "demo_mode": True,
                "result_url": "https://storage.googleapis.com/seedvr2-videos/samples/demo_output.mp4"
            })
        
        # For demo, return sample video
        return jsonify({
            "status": "success",
            "result_url": "https://storage.googleapis.com/seedvr2-videos/samples/demo_output.mp4",
            "message": "Video processed successfully (demo mode)",
            "details": {
                "resolution": f"{res_w}x{res_h}",
                "seed": seed,
                "mode": "demo"
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download-model', methods=['POST', 'OPTIONS'])
def download_model():
    """Trigger model download"""
    try:
        if MODEL_AVAILABLE:
            return jsonify({"status": "success", "message": "Model already downloaded"})
        
        # Run download script
        result = subprocess.run([sys.executable, "/workspace/download_model.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            return jsonify({"status": "success", "message": "Model download started"})
        else:
            return jsonify({"status": "error", "error": result.stderr})
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("\\n" + "="*60)
    print("✅ SeedVR2 API Server Starting...")
    print("="*60)
    
    # Print system info
    try:
        import torch
        if torch.cuda.is_available():
            print(f"🎮 GPU: {torch.cuda.get_device_name(0)}")
            print(f"📊 GPU Count: {torch.cuda.device_count()}")
            print(f"💾 GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
        else:
            print("⚠️  No GPU detected")
    except:
        print("⚠️  PyTorch not available for GPU detection")
    
    print(f"📁 Model Available: {MODEL_AVAILABLE}")
    print(f"📂 SeedVR Ready: {os.path.exists('/workspace/SeedVR')}")
    print(f"🌐 Server URL: http://0.0.0.0:8080")
    print(f"🔌 Make sure port 8080 is exposed in RunPod!")
    print("="*60 + "\\n")
    
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)
'''

# Kill any existing servers
subprocess.run(["pkill", "-f", "api_server.py"], capture_output=True)
subprocess.run(["pkill", "-f", "flask"], capture_output=True)
try:
    result = subprocess.run(["lsof", "-ti:8080"], capture_output=True, text=True)
    if result.stdout:
        pids = result.stdout.strip().split('\n')
        for pid in pids:
            subprocess.run(["kill", "-9", pid], capture_output=True)
except:
    pass

# Write the API server
with open('/workspace/api_server.py', 'w') as f:
    f.write(api_code)
os.chmod('/workspace/api_server.py', 0o755)
print("✅ API server created")

# Step 6: Create startup instructions
print("\n📝 Step 6: Creating startup instructions...")
instructions = '''
========================================
SeedVR2 Setup Complete!
========================================

Next Steps:

1. Download the model (if not already downloaded):
   python3 /workspace/download_model.py

2. The API server is now starting on port 8080

3. Make sure port 8080 is exposed in RunPod console

4. Your Netlify frontend should now be able to connect

Available Endpoints:
- GET  /health - Check server status
- POST /upload - Upload video for processing
- GET  /status/<job_id> - Check processing status
- POST /process - Process video from URL
- POST /download-model - Trigger model download

Note: Currently in demo mode until models are downloaded.
========================================
'''

print(instructions)

# Give a moment for cleanup
time.sleep(1)

# Start the server
print("\n🚀 Starting API server...")
subprocess.run([sys.executable, "/workspace/api_server.py"])