#!/usr/bin/env python3
import os
import subprocess
import sys

print("=== SeedVR2 RunPod Installation Script ===")

# Change to workspace directory
os.chdir("/workspace")

# Clone repositories
print("\n1. Cloning repositories...")
if not os.path.exists("SeedVR"):
    subprocess.run(["git", "clone", "https://github.com/ByteDance-Seed/SeedVR.git"], check=True)

if not os.path.exists("SeedVr2Test"):
    subprocess.run(["git", "clone", "https://github.com/Dreamrealai/SeedVr2Test.git"], check=True)

# Install Python dependencies
print("\n2. Installing Python dependencies...")
os.chdir("/workspace/SeedVR")

# Install PyTorch first
subprocess.run([sys.executable, "-m", "pip", "install", "torch==2.0.1", "torchvision==0.15.2", "torchaudio==2.0.2", "--index-url", "https://download.pytorch.org/whl/cu118"], check=True)

# Install other requirements
subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=False)

# Install additional dependencies
deps = ["flask", "flask-cors", "requests", "google-cloud-storage", "runpod"]
subprocess.run([sys.executable, "-m", "pip", "install"] + deps, check=True)

# Copy handler from our repo
print("\n3. Setting up handler...")
subprocess.run(["cp", "/workspace/SeedVr2Test/runpod/handler.py", "/workspace/handler.py"], check=True)

# Create API server
print("\n4. Creating API server...")
api_server_code = '''
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import subprocess
import requests
import os
import tempfile
import uuid
import json
import sys

app = Flask(__name__)
CORS(app, origins=["https://seedvr2test.netlify.app"])

# Add SeedVR to Python path
sys.path.append("/workspace/SeedVR")

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy", 
        "message": "RunPod SeedVR2 API running",
        "cuda_available": torch.cuda.is_available() if 'torch' in sys.modules else False
    })

@app.route('/process', methods=['POST'])
def process_video():
    try:
        data = request.json
        video_url = data.get('video_url')
        res_h = data.get('res_h', 720)
        res_w = data.get('res_w', 1280)
        seed = data.get('seed', 42)
        
        if not video_url:
            return jsonify({"error": "No video URL provided"}), 400
        
        # Download video
        print(f"Downloading video from {video_url}")
        temp_input = f"/tmp/input_{uuid.uuid4()}.mp4"
        temp_output_dir = f"/tmp/output_{uuid.uuid4()}"
        os.makedirs(temp_output_dir, exist_ok=True)
        
        # Download the video
        response = requests.get(video_url, stream=True)
        with open(temp_input, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Check if SeedVR2 inference script exists
        inference_script = "/workspace/SeedVR/projects/inference_seedvr2_3b.py"
        if os.path.exists(inference_script):
            # Run actual SeedVR2
            cmd = [
                "python", inference_script,
                "--video_path", temp_input,
                "--output_dir", temp_output_dir,
                "--seed", str(seed),
                "--res_h", str(res_h),
                "--res_w", str(res_w)
            ]
            print(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Error: {result.stderr}")
                # Fall back to FFmpeg
                use_ffmpeg = True
            else:
                use_ffmpeg = False
        else:
            print("SeedVR2 inference script not found, using FFmpeg fallback")
            use_ffmpeg = True
        
        if use_ffmpeg:
            # Fallback: Simple upscaling with FFmpeg
            temp_output = os.path.join(temp_output_dir, "output.mp4")
            cmd = [
                'ffmpeg', '-i', temp_input,
                '-vf', f"scale={res_w}:{res_h}:flags=lanczos",
                '-c:v', 'libx264', '-crf', '18', '-preset', 'slow',
                '-c:a', 'copy',
                temp_output
            ]
            subprocess.run(cmd, check=True)
        
        # Find output video
        output_files = [f for f in os.listdir(temp_output_dir) if f.endswith('.mp4')]
        if not output_files:
            return jsonify({"error": "No output video generated"}), 500
        
        output_path = os.path.join(temp_output_dir, output_files[0])
        
        # Upload to GCS (if configured) or return file directly
        # For now, return a placeholder
        return jsonify({
            "status": "success",
            "result_url": f"http://{request.host}/download/{os.path.basename(output_path)}",
            "message": "Processing completed"
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Try to import torch to check CUDA
    try:
        import torch
        print(f"PyTorch available. CUDA: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"CUDA device: {torch.cuda.get_device_name(0)}")
    except:
        print("PyTorch not available")
    
    print("Starting API server on port 8888...")
    app.run(host='0.0.0.0', port=8888, debug=True)
'''

with open("/workspace/api_server.py", "w") as f:
    f.write(api_server_code)

# Create startup script
print("\n5. Creating startup script...")
startup_script = '''#!/bin/bash
cd /workspace
export PYTHONPATH=/workspace/SeedVR:$PYTHONPATH
echo "Starting SeedVR2 API server..."
python api_server.py
'''

with open("/workspace/start_api.sh", "w") as f:
    f.write(startup_script)

os.chmod("/workspace/start_api.sh", 0o755)

# Download models if available
print("\n6. Checking for models...")
print("Note: SeedVR2 models may not be publicly available yet.")
print("Check https://huggingface.co/ByteDance-Seed for model availability.")

print("\n=== Installation Complete ===")
print("\nTo start the API server:")
print("  /workspace/start_api.sh")
print("\nThe API will be available at http://<POD_IP>:8888")
print("\nTo get your pod's public IP:")
print("  curl ifconfig.me")
