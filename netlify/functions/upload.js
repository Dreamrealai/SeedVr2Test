const fetch = require('node-fetch');
const FormData = require('form-data');
const { Storage } = require('@google-cloud/storage');

// Initialize GCS
const storage = new Storage({
    projectId: 'fine-blueprint-455512-k4',
    keyFilename: process.env.GCS_KEY_PATH || './gcs-service-account-key.json'
});
const bucket = storage.bucket('seedvr2-videos');

exports.handler = async (event, context) => {
    if (event.httpMethod !== 'POST') {
        return {
            statusCode: 405,
            body: JSON.stringify({ error: 'Method not allowed' })
        };
    }

    try {
        // Parse multipart form data
        const boundary = event.headers['content-type'].split('boundary=')[1];
        const body = Buffer.from(event.body, 'base64');
        
        // Extract file data (simplified - in production use a proper multipart parser)
        const parts = body.toString().split(`--${boundary}`);
        let fileData = null;
        let fileName = 'video.mp4';
        
        for (const part of parts) {
            if (part.includes('Content-Disposition: form-data') && part.includes('filename=')) {
                const filenameMatch = part.match(/filename="(.+?)"/);
                if (filenameMatch) fileName = filenameMatch[1];
                
                const dataStart = part.indexOf('\r\n\r\n') + 4;
                const dataEnd = part.lastIndexOf('\r\n');
                fileData = Buffer.from(part.substring(dataStart, dataEnd), 'binary');
                break;
            }
        }

        if (!fileData) {
            return {
                statusCode: 400,
                body: JSON.stringify({ error: 'No file uploaded' })
            };
        }

        // Upload to GCS
        const timestamp = new Date().getTime();
        const gcsFileName = `uploads/${timestamp}_${fileName}`;
        const file = bucket.file(gcsFileName);
        
        await file.save(fileData, {
            metadata: {
                contentType: 'video/mp4'
            }
        });
        
        // Make file public
        await file.makePublic();
        const publicUrl = `https://storage.googleapis.com/seedvr2-videos/${gcsFileName}`;

        // Submit to RunPod
        const runpodResponse = await fetch(`https://api.runpod.ai/v2/${process.env.RUNPOD_POD_ID}/run`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${process.env.RUNPOD_API_KEY}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                input: {
                    video_url: publicUrl,
                    res_h: 720,
                    res_w: 1280,
                    seed: 42
                }
            })
        });

        const runpodData = await runpodResponse.json();

        return {
            statusCode: 200,
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            body: JSON.stringify({
                status: 'processing',
                jobId: runpodData.id,
                inputUrl: publicUrl
            })
        };

    } catch (error) {
        console.error('Upload error:', error);
        return {
            statusCode: 500,
            body: JSON.stringify({ error: error.message })
        };
    }
};