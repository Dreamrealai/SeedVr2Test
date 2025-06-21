#!/usr/bin/env python3
"""
SeedVR2 RunPod API Server
Simple FastAPI server for running SeedVR2 inference on RunPod
"""

import os
import sys
import uuid
import shutil
import asyncio
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Add FastAPI imports
try:
    from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
    from fastapi.responses import FileResponse, JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
except ImportError:
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn", "python-multipart"])
    from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
    from fastapi.responses import FileResponse, JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn

# Configuration
MODEL_PATH = "/models/seedvr2-7b"
INFERENCE_SCRIPT = "/app/SeedVR/projects/inference_seedvr2_7b.py"
UPLOAD_DIR = Path("/tmp/seedvr2_uploads")
OUTPUT_DIR = Path("/tmp/seedvr2_outputs")
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB

# Create directories
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Create FastAPI app
app = FastAPI(title="SeedVR2 API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Job storage (in production, use Redis or database)
jobs: Dict[str, Dict[str, Any]] = {}

def validate_dimensions(height: int, width: int) -> tuple[int, int]:
    """Ensure dimensions are multiples of 32"""
    height = (height // 32) * 32
    width = (width // 32) * 32
    return height, width

async def run_seedvr2_async(job_id: str, input_path: str, params: Dict[str, Any]):
    """Run SeedVR2 inference asynchronously"""
    try:
        # Update job status
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["started_at"] = datetime.now().isoformat()
        
        # Prepare output directory
        job_output_dir = OUTPUT_DIR / job_id
        job_output_dir.mkdir(exist_ok=True)
        
        # Validate dimensions
        res_h, res_w = validate_dimensions(
            params.get("res_h", 720),
            params.get("res_w", 1280)
        )
        
        # Determine GPU count
        sp_size = 4 if (res_h > 720 or res_w > 1280) else 1
        
        # Prepare command
        cmd = [
            "conda", "run", "-n", "seedvr",
            "torchrun", f"--nproc-per-node={sp_size}",
            INFERENCE_SCRIPT,
            "--video_path", str(input_path),
            "--output_dir", str(job_output_dir),
            "--seed", str(params.get("seed", 42)),
            "--res_h", str(res_h),
            "--res_w", str(res_w),
            "--sp_size", str(sp_size)
        ]
        
        # Run inference
        print(f"Running command: {' '.join(cmd)}")
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise RuntimeError(f"SeedVR2 inference failed: {stderr.decode()}")
        
        # Find output video
        output_files = list(job_output_dir.glob("*.mp4"))
        if not output_files:
            raise RuntimeError("No output video found")
        
        # Update job with success
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["output_path"] = str(output_files[0])
        jobs[job_id]["completed_at"] = datetime.now().isoformat()
        
    except Exception as e:
        # Update job with error
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["failed_at"] = datetime.now().isoformat()
        print(f"Job {job_id} failed: {str(e)}")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "SeedVR2 API",
        "status": "running",
        "model": "ByteDance-Seed/SeedVR2-7B",
        "gpu": subprocess.check_output(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"]).decode().strip()
    }

@app.post("/api/restore")
async def restore_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    res_h: int = 720,
    res_w: int = 1280,
    seed: int = 42
):
    """Submit video for restoration"""
    
    # Validate file
    if not file.filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
        raise HTTPException(400, "Invalid file format. Supported: MP4, AVI, MOV, MKV")
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Save uploaded file
    input_path = UPLOAD_DIR / f"{job_id}_{file.filename}"
    
    try:
        # Read file in chunks to handle large files
        with open(input_path, "wb") as f:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                f.write(chunk)
        
        # Check file size
        file_size = input_path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            input_path.unlink()
            raise HTTPException(400, f"File too large. Maximum size: {MAX_FILE_SIZE // (1024**3)}GB")
        
        # Create job entry
        jobs[job_id] = {
            "id": job_id,
            "status": "queued",
            "input_filename": file.filename,
            "params": {
                "res_h": res_h,
                "res_w": res_w,
                "seed": seed
            },
            "created_at": datetime.now().isoformat()
        }
        
        # Start processing in background
        background_tasks.add_task(
            run_seedvr2_async,
            job_id,
            input_path,
            jobs[job_id]["params"]
        )
        
        return JSONResponse({
            "job_id": job_id,
            "status": "queued",
            "message": "Video submitted for restoration"
        })
        
    except Exception as e:
        # Clean up on error
        if input_path.exists():
            input_path.unlink()
        raise HTTPException(500, f"Failed to process upload: {str(e)}")

@app.get("/api/status/{job_id}")
async def get_job_status(job_id: str):
    """Check job status"""
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    
    job = jobs[job_id].copy()
    # Don't expose internal paths
    if "output_path" in job:
        job.pop("output_path")
    
    return job

@app.get("/api/download/{job_id}")
async def download_result(job_id: str):
    """Download restored video"""
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    
    job = jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(400, f"Job status: {job['status']}")
    
    output_path = Path(job["output_path"])
    if not output_path.exists():
        raise HTTPException(404, "Output file not found")
    
    return FileResponse(
        output_path,
        media_type="video/mp4",
        filename=f"restored_{job['input_filename']}"
    )

@app.get("/api/jobs")
async def list_jobs():
    """List all jobs"""
    return {
        "jobs": [
            {k: v for k, v in job.items() if k != "output_path"}
            for job in jobs.values()
        ]
    }

@app.delete("/api/cleanup")
async def cleanup_old_files():
    """Clean up old files (admin endpoint)"""
    import time
    current_time = time.time()
    cleaned = {"uploads": 0, "outputs": 0}
    
    # Clean uploads older than 24 hours
    for file in UPLOAD_DIR.glob("*"):
        if file.is_file() and (current_time - file.stat().st_mtime) > 86400:
            file.unlink()
            cleaned["uploads"] += 1
    
    # Clean outputs older than 48 hours
    for dir in OUTPUT_DIR.glob("*"):
        if dir.is_dir() and (current_time - dir.stat().st_mtime) > 172800:
            shutil.rmtree(dir)
            cleaned["outputs"] += 1
    
    return {"message": "Cleanup completed", "cleaned": cleaned}

if __name__ == "__main__":
    # Check if model exists
    if not Path(MODEL_PATH).exists():
        print(f"❌ Model not found at {MODEL_PATH}")
        print("Please run the setup script first!")
        sys.exit(1)
    
    print("🚀 Starting SeedVR2 API Server...")
    print(f"📁 Model path: {MODEL_PATH}")
    print(f"📤 Upload directory: {UPLOAD_DIR}")
    print(f"📥 Output directory: {OUTPUT_DIR}")
    
    # Run server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
