#!/bin/bash

# SeedVR2 Google Cloud Storage Setup Script
# This script helps you set up the necessary GCS bucket and credentials

set -e

echo "SeedVR2 GCS Setup"
echo "=================="
echo

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI is not installed."
    echo "Please install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo "Please authenticate with Google Cloud:"
    gcloud auth login
fi

# Get or set project ID
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)
if [ -z "$CURRENT_PROJECT" ]; then
    echo "No project is currently set."
    echo "Available projects:"
    gcloud projects list --format="table(projectId,name)"
    echo
    read -p "Enter your project ID: " PROJECT_ID
    gcloud config set project $PROJECT_ID
else
    echo "Current project: $CURRENT_PROJECT"
    read -p "Use this project? (y/n): " USE_CURRENT
    if [ "$USE_CURRENT" != "y" ]; then
        gcloud projects list --format="table(projectId,name)"
        echo
        read -p "Enter your project ID: " PROJECT_ID
        gcloud config set project $PROJECT_ID
    else
        PROJECT_ID=$CURRENT_PROJECT
    fi
fi

# Set bucket name
DEFAULT_BUCKET="seedvr2-videos-${PROJECT_ID}"
read -p "Enter bucket name (default: $DEFAULT_BUCKET): " BUCKET_NAME
BUCKET_NAME=${BUCKET_NAME:-$DEFAULT_BUCKET}

# Create bucket
echo
echo "Creating GCS bucket: $BUCKET_NAME"

# Check if bucket exists
if gsutil ls -b gs://$BUCKET_NAME &> /dev/null; then
    echo "Bucket $BUCKET_NAME already exists."
else
    # Ask for location
    echo "Choose a location for your bucket:"
    echo "1. US (multi-region)"
    echo "2. EU (multi-region)"
    echo "3. ASIA (multi-region)"
    echo "4. US-CENTRAL1"
    echo "5. US-EAST1"
    echo "6. EUROPE-WEST1"
    echo "7. ASIA-SOUTHEAST1"
    read -p "Enter your choice (1-7): " LOCATION_CHOICE
    
    case $LOCATION_CHOICE in
        1) LOCATION="US" ;;
        2) LOCATION="EU" ;;
        3) LOCATION="ASIA" ;;
        4) LOCATION="US-CENTRAL1" ;;
        5) LOCATION="US-EAST1" ;;
        6) LOCATION="EUROPE-WEST1" ;;
        7) LOCATION="ASIA-SOUTHEAST1" ;;
        *) LOCATION="US" ;;
    esac
    
    # Create bucket
    gsutil mb -l $LOCATION gs://$BUCKET_NAME
    echo "Bucket created successfully!"
fi

# Set bucket permissions for public read
echo
echo "Setting bucket permissions..."
gsutil iam ch allUsers:objectViewer gs://$BUCKET_NAME
echo "Bucket configured for public read access."

# Create folders
echo
echo "Creating bucket folders..."
gsutil -m cp -r /dev/null gs://$BUCKET_NAME/inputs/
gsutil -m cp -r /dev/null gs://$BUCKET_NAME/outputs/
echo "Folders created."

# Create service account
echo
echo "Creating service account for SeedVR2..."
SERVICE_ACCOUNT_NAME="seedvr2-service"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Check if service account exists
if gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL &> /dev/null; then
    echo "Service account already exists."
else
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
        --display-name="SeedVR2 Service Account" \
        --description="Service account for SeedVR2 video processing"
    echo "Service account created."
fi

# Grant necessary permissions
echo
echo "Granting permissions to service account..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/storage.admin" \
    --quiet

# Create and download key
echo
echo "Creating service account key..."
KEY_FILE="gcs-service-account-key.json"

if [ -f "$KEY_FILE" ]; then
    echo "Key file already exists: $KEY_FILE"
    read -p "Overwrite? (y/n): " OVERWRITE
    if [ "$OVERWRITE" != "y" ]; then
        echo "Using existing key file."
    else
        rm $KEY_FILE
        gcloud iam service-accounts keys create $KEY_FILE \
            --iam-account=$SERVICE_ACCOUNT_EMAIL
        echo "New key created: $KEY_FILE"
    fi
else
    gcloud iam service-accounts keys create $KEY_FILE \
        --iam-account=$SERVICE_ACCOUNT_EMAIL
    echo "Key created: $KEY_FILE"
fi

# Create .env file
echo
echo "Creating .env file..."
cat > backend/.env << EOF
# Google Cloud Storage
GCS_BUCKET_NAME=$BUCKET_NAME
GOOGLE_APPLICATION_CREDENTIALS=/app/gcs-key.json

# RunPod Configuration (update these with your actual values)
RUNPOD_API_KEY=your_runpod_api_key_here
RUNPOD_ENDPOINT_ID=your_runpod_endpoint_id_here
EOF

echo ".env file created in backend/"

# Display summary
echo
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo "Bucket Name: $BUCKET_NAME"
echo "Service Account: $SERVICE_ACCOUNT_EMAIL"
echo "Key File: $KEY_FILE"
echo
echo "Next steps:"
echo "1. Copy the key file to your backend: cp $KEY_FILE backend/"
echo "2. Update the RUNPOD_API_KEY and RUNPOD_ENDPOINT_ID in backend/.env"
echo "3. Deploy your backend with these environment variables"
echo
echo "For RunPod deployment, set this environment variable:"
echo "GCS_KEY_JSON='$(cat $KEY_FILE | jq -c .)'"
echo
