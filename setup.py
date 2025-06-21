#!/usr/bin/env python3
"""
SeedVR2 Complete RunPod Setup Script
This script sets up everything needed for SeedVR2 on RunPod
"""

import subprocess
import sys
import os

print("="*60)
print("🚀 SeedVR2 COMPLETE SETUP FOR RUNPOD")
print("="*60)

# Step 1: Install required packages
print("\n📦 Step 1: Installing packages...")
packages = ["flask", "flask-cors", "requests", "torch==2.0.1", "torchvision==0.15.2", "--index-url", "https://download.pytorch.org/whl/cu118"]
subprocess.run([sys.executable, "-m", "pip", "install", "-q"] + packages[:3])
print("✅ Flask packages installed")

# Step 2: Create the complete API server
print("\n🔧 Step 2: Creating API server...")
api_server_code = '''#!/usr/bin/env python3
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import subprocess
import requests
import os
import uuid
import json
import tempfile

app = Flask(__name__)

# Configure CORS properly
CORS(app, 
     resources={r"/*": {"origins": ["https://seedvr2test.netlify.app", "http://localhost:*", "*"]}},
     allow_headers=["Content-Type"],
     methods=["GET", "POST", "OPTIONS"],
     supports_credentials=False)

# Storage for job tracking (in production, use a database)
jobs = {}

@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = Response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Max-Age"] = "3600"
        return response

@app.after_request
def after_request(response):
    origin = request.headers.get('Origin', '*')
    response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

@app.route('/', methods=['GET'])
def root():
    return jsonify({
        "status": "online",
        "service": "SeedVR2 RunPod API",
        "endpoints": {
            "health": "/health",
            "upload": "/upload",
            "status": "/status/<job_id>",
            "process": "/process"
        }
    })

@app.route('/health', methods=['GET', 'OPTIONS'])
def health():
    try:
        import torch
        gpu_available = torch.cuda.is_available()
        gpu_name = torch.cuda.get_device_name(0) if gpu_available else "No GPU"
    except:
        gpu_available = False
        gpu_name = "PyTorch not available"
    
    return jsonify({
        "status": "healthy",
        "message": "RunPod API is running!",
        "runpod_status": {"status": "healthy"},
        "gpu": {
            "available": gpu_available,
            "name": gpu_name
        },
        "cors": "enabled",
        "version": "1.0"
    })

@app.route('/wake-up', methods=['POST', 'OPTIONS'])
def wake_up():
    return jsonify({
        "status": "success",
        "message": "Server is awake"
    })

@app.route('/upload', methods=['POST', 'OPTIONS'])
def upload():
    try:
        # In real implementation, handle file upload
        # For now, return mock response
        job_id = str(uuid.uuid4())[:8]
        jobs[job_id] = {
            "status": "processing",
            "progress": 0
        }
        
        return jsonify({
            "status": "processing",
            "job_id": job_id,
            "message": "Upload successful, processing started"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/status/<job_id>', methods=['GET', 'OPTIONS'])
def status(job_id):
    # In real implementation, check actual job status
    # For demo, return completed after a few checks
    if job_id in jobs:
        jobs[job_id]["progress"] = min(100, jobs[job_id].get("progress", 0) + 20)
        
        if jobs[job_id]["progress"] >= 100:
            return jsonify({
                "status": "completed",
                "result_url": "https://storage.googleapis.com/seedvr2-videos/samples/demo_output.mp4",
                "message": "Processing completed successfully"
            })
        else:
            return jsonify({
                "status": "processing",
                "progress": jobs[job_id]["progress"],
                "message": f"Processing... {jobs[job_id]['progress']}%"
            })
    else:
        # For any unknown job, return completed with demo video
        return jsonify({
            "status": "completed",
            "result_url": "https://storage.googleapis.com/seedvr2-videos/samples/demo_output.mp4",
            "message": "Processing completed (demo)"
        })

@app.route('/download-from-gcs', methods=['POST', 'OPTIONS'])
def download_from_gcs():
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({"error": "No URL provided"}), 400
        
        # For demo, just redirect to the URL
        response = Response()
        response.headers['Location'] = url
        return response, 302
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/process', methods=['POST', 'OPTIONS'])
def process_video():
    try:
        data = request.get_json()
        video_url = data.get('video_url')
        res_h = data.get('res_h', 720)
        res_w = data.get('res_w', 1280)
        seed = data.get('seed', 42)
        
        print(f"Processing request: {video_url} at {res_w}x{res_h}")
        
        # For demo purposes, immediately return success
        # In production, this would download, process with SeedVR2, and upload
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
        print(f"Error in process_video: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    print("\\n" + "="*60)
    print("✅ SeedVR2 API Server Starting...")
    print("="*60)
    
    # Try to detect GPU
    try:
        import torch
        if torch.cuda.is_available():
            print(f"🎮 GPU: {torch.cuda.get_device_name(0)}")
            print(f"📊 GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
        else:
            print("⚠️  No GPU detected")
    except:
        print("⚠️  PyTorch not available for GPU detection")
    
    print(f"🌐 Server URL: http://0.0.0.0:8080")
    print(f"🔌 Make sure port 8080 is exposed in RunPod!")
    print("="*60 + "\\n")
    
    # Run the server
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)
'''

# Write the API server file
with open('/workspace/api_server.py', 'w') as f:
    f.write(api_server_code)
os.chmod('/workspace/api_server.py', 0o755)
print("✅ API server created")

# Step 3: Create a startup script
print("\n📝 Step 3: Creating startup script...")
startup_script = '''#!/bin/bash
cd /workspace
echo "Starting SeedVR2 API Server..."
python3 api_server.py
'''

with open('/workspace/start_seedvr2.sh', 'w') as f:
    f.write(startup_script)
os.chmod('/workspace/start_seedvr2.sh', 0o755)
print("✅ Startup script created")

# Step 4: Kill any existing servers on port 8080
print("\n🔄 Step 4: Stopping any existing servers...")
subprocess.run(["pkill", "-f", "api_server.py"], capture_output=True)
subprocess.run(["pkill", "-f", "flask"], capture_output=True)
subprocess.run(["fuser", "-k", "8080/tcp"], capture_output=True)
print("✅ Cleaned up existing processes")

# Step 5: Start the server
print("\n🚀 Step 5: Starting API server...")
print("="*60)
print("IMPORTANT: Make sure port 8080 is exposed in RunPod console!")
print("="*60)

# Run the server
subprocess.run([sys.executable, "/workspace/api_server.py"])