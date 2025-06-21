#!/usr/bin/env python3
"""
Test script to verify SeedVR2-7B is working correctly
"""

import os
import sys
import torch
import subprocess
import requests
from pathlib import Path

def check_environment():
    """Check if environment is properly set up"""
    print("🔍 Checking environment...")
    print(f"Python: {sys.version}")
    print(f"PyTorch: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"CUDA device: {torch.cuda.get_device_name(0)}")
        print(f"CUDA memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    
    return torch.cuda.is_available()

def check_model():
    """Check if model is downloaded"""
    model_path = "/models/seedvr2-7b"
    
    if os.path.exists(model_path):
        print(f"✅ Model directory exists: {model_path}")
        
        # Check for key model files
        important_files = ["seedvr2_ema_7b.pth", "ema_vae.pth", "config.json"]
        for file in important_files:
            file_path = os.path.join(model_path, file)
            if os.path.exists(file_path):
                size = os.path.getsize(file_path) / (1024**3)
                print(f"   ✅ {file}: {size:.2f} GB")
            else:
                print(f"   ❌ {file}: NOT FOUND")
                return False
        
        return True
    else:
        print(f"❌ Model directory not found: {model_path}")
        return False

def download_test_video():
    """Download a test video"""
    test_dir = "/tmp/seedvr2_test"
    os.makedirs(test_dir, exist_ok=True)
    
    # Download a small test video
    test_video_url = "https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4"
    test_video_path = f"{test_dir}/test_input.mp4"
    
    if not os.path.exists(test_video_path):
        print("📥 Downloading test video...")
        try:
            response = requests.get(test_video_url)
            with open(test_video_path, 'wb') as f:
                f.write(response.content)
            print(f"✅ Test video downloaded: {test_video_path}")
        except Exception as e:
            print(f"❌ Failed to download test video: {e}")
            return None
    else:
        print(f"✅ Test video already exists: {test_video_path}")
    
    return test_video_path

def run_inference_test(input_video):
    """Run a test inference"""
    output_dir = "/tmp/seedvr2_test/output"
    os.makedirs(output_dir, exist_ok=True)
    
    print("\n🚀 Running SeedVR2-7B inference test...")
    
    cmd = [
        "torchrun",
        "--nproc-per-node=1",
        "/app/SeedVR/projects/inference_seedvr2_7b.py",
        "--video_path", input_video,
        "--output_dir", output_dir,
        "--seed", "42",
        "--res_h", "720",
        "--res_w", "1280",
        "--sp_size", "1"
    ]
    
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Inference completed successfully!")
            
            # Check for output
            output_files = list(Path(output_dir).glob("*.mp4"))
            if output_files:
                print(f"✅ Output video created: {output_files[0]}")
                return True
            else:
                print("❌ No output video found")
                return False
        else:
            print(f"❌ Inference failed with error:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Failed to run inference: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 SeedVR2-7B Test Suite")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        print("\n❌ CUDA is not available. GPU is required for SeedVR2.")
        return 1
    
    # Check model
    if not check_model():
        print("\n❌ Model is not properly downloaded. Please run the setup script first.")
        return 1
    
    # Download test video
    test_video = download_test_video()
    if not test_video:
        print("\n❌ Failed to get test video.")
        return 1
    
    # Run inference test
    if run_inference_test(test_video):
        print("\n✅ All tests passed! SeedVR2-7B is ready to use.")
        return 0
    else:
        print("\n❌ Inference test failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())