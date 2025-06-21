document.addEventListener('DOMContentLoaded', () => {
    const videoFileInput = document.getElementById('videoFile');
    const uploadButton = document.getElementById('uploadButton');
    const statusMessage = document.getElementById('statusMessage');
    const resultDiv = document.getElementById('result');
    const downloadLink = document.getElementById('downloadLink');
    const videoPlayer = document.getElementById('videoPlayer');

    uploadButton.addEventListener('click', async () => {
        const file = videoFileInput.files[0];

        if (!file) {
            alert('Please select a video file first.');
            return;
        }

        statusMessage.textContent = 'Uploading and processing...';
        resultDiv.style.display = 'none';
        videoPlayer.style.display = 'none';

        // Placeholder for Runpod API interaction
        // You will need to replace this with actual API call logic
        try {
            const processedVideoUrl = await uploadAndProcessVideo(file);

            if (processedVideoUrl) {
                statusMessage.textContent = 'Processing complete!';
                downloadLink.href = processedVideoUrl;
                videoPlayer.src = processedVideoUrl;
                resultDiv.style.display = 'block';
                videoPlayer.style.display = 'block';
            } else {
                statusMessage.textContent = 'Processing failed. Check console for details.';
                alert('Video processing failed. The backend did not return a valid video URL.');
            }
        } catch (error) {
            console.error('Error during video processing:', error);
            statusMessage.textContent = `Error: ${error.message}`;
            alert(`An error occurred: ${error.message}`);
        }
    });

    async function uploadAndProcessVideo(videoFile) {
        // #####################################################################
        // #  IMPORTANT: Replace this section with your Runpod API integration #
        // #####################################################################

        // 1. Get your Runpod API Endpoint URL.
        //    This will likely be a serverless endpoint you set up on Runpod
        //    that points to a running instance of the SeedVR2 backend or a
        //    custom handler.
        const RUNPOD_API_ENDPOINT = 'YOUR_RUNPOD_API_ENDPOINT_HERE';

        if (RUNPOD_API_ENDPOINT === 'YOUR_RUNPOD_API_ENDPOINT_HERE') {
            alert("Please configure the RUNPOD_API_ENDPOINT in script.js");
            throw new Error("Runpod API endpoint not configured.");
        }

        const formData = new FormData();
        formData.append('video', videoFile); // The backend might expect a different key, e.g., 'file' or 'video_file'

        try {
            console.log(`Uploading ${videoFile.name} to ${RUNPOD_API_ENDPOINT}`);

            // Example: Using fetch to send the video
            // You might need to adjust headers, method, and body structure
            // based on how your Runpod endpoint is configured.
            const response = await fetch(RUNPOD_API_ENDPOINT, {
                method: 'POST',
                body: formData,
                // Add any necessary headers, e.g., Authorization if your endpoint is secured
                // headers: {
                //   'Authorization': 'Bearer YOUR_API_KEY',
                // },
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`API request failed with status ${response.status}: ${errorText}`);
            }

            const result = await response.json(); // Assuming the API returns JSON

            // Log the full response for debugging
            console.log("API Response:", result);

            // The SeedVR2 backend might return a job ID first, and you'd need to poll for status.
            // Or it might directly return the URL of the processed video if the operation is quick.
            // For this basic example, we'll assume it directly returns an object
            // with a `processed_video_url` or similar key.
            // Adjust `result.processed_video_url` based on the actual response structure.
            if (result && result.processed_video_url) {
                return result.processed_video_url;
            } else if (result && result.output && result.output.video_url) { // Alternative structure
                 return result.output.video_url;
            } else if (result && result.url) { // Another alternative
                 return result.url;
            }
            else {
                console.error("Unexpected API response structure:", result);
                throw new Error('API did not return a valid processed video URL.');
            }

        } catch (error) {
            console.error('Error in uploadAndProcessVideo:', error);
            statusMessage.textContent = `Error: ${error.message || 'Upload/processing failed.'}`;
            // Re-throw the error so it's caught by the event listener's catch block
            throw error;
        }

        // #####################################################################
        // # End of Runpod API integration placeholder                         #
        // #####################################################################
    }
});
