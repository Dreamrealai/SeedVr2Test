import runpod
import os
import subprocess
import torch
import logging
from typing import Dict, Any
import requests
import tempfile
from pathlib import Path
from google.cloud import storage
from google.oauth2 import service_account
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
MODEL_PATH = os.getenv("MODEL_PATH", "/models/seedvr2-3b")  # Use 3B model by default
INFERENCE_SCRIPT_3B = "/app/SeedVR/projects/inference_seedvr2_3b.py"
INFERENCE_SCRIPT_7B = "/app/SeedVR/projects/inference_seedvr2_7b.py"
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "seedvr2-videos")
GCS_KEY_JSON = os.getenv("GCS_KEY_JSON")  # JSON string of the service account key

# Initialize GCS client
gcs_client = None
if GCS_KEY_JSON:
    try:
        key_data = json.loads(GCS_KEY_JSON)
        credentials = service_account.Credentials.from_service_account_info(key_data)
        gcs_client = storage.Client(credentials=credentials)
        logger.info("GCS client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize GCS client: {e}")
        gcs_client = None

def download_video(url: str, output_path: str) -> str:
    """Download video from URL"""
    logger.info(f"Downloading video from {url}")
    
    try:
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        if int(progress) % 10 == 0:
                            logger.info(f"Download progress: {progress:.1f}%")
        
        logger.info(f"Downloaded video to {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Failed to download video: {e}")
        raise

def upload_to_gcs(file_path: str, destination_name: str) -> str:
    """Upload result to Google Cloud Storage"""
    if not gcs_client:
        logger.error("GCS client not initialized")
        raise RuntimeError("GCS client not available")
    
    try:
        bucket = gcs_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(destination_name)
        
        # Upload with resumable upload for large files
        logger.info(f"Uploading {file_path} to GCS: {destination_name}")
        blob.upload_from_filename(file_path, timeout=600)
        
        # Make the blob publicly readable
        blob.make_public()
        
        public_url = blob.public_url
        logger.info(f"Uploaded to GCS: {public_url}")
        return public_url
    except Exception as e:
        logger.error(f"GCS upload failed: {e}")
        raise

def validate_dimensions(height: int, width: int) -> tuple[int, int]:
    """Ensure dimensions are multiples of 32"""
    height = (height // 32) * 32
    width = (width // 32) * 32
    return height, width

def determine_model_and_gpu_count(height: int, width: int) -> tuple[str, int, str]:
    """Determine which model to use and GPU count based on resolution"""
    pixels = height * width
    
    # For 720p and below, use 3B model with 1 GPU
    if pixels <= 1280 * 720:
        return "3b", 1, INFERENCE_SCRIPT_3B
    # For 1080p, use 3B model with 4 GPUs or 7B with 2 GPUs
    elif pixels <= 1920 * 1080:
        # Check if we have multiple GPUs available
        gpu_count = torch.cuda.device_count()
        if gpu_count >= 4:
            return "3b", 4, INFERENCE_SCRIPT_3B
        else:
            return "7b", min(gpu_count, 2), INFERENCE_SCRIPT_7B
    # For 2K and above, use 7B model with 4 GPUs
    else:
        return "7b", 4, INFERENCE_SCRIPT_7B

def run_seedvr2(input_video: str, output_dir: str, params: Dict[str, Any]) -> str:
    """Run SeedVR2 inference"""
    logger.info(f"Running SeedVR2 with params: {params}")
    
    # Validate and adjust dimensions
    res_h, res_w = validate_dimensions(
        params.get('res_h', 720),
        params.get('res_w', 1280)
    )
    
    # Determine model and GPU configuration
    model_size, sp_size, inference_script = determine_model_and_gpu_count(res_h, res_w)
    logger.info(f"Using {model_size} model with {sp_size} GPU(s) for {res_w}x{res_h} resolution")
    
    # Prepare command
    cmd = [
        "torchrun",
        f"--nproc-per-node={sp_size}",
        inference_script,
        "--video_path", input_video,
        "--output_dir", output_dir,
        "--seed", str(params.get('seed', 42)),
        "--res_h", str(res_h),
        "--res_w", str(res_w),
        "--sp_size", str(sp_size)
    ]
    
    # Run inference
    logger.info(f"Running command: {' '.join(cmd)}")
    
    env = os.environ.copy()
    env['CUDA_VISIBLE_DEVICES'] = ','.join(str(i) for i in range(sp_size))
    
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    
    if result.returncode != 0:
        logger.error(f"SeedVR2 stderr: {result.stderr}")
        raise RuntimeError(f"SeedVR2 inference failed: {result.stderr}")
    
    # Find output video
    output_files = list(Path(output_dir).glob("*.mp4"))
    if not output_files:
        # Also check for other video formats
        for ext in ['*.avi', '*.mov', '*.mkv']:
            output_files = list(Path(output_dir).glob(ext))
            if output_files:
                break
    
    if not output_files:
        raise RuntimeError("No output video found")
    
    return str(output_files[0])

def handler(job):
    """RunPod handler function"""
    logger.info(f"Starting job: {job}")
    
    try:
        job_input = job.get("input", {})
        
        # Check if this is a wake-up call
        if job_input.get("wake_up"):
            logger.info("Received wake-up call")
            return {
                "status": "success",
                "message": "Worker is awake"
            }
        
        # Validate input
        video_url = job_input.get("video_url")
        if not video_url:
            raise ValueError("video_url is required")
        
        # Create temporary directories
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = os.path.join(temp_dir, "input.mp4")
            output_dir = os.path.join(temp_dir, "output")
            os.makedirs(output_dir, exist_ok=True)
            
            # Download input video
            download_video(video_url, input_path)
            
            # Run SeedVR2
            output_path = run_seedvr2(input_path, output_dir, job_input)
            
            # Generate output filename
            import uuid
            from datetime import datetime
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            output_filename = f"output_{timestamp}_{unique_id}.mp4"
            
            # Upload result to GCS
            result_url = upload_to_gcs(output_path, f"outputs/{output_filename}")
            
            return {
                "status": "success",
                "result_url": result_url,
                "message": "Video restoration completed successfully",
                "details": {
                    "input_url": video_url,
                    "output_resolution": f"{job_input.get('res_w', 1280)}x{job_input.get('res_h', 720)}",
                    "seed": job_input.get('seed', 42)
                }
            }
            
    except Exception as e:
        logger.error(f"Job failed: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }

# RunPod serverless worker
if __name__ == "__main__":
    runpod.serverless.start({
        "handler": handler
    })