import axios from 'axios';
import { VideoProcessingParams, ProcessingJob } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const submitVideoForProcessing = async (
  video: File,
  params: VideoProcessingParams
): Promise<ProcessingJob> => {
  // First, upload the video
  const formData = new FormData();
  formData.append('video', video);
  
  const uploadResponse = await api.post('/api/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  
  const { video_url } = uploadResponse.data;
  
  // Then, submit for processing
  const processResponse = await api.post('/api/process', {
    video_url,
    ...params,
  });
  
  return processResponse.data;
};

export const getJobStatus = async (jobId: string): Promise<ProcessingJob> => {
  const response = await api.get(`/api/status/${jobId}`);
  return response.data;
};

export const cancelJob = async (jobId: string): Promise<void> => {
  await api.post(`/api/process/${jobId}/cancel`);
};

export const getJobHistory = async (): Promise<ProcessingJob[]> => {
  const response = await api.get('/api/status/history');
  return response.data;
};

// WebSocket connection for real-time updates
export const connectToJobUpdates = (jobId: string, onUpdate: (job: ProcessingJob) => void) => {
  const ws = new WebSocket(`${API_BASE_URL.replace('http', 'ws')}/ws/job/${jobId}`);
  
  ws.onmessage = (event) => {
    const job = JSON.parse(event.data);
    onUpdate(job);
  };
  
  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };
  
  return () => {
    ws.close();
  };
};