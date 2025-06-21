#!/bin/bash
# Connect frontend to RunPod backend

echo "=== Connecting Frontend to RunPod Backend ==="

RUNPOD_URL="https://lh0wm9g482zr28-8888.proxy.runpod.net"

# Test RunPod connection
echo "Testing RunPod API at: $RUNPOD_URL"
if curl -s "$RUNPOD_URL/health" | grep -q "healthy"; then
    echo "✅ RunPod API is running!"
    
    # Update script.js
    echo "Updating frontend configuration..."
    sed -i.bak "s|const API_BASE_URL = '.*'|const API_BASE_URL = '$RUNPOD_URL'|" script.js
    
    # Also update the Netlify function to proxy to RunPod
    cat > netlify/functions/process.js << 'EOF'
const fetch = require('node-fetch');

exports.handler = async (event, context) => {
    const headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS'
    };

    if (event.httpMethod === 'OPTIONS') {
        return { statusCode: 200, headers, body: '' };
    }

    if (event.httpMethod !== 'POST') {
        return {
            statusCode: 405,
            headers,
            body: JSON.stringify({ error: 'Method not allowed' })
        };
    }

    try {
        const data = JSON.parse(event.body);
        
        // Forward to RunPod
        const response = await fetch('https://lh0wm9g482zr28-8888.proxy.runpod.net/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        return {
            statusCode: response.status,
            headers,
            body: JSON.stringify(result)
        };
    } catch (error) {
        return {
            statusCode: 500,
            headers,
            body: JSON.stringify({ error: error.message })
        };
    }
};
EOF

    # Commit and push changes
    git add -A
    git commit -m "Connect frontend to RunPod backend API

- Update API_BASE_URL to RunPod endpoint
- Add Netlify function to proxy RunPod requests
- Enable real video processing

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"
    git push origin main
    
    echo
    echo "✅ Frontend connected to RunPod!"
    echo "Your site will update automatically on Netlify."
    
else
    echo "❌ RunPod API is not responding"
    echo
    echo "Please follow these steps:"
    echo "1. Go to https://www.runpod.io/console/pods"
    echo "2. Open terminal for pod 'SeedVr2Test'"
    echo "3. Run the commands from RUNPOD_MANUAL_SETUP.md"
    echo "4. Make sure port 8888 is exposed in pod settings"
    echo "5. Run this script again"
fi