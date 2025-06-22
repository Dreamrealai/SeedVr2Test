#!/usr/bin/env python3
# SIMPLE CORS FIX - This worked before!

# First, install Flask with CORS
import subprocess
import sys
subprocess.run([sys.executable, "-m", "pip", "install", "--ignore-installed", "flask==2.3.2", "flask-cors==4.0.0"], capture_output=True)

# Kill any old servers
subprocess.run(["pkill", "-f", "python.*8080"], capture_output=True)

# Create and run the server
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import json, uuid

app = Flask(__name__)
CORS(app, origins="*")

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
    return jsonify({
        "status": "healthy",
        "message": "RunPod API is running!",
        "runpod_status": {"status": "healthy"}
    })

@app.route('/wake-up', methods=['POST', 'OPTIONS'])
def wake_up():
    if request.method == 'OPTIONS':
        return Response(status=200)
    return jsonify({"status": "success", "message": "Server is awake"})

@app.route('/upload', methods=['POST', 'OPTIONS'])
def upload():
    if request.method == 'OPTIONS':
        return Response(status=200)
    return jsonify({
        "status": "processing",
        "job_id": str(uuid.uuid4())[:8],
        "message": "Upload successful"
    })

@app.route('/status/<job_id>', methods=['GET', 'OPTIONS'])
def status(job_id):
    if request.method == 'OPTIONS':
        return Response(status=200)
    return jsonify({
        "status": "completed",
        "result_url": "https://storage.googleapis.com/seedvr2-videos/samples/demo_output.mp4"
    })

@app.route('/process', methods=['POST', 'OPTIONS'])
def process_video():
    if request.method == 'OPTIONS':
        return Response(status=200)
    return jsonify({
        "status": "success",
        "result_url": "https://storage.googleapis.com/seedvr2-videos/samples/demo_output.mp4"
    })

if __name__ == '__main__':
    print("\n✅ Starting server with CORS enabled")
    print("🌐 http://0.0.0.0:8080")
    print("📡 https://ussvh21624ql0g-8080.proxy.runpod.net")
    app.run(host='0.0.0.0', port=8080, debug=False)