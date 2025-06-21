import React from 'react';
import { ProcessingJob } from '../types';
import { CheckCircleIcon, XCircleIcon, ArrowDownTrayIcon } from '@heroicons/react/24/solid';
import { ClockIcon } from '@heroicons/react/24/outline';

interface ProcessingStatusProps {
  job: ProcessingJob;
}

const ProcessingStatus: React.FC<ProcessingStatusProps> = ({ job }) => {
  const getStatusIcon = () => {
    switch (job.status) {
      case 'queued':
        return <ClockIcon className="w-6 h-6 text-yellow-500" />;
      case 'processing':
        return (
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
        );
      case 'completed':
        return <CheckCircleIcon className="w-6 h-6 text-green-500" />;
      case 'failed':
        return <XCircleIcon className="w-6 h-6 text-red-500" />;
      default:
        return null;
    }
  };

  const getStatusText = () => {
    switch (job.status) {
      case 'queued':
        return 'Waiting in queue...';
      case 'processing':
        return 'Processing video...';
      case 'completed':
        return 'Processing complete!';
      case 'failed':
        return 'Processing failed';
      default:
        return 'Unknown status';
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold mb-4">Processing Status</h2>
      
      <div className="space-y-4">
        <div className="flex items-center space-x-3">
          {getStatusIcon()}
          <span className="text-lg">{getStatusText()}</span>
        </div>
        
        {job.progress !== undefined && job.status === 'processing' && (
          <div>
            <div className="flex justify-between text-sm text-gray-600 mb-1">
              <span>Progress</span>
              <span>{Math.round(job.progress * 100)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${job.progress * 100}%` }}
              ></div>
            </div>
          </div>
        )}
        
        {job.estimatedTimeRemaining && job.status === 'processing' && (
          <div className="text-sm text-gray-600">
            Estimated time remaining: {formatTime(job.estimatedTimeRemaining)}
          </div>
        )}
        
        {job.error && (
          <div className="bg-red-50 border border-red-200 rounded p-3">
            <p className="text-sm text-red-700">{job.error}</p>
          </div>
        )}
        
        {job.status === 'completed' && job.resultUrl && (
          <div className="pt-4">
            <a
              href={job.resultUrl}
              download
              className="inline-flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
            >
              <ArrowDownTrayIcon className="w-5 h-5 mr-2" />
              Download Restored Video
            </a>
          </div>
        )}
        
        <div className="pt-4 text-xs text-gray-500">
          <p>Job ID: {job.id}</p>
          <p>Created: {new Date(job.createdAt).toLocaleString()}</p>
          <p>Updated: {new Date(job.updatedAt).toLocaleString()}</p>
        </div>
      </div>
    </div>
  );
};

export default ProcessingStatus;