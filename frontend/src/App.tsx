import React, { useState } from 'react';
import { Toaster } from 'react-hot-toast';
import VideoUploader from './components/VideoUploader';
import ParameterControls from './components/ParameterControls';
import ProcessingStatus from './components/ProcessingStatus';
import VideoPreview from './components/VideoPreview';
import { VideoProcessingParams, ProcessingJob } from './types';
import { submitVideoForProcessing, getJobStatus } from './services/api';
import './App.css';

function App() {
  const [uploadedVideo, setUploadedVideo] = useState<File | null>(null);
  const [processingJob, setProcessingJob] = useState<ProcessingJob | null>(null);
  const [parameters, setParameters] = useState<VideoProcessingParams>({
    resolution: '720p',
    seed: 42,
  });

  const handleVideoUpload = (file: File) => {
    setUploadedVideo(file);
    setProcessingJob(null);
  };

  const handleParameterChange = (params: VideoProcessingParams) => {
    setParameters(params);
  };

  const handleStartProcessing = async () => {
    if (!uploadedVideo) return;

    try {
      const job = await submitVideoForProcessing(uploadedVideo, parameters);
      setProcessingJob(job);
      
      // Start polling for status
      const pollInterval = setInterval(async () => {
        const status = await getJobStatus(job.id);
        setProcessingJob(status);
        
        if (status.status === 'completed' || status.status === 'failed') {
          clearInterval(pollInterval);
        }
      }, 5000);
    } catch (error) {
      console.error('Failed to start processing:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <Toaster position="top-right" />
      
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-6 px-4">
          <h1 className="text-3xl font-bold text-gray-900">
            SeedVR2 Video Restoration
          </h1>
          <p className="mt-2 text-gray-600">
            One-click video restoration powered by RunPod
          </p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto py-8 px-4">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="space-y-6">
            <VideoUploader onVideoUpload={handleVideoUpload} />
            
            {uploadedVideo && (
              <ParameterControls
                parameters={parameters}
                onChange={handleParameterChange}
                onStartProcessing={handleStartProcessing}
                isProcessing={processingJob?.status === 'processing'}
              />
            )}
            
            {processingJob && (
              <ProcessingStatus job={processingJob} />
            )}
          </div>
          
          <div>
            {(uploadedVideo || processingJob) && (
              <VideoPreview
                originalVideo={uploadedVideo}
                processedVideoUrl={processingJob?.resultUrl}
              />
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;