export interface VideoProcessingParams {
  resolution: '720p' | '1080p' | '2k';
  seed: number;
}

export interface ProcessingJob {
  id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress?: number;
  resultUrl?: string;
  error?: string;
  createdAt: string;
  updatedAt: string;
  estimatedTimeRemaining?: number;
}