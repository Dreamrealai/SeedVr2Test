// Simple API configuration for frontend
const API_CONFIG = {
    // Backend API URL - will be updated after deployment
    BACKEND_URL: "https://seedvr2-backend.netlify.app/.netlify/functions",
    
    // RunPod configuration
    RUNPOD_API_KEY: "rpa_UFDTAAMZ19E9WYJNTIPAMY4UG6DHWYZCO12RO6EUsi2hmd",
    RUNPOD_POD_ID: "lh0wm9g482zr28",
    
    // GCS configuration
    GCS_BUCKET: "seedvr2-videos",
    
    // API endpoints
    endpoints: {
        upload: "/upload",
        status: "/status",
        download: "/download"
    }
};

// Export for use in script.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = API_CONFIG;
}