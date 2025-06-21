import runpod
import os
import subprocess
import torch
import logging
from typing import Dict, Any
import requests
import tempfile
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Model paths
MODEL_PATH = "/models/seedvr2-7b"
INFERENCE_SCRIPT = "/app/SeedVR/projects/inference_seedvr2_7b.py"

def download_video(url: str, output_path: str) -> str:
    """Download video from URL"""
    logger.info(f"Downloading video from {url}")
    
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    logger.info(f"Downloaded video to {output_path}")
    return output_path

def upload_to_s3(file_path: str) -> str:
    """Upload result to S3 and return URL"""
    # This would use boto3 to upload to S3
    # For now, returning a placeholder
    logger.info(f"Uploading {file_path} to S3")
    
    # TODO: Implement S3 upload
    # import boto3
    # s3 = boto3.client('s3')
    # bucket_name = os.getenv('S3_BUCKET')
    # key = f"results/{Path(file_path).name}"
    # s3.upload_file(file_path, bucket_name, key)
    # return f"https://{bucket_name}.s3.amazonaws.com/{key}"
    
    return f"https://placeholder.com/result/{Path(file_path).name}"

def validate_dimensions(height: int, width: int) -> tuple[int, int]:
    """Ensure dimensions are multiples of 32"""
    height = (height // 32) * 32
    width = (width // 32) * 32
    return height, width

def run_seedvr2(input_video: str, output_dir: str, params: Dict[str, Any]) -> str:
    """Run SeedVR2 inference"""
    logger.info(f"Running SeedVR2 with params: {params}")
    
    # Validate and adjust dimensions
    res_h, res_w = validate_dimensions(
        params.get('res_h', 720),
        params.get('res_w', 1280)
    )
    
    # Determine GPU count based on resolution
    if res_h > 720 or res_w > 1280:
        sp_size = 4  # Use 4 GPUs for 1080p and 2K
    else:
        sp_size = 1  # Use 1 GPU for 720p and below
    
    # Prepare command
    cmd = [
        "torchrun",
        f"--nproc-per-node={sp_size}",
        INFERENCE_SCRIPT,
        "--video_path", input_video,
        "--output_dir", output_dir,
        "--seed", str(params.get('seed', 42)),
        "--res_h", str(res_h),
        "--res_w", str(res_w),
        "--sp_size", str(sp_size)
    ]
    
    # Run inference
    logger.info(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise RuntimeError(f"SeedVR2 inference failed: {result.stderr}")
    
    # Find output video
    output_files = list(Path(output_dir).glob("*.mp4"))
    if not output_files:
        raise RuntimeError("No output video found")
    
    return str(output_files[0])

def handler(job):
    """RunPod handler function"""
    logger.info(f"Starting job: {job}")
    
    try:
        job_input = job["input"]
        
        # Create temporary directories
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = os.path.join(temp_dir, "input.mp4")
            output_dir = os.path.join(temp_dir, "output")
            os.makedirs(output_dir, exist_ok=True)
            
            # Download input video
            download_video(job_input["video_url"], input_path)
            
            # Run SeedVR2
            output_path = run_seedvr2(input_path, output_dir, job_input)
            
            # Upload result
            result_url = upload_to_s3(output_path)
            
            return {
                "status": "success",
                "result_url": result_url,
                "message": "Video restoration completed successfully"
            }
            
    except Exception as e:
        logger.error(f"Job failed: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

# RunPod serverless worker
runpod.serverless.start({
    "handler": handler
})