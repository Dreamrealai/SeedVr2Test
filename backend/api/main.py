from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv

from .routes import upload, process, status
from .services.storage import init_storage

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="SeedVR2 API",
    description="API for SeedVR2 video restoration using RunPod",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize storage
init_storage()

# Mount static files for serving processed videos
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(upload.router, prefix="/api/upload", tags=["upload"])
app.include_router(process.router, prefix="/api/process", tags=["process"])
app.include_router(status.router, prefix="/api/status", tags=["status"])

@app.get("/")
async def root():
    return {
        "message": "SeedVR2 API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/api/upload",
            "process": "/api/process",
            "status": "/api/status"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)