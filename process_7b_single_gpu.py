#!/usr/bin/env python3
"""
Process videos with SeedVR2-7B on SINGLE GPU
7B model provides better quality than 3B
"""

import os
import sys
import subprocess
import torch

sys.path.append("/workspace/SeedVR")

def process_video_7b_single(input_path, output_path, resolution="720x1280", seed=42):
    """Process video using 7B model on single GPU"""
    
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
    print("📊 Using 7B model for better quality")
    
    # 7B model needs more memory - limit to 720p on single GPU
    if res_h * res_w > 1280 * 720:
        print(f"⚠️  {res_w}x{res_h} too large for 7B model on single GPU")
        print("📏 Limiting to 720p (1280x720)")
        res_w, res_h = 1280, 720
    
    # Create output directory
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Use the 7B inference script
    cmd = [
        "python3",  # Single GPU, no torchrun needed
        "/workspace/SeedVR/projects/inference_seedvr2_7b.py",  # 7B script
        "--video_path", input_path,
        "--output_dir", os.path.dirname(output_path),
        "--seed", str(seed),
        "--res_h", str(res_h),
        "--res_w", str(res_w),
        "--sp_size", "1",  # Single GPU
        "--ckpt_path", "/workspace/ckpts/SeedVR2-7B"  # 7B model path
    ]
    
    print(f"\n🚀 Running 7B model on single GPU:")
    print(' '.join(cmd))
    
    # Set single GPU
    env = os.environ.copy()
    env['CUDA_VISIBLE_DEVICES'] = '0'
    
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    
    if result.returncode == 0:
        print("✅ Processing completed with 7B model!")
        
        # Find output file
        import glob
        output_files = glob.glob(os.path.join(os.path.dirname(output_path), "*.mp4"))
        if output_files:
            # Rename to desired output
            os.rename(output_files[0], output_path)
            return True
    else:
        print(f"❌ Error: {result.stderr}")
        
        # If OOM, suggest using 3B model
        if "out of memory" in result.stderr.lower():
            print("\n💡 Suggestion: 7B model ran out of memory")
            print("   Try: 1) Lower resolution, or")
            print("        2) Use 3B model instead")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 process_7b_single_gpu.py <input> <output> [resolution] [seed]")
        print("\nExample: python3 process_7b_single_gpu.py input.mp4 output.mp4 720x1280")
        print("\n📊 7B vs 3B models:")
        print("  • 7B: Better quality, more memory needed")
        print("  • 3B: Faster, less memory, still good quality")
        print("\n⚠️  Single GPU limit: 720p (1280x720)")
        sys.exit(1)
    
    input_video = sys.argv[1]
    output_video = sys.argv[2]
    resolution = sys.argv[3] if len(sys.argv) > 3 else "720x1280"
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 42
    
    print(f"🎬 Processing with 7B model: {input_video}")
    print(f"📐 Resolution: {resolution}")
    print(f"🎲 Seed: {seed}")
    
    if not os.path.exists(input_video):
        print(f"❌ Input not found: {input_video}")
        sys.exit(1)
    
    if process_video_7b_single(input_video, output_video, resolution, seed):
        print(f"\n✅ Output saved: {output_video}")
    else:
        print("\n❌ Processing failed")
        print("💡 Try using 3B model if 7B runs out of memory")
        sys.exit(1)