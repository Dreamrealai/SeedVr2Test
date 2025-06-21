#!/usr/bin/env python3
"""
Install SeedVR2-7B Model on RunPod
This script downloads and sets up the SeedVR2-7B model from HuggingFace
"""

import subprocess
import sys
import os
import time

print("="*60)
print("🚀 INSTALLING SEEDVR2-7B MODEL")
print("="*60)

# Step 1: Install HuggingFace Hub and dependencies
print("\n📦 Step 1: Installing required packages...")
packages = [
    "huggingface_hub>=0.19.0",
    "safetensors",
    "opencv-python",
    "imageio[ffmpeg]",
    "diffusers",
    "transformers",
    "accelerate",
    "einops",
    "omegaconf",
    "scipy",
    "torchvision",
    "tqdm"
]

for package in packages:
    print(f"Installing {package}...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", package], capture_output=True)

print("✅ Dependencies installed")

# Step 2: Clone SeedVR repository if needed
print("\n📂 Step 2: Setting up SeedVR repository...")
if not os.path.exists("/workspace/SeedVR"):
    print("Cloning SeedVR repository...")
    subprocess.run(["git", "clone", "https://github.com/ByteDance-Seed/SeedVR.git", "/workspace/SeedVR"])
    print("✅ Repository cloned")
else:
    print("✅ SeedVR repository already exists")

# Step 3: Create model download script
print("\n📥 Step 3: Creating model download script...")
download_script = '''#!/usr/bin/env python3
"""Download SeedVR2-7B model from HuggingFace"""

from huggingface_hub import snapshot_download, hf_hub_download
import os
import sys

print("Starting SeedVR2-7B model download...")
print("Note: This is a large model and may take some time to download")

# Create directories
save_dir = "/workspace/ckpts"
model_dir = os.path.join(save_dir, "SeedVR2-7B")
os.makedirs(model_dir, exist_ok=True)

# Model repository
repo_id = "ByteDance-Seed/SeedVR2-7B"

try:
    # Method 1: Try snapshot download
    print(f"Downloading from {repo_id}...")
    
    snapshot_download(
        repo_id=repo_id,
        local_dir=model_dir,
        local_dir_use_symlinks=False,
        resume_download=True,
        ignore_patterns=["*.git*", "*.gitattributes"],
        max_workers=4
    )
    
    print("✅ Model downloaded successfully!")
    print(f"📁 Model location: {model_dir}")
    
    # List downloaded files
    print("\\nDownloaded files:")
    for root, dirs, files in os.walk(model_dir):
        for file in files[:10]:  # Show first 10 files
            print(f"  - {file}")
        if len(files) > 10:
            print(f"  ... and {len(files)-10} more files")
        break
    
except Exception as e:
    print(f"\\n❌ Download failed: {e}")
    print("\\nTroubleshooting:")
    print("1. Check your internet connection")
    print("2. Check disk space: df -h")
    print("3. Try logging in to HuggingFace:")
    print("   huggingface-cli login")
    print("4. Visit the model page:")
    print("   https://huggingface.co/ByteDance-Seed/SeedVR2-7B")
    sys.exit(1)
'''

with open('/workspace/download_seedvr2_7b.py', 'w') as f:
    f.write(download_script)
os.chmod('/workspace/download_seedvr2_7b.py', 0o755)

# Run the download
print("Downloading SeedVR2-7B model...")
print("⚠️  This is a large model (several GB) and may take a while...")
result = subprocess.run([sys.executable, "/workspace/download_seedvr2_7b.py"])

if result.returncode != 0:
    print("\n❌ Model download failed. See error messages above.")
    print("You can retry by running: python3 /workspace/download_seedvr2_7b.py")
    sys.exit(1)

