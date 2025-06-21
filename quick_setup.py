#!/usr/bin/env python3
import os
import subprocess

print("Installing dependencies...")
subprocess.run(["pip", "install", "flask", "flask-cors", "requests"], check=True)

print("Creating simple test API...")
api_code = '''
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "message": "RunPod API is running!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888)
'''

with open("/workspace/test_api.py", "w") as f:
    f.write(api_code)

print("Done! Run: python /workspace/test_api.py")