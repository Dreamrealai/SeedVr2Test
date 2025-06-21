# RunPod Setup Troubleshooting Guide

## Common Issues and Solutions

### 1. "Cannot uninstall 'blinker'" Error
**Problem**: System packages installed via distutils can't be uninstalled
**Solution**: 
```bash
python3 -m pip install --ignore-installed flask flask-cors
```

### 2. Flask Import Errors
**Problem**: Flask not properly installed or Python path issues
**Solutions**:
```bash
# Option 1: Force reinstall
python3 -m pip install --force-reinstall flask flask-cors

# Option 2: Install in user space
python3 -m pip install --user flask flask-cors

# Option 3: Use system package manager
apt-get update && apt-get install -y python3-flask
```

### 3. Port 8080 Already in Use
**Problem**: Previous server still running
**Solutions**:
```bash
# Find and kill process
lsof -ti:8080 | xargs kill -9

# Or use pkill
pkill -f "python.*8080"
```

### 4. CORS Errors in Browser
**Problem**: Frontend can't connect to backend
**Checklist**:
- ✅ Port 8080 is exposed in RunPod console
- ✅ API server is running
- ✅ Frontend uses correct URL format: `https://[POD-ID]-8080.proxy.runpod.net`

### 5. Server Won't Start
**Quick Debug Commands**:
```bash
# Test Python environment
python3 -c "import flask; print('Flask OK')"

# Test server file
python3 /workspace/api_server.py

# Check for syntax errors
python3 -m py_compile /workspace/api_server.py
```

## Step-by-Step Setup Process

### 1. Download and Run Setup Script
```bash
wget https://raw.githubusercontent.com/Dreamrealai/SeedVr2Test/main/runpod_simple_setup.py
python3 runpod_simple_setup.py
```

### 2. Verify Installation
```bash
python3 /workspace/verify_setup.py
```

### 3. Start the Server
```bash
# Method 1 (Recommended)
python3 /workspace/api_server.py

# Method 2
cd /workspace && python3 -m flask run --host=0.0.0.0 --port=8080

# Method 3
/workspace/start_api.sh
```

### 4. Test the API
```bash
# From RunPod terminal
curl http://localhost:8080/health

# From browser
https://[YOUR-POD-ID]-8080.proxy.runpod.net/health
```

## Frontend Configuration

Your `script.js` should have:
```javascript
const API_BASE_URL = 'https://[YOUR-POD-ID]-8080.proxy.runpod.net';
```

Current setting in your script.js:
```javascript
const API_BASE_URL = 'https://lh0wm9g482zr28-8080.proxy.runpod.net';
```

This looks correct! ✅

## Manual Installation (If Scripts Fail)

```bash
# 1. Install packages
python3 -m pip install flask==2.3.2 flask-cors==4.0.0 requests==2.31.0

# 2. Create server file
cat > /workspace/api_server.py << 'EOF'
[Paste the API server code from the setup script]
EOF

# 3. Run server
python3 /workspace/api_server.py
```

## Verification Checklist

- [ ] Flask is installed: `python3 -c "import flask"`
- [ ] Port 8080 is free: `lsof -i:8080`
- [ ] API server file exists: `ls -la /workspace/api_server.py`
- [ ] Port 8080 is exposed in RunPod console
- [ ] Frontend URL matches RunPod proxy URL

## Emergency Fallback

If nothing works, use this minimal server:
```python
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "healthy"}).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.end_headers()

HTTPServer(('0.0.0.0', 8080), Handler).serve_forever()
```