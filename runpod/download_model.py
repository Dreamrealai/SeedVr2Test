#!/usr/bin/env python3
"""
Download SeedVR2-3B model from Hugging Face
"""

import os
from huggingface_hub import snapshot_download

def download_seedvr2_model():
    """Download SeedVR2-3B model weights"""
    
    save_dir = "/models/seedvr2-3b"
    repo_id = "ByteDance-Seed/SeedVR2-3B"
    cache_dir = save_dir + "/cache"
    
    print(f"Downloading {repo_id} to {save_dir}")
    
    # Create directory if it doesn't exist
    os.makedirs(save_dir, exist_ok=True)
    
    # Download model files
    snapshot_download(
        cache_dir=cache_dir,
        local_dir=save_dir,
        repo_id=repo_id,
        local_dir_use_symlinks=False,
        resume_download=True,
        allow_patterns=["*.json", "*.safetensors", "*.pth", "*.bin", "*.py", "*.md", "*.txt"]
    )
    
    print(f"Model downloaded successfully to {save_dir}")
    
    # List downloaded files
    for root, dirs, files in os.walk(save_dir):
        level = root.replace(save_dir, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files[:10]:  # Show first 10 files
            print(f"{subindent}{file}")
        if len(files) > 10:
            print(f"{subindent}... and {len(files) - 10} more files")

if __name__ == "__main__":
    download_seedvr2_model()