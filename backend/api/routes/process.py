from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import uuid
import os
from datetime import datetime

from ..services.runpod_client import runpod_client
from ..models.schemas import VideoProcessingParams, ProcessingJob

router = APIRouter()

# In-memory job storage (replace with database in production)
jobs_db = {}

class ProcessRequest(BaseModel):
    video_url: str
    resolution: str = "720p"
    seed: int = 42

@router.post("/", response_model=ProcessingJob)
async def start_processing(
    request: ProcessRequest,
    background_tasks: BackgroundTasks
) -> ProcessingJob:
    """Start video processing job"""
    
    # Create job ID
    job_id = str(uuid.uuid4())
    
    # Create processing parameters
    params = VideoProcessingParams(
        resolution=request.resolution,
        seed=request.seed
    )
    
    # Create job record
    job = ProcessingJob(
        id=job_id,
        status="queued",
        createdAt=datetime.utcnow().isoformat(),
        updatedAt=datetime.utcnow().isoformat()
    )
    
    # Store job
    jobs_db[job_id] = job
    
    # Submit to RunPod in background
    background_tasks.add_task(
        submit_to_runpod,
        job_id,
        request.video_url,
        params
    )
    
    return job

async def submit_to_runpod(
    job_id: str,
    video_url: str,
    params: VideoProcessingParams
):
    """Submit job to RunPod (background task)"""
    try:
        # Submit to RunPod
        runpod_job = runpod_client.submit_job(video_url, params)
        
        # Update job status
        job = jobs_db[job_id]
        job.status = "processing"
        job.updatedAt = datetime.utcnow().isoformat()
        
    except Exception as e:
        # Update job with error
        job = jobs_db[job_id]
        job.status = "failed"
        job.error = str(e)
        job.updatedAt = datetime.utcnow().isoformat()

@router.post("/{job_id}/cancel")
async def cancel_job(job_id: str):
    """Cancel a processing job"""
    
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs_db[job_id]
    
    if job.status in ["completed", "failed"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel job in {job.status} state"
        )
    
    # Cancel in RunPod
    success = runpod_client.cancel_job(job_id)
    
    if success:
        job.status = "cancelled"
        job.updatedAt = datetime.utcnow().isoformat()
        return {"message": "Job cancelled successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to cancel job")

@router.get("/estimate")
async def estimate_cost(resolution: str = "720p") -> dict:
    """Estimate processing cost"""
    
    # GPU requirements by resolution (H100-80G)
    # Based on official SeedVR2 documentation
    gpu_config = {
        "720p": {"gpus": 1, "avg_minutes": 7},   # 1x H100-80G
        "1080p": {"gpus": 4, "avg_minutes": 10}, # 4x H100-80G with sp_size=4
        "2k": {"gpus": 4, "avg_minutes": 15}     # 4x H100-80G with sp_size=4
    }
    
    config = gpu_config.get(resolution, gpu_config["720p"])
    
    # Calculate cost (H100-80G on RunPod)
    gpu_cost_per_hour = 3.50  # Updated H100-80G pricing
    hours = config["avg_minutes"] / 60
    cost = config["gpus"] * gpu_cost_per_hour * hours
    
    # Add markup
    markup = float(os.getenv("MARKUP_PERCENTAGE", "20")) / 100
    total_cost = cost * (1 + markup)
    
    return {
        "resolution": resolution,
        "gpus_required": config["gpus"],
        "estimated_minutes": config["avg_minutes"],
        "estimated_cost": round(total_cost, 2),
        "currency": "USD"
    }