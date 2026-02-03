
import React, { useState, useEffect, useRef } from 'react';
import { Document } from '../types';

interface DocumentItemProps {
  doc: Document;
  onRename: (id: string, name: string) => void;
  onDelete: (id: string) => void;
}

const DocumentItem: React.FC<DocumentItemProps> = ({ doc, onRename, onDelete }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(doc.name);
  const [isConfirmingDelete, setIsConfirmingDelete] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isEditing) {
      inputRef.current?.focus();
      inputRef.current?.select();
    }
  }, [isEditing]);

  const handleBlur = () => {
    setIsEditing(false);
    if (editValue.trim() && editValue !== doc.name) {
      onRename(doc.doc_id, editValue.trim());
    } else {
      setEditValue(doc.name);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleBlur();
    } else if (e.key === 'Escape') {
      setIsEditing(false);
      setEditValue(doc.name);
    }
  };

  const getStatusDisplay = () => {
    switch (doc.status) {
      case 'uploading':
      case 'processing':
        return (
          <div className="flex items-center gap-1.5 text-[10px] font-bold text-amber-600 uppercase tracking-tight">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse"></span>
            Uploading...
          </div>
        );
      case 'ready':
        return (
          <div className="flex items-center gap-1.5 text-[10px] font-bold text-green-600 uppercase tracking-tight">
            <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
            Ready
          </div>
        );
      case 'error':
        return (
          <div className="flex items-center gap-1.5 text-[10px] font-bold text-red-600 uppercase tracking-tight">
            <span className="w-1.5 h-1.5 rounded-full bg-red-500"></span>
            Error
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="group relative bg-white border border-gray-100 rounded-lg p-3 hover:border-indigo-200 hover:shadow-sm transition-all overflow-hidden">
      {isConfirmingDelete ? (
        <div className="flex flex-col gap-2 animate-in fade-in slide-in-from-left-2 duration-200">
          <p className="text-xs font-semibold text-gray-700">Delete document?</p>
          <div className="flex items-center gap-2">
            <button 
              onClick={() => onDelete(doc.doc_id)}
              className="px-2 py-1 bg-red-50 text-red-600 text-[10px] font-bold rounded uppercase hover:bg-red-100 transition-colors"
            >
              Delete
            </button>
            <button 
              onClick={() => setIsConfirmingDelete(false)}
              className="px-2 py-1 bg-gray-50 text-gray-500 text-[10px] font-bold rounded uppercase hover:bg-gray-100 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 mt-1">
            <svg xmlns="http://www.w3.org/2000/svg" className={`w-5 h-5 ${doc.status === 'ready' ? 'text-indigo-500' : 'text-gray-400'}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
          </div>

          <div className="flex-1 min-w-0">
            {isEditing ? (
              <input
                ref={inputRef}
                type="text"
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                onBlur={handleBlur}
                onKeyDown={handleKeyDown}
                className="w-full text-sm font-medium text-gray-900 border-none p-0 focus:ring-0 outline-none"
              />
            ) : (
              <div 
                className="text-sm font-medium text-gray-900 truncate cursor-pointer hover:text-indigo-600"
                onClick={() => setIsEditing(true)}
              >
                {doc.name}
              </div>
            )}
            {getStatusDisplay()}
          </div>

          <button 
            onClick={() => setIsConfirmingDelete(true)}
            className="p-1.5 text-gray-300 hover:text-red-500 hover:bg-red-50 rounded opacity-0 group-hover:opacity-100 transition-opacity"
            title="Delete document"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
          </button>
        </div>
      )}
    </div>
  );
};

export default DocumentItem;
