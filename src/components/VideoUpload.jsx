import { useCallback, useState, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import toast from 'react-hot-toast';
import { CloudArrowUpIcon } from '@heroicons/react/24/outline';

export default function VideoUpload({ apiKey, options, setResults, isAnalyzing, setIsAnalyzing }) {
  const [previewUrl, setPreviewUrl] = useState(null);
  
  // Cleanup the previous preview URL when component unmounts or when a new video is uploaded
  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const onDrop = useCallback(async (acceptedFiles) => {
    // Revoke previous preview URL if it exists
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    
    if (!apiKey) {
      toast.error('Please enter your API key');
      return;
    }
    
    if (
      !options.detectAbusive &&
      !options.detectViolent &&
      !options.detectNSFW &&
      !options.detectPolitical &&
      !options.detectReligious
    ) {
      toast.error('Please select at least one analysis option');
      return;
    }
    
    const file = acceptedFiles[0];
    if (!file) return;
    
    // Create a URL for the video preview
    const videoUrl = URL.createObjectURL(file);
    setPreviewUrl(videoUrl);
    
    const formData = new FormData();
    formData.append('video', file);
    formData.append('gemini_api', apiKey);
    formData.append('detect_abusive', options.detectAbusive);
    formData.append('detect_violent', options.detectViolent);
    formData.append('detect_nsfw', options.detectNSFW);
    formData.append('detect_political', options.detectPolitical);
    formData.append('detect_religious', options.detectReligious);
    
    setIsAnalyzing(true);
    
    try {
      const response = await axios.post('https://civil-daring-halibut.ngrok-free.app/analyze', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setResults(response.data);
      toast.success('Analysis completed successfully!');
    } catch (error) {
      console.error('Analysis failed:', error);
      toast.error('Analysis failed. Please try again.');
    } finally {
      setIsAnalyzing(false);
    }
  }, [apiKey, options, setResults, setIsAnalyzing, previewUrl]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'video/*': []
    },
    maxFiles: 1,
    disabled: isAnalyzing,
  });

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div 
        {...getRootProps()} 
        className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
          isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
        } ${isAnalyzing ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        <input {...getInputProps()} />
        <CloudArrowUpIcon className="h-12 w-12 mx-auto text-gray-400" />
        <p className="mt-4 text-lg text-gray-600">
          {isAnalyzing ? 'Analyzing video...' : isDragActive ? 'Drop the video here' : 'Drag & drop a video, or click to select'}
        </p>
        <p className="mt-2 text-sm text-gray-500">Supported formats: MP4, AVI, MOV</p>
      </div>
      
      {previewUrl && (
        <div className="mt-4 flex flex-col items-center">
          <p className="text-gray-600 text-sm mb-2">Selected video preview:</p>
          <video 
            key={previewUrl} // Add key prop to force re-render when source changes
            controls 
            className="w-full max-w-lg h-auto rounded-lg shadow-lg"
          >
            <source src={previewUrl} type="video/mp4" />
            Your browser does not support the video tag.
          </video>
        </div>
      )}
    </div>
  );
}