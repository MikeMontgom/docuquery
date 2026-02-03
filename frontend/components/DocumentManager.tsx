
import React, { useRef, useState } from 'react';
import { Document } from '../types';
import DocumentItem from './DocumentItem';

interface DocumentManagerProps {
  documents: Document[];
  onUpload: (file: File) => void;
  onRename: (docId: string, newName: string) => void;
  onDelete: (docId: string) => void;
  isLoading: boolean;
  error: string | null;
}

const DocumentManager: React.FC<DocumentManagerProps> = ({ 
  documents, 
  onUpload, 
  onRename, 
  onDelete, 
  isLoading,
  error 
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files[0]) {
      processFile(files[0]);
    }
  };

  const processFile = (file: File) => {
    if (file.type !== 'application/pdf') {
      setUploadError('Only PDF files are accepted.');
      setTimeout(() => setUploadError(null), 3000);
      return;
    }
    setUploadError(null);
    onUpload(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files && files[0]) {
      processFile(files[0]);
    }
  };

  const sortedDocs = [...documents].sort((a, b) => {
    return new Date(b.upload_date || '').getTime() - new Date(a.upload_date || '').getTime();
  });

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <div className="p-4">
        <div 
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`
            border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all
            ${isDragging ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200 hover:border-indigo-400 hover:bg-gray-50'}
          `}
        >
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileChange} 
            accept=".pdf" 
            className="hidden" 
          />
          <div className="flex flex-col items-center gap-2">
            <div className="p-3 rounded-full bg-indigo-100 text-indigo-600">
              <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
            </div>
            <p className="text-sm font-medium text-gray-700">Click or drag PDF to upload</p>
            <p className="text-xs text-gray-500">PDF documents only</p>
          </div>
          {uploadError && (
            <p className="text-xs text-red-500 mt-2 font-medium">{uploadError}</p>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-4 pb-4">
        <div className="flex items-center justify-between mb-3 sticky top-0 bg-white pt-2 pb-1 z-10">
          <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Documents ({documents.length})</h2>
          {isLoading && (
            <div className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
          )}
        </div>

        {sortedDocs.length === 0 ? (
          <div className="py-12 text-center text-gray-400">
            <svg xmlns="http://www.w3.org/2000/svg" className="w-12 h-12 mx-auto mb-3 opacity-20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/></svg>
            <p className="text-sm">No documents yet</p>
          </div>
        ) : (
          <div className="space-y-2">
            {sortedDocs.map(doc => (
              <DocumentItem 
                key={doc.doc_id} 
                doc={doc} 
                onRename={onRename} 
                onDelete={onDelete} 
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default DocumentManager;
