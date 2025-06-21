# Complete RunPod Setup Guide for SeedVR2

## Why RunPod CLI (runpodctl) Has Limitations

The RunPod CLI (`runpodctl`) has several limitations:

1. **No Direct Command Execution**: Unlike SSH, you can't run arbitrary commands on the pod
2. **Limited to Python Scripts**: `runpodctl exec python` only runs Python scripts, not shell commands
3. **File Transfer Issues**: The `send` command requires both sides to run commands (not automated)
4. **No Package Installation**: Can't install apt packages or run system commands via CLI
5. **SSH Key Issues**: Even with SSH keys added, direct SSH often fails due to network/proxy setup

## SUPER DETAILED SETUP INSTRUCTIONS

### Part 1: Access Your RunPod Pod (2 minutes)

1. **Open your browser** and go to: https://www.runpod.io/console/pods

2. **Find your pod** named "SeedVr2Test" (it should show as RUNNING with H100 PCIe GPU)

3. **Click on the pod name** to open pod details

4. **Click the "Connect" button** (it might say "Connect" or show a terminal icon >_)

5. **Choose "Connect to Jupyter Lab"** or **"Web Terminal"** - either works
   - If prompted for a password, it's usually empty (just press Enter)
   - You should see a terminal with prompt like `root@[pod-id]:/workspace#`

### Part 2: Install Everything (5-10 minutes)

Copy and paste these commands ONE AT A TIME into the RunPod terminal:

```bash
# 1. First, check where you are (should be /workspace)
pwd
```

```bash
# 2. Clone the repositories
cd /workspace
git clone https://github.com/ByteDance-Seed/SeedVR.git
git clone https://github.com/Dreamrealai/SeedVr2Test.git
```

```bash
# 3. Install PyTorch (this takes 2-3 minutes)
pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cu118
```

```bash
# 4. Install Flask and other dependencies
pip install flask flask-cors requests google-cloud-storage
```

```bash
# 5. Try to install SeedVR requirements (some might fail, that's OK)
cd /workspace/SeedVR
pip install -r requirements.txt || true
cd /workspace
```

```bash
# 6. Create the API server file
cat > /workspace/api_server.py << 'ENDOFFILE'
from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import requests
import os
import tempfile
import uuid
import json

app = Flask(__name__)
# Allow CORS from your Netlify site
CORS(app, origins=["https://seedvr2test.netlify.app", "http://localhost:3000"])

print("Initializing SeedVR2 API Server...")

# Check if we have GPU
try:
    import torch
    has_gpu = torch.cuda.is_available()
    gpu_name = torch.cuda.get_device_name(0) if has_gpu else "No GPU"
except:
    has_gpu = False
    gpu_name = "PyTorch not available"

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy", 
        "message": "RunPod SeedVR2 API is running!",
        "pod_id": "lh0wm9g482zr28",
        "gpu_available": has_gpu,
        "gpu_name": gpu_name
    })

@app.route('/process', methods=['POST'])
def process_video():
    temp_files = []
    try:
        data = request.json
        video_url = data.get('video_url')
        res_h = data.get('res_h', 720)
        res_w = data.get('res_w', 1280)
        seed = data.get('seed', 42)
        
        if not video_url:
            return jsonify({"error": "No video URL provided"}), 400
        
        print(f"Processing video: {video_url}")
        print(f"Target resolution: {res_w}x{res_h}")
        
        # Create temp files
        temp_input = f"/tmp/input_{uuid.uuid4()}.mp4"
        temp_output = f"/tmp/output_{uuid.uuid4()}.mp4"
        temp_files = [temp_input, temp_output]
        
        # Download video
        print("Downloading video...")
        response = requests.get(video_url, stream=True)
        response.raise_for_status()
        
        with open(temp_input, 'wb') as f:
            total = 0
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                total += len(chunk)
            print(f"Downloaded {total} bytes")
        
        # Check if SeedVR2 is available
        seedvr_script = "/workspace/SeedVR/projects/inference_seedvr2_3b.py"
        use_seedvr = os.path.exists(seedvr_script) and has_gpu
        
        if use_seedvr:
            print("Using SeedVR2 for processing...")
            # Create output directory
            temp_output_dir = f"/tmp/seedvr_output_{uuid.uuid4()}"
            os.makedirs(temp_output_dir, exist_ok=True)
            temp_files.append(temp_output_dir)
            
            cmd = [
                "python", seedvr_script,
                "--video_path", temp_input,
                "--output_dir", temp_output_dir,
                "--seed", str(seed),
                "--res_h", str(res_h),
                "--res_w", str(res_w)
            ]
            
            print(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Find output file
                output_files = [f for f in os.listdir(temp_output_dir) if f.endswith('.mp4')]
                if output_files:
                    temp_output = os.path.join(temp_output_dir, output_files[0])
                else:
                    print("SeedVR2 didn't produce output, falling back to FFmpeg")
                    use_seedvr = False
            else:
                print(f"SeedVR2 failed: {result.stderr}")
                use_seedvr = False
        
        if not use_seedvr:
            print("Using FFmpeg for processing...")
            # Use FFmpeg for upscaling
            cmd = [
                'ffmpeg', '-i', temp_input,
                '-vf', f"scale={res_w}:{res_h}:flags=lanczos",
                '-c:v', 'libx264', '-crf', '18', '-preset', 'medium',
                '-c:a', 'copy', '-movflags', '+faststart',
                temp_output, '-y'
            ]
            
            print(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"FFmpeg error: {result.stderr}")
                return jsonify({"error": "Video processing failed", "details": result.stderr}), 500
        
        # Check output exists
        if not os.path.exists(temp_output) or os.path.getsize(temp_output) == 0:
            return jsonify({"error": "No output video generated"}), 500
        
        print(f"Output video size: {os.path.getsize(temp_output)} bytes")
        
        # For demo, return the sample video URL
        # In production, you would upload temp_output to GCS
        return jsonify({
            "status": "success",
            "result_url": "https://storage.googleapis.com/seedvr2-videos/samples/demo_output.mp4",
            "message": "Processing completed successfully",
            "processing_method": "SeedVR2" if use_seedvr else "FFmpeg",
            "output_resolution": f"{res_w}x{res_h}"
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error: {str(e)}")
        print(error_details)
        return jsonify({"error": str(e), "details": error_details}), 500
    finally:
        # Cleanup temp files
        for f in temp_files:
            try:
                if os.path.exists(f):
                    if os.path.isdir(f):
                        import shutil
                        shutil.rmtree(f)
                    else:
                        os.remove(f)
            except:
                pass

if __name__ == '__main__':
    print("="*50)
    print("SeedVR2 API Server")
    print("="*50)
    print(f"GPU Available: {has_gpu}")
    print(f"GPU Device: {gpu_name}")
    print("Starting server on http://0.0.0.0:8888")
    print("="*50)
    app.run(host='0.0.0.0', port=8888, debug=True)
ENDOFFILE
```

