#!/bin/bash

# Check SeedVR2 deployment status
echo "🔍 Checking SeedVR2 Deployment Status..."
echo "========================================"

export RUNPOD_API_KEY="rpa_UFDTAAMZ19E9WYJNTIPAMY4UG6DHWYZCO12RO6EUsi2hmd"

# Get pod info
POD_INFO=$(runpod pod list --json 2>/dev/null | python3 -c "
import json
import sys

try:
    pods = json.load(sys.stdin)
    for pod in pods:
        if pod.get('desiredStatus') == 'RUNNING':
            gpu = pod.get('machineDisplayName', 'Unknown')
            name = pod.get('name', 'Unknown')
            pod_id = pod.get('id', 'Unknown')
            
            # Get IP if available
            ip = 'Not available'
            if 'ipAddress' in pod:
                ip = pod['ipAddress']
            
            print(f'Pod: {name}')
            print(f'ID: {pod_id}')
            print(f'GPU: {gpu}')
            print(f'IP: {ip}')
            print(f'Status: RUNNING')
            break
except Exception as e:
    print(f'Error: {e}')
")

echo "$POD_INFO"
echo ""
echo "📌 Access your SeedVR2 server at:"
echo "   http://<pod-ip>:8000"
echo ""
echo "📁 Web UI available at:"
echo "   http://<pod-ip>:8000/seedvr2_web_ui.html"
echo ""
echo "🔧 To check server logs:"
echo "   runpod logs <pod-id>"
