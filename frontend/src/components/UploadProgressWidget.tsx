import React from "react";
import { motion } from "framer-motion";
import { CheckCircle, AlertCircle } from "lucide-react";

interface UploadProgressWidgetProps {
  isUploading: boolean;
  uploadProgress: number;
  fileName?: string;
  error?: string;
  className?: string;
}

const UploadProgressWidget: React.FC<UploadProgressWidgetProps> = ({
  isUploading,
  uploadProgress,
  fileName,
  error,
  className = "",
}) => {
  if (!isUploading && !fileName && !error) {
    return null;
  }

  return (
    <div className={`${className}`}>
      {error ? (
        <div className="flex items-center space-x-2 text-error">
          <AlertCircle className="h-4 w-4" />
          <span className="text-sm">{error}</span>
        </div>
      ) : isUploading ? (
        <div className="space-y-2">
          <div className="flex items-center space-x-2 text-blue-700">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
            <span className="text-sm">Uploading {fileName}...</span>
            <span className="text-xs">{Math.round(uploadProgress)}%</span>
          </div>
          <div className="w-full bg-blue-200 rounded-full h-1.5">
            <motion.div
              className="bg-blue-500 h-1.5 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${uploadProgress}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>
        </div>
      ) : fileName ? (
        <div className="flex items-center space-x-2 text-green-700">
          <CheckCircle className="h-4 w-4" />
          <span className="text-sm">File uploaded: {fileName}</span>
        </div>
      ) : null}
    </div>
  );
};

export default UploadProgressWidget;