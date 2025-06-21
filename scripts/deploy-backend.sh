#!/bin/bash

# SeedVR2 Backend Deployment Script
# Deploy the FastAPI backend to various platforms

set -e

echo "SeedVR2 Backend Deployment"
echo "========================="
echo

# Check if backend directory exists
if [ ! -d "backend" ]; then
    echo "Error: backend directory not found."
    exit 1
fi

cd backend

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Error: backend/.env not found."
    echo "Please run scripts/setup-gcs.sh and scripts/deploy-runpod.sh first."
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

echo "Choose deployment platform:"
echo "1. Local (for testing)"
echo "2. Heroku"
echo "3. Google Cloud Run"
echo "4. Railway"
echo "5. Docker (custom deployment)"
read -p "Enter your choice (1-5): " DEPLOY_CHOICE

case $DEPLOY_CHOICE in
    1)
        echo
        echo "Starting local backend server..."
        echo "Installing dependencies..."
        pip install -r requirements.txt
        
        echo
        echo "Starting server on http://localhost:8000"
        echo "Press Ctrl+C to stop"
        python main.py
        ;;
        
    2)
        echo
        echo "Deploying to Heroku..."
        
        # Check if Heroku CLI is installed
        if ! command -v heroku &> /dev/null; then
            echo "Error: Heroku CLI not installed."
            echo "Install from: https://devcenter.heroku.com/articles/heroku-cli"
            exit 1
        fi
        
        # Create Procfile
        echo "web: uvicorn main:app --host 0.0.0.0 --port \$PORT" > Procfile
        
        # Create runtime.txt
        echo "python-3.10.13" > runtime.txt
        
        # Initialize git if needed
        if [ ! -d ".git" ]; then
            git init
            git add .
            git commit -m "Initial commit"
        fi
        
        # Create Heroku app
        read -p "Enter Heroku app name: " HEROKU_APP_NAME
        heroku create $HEROKU_APP_NAME || echo "App may already exist"
        
        # Set environment variables
        heroku config:set \
            RUNPOD_API_KEY=$RUNPOD_API_KEY \
            RUNPOD_ENDPOINT_ID=$RUNPOD_ENDPOINT_ID \
            GCS_BUCKET_NAME=$GCS_BUCKET_NAME \
            --app $HEROKU_APP_NAME
        
        # Set GCS credentials
        heroku config:set GCS_KEY_JSON="$(cat ../gcs-service-account-key.json | jq -c .)" \
            --app $HEROKU_APP_NAME
        
        # Deploy
        git push heroku main
        
        echo
        echo "Backend deployed to: https://$HEROKU_APP_NAME.herokuapp.com"
        ;;
        
    3)
        echo
        echo "Deploying to Google Cloud Run..."
        
        # Create Dockerfile for backend
        cat > Dockerfile << 'EOF'
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
EOF
        
        # Create .gcloudignore
        cat > .gcloudignore << 'EOF'
.gcloudignore
.git
.gitignore
__pycache__/
*.pyc
*.pyo
*.pyd
.env
gcs-service-account-key.json
EOF
        
        # Get project ID
        PROJECT_ID=$(gcloud config get-value project)
        SERVICE_NAME="seedvr2-backend"
        REGION="us-central1"
        
        echo "Building and deploying to Cloud Run..."
        echo "Service: $SERVICE_NAME"
        echo "Region: $REGION"
        echo
        
        # Build and deploy
        gcloud run deploy $SERVICE_NAME \
            --source . \
            --region $REGION \
            --platform managed \
            --allow-unauthenticated \
            --set-env-vars "RUNPOD_API_KEY=$RUNPOD_API_KEY,RUNPOD_ENDPOINT_ID=$RUNPOD_ENDPOINT_ID,GCS_BUCKET_NAME=$GCS_BUCKET_NAME" \
            --set-env-vars "GCS_KEY_JSON=$(cat ../gcs-service-account-key.json | jq -c .)" \
            --memory 2Gi \
            --cpu 2 \
            --timeout 3600 \
            --concurrency 1000 \
            --max-instances 10
        
        # Get service URL
        SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')
        echo
        echo "Backend deployed to: $SERVICE_URL"
        ;;
        
    4)
        echo
        echo "Deploying to Railway..."
        
        # Check if Railway CLI is installed
        if ! command -v railway &> /dev/null; then
            echo "Error: Railway CLI not installed."
            echo "Install from: https://docs.railway.app/develop/cli"
            exit 1
        fi
        
        # Create railway.json
        cat > railway.json << EOF
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "numReplicas": 1,
    "startCommand": "uvicorn main:app --host 0.0.0.0 --port \$PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
EOF
        
        # Initialize Railway project
        railway login
        railway init
        
        # Set environment variables
        railway variables set RUNPOD_API_KEY=$RUNPOD_API_KEY
        railway variables set RUNPOD_ENDPOINT_ID=$RUNPOD_ENDPOINT_ID
        railway variables set GCS_BUCKET_NAME=$GCS_BUCKET_NAME
        railway variables set GCS_KEY_JSON="$(cat ../gcs-service-account-key.json | jq -c .)"
        
        # Deploy
        railway up
        
        # Get deployment URL
        railway domain
        ;;
        
    5)
        echo
        echo "Creating Docker image for custom deployment..."
        
        # Create comprehensive Dockerfile
        cat > Dockerfile << 'EOF'
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
        
        # Create docker-compose.yml
        cat > docker-compose.yml << EOF
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - RUNPOD_API_KEY=${RUNPOD_API_KEY}
      - RUNPOD_ENDPOINT_ID=${RUNPOD_ENDPOINT_ID}
      - GCS_BUCKET_NAME=${GCS_BUCKET_NAME}
      - GCS_KEY_JSON=${GCS_KEY_JSON}
    volumes:
      - ../gcs-service-account-key.json:/app/gcs-key.json:ro
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
EOF
        
        echo "Docker files created!"
        echo
        echo "To build and run:"
        echo "  docker-compose up --build"
        echo
        echo "To deploy to a VPS or cloud VM:"
        echo "1. Copy the backend directory to your server"
        echo "2. Copy gcs-service-account-key.json to the parent directory"
        echo "3. Run: docker-compose up -d"
        ;;
esac

# Create deployment info file
cd ..
cat > DEPLOYMENT_INFO.md << EOF
# SeedVR2 Deployment Information

## Backend API
- Platform: $DEPLOY_CHOICE
- URL: [Update after deployment]

## RunPod Endpoint
- Endpoint ID: $RUNPOD_ENDPOINT_ID
- Model Size: [Update based on deployment]

## Google Cloud Storage
- Bucket: $GCS_BUCKET_NAME

## Frontend Configuration
Update the API_BASE_URL in script.js to point to your deployed backend.

## Testing the Setup
1. Check backend health: curl YOUR_BACKEND_URL/health
2. Wake up RunPod: curl -X POST YOUR_BACKEND_URL/wake-up
3. Upload a test video through the web interface

## Monitoring
- Backend logs: Check your platform's logging service
- RunPod status: https://www.runpod.io/console/serverless
- GCS usage: https://console.cloud.google.com/storage
EOF

echo
echo "========================================="
echo "Backend Deployment Instructions Complete!"
echo "========================================="
echo "Don't forget to:"
echo "1. Update the API_BASE_URL in frontend/script.js"
echo "2. Deploy the frontend to Netlify"
echo "3. Test the complete workflow"
echo
