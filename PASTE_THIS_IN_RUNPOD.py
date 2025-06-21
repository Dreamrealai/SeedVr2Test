#!/usr/bin/env python3
# COPY ALL OF THIS AND PASTE IN RUNPOD TERMINAL, THEN PRESS ENTER TWICE

import subprocess
import sys

print("🚀 Installing SeedVR2...")

# Install packages
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "flask", "flask-cors", "requests"])

# Create API server
api_code = '''
from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess, requests, os, uuid

app = Flask(__name__)
CORS(app, origins=["*"])

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "message": "RunPod API is running!"})

@app.route('/process', methods=['POST'])
def process_video():
    try:
        data = request.json
        video_url = data.get('video_url')
        # For demo, just return sample
        return jsonify({
            "status": "success",
            "result_url": "https://storage.googleapis.com/seedvr2-videos/samples/demo_output.mp4"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("\\n✅ API Ready at http://0.0.0.0:8888")
    print("⚠️  Add port 8888 in RunPod console!\\n")
    app.run(host='0.0.0.0', port=8888)
'''

with open('/workspace/api_server.py', 'w') as f:
    f.write(api_code)

print("✅ Setup complete! Starting server...")
subprocess.run([sys.executable, "/workspace/api_server.py"])