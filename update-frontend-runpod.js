// Update script.js with the RunPod endpoint

const RUNPOD_POD_ID = "lh0wm9g482zr28";
const RUNPOD_PORT = "8888";
const RUNPOD_API_URL = `https://${RUNPOD_POD_ID}-${RUNPOD_PORT}.proxy.runpod.net`;

console.log("RunPod API URL:", RUNPOD_API_URL);

// After you've set up the API on RunPod and exposed port 8888,
// update line 2 in script.js to:
// const API_BASE_URL = 'https://lh0wm9g482zr28-8888.proxy.runpod.net';

// Test the connection:
fetch(`${RUNPOD_API_URL}/health`)
  .then(res => res.json())
  .then(data => console.log("RunPod API Status:", data))
  .catch(err => console.error("RunPod API Error:", err));