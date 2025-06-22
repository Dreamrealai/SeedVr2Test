#!/usr/bin/env python3
"""
Fix SeedVR2 Python paths and run processing correctly
"""

import subprocess
import sys
import os

print("🔧 Fixing SeedVR2 paths and dependencies...")

# First, make sure we're in the right directory structure
print("\n📂 Checking SeedVR directory structure...")
seedvr_path = "/workspace/SeedVR"
if os.path.exists(f"{seedvr_path}/models") and os.path.exists(f"{seedvr_path}/projects"):
    print("✅ SeedVR directory structure looks good")
else:
    print("❌ SeedVR directory structure issue")
    print("Contents of /workspace/SeedVR:")
    subprocess.run(["ls", "-la", seedvr_path])

# Create a wrapper script that sets up the environment correctly
print("\n🔧 Creating SeedVR2 wrapper script...")
wrapper_script = '''#!/usr/bin/env python3
import os
import sys
import subprocess

def run_seedvr2_inference(video_path, output_dir, res_h=720, res_w=1280, seed=42):
    """Run SeedVR2 with correct Python paths"""
    
    # Change to SeedVR directory (IMPORTANT!)
    os.chdir("/workspace/SeedVR")
    
    # Add SeedVR to Python path
    sys.path.insert(0, "/workspace/SeedVR")
    
    # Run the inference script from the correct directory
    cmd = [
        sys.executable,
        "projects/inference_seedvr2_7b.py",  # Relative path from SeedVR dir
        "--video_path", video_path,
        "--output_dir", output_dir,
        "--seed", str(seed),
        "--res_h", str(res_h),
        "--res_w", str(res_w),
        "--sp_size", "2",
        "--ckpt_path", "/workspace/ckpts/SeedVR2-7B"
    ]
    
    print(f"Running from directory: {os.getcwd()}")
    print(f"Command: {' '.join(cmd)}")
    
    # Set environment
    env = os.environ.copy()
    env['PYTHONPATH'] = "/workspace/SeedVR:" + env.get('PYTHONPATH', '')
    env['CUDA_VISIBLE_DEVICES'] = "0,1"  # Use both GPUs
    
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    
    if result.returncode == 0:
        print("✅ SeedVR2 inference completed successfully!")
        return True, result.stdout
    else:
        print(f"❌ SeedVR2 inference failed: {result.stderr}")
        return False, result.stderr

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: seedvr2_wrapper.py <input_video> <output_dir>")
        sys.exit(1)
    
    success, output = run_seedvr2_inference(sys.argv[1], sys.argv[2])
    print(output)
    sys.exit(0 if success else 1)
'''

with open('/workspace/seedvr2_wrapper.py', 'w') as f:
    f.write(wrapper_script)
os.chmod('/workspace/seedvr2_wrapper.py', 0o755)

# Create the final server that uses the wrapper
print("\n🌐 Creating fixed server...")
server_code = '''#!/usr/bin/env python3
from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
import os, uuid, subprocess, threading, time, glob
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app, origins="*")

UPLOAD_FOLDER = '/workspace/uploads'
OUTPUT_FOLDER = '/workspace/outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

jobs = {}

def run_seedvr2_processing(job_id, input_path, output_dir):
    """Run SeedVR2 using the wrapper script"""
    print(f"\\n🚀 Processing {job_id} with SeedVR2...")
    
    # Use the wrapper script
    cmd = ["python3", "/workspace/seedvr2_wrapper.py", input_path, output_dir]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Processing completed for {job_id}")
            # Find output file
            outputs = glob.glob(os.path.join(output_dir, "*.mp4"))
            if outputs:
                jobs[job_id]["status"] = "completed"
                jobs[job_id]["output_file"] = outputs[0]
            else:
                jobs[job_id]["status"] = "error"
                jobs[job_id]["error"] = "No output file generated"
        else:
            print(f"❌ Processing failed:\\n{result.stderr}")
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = result.stderr[:1000]
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
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
    return jsonify({
        "status": "online",
        "message": "SeedVR2 Server (Path Fixed)",
        "mode": "real"
    })

@app.route('/health', methods=['GET', 'OPTIONS'])
def health():
    if request.method == 'OPTIONS':
        return Response(status=200)
    return jsonify({
        "status": "healthy",
        "message": "Server running with path fixes",
        "mode": "real"
    })

@app.route('/upload', methods=['POST', 'OPTIONS'])
def upload():
    if request.method == 'OPTIONS':
        return Response(status=200)
    
    if 'video' not in request.files:
        return jsonify({"error": "No video file"}), 400
    
    file = request.files['video']
    job_id = str(uuid.uuid4())[:8]
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, f"{job_id}_{filename}")
    file.save(filepath)
    
    # Create output directory
    job_output_dir = os.path.join(OUTPUT_FOLDER, job_id)
    os.makedirs(job_output_dir, exist_ok=True)
    
    jobs[job_id] = {
        "status": "processing",
        "started": time.time(),
        "input_file": filepath
    }
    
    # Process in background
    thread = threading.Thread(
        target=run_seedvr2_processing,
        args=(job_id, filepath, job_output_dir)
    )
    thread.start()
    
    return jsonify({
        "status": "processing",
        "job_id": job_id,
        "message": "SeedVR2 processing started"
    })

@app.route('/status/<job_id>', methods=['GET', 'OPTIONS'])
def status(job_id):
    if request.method == 'OPTIONS':
        return Response(status=200)
    
    if job_id not in jobs:
        return jsonify({"error": "Job not found"}), 404
    
    job = jobs[job_id]
    
    if job["status"] == "completed":
        return jsonify({
            "status": "completed",
            "result_url": f"/download/{job_id}",
            "message": "Processing complete!"
        })
    elif job["status"] == "error":
        return jsonify({
            "status": "error",
            "error": job.get("error", "Processing failed"),
            "message": "SeedVR2 processing failed"
        })
    else:
        elapsed = time.time() - job["started"]
        progress = min(90, int(elapsed * 1.5))
        return jsonify({
            "status": "processing",
            "progress": progress,
            "message": f"Processing... {progress}%"
        })

@app.route('/download/<job_id>')
def download(job_id):
    if job_id in jobs and "output_file" in jobs[job_id]:
        output_file = jobs[job_id]["output_file"]
        if os.path.exists(output_file):
            return send_file(output_file, as_attachment=True, download_name=f"seedvr2_{job_id}.mp4")
    return jsonify({"error": "File not found"}), 404

@app.route('/process', methods=['POST', 'OPTIONS'])
def process_video():
    if request.method == 'OPTIONS':
        return Response(status=200)
    return jsonify({"status": "ready", "mode": "real"})

if __name__ == '__main__':
    print("\\n" + "="*60)
    print("🚀 SeedVR2 Server with PATH FIXES")
    print("="*60)
    print("✅ Using wrapper script to handle Python paths")
    print("📡 https://ussvh2i624ql0g-8080.proxy.runpod.net")
    print("="*60 + "\\n")
    
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)
'''

with open('/workspace/seedvr2_fixed_server.py', 'w') as f:
    f.write(server_code)
os.chmod('/workspace/seedvr2_fixed_server.py', 0o755)

print("\n✅ Created path-fixed server and wrapper")
print("\n🚀 To start the server:")
print("   python3 /workspace/seedvr2_fixed_server.py")
print("\nThis fixes the 'models' module not found error!")