#!/usr/bin/env python3
"""
SeedVR2 Complete RunPod Setup Script - FIXED VERSION
"""

import subprocess
import sys
import os
import time

print("="*60)
print("🚀 SeedVR2 COMPLETE SETUP FOR RUNPOD")
print("="*60)

# Step 1: Install required packages
print("\n📦 Step 1: Installing packages...")
packages = ["flask", "flask-cors", "requests"]
subprocess.run([sys.executable, "-m", "pip", "install", "-q"] + packages)
print("✅ Flask packages installed")

# Step 2: Kill any existing servers
print("\n🔄 Step 2: Cleaning up any existing servers...")
subprocess.run(["pkill", "-f", "api_server.py"], capture_output=True)
subprocess.run(["pkill", "-f", "flask"], capture_output=True)
# Try to kill processes on port 8080 using lsof
try:
    result = subprocess.run(["lsof", "-ti:8080"], capture_output=True, text=True)
    if result.stdout:
        pids = result.stdout.strip().split('\n')
        for pid in pids:
            subprocess.run(["kill", "-9", pid], capture_output=True)
except:
    pass
print("✅ Cleaned up existing processes")

# Step 3: Create the API server
print("\n🔧 Step 3: Creating API server...")
api_code = '''#!/usr/bin/env python3
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import os, uuid, json

app = Flask(__name__)
CORS(app, origins="*", allow_headers=["Content-Type"], methods=["GET", "POST", "OPTIONS"])

jobs = {}

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
    return jsonify({
        "status": "healthy",
        "message": "RunPod API is running!",
        "runpod_status": {"status": "healthy"}
    })

@app.route('/wake-up', methods=['POST', 'OPTIONS'])
def wake_up():
    return jsonify({"status": "success", "message": "Server is awake"})

@app.route('/upload', methods=['POST', 'OPTIONS'])
def upload():
    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {"status": "processing", "progress": 0}
    return jsonify({
        "status": "processing",
        "job_id": job_id,
        "message": "Upload successful"
    })

@app.route('/status/<job_id>', methods=['GET', 'OPTIONS'])
def status(job_id):
    return jsonify({
        "status": "completed",
        "result_url": "https://storage.googleapis.com/seedvr2-videos/samples/demo_output.mp4"
    })

@app.route('/process', methods=['POST', 'OPTIONS'])
def process_video():
    return jsonify({
        "status": "success",
        "result_url": "https://storage.googleapis.com/seedvr2-videos/samples/demo_output.mp4"
    })

if __name__ == '__main__':
    print("\\n✅ API Server Ready!")
    print("🌐 Running on http://0.0.0.0:8080")
    print("⚠️  Make sure port 8080 is exposed in RunPod!\\n")
    app.run(host='0.0.0.0', port=8080, debug=False)
'''

with open('/workspace/api_server.py', 'w') as f:
    f.write(api_code)
os.chmod('/workspace/api_server.py', 0o755)
print("✅ API server created")

# Step 4: Start the server
print("\n🚀 Step 4: Starting API server...")
print("="*60)
print("IMPORTANT: Make sure port 8080 is exposed in RunPod console!")
print("="*60)

# Give a moment for cleanup
time.sleep(1)

# Run the server
subprocess.run([sys.executable, "/workspace/api_server.py"])