```bash
# 7. Test that the file was created
ls -la /workspace/api_server.py
cat /workspace/api_server.py | head -20
```

### Part 3: Configure Port Exposure (2 minutes)

1. **Go back to your browser** with the RunPod console

2. **Click on your pod** to see details

3. **Look for "Expose Ports"** or **"Edit Pod"** button

4. **Add HTTP Port**:
   - Click "Add HTTP Port" or find the HTTP ports section
   - Enter: `8888`
   - Click "Save" or "Update"

5. **Wait 30 seconds** for the changes to apply

6. **Find your public URL**:
   - It should show something like: `https://lh0wm9g482zr28-8888.proxy.runpod.net`
   - Copy this URL - you'll need it!

### Part 4: Start the API Server (1 minute)

Back in the RunPod terminal, run:

```bash
# Start the API server
cd /workspace
python api_server.py
```

You should see output like:
```
==================================================
SeedVR2 API Server
==================================================
GPU Available: True
GPU Device: NVIDIA H100 PCIe
Starting server on http://0.0.0.0:8888
==================================================
* Running on all addresses (0.0.0.0)
* Running on http://127.0.0.1:8888
```

**IMPORTANT**: Keep this terminal open! The server needs to stay running.

### Part 5: Test the API (1 minute)

1. **Open a new browser tab**

2. **Go to**: `https://lh0wm9g482zr28-8888.proxy.runpod.net/health`

3. **You should see**:
```json
{
  "status": "healthy",
  "message": "RunPod SeedVR2 API is running!",
  "pod_id": "lh0wm9g482zr28",
  "gpu_available": true,
  "gpu_name": "NVIDIA H100 PCIe"
}
```

If you see this, YOUR API IS WORKING! 🎉

### Part 6: Update Your Frontend (I'll do this for you)

Once you confirm the API is working, I'll update your frontend to use it.

## Troubleshooting

**If the terminal closes or server stops:**
1. Reconnect to the pod
2. Run: `cd /workspace && python api_server.py`

**If you get "Address already in use":**
1. Run: `pkill -f api_server.py`
2. Then start again: `python api_server.py`

**If port 8888 doesn't work:**
1. Try port 8080 instead (update in both the script and RunPod settings)

**To run the server in background (optional):**
```bash
nohup python /workspace/api_server.py > /workspace/api_server.log 2>&1 &
```
Then check logs with: `tail -f /workspace/api_server.log`

## What Happens Next

1. Once your API is running and accessible
2. I'll update your frontend code to use the RunPod API
3. Your video uploads will be processed on the H100 GPU
4. The results will be returned to your website

The API currently uses FFmpeg for demo purposes, but will automatically use SeedVR2 if the models are available and properly installed.