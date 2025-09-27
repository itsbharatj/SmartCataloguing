import React, { useRef, useState } from "react";
import { useDropzone } from "react-dropzone";

export const FileUpload = ({ onChange }) => {
  const [files, setFiles] = useState([]);
  const fileInputRef = useRef(null);

  const handleFileChange = (newFiles) => {
    console.log("Files selected:", newFiles); // Debug log
    setFiles(newFiles);
    onChange && onChange(newFiles);
  };

  const { getRootProps, getInputProps, isDragActive, open } = useDropzone({
    multiple: false,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.gif', '.bmp', '.webp']
    },
    onDrop: handleFileChange,
    onDropRejected: (error) => {
      console.log("Drop rejected:", error);
    },
    noClick: false, // Explicitly enable click
  });

  const handleManualClick = () => {
    console.log("Manual click triggered"); // Debug log
    open();
  };

  return (
    <div className="w-full">
      <div 
        {...getRootProps()} 
        className={`
          p-10 border-2 border-dashed rounded-lg cursor-pointer 
          transition-all duration-200 ease-in-out
          ${isDragActive 
            ? 'border-blue-500 bg-blue-50 dark:bg-blue-950/20' 
            : 'border-gray-300 dark:border-gray-600 hover:border-blue-400 dark:hover:border-blue-500'
          }
          bg-white dark:bg-gray-800/50
        `}
        onClick={handleManualClick}
      >
        <input {...getInputProps()} />
        
        <div className="flex flex-col items-center justify-center text-center space-y-4">
          {/* Upload Icon */}
          <div className="w-16 h-16 mx-auto">
            <svg
              className="w-full h-full text-gray-400 dark:text-gray-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
          </div>

          {/* Text */}
          <div>
            <p className="text-xl font-semibold text-gray-700 dark:text-gray-300 mb-2">
              Upload Image
            </p>
            <p className="text-gray-500 dark:text-gray-400">
              {isDragActive 
                ? "Drop your image here..." 
                : "Click to browse or drag and drop your image here"
              }
            </p>
            <p className="text-sm text-gray-400 dark:text-gray-500 mt-2">
              Supports: JPG, PNG, GIF, BMP, WEBP
            </p>
          </div>

          {/* Alternative Click Button */}
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              console.log("Button clicked"); // Debug log
              handleManualClick();
            }}
            className="mt-4 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors duration-200"
          >
            Choose File
          </button>
        </div>
      </div>

      {/* Show selected files */}
      {files.length > 0 && (
        <div className="mt-4 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
          <p className="text-green-700 dark:text-green-300 font-medium">
            Selected: {files[0].name}
          </p>
        </div>
      )}
    </div>
  );
};


