#!/bin/bash

# Deploy and setup SeedVR2-7B on RunPod pod

POD_ID="8ybijjxidw6y6j"
SCRIPT_DIR="$(dirname "$0")"

echo "🚀 Deploying SeedVR2-7B to RunPod pod ${POD_ID}..."

# Copy setup script to pod
echo "📤 Copying setup script to pod..."
runpodctl send ${POD_ID} "${SCRIPT_DIR}/setup-runpod-pod.sh" /tmp/setup-runpod-pod.sh

# Make script executable and run it
echo "🔧 Running setup on pod..."
runpodctl exec ${POD_ID} "chmod +x /tmp/setup-runpod-pod.sh && /tmp/setup-runpod-pod.sh"

echo "✅ Deployment complete!"
echo ""
echo "To connect to the pod and test:"
echo "runpodctl exec ${POD_ID} bash"
echo ""
echo "Pod details:"
runpodctl get pod ${POD_ID}