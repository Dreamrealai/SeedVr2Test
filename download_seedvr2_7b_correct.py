#!/usr/bin/env python3
"""
Download the CORRECT SeedVR2-7B model from HuggingFace
"""

from huggingface_hub import snapshot_download
import os
import sys

print("="*60)
print("📥 Downloading SeedVR2-7B Model")
print("="*60)

# Create directories
save_dir = "/workspace/ckpts"
os.makedirs(save_dir, exist_ok=True)

# Download the 7B model (not 3B!)
repo_id = "ByteDance-Seed/SeedVR2-7B"  # 7B model
model_dir = os.path.join(save_dir, "SeedVR2-7B")

print(f"\n🎯 Downloading from: {repo_id}")
print(f"📁 Saving to: {model_dir}")
print("\nThis is the 7B parameter model - larger and better quality than 3B")
print("Note: This will take longer to download (~14GB+)\n")

try:
    # Clear any partial 3B downloads first
    if os.path.exists(os.path.join(save_dir, "SeedVR2-3B")):
        print("⚠️  Found 3B model, you wanted 7B. Keep both? (y/n): ", end="")
        # Auto-answer 'y' for script mode
        print("y")
    
    # Download 7B model
    snapshot_download(
        repo_id=repo_id,
        local_dir=model_dir,
        local_dir_use_symlinks=False,
        resume_download=True,
        ignore_patterns=["*.git*", ".gitattributes"]
    )
    
    print("\n✅ SeedVR2-7B model downloaded successfully!")
    print(f"📁 Location: {model_dir}")
    
    # List files
    print("\n📋 Downloaded files:")
    total_size = 0
    for root, dirs, files in os.walk(model_dir):
        for file in files:
            file_path = os.path.join(root, file)
            size = os.path.getsize(file_path) / (1024**3)  # GB
            total_size += size
            print(f"  - {file} ({size:.2f} GB)")
    
    print(f"\n💾 Total size: {total_size:.2f} GB")
    
except Exception as e:
    print(f"\n❌ Download failed: {e}")
    print("\nTroubleshooting:")
    print("1. Check disk space: df -h")
    print("2. Check internet connection")
    print("3. Try: huggingface-cli login")
    sys.exit(1)

print("\n" + "="*60)
print("✅ SeedVR2-7B Ready!")
print("="*60)
print("\nNote: 7B model can still run on single GPU for 720p")
print("but will use more memory than 3B model")
print("="*60)