# Step 4: Create processing script for 7B model
print("\n🎬 Step 4: Creating 7B model processing script...")
process_script = '''#!/usr/bin/env python3
"""
SeedVR2-7B Video Processing Script
Optimized for the 7B parameter model
"""
import os
import sys
import subprocess
import torch

# Add SeedVR to path
sys.path.append("/workspace/SeedVR")

def process_video_7b(input_path, output_path, resolution="1080x1920", seed=42):
    """Process a video using SeedVR2-7B model"""
    
    res_h, res_w = map(int, resolution.split('x'))
    
    # Ensure dimensions are multiples of 32
    res_h = (res_h // 32) * 32
    res_w = (res_w // 32) * 32
    
    # Check GPU availability
    if not torch.cuda.is_available():
        print("❌ No GPU available!")
        return False
    
    gpu_count = torch.cuda.device_count()
    gpu_name = torch.cuda.get_device_name(0)
    gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
    
    print(f"🎮 GPU Info:")
    print(f"  - Device: {gpu_name}")
    print(f"  - Count: {gpu_count}")
    print(f"  - Memory: {gpu_memory:.1f} GB")
    
    # 7B model requires more GPUs for higher resolutions
    pixels = res_h * res_w
    if pixels <= 1280 * 720:
        sp_size = min(gpu_count, 2)  # 2 GPUs for 720p
    elif pixels <= 1920 * 1080:
        sp_size = min(gpu_count, 4)  # 4 GPUs for 1080p
    else:
        sp_size = gpu_count  # All GPUs for 2K+
    
    print(f"Using {sp_size} GPU(s) for {res_w}x{res_h} resolution")
    
    # Create output directory
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Run SeedVR2-7B inference
    cmd = [
        "torchrun",
        f"--nproc-per-node={sp_size}",
        "/workspace/SeedVR/projects/inference_seedvr2_7b.py",
        "--video_path", input_path,
        "--output_dir", os.path.dirname(output_path),
        "--seed", str(seed),
        "--res_h", str(res_h),
        "--res_w", str(res_w),
        "--sp_size", str(sp_size),
        "--ckpt_path", "/workspace/ckpts/SeedVR2-7B"
    ]
    
    print(f"\\nRunning command:")
    print(' '.join(cmd))
    
    # Set environment for better GPU utilization
    env = os.environ.copy()
    env['CUDA_VISIBLE_DEVICES'] = ','.join(str(i) for i in range(sp_size))
    
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    
    if result.returncode == 0:
        print("✅ Processing completed!")
        return True
    else:
        print(f"❌ Processing failed:")
        print(result.stderr)
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 process_seedvr2_7b.py <input_video> <output_video> [resolution] [seed]")
        print("Example: python3 process_seedvr2_7b.py input.mp4 output.mp4 1080x1920 42")
        sys.exit(1)
    
    input_video = sys.argv[1]
    output_video = sys.argv[2]
    resolution = sys.argv[3] if len(sys.argv) > 3 else "1080x1920"
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 42
    
    if not os.path.exists(input_video):
        print(f"❌ Input video not found: {input_video}")
        sys.exit(1)
    
    print(f"Processing {input_video} -> {output_video}")
    print(f"Resolution: {resolution}, Seed: {seed}")
    
    if process_video_7b(input_video, output_video, resolution, seed):
        print(f"\\n✅ Output saved to: {output_video}")
    else:
        print("\\n❌ Processing failed")
        sys.exit(1)
'''

with open('/workspace/process_seedvr2_7b.py', 'w') as f:
    f.write(process_script)
os.chmod('/workspace/process_seedvr2_7b.py', 0o755)

# Step 5: Create verification script
print("\n🧪 Step 5: Creating verification script...")
verify_script = '''#!/bin/bash
echo "="*60
echo "SeedVR2-7B Installation Verification"
echo "="*60
echo ""

# Check model files
echo "📁 Checking model files..."
if [ -d "/workspace/ckpts/SeedVR2-7B" ]; then
    echo "✅ Model directory found"
    echo "Files in model directory:"
    ls -lah /workspace/ckpts/SeedVR2-7B/ | head -10
    echo ""
    # Check total size
    echo "Total model size:"
    du -sh /workspace/ckpts/SeedVR2-7B/
else
    echo "❌ Model directory not found at /workspace/ckpts/SeedVR2-7B"
fi

echo ""
echo "🎮 GPU Information:"
python3 -c "
import torch
if torch.cuda.is_available():
    print(f'✅ CUDA Available')
    print(f'GPU Count: {torch.cuda.device_count()}')
    for i in range(torch.cuda.device_count()):
        print(f'GPU {i}: {torch.cuda.get_device_name(i)}')
        print(f'  Memory: {torch.cuda.get_device_properties(i).total_memory / 1e9:.1f} GB')
else:
    print('❌ No GPU detected')
"

echo ""
echo "📊 Disk Space:"
df -h /workspace

echo ""
echo "🔧 SeedVR Repository:"
if [ -d "/workspace/SeedVR" ]; then
    echo "✅ SeedVR repository found"
    if [ -f "/workspace/SeedVR/projects/inference_seedvr2_7b.py" ]; then
        echo "✅ 7B inference script found"
    else
        echo "❌ 7B inference script not found"
    fi
else
    echo "❌ SeedVR repository not found"
fi

echo ""
echo "="*60
echo "To test the 7B model:"
echo "1. Upload a test video to /workspace/test_input.mp4"
echo "2. Run: python3 /workspace/process_seedvr2_7b.py /workspace/test_input.mp4 /workspace/test_output.mp4"
echo "="*60
'''

with open('/workspace/verify_seedvr2_7b.sh', 'w') as f:
    f.write(verify_script)
os.chmod('/workspace/verify_seedvr2_7b.sh', 0o755)

# Step 6: Check installation
print("\n✅ Running verification...")
subprocess.run(["/workspace/verify_seedvr2_7b.sh"])

print("\n" + "="*60)
print("✅ SEEDVR2-7B INSTALLATION COMPLETE!")
print("="*60)
print("\n📋 Next Steps:")
print("1. Verify installation: /workspace/verify_seedvr2_7b.sh")
print("2. Process a video: python3 /workspace/process_seedvr2_7b.py <input> <output>")
print("3. Restart API server to enable 7B model processing")
print("\n⚠️  Note: 7B model requires more GPU memory than 3B")
print("Recommended: 2-4 H100 GPUs for optimal performance")
print("="*60)