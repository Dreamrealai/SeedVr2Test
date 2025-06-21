#!/usr/bin/env python3
"""
Download SeedVR2 model weights from Hugging Face.
"""

import os
import sys
import argparse
from huggingface_hub import snapshot_download

def download_model(model_size="3b"):
    """Download SeedVR2 model weights."""
    
    # Model mapping
    model_repos = {
        "3b": "ByteDance-Seed/SeedVR2-3B",
        "7b": "ByteDance-Seed/SeedVR2-7B"
    }
    
    if model_size not in model_repos:
        print(f"Invalid model size: {model_size}. Choose from: {list(model_repos.keys())}")
        sys.exit(1)
    
    repo_id = model_repos[model_size]
    save_dir = f"/models/seedvr2-{model_size}"
    cache_dir = save_dir + "/cache"
    
    print(f"Downloading {repo_id} to {save_dir}...")
    
    # Create directory if it doesn't exist
    os.makedirs(save_dir, exist_ok=True)
    
    try:
        snapshot_download(
            cache_dir=cache_dir,
            local_dir=save_dir,
            repo_id=repo_id,
            local_dir_use_symlinks=False,
            resume_download=True,
            allow_patterns=["*.json", "*.safetensors", "*.pth", "*.bin", "*.py", "*.md", "*.txt"],
        )
        
        print(f"Model downloaded successfully to {save_dir}")
        
        # Copy required embeddings to the main directory
        import shutil
        seedvr_dir = "/app/SeedVR"
        
        # Check if embeddings exist in the model directory
        pos_emb_path = os.path.join(save_dir, "pos_emb.pt")
        neg_emb_path = os.path.join(save_dir, "neg_emb.pt")
        
        if os.path.exists(pos_emb_path) and os.path.exists(neg_emb_path):
            print("Copying embeddings to SeedVR directory...")
            shutil.copy(pos_emb_path, os.path.join(seedvr_dir, "pos_emb.pt"))
            shutil.copy(neg_emb_path, os.path.join(seedvr_dir, "neg_emb.pt"))
        else:
            print("Embeddings not found in model directory, they should be in the SeedVR repo")
        
        # List downloaded files
        print("\nDownloaded files:")
        for root, dirs, files in os.walk(save_dir):
            level = root.replace(save_dir, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files[:10]:  # Show first 10 files
                print(f"{subindent}{file}")
            if len(files) > 10:
                print(f"{subindent}... and {len(files) - 10} more files")
        
    except Exception as e:
        print(f"Error downloading model: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Download SeedVR2 model weights")
    parser.add_argument(
        "--model-size",
        default="3b",
        choices=["3b", "7b"],
        help="Model size to download (3b or 7b)"
    )
    
    args = parser.parse_args()
    download_model(args.model_size)

if __name__ == "__main__":
    main()
