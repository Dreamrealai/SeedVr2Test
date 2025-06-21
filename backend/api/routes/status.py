from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import List
import asyncio
import json
from datetime import datetime, timedelta

from ..models.schemas import ProcessingJob

router = APIRouter()

# Import jobs_db from process.py (in production, use proper database)
from .process import jobs_db

@router.get("/{job_id}", response_model=ProcessingJob)
async def get_job_status(job_id: str) -> ProcessingJob:
    """Get status of a specific job"""
    
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs_db[job_id]
    
    # Update job status from RunPod if processing
    if job.status == "processing":
        try:
            from ..services.runpod_client import runpod_client
            status = runpod_client.get_job_status(job_id)
            
            job.status = status["status"]
            job.progress = status.get("progress")
            
            if status["status"] == "completed":
                job.resultUrl = status["output"].get("result_url")
            elif status["status"] == "failed":
                job.error = status.get("error", "Unknown error")
            
            job.updatedAt = datetime.utcnow().isoformat()
            
        except Exception as e:
            # Log error but don't fail the request
            print(f"Error updating job status: {e}")
    
    # Estimate remaining time
    if job.status == "processing" and job.progress:
        elapsed = (datetime.utcnow() - datetime.fromisoformat(job.createdAt)).total_seconds()
        if job.progress > 0:
            total_estimated = elapsed / job.progress
            job.estimatedTimeRemaining = int(total_estimated - elapsed)
    
    return job

@router.get("/history", response_model=List[ProcessingJob])
async def get_job_history(
    limit: int = 10,
    status: str = None
) -> List[ProcessingJob]:
    """Get job history"""
    
    jobs = list(jobs_db.values())
    
    # Filter by status if provided
    if status:
        jobs = [j for j in jobs if j.status == status]
    
    # Sort by creation date (newest first)
    jobs.sort(key=lambda j: j.createdAt, reverse=True)
    
    # Limit results
    return jobs[:limit]

@router.websocket("/ws/{job_id}")
async def job_status_websocket(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for real-time job status updates"""
    
    await websocket.accept()
    
    try:
        while True:
            if job_id not in jobs_db:
                await websocket.send_json({
                    "error": "Job not found"
                })
                break
            
            job = jobs_db[job_id]
            
            # Send current status
            await websocket.send_json(job.dict())
            
            # If job is complete, close connection
            if job.status in ["completed", "failed", "cancelled"]:
                break
            
            # Wait before next update
            await asyncio.sleep(2)
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({
            "error": str(e)
        })
    finally:
        await websocket.close()

@router.delete("/cleanup")
async def cleanup_old_jobs(days: int = 1):
    """Clean up old completed jobs"""
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    deleted_count = 0
    
    jobs_to_delete = []
    for job_id, job in jobs_db.items():
        job_date = datetime.fromisoformat(job.updatedAt)
        if job_date < cutoff_date and job.status in ["completed", "failed", "cancelled"]:
            jobs_to_delete.append(job_id)
    
    for job_id in jobs_to_delete:
        del jobs_db[job_id]
        deleted_count += 1
    
    return {
        "deleted_jobs": deleted_count,
        "message": f"Cleaned up {deleted_count} old jobs"
    }