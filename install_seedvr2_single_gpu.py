#!/usr/bin/env python3
"""
Install SeedVR2 for SINGLE GPU Setup
Optimized for single H100 GPU operation
"""

import subprocess
import sys
import os

print("="*60)
print("🚀 INSTALLING SEEDVR2 FOR SINGLE GPU")
print("="*60)

# Step 1: Install dependencies
print("\n📦 Installing required packages...")
packages = [
    "huggingface_hub>=0.19.0",
    "safetensors",
    "opencv-python",
    "imageio[ffmpeg]",
    "diffusers",
    "transformers",
    "accelerate",
    "einops",
    "omegaconf"
]

for package in packages:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", package], capture_output=True)
print("✅ Dependencies installed")

# Step 2: Clone SeedVR repo
print("\n📂 Setting up SeedVR repository...")
if not os.path.exists("/workspace/SeedVR"):
    subprocess.run(["git", "clone", "https://github.com/ByteDance-Seed/SeedVR.git", "/workspace/SeedVR"])
print("✅ Repository ready")

# Step 3: Download model (3B is better for single GPU)
print("\n📥 Creating model download script...")
download_script = '''#!/usr/bin/env python3
from huggingface_hub import snapshot_download
import os

print("Downloading SeedVR2-3B model (optimized for single GPU)...")

save_dir = "/workspace/ckpts"
os.makedirs(save_dir, exist_ok=True)

# 3B model is more suitable for single GPU
repo_id = "ByteDance-Seed/SeedVR2-3B"

try:
    snapshot_download(
        repo_id=repo_id,
        local_dir=os.path.join(save_dir, "SeedVR2-3B"),
        resume_download=True,
        ignore_patterns=["*.git*"]
    )
    print("✅ Model downloaded!")
except Exception as e:
    print(f"❌ Download failed: {e}")
    print("Try: huggingface-cli login")
'''

with open('/workspace/download_model.py', 'w') as f:
    f.write(download_script)

print("Downloading model...")
subprocess.run([sys.executable, "/workspace/download_model.py"])

# Step 4: Create SINGLE GPU processing script
print("\n🎬 Creating single GPU processing script...")
process_script = '''#!/usr/bin/env python3
"""
SeedVR2 Single GPU Processing
Optimized for 1x H100-80G
"""
import os
import sys
import subprocess
import torch

sys.path.append("/workspace/SeedVR")

def process_video_single_gpu(input_path, output_path, resolution="720x1280", seed=42):
    """Process video using SINGLE GPU"""
    
    res_h, res_w = map(int, resolution.split('x'))
    
    # Ensure multiples of 32
    res_h = (res_h // 32) * 32
    res_w = (res_w // 32) * 32
    
    # Check GPU
    if not torch.cuda.is_available():
        print("❌ No GPU available!")
        return False
    
    gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
    print(f"🎮 GPU: {torch.cuda.get_device_name(0)} ({gpu_memory:.1f} GB)")
    
    # Single GPU can handle up to 720p
    if res_h * res_w > 1280 * 720:
        print(f"⚠️  Resolution {res_w}x{res_h} may be too large for single GPU")
        print("📏 Recommended max: 1280x720 for single H100")
    
    # Create output directory
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Run with SINGLE GPU (sp_size=1)
    cmd = [
        "python3",  # Use python3 directly for single GPU
        "/workspace/SeedVR/projects/inference_seedvr2_3b.py",
        "--video_path", input_path,
        "--output_dir", os.path.dirname(output_path),
        "--seed", str(seed),
        "--res_h", str(res_h),
        "--res_w", str(res_w),
        "--sp_size", "1"  # SINGLE GPU!
    ]
    
    print(f"\\n🚀 Running on SINGLE GPU:")
    print(' '.join(cmd))
    
    # Set single GPU
    env = os.environ.copy()
    env['CUDA_VISIBLE_DEVICES'] = '0'
    
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    
    if result.returncode == 0:
        print("✅ Processing completed!")
        return True
    else:
        print(f"❌ Error: {result.stderr}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 process_single_gpu.py <input> <output> [resolution] [seed]")
        print("Example: python3 process_single_gpu.py input.mp4 output.mp4 720x1280")
        print("\\n⚠️  Single H100 supports up to 720p (1280x720)")
        sys.exit(1)
    
    input_video = sys.argv[1]
    output_video = sys.argv[2]
    resolution = sys.argv[3] if len(sys.argv) > 3 else "720x1280"
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 42
    
    print(f"🎬 Processing {input_video}")
    print(f"📐 Resolution: {resolution}")
    print(f"🎲 Seed: {seed}")
    
    if process_video_single_gpu(input_video, output_video, resolution, seed):
        print(f"\\n✅ Output: {output_video}")
    else:
        sys.exit(1)
'''

