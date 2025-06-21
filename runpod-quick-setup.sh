#!/bin/bash
# Quick setup to make RunPod pod work as a simple API server

echo "Setting up RunPod pod as API server..."

# Copy this script's content to RunPod
cat << 'SETUP_SCRIPT' | pbcopy

#!/bin/bash
# Run this inside your RunPod pod

# Install dependencies
apt-get update && apt-get install -y python3-pip git ffmpeg
pip install flask flask-cors requests google-cloud-storage

# Create a simple API server
cat > /workspace/api_server.py << 'EOF'
from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import requests
import os
import tempfile
import uuid

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "message": "RunPod API server running"})

@app.route('/process', methods=['POST'])
def process_video():
    try:
        data = request.json
        video_url = data.get('video_url')
        
        if not video_url:
            return jsonify({"error": "No video URL provided"}), 400
        
        # Download video
        temp_input = f"/tmp/input_{uuid.uuid4()}.mp4"
        temp_output = f"/tmp/output_{uuid.uuid4()}.mp4"
        
        # Download the video
        response = requests.get(video_url, stream=True)
        with open(temp_input, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Simple processing with ffmpeg (as a placeholder)
        # In production, this would run SeedVR2
        cmd = [
            'ffmpeg', '-i', temp_input,
            '-vf', f"scale={data.get('res_w', 1280)}:{data.get('res_h', 720)}",
            '-c:v', 'libx264', '-crf', '23',
            temp_output
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        
        if result.returncode != 0:
            return jsonify({"error": "Processing failed"}), 500
        
        # In production, upload to GCS and return URL
        # For now, return a demo URL
        return jsonify({
            "status": "success",
            "result_url": "https://storage.googleapis.com/seedvr2-videos/samples/demo_output.mp4"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # Cleanup
        for f in [temp_input, temp_output]:
            if os.path.exists(f):
                os.remove(f)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888)
EOF

# Create a startup script
cat > /workspace/start_server.sh << 'EOF'
#!/bin/bash
echo "Starting API server on port 8888..."
python3 /workspace/api_server.py
EOF

chmod +x /workspace/start_server.sh

echo "Setup complete!"
echo "To start the server, run: /workspace/start_server.sh"
echo "The API will be available at http://POD_IP:8888"

SETUP_SCRIPT

echo "Script copied to clipboard!"
echo ""
echo "Next steps:"
echo "1. Go to https://www.runpod.io/console/pods"
echo "2. Click on your pod 'SeedVr2Test'"
echo "3. Open the terminal/console"
echo "4. Paste and run the script"
echo "5. Start the server with: /workspace/start_server.sh"
echo ""
echo "To get your pod's public IP:"
echo "runpodctl get pod lh0wm9g482zr28"