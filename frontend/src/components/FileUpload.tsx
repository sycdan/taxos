import React, { useState, useCallback } from "react";
import { motion } from "framer-motion";
import { Upload, FileImage, AlertCircle, CheckCircle } from "lucide-react";

interface FileUploadProps {
  onFileSelect: (file: File, hash: string) => void;
  onUploadComplete?: (hash: string, filename: string) => void;
  onUploadError?: (error: string) => void;
  acceptedTypes?: string[];
  isUploading?: boolean;
  uploadProgress?: number;
  className?: string;
}

// Web Crypto API for file hashing
const calculateSHA256 = async (file: File): Promise<string> => {
  const arrayBuffer = await file.arrayBuffer();
  const hashBuffer = await crypto.subtle.digest('SHA-256', arrayBuffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  return hashHex;
};

const FileUpload: React.FC<FileUploadProps> = ({
  onFileSelect,
  onUploadComplete,
  onUploadError,
  acceptedTypes = ['image/*', 'application/pdf'],
  isUploading = false,
  uploadProgress = 0,
  className = "",
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [filePreview, setFilePreview] = useState<string | null>(null);
  const [selectedFileName, setSelectedFileName] = useState<string>("");

  const validateFile = (file: File): string | null => {
    // Check file type
    const isValidType = acceptedTypes.some(type => {
      if (type.endsWith('/*')) {
        return file.type.startsWith(type.slice(0, -1));
      }
      return file.type === type;
    });

    if (!isValidType) {
      return `File type not supported. Please upload: ${acceptedTypes.join(', ')}`;
    }

    // Check file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      return "File size must be less than 10MB";
    }

    return null;
  };

  const handleFile = useCallback(async (file: File) => {
    const error = validateFile(file);
    if (error) {
      onUploadError?.(error);
      return;
    }

    setSelectedFileName(file.name);

    // Create preview for images
    if (file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setFilePreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    } else {
      setFilePreview(null);
    }

    try {
      // Calculate file hash
      const hash = await calculateSHA256(file);
      onFileSelect(file, hash);
    } catch (err) {
      onUploadError?.(`Failed to process file: ${err}`);
    }
  }, [onFileSelect, onUploadError]);

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 1) {
      onUploadError?.("Please upload only one file at a time");
      return;
    }

    if (files.length === 1) {
      handleFile(files[0]);
    }
  }, [handleFile, onUploadError]);

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  }, []);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFile(files[0]);
    }
  }, [handleFile]);

  return (
    <div className={`w-full ${className}`}>
      <motion.div
        className={`
          relative border-2 border-dashed rounded-lg p-6 text-center transition-colors
          ${dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}
          ${isUploading ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
        `}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        whileHover={!isUploading ? { scale: 1.02 } : {}}
        whileTap={!isUploading ? { scale: 0.98 } : {}}
      >
        <input
          type="file"
          className="hidden"
          id="file-upload"
          accept={acceptedTypes.join(',')}
          onChange={handleFileInput}
          disabled={isUploading}
        />
        
        <label htmlFor="file-upload" className="cursor-pointer">
          {isUploading ? (
            <div className="space-y-4">
              <div className="flex justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-700">
                  Uploading {selectedFileName}...
                </p>
                <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                  <motion.div
                    className="bg-blue-500 h-2 rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${uploadProgress}%` }}
                    transition={{ duration: 0.3 }}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {Math.round(uploadProgress)}% complete
                </p>
              </div>
            </div>
          ) : selectedFileName ? (
            <div className="space-y-4">
              {filePreview && (
                <div className="flex justify-center">
                  <img
                    src={filePreview}
                    alt="Preview"
                    className="max-h-32 max-w-full object-contain rounded"
                  />
                </div>
              )}
              <div className="flex items-center justify-center space-x-2">
                <CheckCircle className="h-5 w-5 text-green-500" />
                <p className="text-sm font-medium text-gray-700">
                  {selectedFileName} ready
                </p>
              </div>
              <p className="text-xs text-gray-500">
                Click to select a different file
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex justify-center">
                <div className="p-3 bg-gray-100 rounded-full">
                  <Upload className="h-8 w-8 text-gray-600" />
                </div>
              </div>
              <div>
                <p className="text-lg font-medium text-gray-700">
                  Drop a receipt file here
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  or click to browse
                </p>
                <p className="text-xs text-gray-400 mt-2">
                  Supports: Images (JPEG, PNG) and PDF files (max 10MB)
                </p>
              </div>
            </div>
          )}
        </label>
      </motion.div>
    </div>
  );
};

export default FileUpload;