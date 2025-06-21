import os
import json
import asyncio
import tempfile
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import uvicorn
from google.cloud import storage
from google.oauth2 import service_account
import httpx
import uuid
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
RUNPOD_ENDPOINT_ID = os.getenv("RUNPOD_ENDPOINT_ID")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "seedvr2-videos")
GCS_KEY_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "/app/gcs-key.json")
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB

# Global variables
gcs_client = None
runpod_health_status = {"status": "initializing", "last_check": None}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup"""
    global gcs_client
    
    # Initialize GCS client
    try:
        if os.path.exists(GCS_KEY_PATH):
            credentials = service_account.Credentials.from_service_account_file(GCS_KEY_PATH)
            gcs_client = storage.Client(credentials=credentials)
            logger.info("GCS client initialized successfully")
        else:
            logger.warning("GCS key file not found, using default credentials")
            gcs_client = storage.Client()
    except Exception as e:
        logger.error(f"Failed to initialize GCS client: {e}")
    
    # Start background task for health checks
    asyncio.create_task(periodic_health_check())
    
    yield
    
    # Cleanup
    logger.info("Shutting down...")

app = FastAPI(lifespan=lifespan)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Netlify domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def check_runpod_health():
    """Check if RunPod endpoint is healthy"""
    global runpod_health_status
    
    if not RUNPOD_API_KEY or not RUNPOD_ENDPOINT_ID:
        runpod_health_status = {
            "status": "unconfigured",
            "message": "RunPod credentials not configured",
            "last_check": datetime.utcnow().isoformat()
        }
        return
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/health",
                headers={"Authorization": f"Bearer {RUNPOD_API_KEY}"},
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                runpod_health_status = {
                    "status": "healthy",
                    "workers": data.get("workers", {}).get("running", 0),
                    "jobs_in_queue": data.get("jobs", {}).get("in_queue", 0),
                    "last_check": datetime.utcnow().isoformat()
                }
            else:
                runpod_health_status = {
                    "status": "unhealthy",
                    "message": f"Health check failed with status {response.status_code}",
                    "last_check": datetime.utcnow().isoformat()
                }
    except Exception as e:
        runpod_health_status = {
            "status": "error",
            "message": str(e),
            "last_check": datetime.utcnow().isoformat()
        }

async def periodic_health_check():
    """Periodically check RunPod health"""
    while True:
        await check_runpod_health()
        await asyncio.sleep(30)  # Check every 30 seconds

async def wake_up_runpod():
    """Wake up RunPod workers"""
    if not RUNPOD_API_KEY or not RUNPOD_ENDPOINT_ID:
        raise HTTPException(status_code=500, detail="RunPod not configured")
    
    try:
        async with httpx.AsyncClient() as client:
            # Submit a dummy job to wake up workers
            response = await client.post(
                f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/run",
                headers={"Authorization": f"Bearer {RUNPOD_API_KEY}"},
                json={"input": {"wake_up": True}},
                timeout=10.0
            )
            
            if response.status_code in [200, 201]:
                return {"status": "success", "message": "Wake-up signal sent"}
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to wake up RunPod: {response.text}"
                )
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")

def upload_to_gcs(file_path: str, destination_name: str) -> str:
    """Upload file to Google Cloud Storage"""
    if not gcs_client:
        raise HTTPException(status_code=500, detail="GCS client not initialized")
    
    try:
        bucket = gcs_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(destination_name)
        
        # Upload with resumable upload for large files
        blob.upload_from_filename(file_path, timeout=300)
        
        # Make the blob publicly readable
        blob.make_public()
        
        return blob.public_url
    except Exception as e:
        logger.error(f"GCS upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload to GCS: {str(e)}")

async def submit_to_runpod(video_url: str, params: Dict[str, Any]) -> str:
    """Submit job to RunPod"""
    if not RUNPOD_API_KEY or not RUNPOD_ENDPOINT_ID:
        raise HTTPException(status_code=500, detail="RunPod not configured")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/run",
                headers={"Authorization": f"Bearer {RUNPOD_API_KEY}"},
                json={
                    "input": {
                        "video_url": video_url,
                        "res_h": params.get("res_h", 720),
                        "res_w": params.get("res_w", 1280),
                        "seed": params.get("seed", 42)
                    }
                },
                timeout=30.0
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                return data.get("id")
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"RunPod submission failed: {response.text}"
                )
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")

async def check_job_status(job_id: str) -> Dict[str, Any]:
    """Check RunPod job status"""
    if not RUNPOD_API_KEY or not RUNPOD_ENDPOINT_ID:
        raise HTTPException(status_code=500, detail="RunPod not configured")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/status/{job_id}",
                headers={"Authorization": f"Bearer {RUNPOD_API_KEY}"},
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to check job status: {response.text}"
                )
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "SeedVR2 Backend",
        "version": "1.0.0",
        "runpod_status": runpod_health_status
    }

@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "gcs_configured": gcs_client is not None,
        "runpod_configured": bool(RUNPOD_API_KEY and RUNPOD_ENDPOINT_ID),
        "runpod_status": runpod_health_status
    }

@app.post("/wake-up")
async def wake_up():
    """Wake up RunPod workers"""
    result = await wake_up_runpod()
    await check_runpod_health()  # Update health status
    return result

@app.post("/upload")
async def upload_video(
    video: UploadFile = File(...),
    res_h: Optional[int] = 720,
    res_w: Optional[int] = 1280,
    seed: Optional[int] = 42
):
    """Upload video and process with SeedVR2"""
    
    # Validate file
    if not video.filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):
        raise HTTPException(status_code=400, detail="Invalid file format")
    
    # Check file size
    video.file.seek(0, 2)
    file_size = video.file.tell()
    video.file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large. Maximum size is {MAX_FILE_SIZE/1024/1024}MB")
    
    # Create unique filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    filename = f"input_{timestamp}_{unique_id}_{video.filename}"
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(video.filename).suffix) as tmp_file:
            content = await video.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        # Upload to GCS
        gcs_url = upload_to_gcs(tmp_path, f"inputs/{filename}")
        logger.info(f"Uploaded to GCS: {gcs_url}")
        
        # Submit to RunPod
        job_id = await submit_to_runpod(gcs_url, {
            "res_h": res_h,
            "res_w": res_w,
            "seed": seed
        })
        
        return {
            "status": "processing",
            "job_id": job_id,
            "input_url": gcs_url,
            "message": "Video uploaded and processing started"
        }
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise
    finally:
        # Clean up temporary file
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)

@app.get("/status/{job_id}")
async def get_status(job_id: str):
    """Get job status"""
    status = await check_job_status(job_id)
    
    # Map RunPod status to our format
    runpod_status = status.get("status", "UNKNOWN")
    
    if runpod_status == "COMPLETED":
        output = status.get("output", {})
        return {
            "status": "completed",
            "result_url": output.get("result_url"),
            "message": "Processing completed successfully"
        }
    elif runpod_status == "FAILED":
        return {
            "status": "failed",
            "error": status.get("error", "Unknown error"),
            "message": "Processing failed"
        }
    elif runpod_status in ["IN_QUEUE", "IN_PROGRESS"]:
        return {
            "status": "processing",
            "message": f"Job is {runpod_status.lower().replace('_', ' ')}"
        }
    else:
        return {
            "status": "unknown",
            "message": f"Unknown status: {runpod_status}"
        }

@app.post("/download-from-gcs")
async def download_from_gcs(request: Request):
    """Download video from GCS URL"""
    data = await request.json()
    gcs_url = data.get("url")
    
    if not gcs_url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(gcs_url, timeout=60.0)
            response.raise_for_status()
            
            filename = gcs_url.split("/")[-1]
            
            return StreamingResponse(
                io.BytesIO(response.content),
                media_type="video/mp4",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}"
                }
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
