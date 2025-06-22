// SeedVR2 Web Interface
const API_BASE_URL = 'https://ussvh2i624ql0g-8080.proxy.runpod.net'; // Using RunPod Backend
const RUNPOD_API_KEY = 'rpa_UFDTAAMZ19E9WYJNTIPAMY4UG6DHWYZCO12RO6EUsi2hmd';
const RUNPOD_ENDPOINT = 'https://api.runpod.ai/v2/lh0wm9g482zr28';

// DOM Elements
let uploadArea, videoFile, uploadButton, statusIndicator, statusDot, statusText;
let wakeUpButton, fileInfo, fileName, fileSize, removeFile;
let progressSection, progressFill, progressText, statusMessages;
let resultSection, downloadBrowser, downloadGCS, videoPlayer;
let resolutionSelect, seedInput;

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    initializeElements();
    initializeEventListeners();
    checkServerStatus();
    
    // Check server status every 30 seconds
    setInterval(checkServerStatus, 30000);
});

function initializeElements() {
    // Upload elements
    uploadArea = document.getElementById('uploadArea');
    videoFile = document.getElementById('videoFile');
    uploadButton = document.getElementById('uploadButton');
    
    // Status elements
    statusIndicator = document.getElementById('statusIndicator');
    statusDot = document.getElementById('statusDot');
    statusText = document.getElementById('statusText');
    wakeUpButton = document.getElementById('wakeUpButton');
    
    // File info elements
    fileInfo = document.getElementById('fileInfo');
    fileName = document.getElementById('fileName');
    fileSize = document.getElementById('fileSize');
    removeFile = document.getElementById('removeFile');
    
    // Progress elements
    progressSection = document.getElementById('progressSection');
    progressFill = document.getElementById('progressFill');
    progressText = document.getElementById('progressText');
    statusMessages = document.getElementById('statusMessages');
    
    // Result elements
    resultSection = document.getElementById('result');
    downloadBrowser = document.getElementById('downloadBrowser');
    downloadGCS = document.getElementById('downloadGCS');
    videoPlayer = document.getElementById('videoPlayer');
    
    // Settings elements
    resolutionSelect = document.getElementById('resolution');
    seedInput = document.getElementById('seed');
}

function initializeEventListeners() {
    // Upload area events
    uploadArea.addEventListener('click', () => videoFile.click());
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('drop', handleDrop);
    
    // File input change
    videoFile.addEventListener('change', handleFileSelect);
    
    // Remove file button
    removeFile.addEventListener('click', clearSelectedFile);
    
    // Upload button
    uploadButton.addEventListener('click', handleUpload);
    
    // Wake up button
    wakeUpButton.addEventListener('click', wakeUpServer);
}

function handleDragOver(e) {
    e.preventDefault();
    uploadArea.classList.add('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    uploadArea.classList.remove('drag-over');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        videoFile.files = files;
        handleFileSelect();
    }
}

function handleFileSelect() {
    const file = videoFile.files[0];
    if (!file) return;
    
    // Validate file type
    const validTypes = ['video/mp4', 'video/avi', 'video/quicktime', 'video/x-matroska', 'video/webm'];
    if (!validTypes.includes(file.type) && !file.name.match(/\.(mp4|avi|mov|mkv|webm)$/i)) {
        showMessage('Please select a valid video file (MP4, AVI, MOV, MKV, WebM)', 'error');
        return;
    }
    
    // Validate file size (500MB)
    if (file.size > 500 * 1024 * 1024) {
        showMessage('File size must be less than 500MB', 'error');
        return;
    }
    
    // Show file info
    fileName.textContent = file.name;
    fileSize.textContent = formatFileSize(file.size);
    uploadArea.style.display = 'none';
    fileInfo.style.display = 'flex';
    uploadButton.disabled = false;
}

function clearSelectedFile() {
    videoFile.value = '';
    uploadArea.style.display = 'flex';
    fileInfo.style.display = 'none';
    uploadButton.disabled = true;
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

async function checkServerStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        
        if (data.runpod_status?.status === 'healthy') {
            updateStatus('online', 'Server online');
            wakeUpButton.style.display = 'none';
        } else {
            updateStatus('offline', 'Server sleeping');
            wakeUpButton.style.display = 'inline-block';
        }
    } catch (error) {
        updateStatus('offline', 'Server unreachable');
        wakeUpButton.style.display = 'inline-block';
    }
}

