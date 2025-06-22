#!/usr/bin/env python3
"""
REAL SeedVR2 Processing Server - Actually runs the model
"""

import subprocess
import sys

# Install dependencies
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "flask", "flask-cors"], capture_output=True)

from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
import os, uuid, shutil, threading, time
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app, origins="*")

UPLOAD_FOLDER = '/workspace/uploads'
OUTPUT_FOLDER = '/workspace/outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Add SeedVR to Python path
sys.path.append("/workspace/SeedVR")

jobs = {}

def run_seedvr2_processing(job_id, input_path, output_dir):
    """Actually run SeedVR2 processing"""
    print(f"\n🚀 Starting REAL SeedVR2 processing for job {job_id}")
    
    # Build the command to run SeedVR2
    cmd = [
        "python3",
        "/workspace/SeedVR/projects/inference_seedvr2_7b.py",
        "--video_path", input_path,
        "--output_dir", output_dir,
        "--seed", "42",
        "--res_h", "720",  # Start with 720p for faster processing
        "--res_w", "1280",
        "--sp_size", "2",  # Use both GPUs
        "--ckpt_path", "/workspace/ckpts/SeedVR2-7B"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        # Run the actual SeedVR2 model
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ SeedVR2 processing completed for {job_id}")
            jobs[job_id]["status"] = "completed"
            
            # Find the output file
            import glob
            output_files = glob.glob(os.path.join(output_dir, "*.mp4"))
            if output_files:
                jobs[job_id]["output_file"] = output_files[0]
            else:
                print(f"⚠️ No output file found for {job_id}")
                jobs[job_id]["status"] = "error"
                jobs[job_id]["error"] = "No output file generated"
        else:
            print(f"❌ SeedVR2 processing failed: {result.stderr}")
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = result.stderr[:500]  # First 500 chars of error
            
    except Exception as e:
        print(f"❌ Exception during processing: {str(e)}")
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)

@app.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.route('/')
def root():
    model_exists = os.path.exists("/workspace/ckpts/SeedVR2-7B")
    seedvr_exists = os.path.exists("/workspace/SeedVR/projects/inference_seedvr2_7b.py")
    
    return jsonify({
        "status": "online",
        "message": "SeedVR2 REAL Processing Server",
        "model_loaded": model_exists,
        "seedvr_ready": seedvr_exists,
        "mode": "REAL" if model_exists and seedvr_exists else "ERROR"
    })

@app.route('/health', methods=['GET', 'OPTIONS'])
def health():
    if request.method == 'OPTIONS':
        return Response(status=200)
    
    import torch
    return jsonify({
        "status": "healthy",
        "message": "Real SeedVR2 server running!",
        "runpod_status": {"status": "healthy"},
        "gpu_count": torch.cuda.device_count(),
        "model_path": "/workspace/ckpts/SeedVR2-7B",
        "processing_mode": "REAL"
    })

@app.route('/upload', methods=['POST', 'OPTIONS'])
def upload():
    if request.method == 'OPTIONS':
        return Response(status=200)
    
    if 'video' not in request.files:
        return jsonify({"error": "No video file"}), 400
    
    file = request.files['video']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    # Save uploaded file
    job_id = str(uuid.uuid4())[:8]
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, f"{job_id}_{filename}")
    file.save(filepath)
    
    # Create job
    jobs[job_id] = {
        "status": "processing",
        "input_file": filepath,
        "progress": 0,
        "started": time.time()
    }
    
    # Create output directory for this job
    job_output_dir = os.path.join(OUTPUT_FOLDER, job_id)
    os.makedirs(job_output_dir, exist_ok=True)
    
    # Start REAL processing in background thread
    thread = threading.Thread(
        target=run_seedvr2_processing,
        args=(job_id, filepath, job_output_dir)
    )
    thread.start()
    
    return jsonify({
        "status": "processing",
        "job_id": job_id,
        "message": "REAL SeedVR2 processing started!"
    })

@app.route('/status/<job_id>', methods=['GET', 'OPTIONS'])
def status(job_id):
    if request.method == 'OPTIONS':
        return Response(status=200)
    
    if job_id not in jobs:
        return jsonify({"error": "Job not found"}), 404
    
    job = jobs[job_id]
    
    if job["status"] == "completed":
        if "output_file" in job and os.path.exists(job["output_file"]):
            # Return download URL
            return jsonify({
                "status": "completed",
                "result_url": f"/download/{job_id}",
                "message": "SeedVR2 processing completed!",
                "processing_time": time.time() - job["started"]
            })
        else:
            return jsonify({
                "status": "error",
                "error": "Output file not found",
                "message": "Processing may have failed"
            })
    
    elif job["status"] == "error":
        return jsonify({
            "status": "error",
            "error": job.get("error", "Unknown error"),
            "message": "SeedVR2 processing failed"
        })
    
    else:  # still processing
        # Calculate approximate progress based on time
        elapsed = time.time() - job["started"]
        estimated_progress = min(90, int(elapsed * 2))  # ~45 seconds estimate
        
        return jsonify({
            "status": "processing",
            "progress": estimated_progress,
            "message": f"SeedVR2 processing... {estimated_progress}%",
            "elapsed_time": elapsed
        })

@app.route('/download/<job_id>')
def download(job_id):
    if job_id not in jobs:
        return jsonify({"error": "Job not found"}), 404
    
    job = jobs[job_id]
    if "output_file" in job and os.path.exists(job["output_file"]):
        return send_file(
            job["output_file"],
            as_attachment=True,
            download_name=f"seedvr2_{job_id}.mp4",
            mimetype='video/mp4'
        )
    
    return jsonify({"error": "Output file not found"}), 404

@app.route('/process', methods=['POST', 'OPTIONS'])
def process_video():
    if request.method == 'OPTIONS':
        return Response(status=200)
    
    # This endpoint is for compatibility
    # Real processing happens in /upload
    return jsonify({
        "status": "ready",
        "message": "Use /upload endpoint for real processing",
        "mode": "REAL"
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 REAL SEEDVR2 PROCESSING SERVER")
    print("="*60)
    
    # Check setup
    model_ok = os.path.exists("/workspace/ckpts/SeedVR2-7B")
    script_ok = os.path.exists("/workspace/SeedVR/projects/inference_seedvr2_7b.py")
    
    if model_ok and script_ok:
        print("✅ SeedVR2 Model: FOUND")
        print("✅ Inference Script: FOUND")
        print("✅ Mode: REAL PROCESSING")
    else:
        print("❌ Setup incomplete:")
        if not model_ok:
            print("   - Model not found at /workspace/ckpts/SeedVR2-7B")
        if not script_ok:
            print("   - Script not found at /workspace/SeedVR/projects/inference_seedvr2_7b.py")
    
    print("\n📡 Server: http://0.0.0.0:8080")
    print("🌐 RunPod: https://ussvh2i624ql0g-8080.proxy.runpod.net")
    print("\n⚠️  Upload a video to see REAL SeedVR2 processing!")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)