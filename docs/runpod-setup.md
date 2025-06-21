# RunPod Setup Guide for SeedVR2-7B

## Overview

This guide walks you through setting up SeedVR2-7B on RunPod with GPU support.

## Prerequisites

- RunPod account with API key
- Docker (for building images)
- RunPod CLI installed

## Current Pod Information

- **Pod ID**: 8ybijjxidw6y6j
- **GPU**: NVIDIA A100 80GB PCIe
- **Cost**: $1.190/hour
- **Status**: RUNNING

## Setup Steps

### 1. Connect to the Pod

```bash
runpodctl exec 8ybijjxidw6y6j bash
```

### 2. Run the Setup Script

Inside the pod, run:

```bash
# Download and run setup script
wget https://raw.githubusercontent.com/Dreamrealai/SeedVr2Test/main/scripts/setup-runpod-pod.sh
chmod +x setup-runpod-pod.sh
./setup-runpod-pod.sh
```

This script will:
- Install all system dependencies
- Set up Miniconda and Python environment
- Clone the SeedVR repository
- Install PyTorch and all required packages
- Download the SeedVR2-7B model (~33GB)
- Run a test to verify setup

### 3. Test the Installation

After setup completes, test with:

```bash
conda activate seedvr
python /app/test_seedvr2.py
```

### 4. Run Video Restoration

To process a video:

```bash
conda activate seedvr

torchrun --nproc-per-node=1 /app/SeedVR/projects/inference_seedvr2_7b.py \
  --video_path /path/to/input.mp4 \
  --output_dir /path/to/output \
  --seed 42 \
  --res_h 720 \
  --res_w 1280 \
  --sp_size 1
```

## GPU Requirements

- **720p and below**: 1x GPU (A100 80GB or H100)
- **1080p and 2K**: 4x GPUs (use `--sp_size 4`)

## Important Notes

1. **Model Size**: The SeedVR2-7B model is ~33GB. Download may take 10-20 minutes.

2. **Input Constraints**: Video dimensions must be multiples of 32.

3. **Memory Usage**: The 7B model requires significant GPU memory. A100 80GB should handle most videos.

4. **Processing Time**: Expect ~2x realtime for 720p on single GPU.

## Troubleshooting

### CUDA Out of Memory
- Reduce resolution
- Process shorter video segments
- Ensure no other processes are using GPU

### Model Not Found
- Check `/models/seedvr2-7b` directory
- Re-run the download portion of setup script

### Inference Script Not Found
- The script should be at: `/app/SeedVR/projects/inference_seedvr2_7b.py`
- If missing, check if SeedVR repo cloned correctly

## Cost Optimization

- Use spot instances when available (~$0.60/hr vs $1.19/hr)
- Stop the pod when not in use
- Process videos in batches to minimize idle time

## API Integration

To integrate with the web GUI:

1. Set up the FastAPI backend with RunPod SDK
2. Configure the endpoint ID in `.env`
3. The backend will submit jobs to this pod

## Monitoring

Check pod status:
```bash
runpodctl get pod 8ybijjxidw6y6j
```

View GPU usage inside pod:
```bash
nvidia-smi
```

## Stopping the Pod

When done, stop the pod to avoid charges:
```bash
runpodctl stop pod 8ybijjxidw6y6j
```

To restart later:
```bash
runpodctl start pod 8ybijjxidw6y6j
```