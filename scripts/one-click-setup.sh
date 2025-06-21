#!/bin/bash
# One-click setup script for SeedVR2-7B on RunPod
# Run this in the RunPod web terminal

set -e

echo "🚀 Starting SeedVR2-7B one-click setup..."

# Download and run the full setup script
cd /tmp
wget -q https://raw.githubusercontent.com/Dreamrealai/SeedVr2Test/main/scripts/setup-runpod-pod.sh
chmod +x setup-runpod-pod.sh
./setup-runpod-pod.sh

echo "✅ Setup complete!"