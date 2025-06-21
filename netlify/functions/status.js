// Job status tracking
const jobs = new Map();

// Store job in memory (in production, use a database)
global.jobStore = global.jobStore || jobs;

exports.handler = async (event, context) => {
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'GET, OPTIONS'
  };

  if (event.httpMethod === 'OPTIONS') {
    return { statusCode: 200, headers, body: '' };
  }

  if (event.httpMethod !== 'GET') {
    return {
      statusCode: 405,
      headers,
      body: JSON.stringify({ error: 'Method not allowed' })
    };
  }

  // Extract job ID from path
  const pathParts = event.path.split('/');
  const jobId = pathParts[pathParts.length - 1];

  if (!jobId) {
    return {
      statusCode: 400,
      headers,
      body: JSON.stringify({ error: 'Job ID required' })
    };
  }

  // For demo purposes, always return completed after 10 seconds
  const demoJobAge = Date.now() - (parseInt(jobId, 36) || Date.now());
  
  if (demoJobAge > 10000) {
    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({
        status: 'completed',
        result_url: 'https://storage.googleapis.com/seedvr2-videos/samples/demo_output.mp4',
        message: 'Processing completed successfully'
      })
    };
  } else {
    const progress = Math.min(90, (demoJobAge / 10000) * 90);
    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({
        status: 'processing',
        progress: progress,
        message: `Processing video... ${Math.round(progress)}%`
      })
    };
  }
};