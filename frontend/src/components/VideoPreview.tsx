import React, { useState, useEffect } from 'react';

interface VideoPreviewProps {
  originalVideo: File | null;
  processedVideoUrl?: string;
}

const VideoPreview: React.FC<VideoPreviewProps> = ({ originalVideo, processedVideoUrl }) => {
  const [originalUrl, setOriginalUrl] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'original' | 'processed'>('original');

  useEffect(() => {
    if (originalVideo) {
      const url = URL.createObjectURL(originalVideo);
      setOriginalUrl(url);
      
      return () => {
        URL.revokeObjectURL(url);
      };
    }
  }, [originalVideo]);

  if (!originalUrl && !processedVideoUrl) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold mb-4">Video Preview</h2>
      
      {processedVideoUrl && (
        <div className="mb-4">
          <div className="flex space-x-1 border-b">
            <button
              onClick={() => setActiveTab('original')}
              className={`px-4 py-2 font-medium transition-colors ${
                activeTab === 'original'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              Original
            </button>
            <button
              onClick={() => setActiveTab('processed')}
              className={`px-4 py-2 font-medium transition-colors ${
                activeTab === 'processed'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              Restored
            </button>
          </div>
        </div>
      )}
      
      <div className="relative">
        {activeTab === 'original' && originalUrl && (
          <video
            key="original"
            src={originalUrl}
            controls
            className="w-full rounded-lg"
          >
            Your browser does not support the video tag.
          </video>
        )}
        
        {activeTab === 'processed' && processedVideoUrl && (
          <video
            key="processed"
            src={processedVideoUrl}
            controls
            className="w-full rounded-lg"
          >
            Your browser does not support the video tag.
          </video>
        )}
      </div>
      
      {originalVideo && (
        <div className="mt-4 text-sm text-gray-600">
          <p>File: {originalVideo.name}</p>
          <p>Size: {(originalVideo.size / (1024 * 1024)).toFixed(2)} MB</p>
        </div>
      )}
    </div>
  );
};

export default VideoPreview;