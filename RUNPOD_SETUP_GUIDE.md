# SEEDVR2 7B Model Setup on RunPod

## 🚀 Quick Setup Guide

### Prerequisites
- RunPod account with API key
- RunPod pod with H100 GPU (80GB VRAM)
- Your RunPod API key set in environment

### Step 1: Install RunPod CLI (Local Machine)
```bash
pip install runpod
```

### Step 2: Configure RunPod API Key
```bash
export RUNPOD_API_KEY="your-api-key-here"
```

### Step 3: Deploy to RunPod

#### Option A: One-Click Setup (Recommended)
If you have a running RunPod pod, SSH into it and run:
```bash
wget -qO- https://raw.githubusercontent.com/dreamrealai/SeedVr2Test/main/scripts/setup-runpod-pod.sh | bash
```

#### Option B: Manual Setup
1. Run the deployment script:
```bash
./deploy-to-runpod.sh
```

2. Select your pod ID when prompted

3. Wait for setup to complete (15-20 minutes for model download)

### Step 4: Test the Installation
SSH into your pod:
```bash
runpod ssh <your-pod-id>
```

Run a test:
```bash
conda run -n seedvr python /app/quick_inference.py /path/to/test.mp4 720 1280
```

## 📊 GPU Memory Requirements

| Resolution | GPUs Required | VRAM per GPU | Total VRAM |
|------------|---------------|--------------|------------|
| 720p       | 1x H100       | ~40GB        | 40GB       |
| 1080p      | 4x H100       | ~60GB        | 240GB      |
| 2K         | 4x H100       | ~70GB        | 280GB      |

## 🎥 Running Inference

### Basic Command
```bash
conda run -n seedvr torchrun --nproc-per-node=1 \
  /app/SeedVR/projects/inference_seedvr2_7b.py \
  --video_path input.mp4 \
  --output_dir output/ \
  --seed 42 \
  --res_h 720 \
  --res_w 1280 \
  --sp_size 1
```

### Parameters
- `--video_path`: Input video file
- `--output_dir`: Output directory
- `--seed`: Random seed (default: 42)
- `--res_h`: Output height (must be multiple of 32)
- `--res_w`: Output width (must be multiple of 32)
- `--sp_size`: Number of GPUs (1 for 720p, 4 for higher)

## 🌐 API Server Setup

### Start the API Server
```bash
cd /app/SeedVr2Test/backend
conda run -n seedvr python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### API Endpoints
- `POST /api/restore`: Submit video for restoration
- `GET /api/status/{job_id}`: Check job status
- `GET /api/download/{job_id}`: Download result

## 🐛 Troubleshooting

### Model Download Issues
If model download fails:
```bash
conda run -n seedvr python -c "
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id='ByteDance-Seed/SeedVR2-7B',
    local_dir='/models/seedvr2-7b',
    resume_download=True
)"
```

### CUDA Out of Memory
- Reduce resolution
- Ensure using correct sp_size
- Check no other processes using GPU: `nvidia-smi`

### Flash Attention Issues
If flash attention fails to install:
```bash
pip install ninja
pip install flash-attn --no-build-isolation
```

## 📝 Notes

1. **Input Requirements**: 
   - Video dimensions must be multiples of 32
   - Supported formats: MP4, AVI, MOV, MKV

2. **Processing Time**:
   - 720p: 5-10 minutes per video
   - 1080p: 8-12 minutes per video
   - 2K: 12-18 minutes per video

3. **Quality Settings**:
   - Lower resolutions process faster
   - Higher resolutions need more GPUs
   - Seed affects randomness in restoration

## 🔗 Resources

- [Original SeedVR Repository](https://github.com/bytedance-seed/SeedVR)
- [Model on HuggingFace](https://huggingface.co/ByteDance-Seed/SeedVR2-7B)
- [RunPod Documentation](https://docs.runpod.io)

## 📞 Support

For issues:
1. Check RunPod pod logs: `runpod logs <pod-id>`
2. Check GPU status: `nvidia-smi`
3. Check conda environment: `conda info --envs`
