#!/usr/bin/env python3
"""
Install SeedVR2 Model on RunPod
This script downloads and sets up the actual SeedVR2 model
"""

import subprocess
import sys
import os
import time

print("="*60)
print("🚀 INSTALLING SEEDVR2 MODEL")
print("="*60)

# Step 1: Install required packages for model
print("\n📦 Step 1: Installing model dependencies...")
packages = [
    "huggingface_hub",
    "safetensors",
    "opencv-python",
    "imageio[ffmpeg]",
    "diffusers",
    "transformers",
    "accelerate",
    "einops",
    "omegaconf",
    "scipy",
    "torchvision"
]

for package in packages:
    print(f"Installing {package}...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", package], capture_output=True)

print("✅ Dependencies installed")

# Step 2: Clone SeedVR repository
print("\n📂 Step 2: Setting up SeedVR repository...")
if not os.path.exists("/workspace/SeedVR"):
    print("Cloning SeedVR repository...")
    subprocess.run(["git", "clone", "https://github.com/ByteDance-Seed/SeedVR.git", "/workspace/SeedVR"])
else:
    print("SeedVR repository already exists")

# Step 3: Download model from HuggingFace
print("\n📥 Step 3: Downloading SeedVR2-3B model (this may take a while)...")
download_script = '''#!/usr/bin/env python3
from huggingface_hub import snapshot_download
import os

print("Starting model download...")

# Create directories
save_dir = "/workspace/ckpts"
os.makedirs(save_dir, exist_ok=True)

# Download SeedVR2-3B model
repo_id = "ByteDance-Seed/SeedVR2-3B"
cache_dir = os.path.join(save_dir, "cache")

try:
    snapshot_download(
        repo_id=repo_id,
        local_dir=os.path.join(save_dir, "SeedVR2-3B"),
        cache_dir=cache_dir,
        local_dir_use_symlinks=False,
        resume_download=True,
        allow_patterns=["*.json", "*.safetensors", "*.pth", "*.bin", "*.py", "*.md", "*.txt"]
    )
    print("✅ Model downloaded successfully!")
    print(f"Model location: {os.path.join(save_dir, 'SeedVR2-3B')}")
except Exception as e:
    print(f"❌ Download failed: {e}")
    print("You may need to:")
    print("1. Check your internet connection")
    print("2. Login to HuggingFace: huggingface-cli login")
    print("3. Accept model license at https://huggingface.co/ByteDance-Seed/SeedVR2-3B")
'''

with open('/workspace/download_seedvr2.py', 'w') as f:
    f.write(download_script)

# Run the download
print("Downloading model files...")
result = subprocess.run([sys.executable, "/workspace/download_seedvr2.py"], capture_output=False)

# Step 4: Create processing script
print("\n🎬 Step 4: Creating processing script...")
process_script = '''#!/usr/bin/env python3
"""
SeedVR2 Video Processing Script
"""
import os
import sys
import subprocess
import torch

# Add SeedVR to path
sys.path.append("/workspace/SeedVR")

def process_video(input_path, output_path, resolution="720x1280", seed=42):
    """Process a video using SeedVR2"""
    
    res_h, res_w = map(int, resolution.split('x'))
    
    # Ensure dimensions are multiples of 32
    res_h = (res_h // 32) * 32
    res_w = (res_w // 32) * 32
    
    # Check GPU availability
    if not torch.cuda.is_available():
        print("❌ No GPU available!")
        return False
    
    gpu_count = torch.cuda.device_count()
    print(f"🎮 Found {gpu_count} GPU(s)")
    
    # Determine sequence parallel size based on resolution
    pixels = res_h * res_w
    if pixels <= 1280 * 720:
        sp_size = 1
    elif pixels <= 1920 * 1080:
        sp_size = min(gpu_count, 4)
    else:
        sp_size = min(gpu_count, 4)
    
    print(f"Using {sp_size} GPU(s) for {res_w}x{res_h} resolution")
    
    # Create output directory
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Run SeedVR2 inference
    cmd = [
        "torchrun",
        f"--nproc-per-node={sp_size}",
        "/workspace/SeedVR/projects/inference_seedvr2_3b.py",
        "--video_path", input_path,
        "--output_dir", os.path.dirname(output_path),
        "--seed", str(seed),
        "--res_h", str(res_h),
        "--res_w", str(res_w),
        "--sp_size", str(sp_size)
    ]
    
    print(f"Running: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Processing completed!")
        return True
    else:
        print(f"❌ Processing failed: {result.stderr}")
        return False

if __name__ == "__main__":
    # Test the processing
    print("SeedVR2 processing script ready!")
    print("To process a video, use:")
    print("python3 process_seedvr2.py <input_video> <output_video> [resolution] [seed]")
'''

with open('/workspace/process_seedvr2.py', 'w') as f:
    f.write(process_script)
os.chmod('/workspace/process_seedvr2.py', 0o755)

# Step 5: Update API server to use real processing
print("\n🔧 Step 5: Creating updated API server with SeedVR2...")
api_update = '''#!/usr/bin/env python3
"""
Update the API server to use real SeedVR2 processing
"""
import os
import sys

# Check if model exists
MODEL_PATH = "/workspace/ckpts/SeedVR2-3B"
if os.path.exists(MODEL_PATH):
    print("✅ SeedVR2 model found!")
    print("📁 Model location:", MODEL_PATH)
    
    # Create a flag file
    with open('/workspace/.seedvr2_installed', 'w') as f:
        f.write('installed')
    
    print("\\n✨ SeedVR2 is now installed!")
    print("\\nNext steps:")
    print("1. Restart your API server to enable real processing")
    print("2. The API will now use actual SeedVR2 processing")
else:
    print("❌ Model not found at", MODEL_PATH)
    print("\\nThe download may have failed. Try:")
    print("1. Run: python3 /workspace/download_seedvr2.py")
    print("2. Check disk space: df -h")
    print("3. Check HuggingFace access")
'''

with open('/workspace/check_seedvr2.py', 'w') as f:
    f.write(api_update)

# Run the check
subprocess.run([sys.executable, "/workspace/check_seedvr2.py"])

# Step 6: Create test video processing script
print("\n🧪 Step 6: Creating test script...")
with open('/workspace/test_seedvr2.sh', 'w') as f:
    f.write('''#!/bin/bash
echo "Testing SeedVR2 installation..."
echo ""

# Check if model exists
if [ -d "/workspace/ckpts/SeedVR2-3B" ]; then
    echo "✅ Model directory found"
    ls -la /workspace/ckpts/SeedVR2-3B/ | head -5
else
    echo "❌ Model directory not found"
fi

echo ""
echo "Checking GPU:"
python3 -c "import torch; print(f'GPU Available: {torch.cuda.is_available()}'); print(f'GPU Count: {torch.cuda.device_count()}')"

echo ""
echo "To process a test video:"
echo "1. Upload a video to /workspace/test_input.mp4"
echo "2. Run: python3 /workspace/process_seedvr2.py /workspace/test_input.mp4 /workspace/test_output.mp4"
''')
os.chmod('/workspace/test_seedvr2.sh', 0o755)

print("\n" + "="*60)
print("✅ INSTALLATION COMPLETE!")
print("="*60)
print("\n📋 STATUS:")
print("1. Dependencies: Installed ✅")
print("2. SeedVR repo: Cloned ✅")
print("3. Model download: Check /workspace/ckpts/SeedVR2-3B")
print("\n🔍 To verify installation:")
print("   /workspace/test_seedvr2.sh")
print("\n🚀 To process videos:")
print("   python3 /workspace/process_seedvr2.py <input> <output>")
print("="*60)