# 🚀 Quick Setup for RunPod Terminal

## Your Pod Info
- **Pod ID**: `8ybijjxidw6y6j`  
- **GPU**: NVIDIA A100 80GB
- **Status**: RUNNING

## Step 1: Connect to Your Pod

1. Go to: https://www.runpod.io/console/pods
2. Find pod `8ybijjxidw6y6j`
3. Click "Connect" → "Connect to Web Terminal"

## Step 2: Run This Single Command

Copy and paste this entire block into the terminal:

```bash
apt-get update && apt-get install -y git wget ffmpeg && \
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh && \
bash /tmp/miniconda.sh -b -p /opt/conda && rm /tmp/miniconda.sh && \
export PATH="/opt/conda/bin:${PATH}" && \
git clone https://github.com/bytedance-seed/SeedVR.git /app/SeedVR && \
cd /app/SeedVR && \
conda create -n seedvr python=3.10 -y && \
source /opt/conda/etc/profile.d/conda.sh && \
conda activate seedvr && \
pip install torch==2.3.0 torchvision==0.18.0 torchaudio==2.3.0 --index-url https://download.pytorch.org/whl/cu118 && \
pip install numpy'<2' opencv-python imageio imageio-ffmpeg av decord einops tensorboard tqdm omegaconf transformers diffusers accelerate xformers ftfy gradio soundfile moviepy oss2 huggingface_hub && \
pip install flash_attn==2.5.9.post1 --no-build-isolation && \
python -c "from huggingface_hub import snapshot_download; import os; save_dir = '/models/seedvr2-7b'; repo_id = 'ByteDance-Seed/SeedVR2-7B'; print(f'Downloading {repo_id}...'); os.makedirs(save_dir, exist_ok=True); snapshot_download(cache_dir=save_dir + '/cache', local_dir=save_dir, repo_id=repo_id, local_dir_use_symlinks=False, resume_download=True); print('✅ Model downloaded!')" && \
echo "✅ Setup complete!"
```

This will take about 15-20 minutes (mostly for downloading the 33GB model).

## Step 3: Test It Works

After setup completes, test with:

```bash
conda activate seedvr
cd /app/SeedVR
wget https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4 -O /tmp/test.mp4
torchrun --nproc-per-node=1 projects/inference_seedvr2_7b.py --video_path /tmp/test.mp4 --output_dir /tmp/output --seed 42 --res_h 720 --res_w 1280 --sp_size 1
ls -la /tmp/output/
```

## That's it! 🎉

Your SeedVR2-7B is ready to restore videos!