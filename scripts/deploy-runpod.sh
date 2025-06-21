#!/bin/bash

# SeedVR2 RunPod Deployment Script
# This script helps you deploy the SeedVR2 handler to RunPod

set -e

echo "SeedVR2 RunPod Deployment"
echo "========================="
echo

# Check if runpodctl is installed
if ! command -v runpodctl &> /dev/null; then
    echo "Error: runpodctl is not installed."
    echo "Install it with: brew install runpod/runpodctl/runpodctl (macOS)"
    echo "Or: wget -qO- cli.runpod.net | sudo bash (Linux)"
    exit 1
fi

# Check RunPod API key
if [ -z "$RUNPOD_API_KEY" ]; then
    echo "RUNPOD_API_KEY not set."
    read -p "Enter your RunPod API key: " RUNPOD_API_KEY
    export RUNPOD_API_KEY
fi

# Configure runpodctl
echo "Configuring runpodctl..."
runpodctl config --apiKey $RUNPOD_API_KEY

# Check if GCS key exists
if [ ! -f "gcs-service-account-key.json" ]; then
    echo "Error: gcs-service-account-key.json not found."
    echo "Please run scripts/setup-gcs.sh first."
    exit 1
fi

# Get GCS key as JSON string
GCS_KEY_JSON=$(cat gcs-service-account-key.json | jq -c .)

# Docker image configuration
echo
echo "Docker Image Configuration"
echo "========================="
echo "Choose model size to deploy:"
echo "1. 3B model (recommended for most use cases)"
echo "2. 7B model (better quality, requires more GPU)"
read -p "Enter your choice (1-2): " MODEL_CHOICE

case $MODEL_CHOICE in
    1) MODEL_SIZE="3b" ;;
    2) MODEL_SIZE="7b" ;;
    *) MODEL_SIZE="3b" ;;
esac

# Set Docker image name
DOCKER_IMAGE="dreamrealai/seedvr2:${MODEL_SIZE}-latest"

echo
echo "Building Docker image..."
echo "This may take a while on first build..."

# Build Docker image
cd runpod
docker build \
    --build-arg MODEL_SIZE=$MODEL_SIZE \
    -t $DOCKER_IMAGE \
    -f Dockerfile .

echo
echo "Docker image built successfully!"

# Push to Docker Hub (optional)
echo
read -p "Push image to Docker Hub? (requires docker login) (y/n): " PUSH_IMAGE
if [ "$PUSH_IMAGE" = "y" ]; then
    docker push $DOCKER_IMAGE
    echo "Image pushed to Docker Hub"
fi

# Create RunPod template
echo
echo "Creating RunPod serverless template..."

# Generate template JSON
cat > runpod-template.json << EOF
{
  "name": "SeedVR2-${MODEL_SIZE^^}",
  "imageName": "$DOCKER_IMAGE",
  "dockerArgs": "",
  "containerDiskInGb": 50,
  "volumeInGb": 100,
  "volumeMountPath": "/workspace",
  "env": [
    {
      "key": "MODEL_SIZE",
      "value": "$MODEL_SIZE"
    },
    {
      "key": "GCS_KEY_JSON",
      "value": "$GCS_KEY_JSON"
    },
    {
      "key": "GCS_BUCKET_NAME",
      "value": "${GCS_BUCKET_NAME:-seedvr2-videos}"
    }
  ],
  "serverless": {
    "scalerType": "QUEUE_DEPTH",
    "scalerValue": 1,
    "scalingConfig": {
      "minWorkers": 0,
      "maxWorkers": 3
    }
  },
  "machineType": "GPU",
  "gpuType": "H100",
  "minMemoryInGb": 80,
  "minVcpuCount": 16
}
EOF

echo "Template created: runpod-template.json"

# Create endpoint
echo
echo "Creating RunPod endpoint..."
echo "This will create a serverless endpoint with:"
echo "- Model: SeedVR2-${MODEL_SIZE^^}"
echo "- GPU: H100 (80GB)"
echo "- Auto-scaling: 0-3 workers"
echo

read -p "Continue? (y/n): " CREATE_ENDPOINT
if [ "$CREATE_ENDPOINT" = "y" ]; then
    # Note: RunPod CLI doesn't directly support creating serverless endpoints
    # You'll need to use the web UI or API
    echo
    echo "Please complete the setup in the RunPod web console:"
    echo "1. Go to https://www.runpod.io/console/serverless"
    echo "2. Click 'New Endpoint'"
    echo "3. Select 'Custom' template"
    echo "4. Use these settings:"
    echo "   - Container Image: $DOCKER_IMAGE"
    echo "   - Container Disk: 50 GB"
    echo "   - Volume Size: 100 GB"
    echo "   - GPU Type: H100 PCIe"
    echo "   - Min Workers: 0"
    echo "   - Max Workers: 3"
    echo "5. Add these environment variables:"
    echo "   - MODEL_SIZE=$MODEL_SIZE"
    echo "   - GCS_BUCKET_NAME=${GCS_BUCKET_NAME:-seedvr2-videos}"
    echo "   - GCS_KEY_JSON='$GCS_KEY_JSON'"
    echo
    echo "After creating the endpoint, copy the Endpoint ID and API Key"
fi

# Update backend .env
echo
echo "Updating backend configuration..."
read -p "Enter your RunPod Endpoint ID: " RUNPOD_ENDPOINT_ID

if [ -f "backend/.env" ]; then
    # Update existing .env
    sed -i.bak "s/RUNPOD_API_KEY=.*/RUNPOD_API_KEY=$RUNPOD_API_KEY/" backend/.env
    sed -i.bak "s/RUNPOD_ENDPOINT_ID=.*/RUNPOD_ENDPOINT_ID=$RUNPOD_ENDPOINT_ID/" backend/.env
else
    # Create new .env
    cat > backend/.env << EOF
# Google Cloud Storage
GCS_BUCKET_NAME=${GCS_BUCKET_NAME:-seedvr2-videos}
GOOGLE_APPLICATION_CREDENTIALS=/app/gcs-key.json

# RunPod Configuration
RUNPOD_API_KEY=$RUNPOD_API_KEY
RUNPOD_ENDPOINT_ID=$RUNPOD_ENDPOINT_ID
EOF
fi

echo
echo "========================================="
echo "Deployment Configuration Complete!"
echo "========================================="
echo "Docker Image: $DOCKER_IMAGE"
echo "Model Size: ${MODEL_SIZE^^}"
echo "Endpoint ID: $RUNPOD_ENDPOINT_ID"
echo
echo "Next steps:"
echo "1. Deploy the backend API (see deploy-backend.sh)"
echo "2. Update the frontend API_BASE_URL in script.js"
echo "3. Deploy to Netlify"
echo
echo "To test the endpoint:"
echo "curl -X POST https://api.runpod.ai/v2/$RUNPOD_ENDPOINT_ID/run \\"
echo "  -H 'Authorization: Bearer $RUNPOD_API_KEY' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"input\": {\"wake_up\": true}}'"
echo