with open('/workspace/process_single_gpu.py', 'w') as f:
    f.write(process_script)
os.chmod('/workspace/process_single_gpu.py', 0o755)

# Step 5: Create memory-efficient API server update
print("\n🌐 Creating optimized API server...")
api_update = '''#!/usr/bin/env python3
"""Add this to your API server for single GPU processing"""

# In your process endpoint, use:
def process_with_seedvr2(video_path, res_h=720, res_w=1280, seed=42):
    """Process video with single GPU"""
    
    # Single GPU limit: 720p
    if res_h * res_w > 1280 * 720:
        res_h, res_w = 720, 1280
        print(f"📏 Resized to {res_w}x{res_h} for single GPU")
    
    output_path = f"/workspace/outputs/{uuid.uuid4()}.mp4"
    
    cmd = [
        "python3",
        "/workspace/process_single_gpu.py",
        video_path,
        output_path,
        f"{res_h}x{res_w}",
        str(seed)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0 and os.path.exists(output_path):
        return output_path
    else:
        return None
'''

with open('/workspace/api_seedvr2_update.py', 'w') as f:
    f.write(api_update)

# Step 6: Verification
print("\n🧪 Creating verification script...")
verify_script = '''#!/bin/bash
echo "="*50
echo "SINGLE GPU SeedVR2 Setup Verification"
echo "="*50

echo "\\n🎮 GPU Check:"
python3 -c "
import torch
if torch.cuda.is_available():
    gpu = torch.cuda.get_device_properties(0)
    print(f'✅ GPU: {torch.cuda.get_device_name(0)}')
    print(f'💾 Memory: {gpu.total_memory / 1e9:.1f} GB')
    print(f'🔧 Capability: {gpu.major}.{gpu.minor}')
    
    # Check if it's H100
    if 'H100' in torch.cuda.get_device_name(0):
        print('✅ H100 detected - Perfect for 720p videos!')
    else:
        print('⚠️  Not H100, but should still work')
else:
    print('❌ No GPU found')
"

echo "\\n📁 Model Check:"
if [ -d "/workspace/ckpts/SeedVR2-3B" ]; then
    echo "✅ SeedVR2-3B model found (optimized for single GPU)"
    du -sh /workspace/ckpts/SeedVR2-3B
else
    echo "❌ Model not found"
fi

echo "\\n📊 Supported Resolutions (Single H100):"
echo "✅ 640x480   (SD)"
echo "✅ 1280x720  (HD/720p) - RECOMMENDED"
echo "⚠️  1920x1080 (FHD) - May exceed memory"
echo "❌ 2560x1440 (2K) - Requires multi-GPU"

echo "\\n🚀 Ready to process!"
echo "Run: python3 /workspace/process_single_gpu.py input.mp4 output.mp4"
'''

with open('/workspace/verify_single_gpu.sh', 'w') as f:
    f.write(verify_script)
os.chmod('/workspace/verify_single_gpu.sh', 0o755)

print("\n" + "="*60)
print("✅ SINGLE GPU SETUP COMPLETE!")
print("="*60)
print("\n📋 Key Points:")
print("• Single H100-80G supports up to 720p (1280x720)")
print("• Using SeedVR2-3B model (optimized for single GPU)")
print("• No need for torchrun or multi-GPU setup")
print("\n🚀 To process a video:")
print("   python3 /workspace/process_single_gpu.py input.mp4 output.mp4")
print("\n🔍 To verify:")
print("   /workspace/verify_single_gpu.sh")
print("="*60)