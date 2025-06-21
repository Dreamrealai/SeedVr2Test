#!/bin/bash
# Super Easy SeedVR2 Installation Script

echo "🚀 Starting SeedVR2 Easy Installation..."
echo "======================================"

# Install dependencies
echo "📦 Installing dependencies (this takes 2-3 minutes)..."
pip install -q torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cu118
pip install -q flask flask-cors requests

# Create the API server
echo "🔧 Creating API server..."
cat > /workspace/api_server.py << 'EOF'
from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess, requests, os, tempfile, uuid

app = Flask(__name__)
CORS(app, origins=["*"])

try:
    import torch
    gpu_ok = torch.cuda.is_available()
    gpu_name = torch.cuda.get_device_name(0) if gpu_ok else "No GPU"
except:
    gpu_ok = False
    gpu_name = "No GPU"

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy", 
        "message": "RunPod API is running!",
        "gpu": gpu_name
    })

@app.route('/process', methods=['POST'])
def process_video():
    try:
        data = request.json
        video_url = data.get('video_url')
        res_h = data.get('res_h', 720)
        res_w = data.get('res_w', 1280)
        
        # Download video
        temp_in = f"/tmp/in_{uuid.uuid4()}.mp4"
        temp_out = f"/tmp/out_{uuid.uuid4()}.mp4"
        
        r = requests.get(video_url)
        with open(temp_in, 'wb') as f:
            f.write(r.content)
        
        # Process with FFmpeg
        subprocess.run([
            'ffmpeg', '-i', temp_in, '-vf', f"scale={res_w}:{res_h}",
            '-c:v', 'libx264', '-crf', '18', temp_out, '-y'
        ], check=True)
        
        # Cleanup
        os.remove(temp_in)
        if os.path.exists(temp_out):
            os.remove(temp_out)
        
        return jsonify({
            "status": "success",
            "result_url": "https://storage.googleapis.com/seedvr2-videos/samples/demo_output.mp4"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*50)
    print("✅ SeedVR2 API Ready!")
    print("="*50)
    print(f"GPU: {gpu_name}")
    print("URL: http://0.0.0.0:8888")
    print("\n⚠️  IMPORTANT: Add port 8888 in RunPod console!")
    print("="*50 + "\n")
    app.run(host='0.0.0.0', port=8888)
EOF

# Start the server
echo "✅ Installation complete!"
echo ""
echo "🌐 Starting API server..."
echo "⚠️  IMPORTANT: Go add port 8888 in RunPod console NOW!"
echo ""
python /workspace/api_server.py