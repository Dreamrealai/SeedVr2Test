#!/bin/bash

# RunPod Deployment Script for SeedVR2

set -e

echo "🚀 Starting RunPod deployment for SeedVR2..."

# Configuration
PROJECT_NAME="seedvr2-handler"
DOCKER_REGISTRY="docker.io"
DOCKER_USERNAME="dreamrealai"
IMAGE_NAME="${DOCKER_USERNAME}/${PROJECT_NAME}"
IMAGE_TAG="latest"

# Navigate to runpod directory
cd "$(dirname "$0")/../runpod"

# Build Docker image
echo "📦 Building Docker image..."
docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .

# Push to Docker Hub (requires docker login)
echo "📤 Pushing image to Docker Hub..."
echo "Please ensure you're logged in to Docker Hub (docker login)"
docker push ${IMAGE_NAME}:${IMAGE_TAG}

# Create RunPod serverless endpoint
echo "🔧 Creating RunPod serverless endpoint..."

# Create endpoint configuration
cat > endpoint-config.json << EOF
{
  "name": "SeedVR2-3B-Handler",
  "dockerImage": "${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}",
  "gpuType": "H100 PCIe",
  "minWorkers": 0,
  "maxWorkers": 2,
  "scalerType": "QUEUE_DELAY",
  "scalerValue": 5,
  "containerDiskInGb": 50,
  "volumeInGb": 100,
  "volumeMountPath": "/models",
  "env": {
    "MODEL_PATH": "/models/seedvr2-3b",
    "PYTHONPATH": "/app/SeedVR:$PYTHONPATH"
  },
  "timeout": 3600,
  "idleTimeout": 60,
  "flashBoot": false
}
EOF

# Deploy using RunPod CLI
echo "🚀 Deploying to RunPod..."

# Create the serverless endpoint
ENDPOINT_RESPONSE=$(runpodctl create serverless \
  --name "SeedVR2-3B-Handler" \
  --dockerImage "${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}" \
  --gpuType "NVIDIA H100 80GB PCIe" \
  --minWorkers 0 \
  --maxWorkers 2 \
  --scalerType "QUEUE_DELAY" \
  --scalerValue 5 \
  --containerDiskInGb 50 \
  --volumeInGb 100 \
  --env MODEL_PATH=/models/seedvr2-3b \
  --env PYTHONPATH=/app/SeedVR:$PYTHONPATH \
  --timeout 3600 \
  --idleTimeout 60)

echo "$ENDPOINT_RESPONSE"

# Extract endpoint ID from response
ENDPOINT_ID=$(echo "$ENDPOINT_RESPONSE" | grep -oP 'endpoint_id":\s*"\K[^"]+' || echo "")

if [ -n "$ENDPOINT_ID" ]; then
    echo "✅ Endpoint created successfully!"
    echo "📝 Endpoint ID: $ENDPOINT_ID"
    echo ""
    echo "🔗 Endpoint URL: https://api.runpod.ai/v2/${ENDPOINT_ID}/runsync"
    echo ""
    echo "📋 Next steps:"
    echo "1. Update your .env file with:"
    echo "   RUNPOD_ENDPOINT_ID=${ENDPOINT_ID}"
    echo "   RUNPOD_API_KEY=${RUNPOD_API_KEY}"
    echo ""
    echo "2. The endpoint will take a few minutes to initialize and download the model"
    echo "3. Monitor the endpoint status in the RunPod dashboard"
else
    echo "❌ Failed to extract endpoint ID from response"
    echo "Please check the RunPod dashboard for the endpoint details"
fi

# Clean up
rm -f endpoint-config.json

echo "🎉 Deployment script completed!"