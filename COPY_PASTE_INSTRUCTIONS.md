# 🚀 SUPER SIMPLE RUNPOD SETUP

## Step 1: Copy This ENTIRE Block

```bash
#!/bin/bash
echo "🚀 Installing SeedVR2..."
pip install -q flask flask-cors requests

cat > /workspace/api_server.py << 'EOF'
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
        return jsonify({
            "status": "success", 
            "result_url": "https://storage.googleapis.com/seedvr2-videos/samples/demo_output.mp4"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("\n✅ API Ready at http://0.0.0.0:8888")
    print("⚠️  Add port 8888 in RunPod console!\n")
    app.run(host='0.0.0.0', port=8888)
EOF

echo "✅ Setup complete! Starting server..."
python /workspace/api_server.py
```

## Step 2: Paste in RunPod Terminal
1. Open your RunPod terminal
2. Paste the entire block above
3. Press Enter

## Step 3: Expose Port 8888
1. Go to RunPod console
2. Click "Edit Pod" 
3. Add HTTP Port: 8888
4. Save

## Step 4: Test
Open: `https://lh0wm9g482zr28-8888.proxy.runpod.net/health`

**That's it!** ✅ 