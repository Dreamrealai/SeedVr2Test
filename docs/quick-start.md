# Quick Start Guide

## Overview

This project provides a web-based GUI for running SeedVR2 (7B model) video restoration on RunPod with one-click functionality.

## Prerequisites

1. **RunPod Account**: Sign up at https://runpod.io
2. **RunPod API Key**: Generate from your RunPod dashboard
3. **Storage Solution**: AWS S3 or Cloudflare R2 account
4. **Local Development**: Node.js 18+, Python 3.10+, Docker

## Local Setup

1. **Clone the repository**:
   ```bash
   cd SeedVr2Test
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Run setup script**:
   ```bash
   chmod +x scripts/setup.sh
   ./scripts/setup.sh
   ```

4. **Start services**:
   ```bash
   docker-compose up
   ```

   Or run individually:
   ```bash
   # Backend
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   uvicorn api.main:app --reload

   # Frontend (new terminal)
   cd frontend
   npm install
   npm start
   ```

5. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## RunPod Deployment

1. **Build Docker image**:
   ```bash
   cd runpod
   docker build -t your-registry/seedvr2-handler:latest .
   docker push your-registry/seedvr2-handler:latest
   ```

2. **Create RunPod endpoint**:
   - Go to RunPod Dashboard > Serverless > New Endpoint
   - Set container image: `your-registry/seedvr2-handler:latest`
   - GPU Type: H100 80GB
   - Min Workers: 0, Max Workers: 4

3. **Update .env**:
   ```
   RUNPOD_API_KEY=your_key
   RUNPOD_ENDPOINT_ID=your_endpoint_id
   ```

## Usage

1. Open http://localhost:3000
2. Drag and drop or upload a video file
3. Select output resolution (720p, 1080p, or 2K)
4. Click "Restore Video"
5. Wait for processing (5-15 minutes)
6. Download the restored video

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│   Backend   │────▶│   RunPod    │
│   (React)   │     │  (FastAPI)  │     │  (Handler)  │
└─────────────┘     └─────────────┘     └─────────────┘
                           │                     │
                           ▼                     ▼
                    ┌─────────────┐     ┌─────────────┐
                    │   Storage   │     │  SeedVR2-7B │
                    │   (S3/R2)   │     │    Model    │
                    └─────────────┘     └─────────────┘
```

## Key Features

- ✅ One-click video restoration
- ✅ Drag-and-drop upload
- ✅ Real-time processing status
- ✅ Auto-scaling with RunPod
- ✅ Cost estimation
- ✅ Progress tracking
- ✅ Download results

## Cost Breakdown

- 720p (1 GPU): ~$0.32-$0.40 per video
- 1080p (4 GPUs): ~$0.65-$0.80 per video
- 2K (4 GPUs): ~$0.97-$1.20 per video

## Troubleshooting

### RunPod Issues
- Check endpoint logs in RunPod dashboard
- Verify Docker image is pushed correctly
- Ensure GPU availability

### Upload Issues
- Check file size limits (2GB default)
- Verify supported formats: MP4, AVI, MOV, MKV, WebM

### Processing Failures
- Monitor RunPod worker logs
- Check GPU memory usage
- Verify model weights are downloaded

## Next Steps

1. Deploy to production (see docs/deployment.md)
2. Set up monitoring and logging
3. Configure auto-scaling policies
4. Add authentication if needed
5. Set up billing/usage tracking