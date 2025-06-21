import React from 'react';
import { VideoProcessingParams } from '../types';

interface ParameterControlsProps {
  parameters: VideoProcessingParams;
  onChange: (params: VideoProcessingParams) => void;
  onStartProcessing: () => void;
  isProcessing: boolean;
}

const ParameterControls: React.FC<ParameterControlsProps> = ({
  parameters,
  onChange,
  onStartProcessing,
  isProcessing
}) => {
  const resolutions = [
    { value: '720p', label: '720p (1280×720)', gpus: 1 },
    { value: '1080p', label: '1080p (1920×1080)', gpus: 4 },
    { value: '2k', label: '2K (2560×1440)', gpus: 4 }
  ];

  const handleResolutionChange = (resolution: string) => {
    onChange({ ...parameters, resolution });
  };

  const handleSeedChange = (seed: number) => {
    onChange({ ...parameters, seed });
  };

  const selectedResolution = resolutions.find(r => r.value === parameters.resolution);

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold mb-4">Processing Parameters</h2>
      
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Output Resolution
          </label>
          <select
            value={parameters.resolution}
            onChange={(e) => handleResolutionChange(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isProcessing}
          >
            {resolutions.map((res) => (
              <option key={res.value} value={res.value}>
                {res.label} ({res.gpus} GPU{res.gpus > 1 ? 's' : ''})
              </option>
            ))}
          </select>
          <p className="mt-1 text-sm text-gray-500">
            Higher resolutions require more GPUs and processing time
          </p>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Random Seed
          </label>
          <input
            type="number"
            value={parameters.seed}
            onChange={(e) => handleSeedChange(parseInt(e.target.value) || 0)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isProcessing}
          />
          <p className="mt-1 text-sm text-gray-500">
            Use the same seed for reproducible results
          </p>
        </div>
        
        <div className="pt-4">
          <button
            onClick={onStartProcessing}
            disabled={isProcessing}
            className={`w-full py-3 px-4 rounded-md font-medium transition-colors
              ${isProcessing 
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed' 
                : 'bg-blue-600 text-white hover:bg-blue-700'}`}
          >
            {isProcessing ? 'Processing...' : 'Restore Video'}
          </button>
          
          <div className="mt-3 text-sm text-gray-600">
            <p>Estimated processing time: 5-15 minutes</p>
            <p>Estimated cost: $0.32-$0.65 ({selectedResolution?.gpus} H100 GPU{selectedResolution?.gpus! > 1 ? 's' : ''})</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ParameterControls;