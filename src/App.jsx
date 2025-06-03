import { useState } from 'react';
import { Toaster } from 'react-hot-toast';
import { EyeIcon, EyeSlashIcon } from "@heroicons/react/24/solid";
import Navbar from './components/Navbar';
import VideoUpload from './components/VideoUpload';
import AnalysisOptions from './components/AnalysisOptions';
import ResultsDisplay from './components/ResultsDisplay';

export default function App() {
  const [apiKey, setApiKey] = useState(() => import.meta.env.VITE_GEMINI_API_KEY || '');
  const [isPasswordVisible, setIsPasswordVisible] = useState(false);
  const [results, setResults] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [options, setOptions] = useState({
    detectAbusive: false,
    detectViolent: false,
    detectNSFW: false,
    detectPolitical: false,
    detectReligious: false,
  });

  return (
    <div className="min-h-screen bg-gray-50">
      <Toaster position="top-right" />
      <Navbar />
      
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto space-y-8">
          {/* API Key Input */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-lg font-semibold mb-4">API Configuration</h2>
            <div className="relative">
              <input
                type={isPasswordVisible ? "text" : "password"}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Enter your Gemini API Key"
                className="w-full px-4 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent pr-10"
              />
              <button
                type="button"
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500"
                onClick={() => setIsPasswordVisible(!isPasswordVisible)}
              >
                {isPasswordVisible ? (
                  <EyeSlashIcon className="w-5 h-5" />
                ) : (
                  <EyeIcon className="w-5 h-5" />
                )}
              </button>
            </div>
          </div>

          {/* Analysis Options */}
          <AnalysisOptions options={options} setOptions={setOptions} />

          {/* Video Upload */}
          <VideoUpload
            apiKey={apiKey}
            options={options}
            setResults={setResults}
            isAnalyzing={isAnalyzing}
            setIsAnalyzing={setIsAnalyzing}
          />

          {/* Results Display */}
          {results && <ResultsDisplay results={results} />}
        </div>
      </main>
    </div>
  );
}