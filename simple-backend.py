#!/usr/bin/env python3
"""
Simple backend to bridge frontend and RunPod
Run this on a cloud server or locally with ngrok
"""
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import requests
import os
import tempfile
import uuid
from google.cloud import storage
import json

app = Flask(__name__)
CORS(app)

# Configuration
RUNPOD_API_KEY = "rpa_UFDTAAMZ19E9WYJNTIPAMY4UG6DHWYZCO12RO6EUsi2hmd"
RUNPOD_POD_ID = "lh0wm9g482zr28"
GCS_BUCKET = "seedvr2-videos"

# Initialize GCS
with open('gcs-service-account-key.json') as f:
    gcs_key = json.load(f)
    
storage_client = storage.Client.from_service_account_info(gcs_key)
bucket = storage_client.bucket(GCS_BUCKET)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "runpod_configured": bool(RUNPOD_API_KEY),
        "gcs_configured": bool(storage_client)
    })

@app.route('/upload', methods=['POST'])
def upload():
    try:
        # Get uploaded file
        video_file = request.files.get('video')
        if not video_file:
            return jsonify({"error": "No video file provided"}), 400
        
        # Save to temp file
        temp_path = f"/tmp/{uuid.uuid4()}.mp4"
        video_file.save(temp_path)
        
        # Upload to GCS
        blob_name = f"uploads/{uuid.uuid4()}_{video_file.filename}"
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(temp_path)
        blob.make_public()
        
        # Clean up temp file
        os.remove(temp_path)
        
        # Get public URL
        public_url = blob.public_url
        
        # TODO: Submit to RunPod for processing
        # For now, return a mock job ID
        job_id = str(uuid.uuid4())
        
        return jsonify({
            "status": "processing",
            "job_id": job_id,
            "input_url": public_url
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/status/<job_id>', methods=['GET'])
def status(job_id):
    # TODO: Check actual RunPod job status
    # For now, return mock status
    return jsonify({
        "status": "processing",
        "message": "Video is being processed"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)