async function wakeUpServer() {
    try {
        wakeUpButton.disabled = true;
        wakeUpButton.textContent = 'Waking up...';
        
        const response = await fetch(`${API_BASE_URL}/wake-up`, {
            method: 'POST'
        });
        
        if (response.ok) {
            showMessage('Server is waking up. This may take a minute...', 'info');
            setTimeout(checkServerStatus, 5000);
        }
    } catch (error) {
        showMessage('Failed to wake up server', 'error');
    } finally {
        wakeUpButton.disabled = false;
        wakeUpButton.textContent = 'Wake Up Server';
    }
}

function updateStatus(status, text) {
    statusDot.className = `status-dot ${status}`;
    statusText.textContent = text;
}

async function handleUpload() {
    const file = videoFile.files[0];
    if (!file) return;
    
    // Get settings
    const [resH, resW] = resolutionSelect.value.split('x').map(Number);
    const seed = seedInput.value || Math.floor(Math.random() * 2147483647);
    
    // Disable upload button
    uploadButton.disabled = true;
    uploadButton.querySelector('.btn-text').style.display = 'none';
    uploadButton.querySelector('.loading-spinner').style.display = 'block';
    
    // Show progress
    progressSection.style.display = 'block';
    resultSection.style.display = 'none';
    clearMessages();
    
    try {
        // Upload file
        updateProgress(0, 'Uploading video...');
        const jobData = await uploadVideo(file, resH, resW, seed);
        
        // Poll for status
        updateProgress(20, 'Processing video...');
        const result = await pollJobStatus(jobData.job_id);
        
        // Show result
        updateProgress(100, 'Complete!');
        showResult(result);
        
    } catch (error) {
        showMessage(`Error: ${error.message}`, 'error');
        console.error('Upload error:', error);
    } finally {
        uploadButton.disabled = false;
        uploadButton.querySelector('.btn-text').style.display = 'block';
        uploadButton.querySelector('.loading-spinner').style.display = 'none';
    }
}

async function uploadVideo(file, resH, resW, seed) {
    const formData = new FormData();
    formData.append('video', file);
    formData.append('res_h', resH);
    formData.append('res_w', resW);
    formData.append('seed', seed);
    
    // For now, use the mock API endpoint
    // In production, this would upload to the real backend
    try {
        const response = await fetch(`${API_BASE_URL}/upload`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Upload failed: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // For demo, also show a message
        showMessage('Demo mode: Using sample video for processing', 'info');
        
        return data;
    } catch (error) {
        console.error('Upload error:', error);
        throw error;
    }
}

async function pollJobStatus(jobId) {
    let attempts = 0;
    const maxAttempts = 120; // 10 minutes max
    
    while (attempts < maxAttempts) {
        const response = await fetch(`${API_BASE_URL}/status/${jobId}`);
        const data = await response.json();
        
        if (data.status === 'completed') {
            return data;
        } else if (data.status === 'failed') {
            throw new Error(data.error || 'Processing failed');
        }
        
        // Update progress (20-90%)
        const progress = 20 + (attempts / maxAttempts) * 70;
        updateProgress(progress, data.message || 'Processing video...');
        
        // Wait before next poll
        await new Promise(resolve => setTimeout(resolve, 5000)); // 5 seconds
        attempts++;
    }
    
    throw new Error('Processing timeout');
}

function updateProgress(percent, text) {
    progressFill.style.width = `${percent}%`;
    progressText.textContent = text;
}

function showResult(result) {
    resultSection.style.display = 'block';
    progressSection.style.display = 'none';
    
    // Set video source
    videoPlayer.src = result.result_url;
    
    // Set download buttons
    downloadBrowser.onclick = () => {
        const a = document.createElement('a');
        a.href = result.result_url;
        a.download = 'seedvr2_output.mp4';
        a.click();
    };
    
    downloadGCS.onclick = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/download-from-gcs`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url: result.result_url })
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'seedvr2_output.mp4';
                a.click();
                window.URL.revokeObjectURL(url);
            }
        } catch (error) {
            showMessage('Download failed', 'error');
        }
    };
    
    showMessage('Video processing complete!', 'success');
}

function showMessage(text, type = 'info') {
    const message = document.createElement('div');
    message.className = `status-message ${type}`;
    message.textContent = text;
    statusMessages.appendChild(message);
    
    // Auto-remove after 5 seconds
    setTimeout(() => message.remove(), 5000);
}

function clearMessages() {
    statusMessages.innerHTML = '';
}