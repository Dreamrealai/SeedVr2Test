// SeedVR2 Web Interface - CORS Fixed Version
const API_BASE_URL = 'https://lh0wm9g482zr28-8080.proxy.runpod.net';

// Add these headers to all fetch requests
const fetchOptions = {
    mode: 'cors',
    credentials: 'omit', // Don't send credentials
    headers: {
        'Content-Type': 'application/json',
    }
};

// Modified checkServerStatus function
async function checkServerStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`, {
            method: 'GET',
            mode: 'cors',
            credentials: 'omit',
            headers: {
                'Accept': 'application/json',
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.status === 'healthy' || data.runpod_status?.status === 'healthy') {
            updateStatus('online', 'Server online');
            wakeUpButton.style.display = 'none';
        } else {
            updateStatus('offline', 'Server sleeping');
            wakeUpButton.style.display = 'inline-block';
        }
    } catch (error) {
        console.error('Server check error:', error);
        updateStatus('offline', 'Server unreachable');
        wakeUpButton.style.display = 'inline-block';
    }
}

// Modified wakeUpServer function
async function wakeUpServer() {
    try {
        wakeUpButton.disabled = true;
        wakeUpButton.textContent = 'Waking up...';
        
        const response = await fetch(`${API_BASE_URL}/wake-up`, {
            method: 'POST',
            mode: 'cors',
            credentials: 'omit',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            body: JSON.stringify({})
        });
        
        if (response.ok) {
            showMessage('Server is waking up. This may take a minute...', 'info');
            setTimeout(checkServerStatus, 5000);
        }
    } catch (error) {
        console.error('Wake up error:', error);
        showMessage('Failed to wake up server', 'error');
    } finally {
        wakeUpButton.disabled = false;
        wakeUpButton.textContent = 'Wake Up Server';
    }
}

// Modified uploadVideo function
async function uploadVideo(file, resH, resW, seed) {
    const formData = new FormData();
    formData.append('video', file);
    formData.append('res_h', resH);
    formData.append('res_w', resW);
    formData.append('seed', seed);
    
    try {
        const response = await fetch(`${API_BASE_URL}/upload`, {
            method: 'POST',
            mode: 'cors',
            credentials: 'omit',
            body: formData
            // Don't set Content-Type header for FormData
        });
        
        if (!response.ok) {
            throw new Error(`Upload failed: ${response.statusText}`);
        }
        
        const data = await response.json();
        showMessage('Demo mode: Using sample video for processing', 'info');
        return data;
    } catch (error) {
        console.error('Upload error:', error);
        throw error;
    }
}

// Modified pollJobStatus function
async function pollJobStatus(jobId) {
    let attempts = 0;
    const maxAttempts = 120;
    
    while (attempts < maxAttempts) {
        try {
            const response = await fetch(`${API_BASE_URL}/status/${jobId}`, {
                method: 'GET',
                mode: 'cors',
                credentials: 'omit',
                headers: {
                    'Accept': 'application/json',
                }
            });
            
            if (!response.ok) {
                throw new Error(`Status check failed: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.status === 'completed') {
                return data;
            } else if (data.status === 'failed') {
                throw new Error(data.error || 'Processing failed');
            }
            
            const progress = 20 + (attempts / maxAttempts) * 70;
            updateProgress(progress, data.message || 'Processing video...');
            
            await new Promise(resolve => setTimeout(resolve, 5000));
            attempts++;
        } catch (error) {
            console.error('Status check error:', error);
            throw error;
        }
    }
    
    throw new Error('Processing timeout');
}

// Add this to test CORS immediately when page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('Testing CORS connection to:', API_BASE_URL);
    
    // Test with a simple fetch
    fetch(`${API_BASE_URL}/health`, {
        method: 'GET',
        mode: 'cors',
        credentials: 'omit'
    })
    .then(response => {
        console.log('CORS test response:', response);
        if (response.ok) {
            console.log('✅ CORS is working!');
        } else {
            console.log('❌ CORS failed with status:', response.status);
        }
        return response.json();
    })
    .then(data => {
        console.log('Server response:', data);
    })
    .catch(error => {
        console.error('❌ CORS test failed:', error);
    });
});

// Copy all other functions from original script.js below this line...
// (DOM elements, event listeners, etc.)