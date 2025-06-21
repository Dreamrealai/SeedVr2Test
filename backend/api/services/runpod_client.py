import os
import runpod
from typing import Dict, Any, Optional
import logging
from ..models.schemas import VideoProcessingParams, ProcessingJob

logger = logging.getLogger(__name__)

class RunPodClient:
    def __init__(self):
        self.api_key = os.getenv("RUNPOD_API_KEY")
        self.endpoint_id = os.getenv("RUNPOD_ENDPOINT_ID")
        
        if not self.api_key:
            raise ValueError("RUNPOD_API_KEY not set in environment variables")
        
        if not self.endpoint_id:
            raise ValueError("RUNPOD_ENDPOINT_ID not set in environment variables")
        
        runpod.api_key = self.api_key
        self.endpoint = runpod.Endpoint(self.endpoint_id)
    
    def submit_job(self, video_url: str, params: VideoProcessingParams) -> ProcessingJob:
        """Submit a video processing job to RunPod"""
        
        # Map resolution to actual dimensions
        resolution_map = {
            "720p": {"height": 720, "width": 1280, "sp_size": 1},
            "1080p": {"height": 1080, "width": 1920, "sp_size": 4},
            "2k": {"height": 1440, "width": 2560, "sp_size": 4}
        }
        
        res_config = resolution_map[params.resolution]
        
        job_input = {
            "video_url": video_url,
            "res_h": res_config["height"],
            "res_w": res_config["width"],
            "sp_size": res_config["sp_size"],
            "seed": params.seed
        }
        
        try:
            # Submit job to RunPod
            run_request = self.endpoint.run(job_input)
            
            # Create job record
            job = ProcessingJob(
                id=run_request.job_id,
                status="queued",
                runpod_job_id=run_request.job_id,
                input_video_url=video_url,
                parameters=params.dict()
            )
            
            logger.info(f"Submitted job {job.id} to RunPod")
            return job
            
        except Exception as e:
            logger.error(f"Failed to submit job to RunPod: {str(e)}")
            raise
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get the status of a RunPod job"""
        
        try:
            status = self.endpoint.status(job_id)
            
            result = {
                "status": self._map_runpod_status(status.status),
                "progress": self._calculate_progress(status)
            }
            
            if status.status == "COMPLETED":
                result["output"] = status.output
            elif status.status == "FAILED":
                result["error"] = status.error
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get job status from RunPod: {str(e)}")
            raise
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a RunPod job"""
        
        try:
            self.endpoint.cancel(job_id)
            logger.info(f"Cancelled job {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel job: {str(e)}")
            return False
    
    def _map_runpod_status(self, runpod_status: str) -> str:
        """Map RunPod status to our status"""
        
        status_map = {
            "IN_QUEUE": "queued",
            "IN_PROGRESS": "processing",
            "COMPLETED": "completed",
            "FAILED": "failed",
            "CANCELLED": "cancelled",
            "TIMED_OUT": "failed"
        }
        
        return status_map.get(runpod_status, "unknown")
    
    def _calculate_progress(self, status: Any) -> Optional[float]:
        """Calculate job progress based on RunPod status"""
        
        # RunPod doesn't provide granular progress, so we estimate
        if status.status == "IN_QUEUE":
            return 0.0
        elif status.status == "IN_PROGRESS":
            # Estimate based on time elapsed
            # This is a simplified estimation
            return 0.5
        elif status.status == "COMPLETED":
            return 1.0
        else:
            return None

# Singleton instance
runpod_client = RunPodClient()