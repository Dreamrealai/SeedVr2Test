# 🚀 One-Click Setup for SeedVR2-7B on RunPod

## Your Pod is Ready!

- **Pod ID**: `8ybijjxidw6y6j`  
- **GPU**: NVIDIA A100 80GB PCIe (80GB VRAM)
- **Status**: ✅ RUNNING
- **Cost**: $1.19/hour

## One-Click Setup Instructions

### Option 1: Via RunPod Web Interface (Easiest)

1. **Open RunPod Dashboard**: https://www.runpod.io/console/pods

2. **Find your pod** (ID: 8ybijjxidw6y6j) and click "Connect"

3. **Open the Web Terminal**

4. **Copy and paste this single command**:
   ```bash
   wget -qO- https://raw.githubusercontent.com/Dreamrealai/SeedVr2Test/main/scripts/setup-runpod-pod.sh | bash
   ```

5. **Wait for completion** (~15-20 minutes for model download)

### Option 2: Via RunPod CLI

If you have RunPod CLI access, run:
```bash
# Connect to pod
runpodctl exec python 8ybijjxidw6y6j

# In the Python shell, run:
import os
os.system("wget -qO- https://raw.githubusercontent.com/Dreamrealai/SeedVr2Test/main/scripts/setup-runpod-pod.sh | bash")
exit()
```

## What the Setup Does

1. ✅ Installs all system dependencies
2. ✅ Sets up Python environment with Conda
3. ✅ Clones SeedVR repository
4. ✅ Installs PyTorch with CUDA support
5. ✅ Downloads SeedVR2-7B model (~33GB)
6. ✅ Runs verification tests

## Testing Your Setup

After setup completes, test with a sample video:

```bash
# Activate environment
source /opt/conda/etc/profile.d/conda.sh
conda activate seedvr

# Download test video
wget https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4 -O /tmp/test.mp4

# Run SeedVR2-7B
cd /app/SeedVR
torchrun --nproc-per-node=1 projects/inference_seedvr2_7b.py \
  --video_path /tmp/test.mp4 \
  --output_dir /tmp/output \
  --seed 42 \
  --res_h 720 \
  --res_w 1280 \
  --sp_size 1

# Check output
ls -la /tmp/output/
```

## Quick Usage

Once setup is complete, to process any video:

```bash
conda activate seedvr
cd /app/SeedVR

torchrun --nproc-per-node=1 projects/inference_seedvr2_7b.py \
  --video_path YOUR_VIDEO.mp4 \
  --output_dir OUTPUT_FOLDER \
  --seed 42 \
  --res_h 720 \
  --res_w 1280 \
  --sp_size 1
```

## Monitoring Progress

Check GPU usage:
```bash
watch -n 1 nvidia-smi
```

Check disk space:
```bash
df -h
```

## Troubleshooting

### If setup fails:
1. Check internet connection: `ping google.com`
2. Check disk space: `df -h` (need ~50GB free)
3. Check GPU: `nvidia-smi`

### Common Issues:
- **"CUDA out of memory"**: Reduce resolution or video length
- **"Model not found"**: Re-run the model download part
- **"Command not found"**: Make sure to activate conda environment

## Cost Management

- **Stop pod when not using**: 
  ```bash
  runpodctl stop pod 8ybijjxidw6y6j
  ```
- **Restart when needed**:
  ```bash
  runpodctl start pod 8ybijjxidw6y6j
  ```

## Support

- GitHub Issues: https://github.com/Dreamrealai/SeedVr2Test/issues
- RunPod Discord: https://discord.gg/runpod

---

**Ready to go!** Just run the one-click command in your pod's web terminal. 🎉