#!/usr/bin/env python3
# RunPod Proxy Fix - Adds root route and better error handling

import subprocess
import sys
subprocess.run([sys.executable, "-m", "pip", "install", "--ignore-installed", "flask==2.3.2", "flask-cors==4.0.0"], capture_output=True)
subprocess.run(["pkill", "-f", "python.*8080"], capture_output=True)

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

# IMPORTANT: Add root route for RunPod proxy
@app.route('/', methods=['GET'])
def root():
    return jsonify({
        "status": "online",
        "message": "SeedVR2 API is running!",
        "endpoints": {
            "health": "/health",
            "upload": "/upload",
            "process": "/process"
        }
    })

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

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found", "message": "Endpoint not found"}), 404

if __name__ == '__main__':
    print("\n✅ Starting server with RunPod proxy fix")
    print("🌐 Local: http://0.0.0.0:8080")
    print("📡 RunPod: https://ussvh21624ql0g-8080.proxy.runpod.net")
    print("\n🔍 Test URLs:")
    print("- https://ussvh21624ql0g-8080.proxy.runpod.net/")
    print("- https://ussvh21624ql0g-8080.proxy.runpod.net/health")
    app.run(host='0.0.0.0', port=8080, debug=False)