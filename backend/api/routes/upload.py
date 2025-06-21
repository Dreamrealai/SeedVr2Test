from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict
import os
import uuid
from pathlib import Path
import aiofiles

router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}
MAX_FILE_SIZE = int(os.getenv("MAX_VIDEO_SIZE_MB", "2048")) * 1024 * 1024  # Convert MB to bytes

@router.post("/")
async def upload_video(video: UploadFile = File(...)) -> Dict[str, str]:
    """Upload a video file for processing"""
    
    # Validate file extension
    file_extension = Path(video.filename).suffix.lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file format. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    filename = f"{file_id}{file_extension}"
    file_path = UPLOAD_DIR / filename
    
    # Save file with size validation
    total_size = 0
    async with aiofiles.open(file_path, 'wb') as f:
        while chunk := await video.read(1024 * 1024):  # Read 1MB at a time
            total_size += len(chunk)
            if total_size > MAX_FILE_SIZE:
                # Delete partial file
                await aiofiles.os.remove(file_path)
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024 * 1024)}MB"
                )
            await f.write(chunk)
    
    # Generate URL for the uploaded file
    # In production, this would be an S3 URL
    video_url = f"/uploads/{filename}"
    
    return {
        "video_url": video_url,
        "file_id": file_id,
        "filename": video.filename,
        "size": total_size
    }

@router.delete("/{file_id}")
async def delete_upload(file_id: str):
    """Delete an uploaded file"""
    
    # Find file with this ID
    for file in UPLOAD_DIR.glob(f"{file_id}.*"):
        try:
            os.remove(file)
            return {"message": "File deleted successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    raise HTTPException(status_code=404, detail="File not found")