#!/usr/bin/env python3
"""
Deploy SeedVR2 to RunPod Serverless
"""
import os
import json
import requests
from datetime import datetime

# Configuration
RUNPOD_API_KEY = "rpa_UFDTAAMZ19E9WYJNTIPAMY4UG6DHWYZCO12RO6EUsi2hmd"
API_BASE = "https://api.runpod.io/v2"

# Read GCS key
with open("gcs-service-account-key.json", "r") as f:
    gcs_key = json.load(f)

# Create serverless endpoint configuration
endpoint_config = {
    "name": f"seedvr2-endpoint-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
    "templateId": "runpod-worker-v1-default",  # Use default worker template
    "gpuIds": ["NVIDIA H100 PCIe"],  # Use H100
    "networkVolumeId": None,
    "locations": ["US"],
    "idleTimeout": 5,  # 5 seconds idle timeout
    "scalerType": "REQUEST_COUNT",
    "scalerValue": 1,
    "workersMin": 0,
    "workersMax": 1,
    "dockerArgs": "",
    "containerDiskInGb": 50,
    "env": [
        {"key": "GCS_BUCKET_NAME", "value": "seedvr2-videos"},
        {"key": "GCS_KEY_JSON", "value": json.dumps(gcs_key)},
        {"key": "MODEL_SIZE", "value": "3b"}
    ]
}

# Create endpoint
headers = {
    "Authorization": f"Bearer {RUNPOD_API_KEY}",
    "Content-Type": "application/json"
}

print("Creating RunPod serverless endpoint...")
response = requests.post(
    f"{API_BASE}/serverless",
    headers=headers,
    json=endpoint_config
)

if response.status_code == 200:
    result = response.json()
    endpoint_id = result.get("id")
    print(f"✅ Endpoint created successfully!")
    print(f"Endpoint ID: {endpoint_id}")
    print(f"Endpoint URL: https://api.runpod.ai/v2/{endpoint_id}/run")
    
    # Update frontend configuration
    print("\nUpdating frontend configuration...")
    with open("update-frontend-config.js", "w") as f:
        f.write(f"const RUNPOD_ENDPOINT_ID = '{endpoint_id}';\n")
        f.write(f"const RUNPOD_API_KEY = '{RUNPOD_API_KEY}';\n")
        f.write(f"console.log('RunPod endpoint configured: ' + RUNPOD_ENDPOINT_ID);\n")
    
else:
    print(f"❌ Failed to create endpoint: {response.status_code}")
    print(response.text)