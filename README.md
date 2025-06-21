# SeedVR2 RunPod GUI

A web-based interface for running SeedVR2-7B video restoration on RunPod with one-click functionality.

## Features

- 🎥 Easy video upload with drag-and-drop
- ⚡ One-click video restoration using SeedVR2-7B model
- 🖥️ RunPod integration for GPU processing
- 📊 Real-time processing status
- 🎛️ Adjustable parameters (resolution, seed)
- 💾 Automatic result download

## Architecture

- **Frontend**: React + TypeScript
- **Backend**: FastAPI + Python
- **Processing**: RunPod Serverless (H100 GPUs)
- **Model**: ByteDance-Seed/SeedVR2-7B

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.10+
- RunPod API key
- Docker (for local testing)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/dreamrealai/seedvr2-runpod-gui.git
cd seedvr2-runpod-gui
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your RunPod API key and other settings
```

3. Install dependencies:
```bash
# Frontend
cd frontend
npm install

# Backend
cd ../backend
pip install -r requirements.txt
```

4. Run locally:
```bash
# Start backend
cd backend
uvicorn api.main:app --reload

# Start frontend (new terminal)
cd frontend
npm start
```

## Deployment

### RunPod Setup

1. Build and push Docker image:
```bash
cd runpod
docker build -t seedvr2-handler .
docker push your-registry/seedvr2-handler
```

2. Create RunPod serverless endpoint with the Docker image

3. Update `.env` with your RunPod endpoint URL

### Production Deployment

See [docs/deployment.md](docs/deployment.md) for detailed deployment instructions.

## Usage

1. Open the web interface
2. Upload or drag-and-drop a video file
3. Select output resolution (720p, 1080p, or 2K)
4. Click "Restore Video"
5. Wait for processing (5-15 minutes depending on video length)
6. Download the restored video

## API Documentation

See [docs/api.md](docs/api.md) for API endpoint documentation.

## GPU Requirements & Cost Estimation

### GPU Requirements
- **720p and below**: 1x H100-80G GPU
- **1080p and 2K**: 4x H100-80G GPUs (with sp_size=4)

### Cost Estimates (H100-80G on RunPod)
- H100-80G GPU: ~$3.50/hour
- **720p**: ~$0.40-$0.70 per video (1 GPU, 5-10 min)
- **1080p**: ~$2.30-$3.50 per video (4 GPUs, 8-12 min)  
- **2K**: ~$3.50-$5.25 per video (4 GPUs, 12-18 min)

### Known Limitations
- Input dimensions must be multiples of 32
- Not robust to heavily degraded videos
- May fail with very large motions
- Can over-sharpen lightly degraded inputs

## License

Apache 2.0 (matching SeedVR2 license)