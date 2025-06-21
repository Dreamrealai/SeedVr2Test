// Netlify Functions API for SeedVR2
const https = require('https');

// Store jobs in memory (in production, use a database)
const jobs = new Map();

exports.handler = async (event, context) => {
    const path = event.path.replace('/.netlify/functions/api', '');
    
    // CORS headers
    const headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
    };

    // Handle OPTIONS
    if (event.httpMethod === 'OPTIONS') {
        return { statusCode: 200, headers, body: '' };
    }

    try {
        // Health check
        if (path === '/health' && event.httpMethod === 'GET') {
            return {
                statusCode: 200,
                headers,
                body: JSON.stringify({
                    status: 'healthy',
                    runpod_status: { status: 'healthy' }
                })
            };
        }

        // Wake up server (mock)
        if (path === '/wake-up' && event.httpMethod === 'POST') {
            return {
                statusCode: 200,
                headers,
                body: JSON.stringify({
                    status: 'success',
                    message: 'Server is awake'
                })
            };
        }

        // Upload endpoint - redirect to dedicated function
        if (path === '/upload' && event.httpMethod === 'POST') {
            // The actual upload is handled by upload.js
            // For the api.js endpoint, return a mock response
            const jobId = Date.now().toString(36);
            
            return {
                statusCode: 200,
                headers,
                body: JSON.stringify({
                    status: 'processing',
                    job_id: jobId,
                    message: 'Upload successful, processing started'
                })
            };
        }

        // Status endpoint
        if (path.startsWith('/status/') && event.httpMethod === 'GET') {
            const jobId = path.split('/')[2];
            const job = jobs.get(jobId);
            
            if (!job) {
                return {
                    statusCode: 404,
                    headers,
                    body: JSON.stringify({ error: 'Job not found' })
                };
            }
            
            return {
                statusCode: 200,
                headers,
                body: JSON.stringify(job)
            };
        }

        // Download from GCS
        if (path === '/download-from-gcs' && event.httpMethod === 'POST') {
            const { url } = JSON.parse(event.body);
            
            // In production, this would proxy the download
            return {
                statusCode: 302,
                headers: {
                    ...headers,
                    'Location': url
                },
                body: ''
            };
        }

        // 404 for unknown paths
        return {
            statusCode: 404,
            headers,
            body: JSON.stringify({ error: 'Not found' })
        };

    } catch (error) {
        return {
            statusCode: 500,
            headers,
            body: JSON.stringify({ error: error.message })
        };
    }
};