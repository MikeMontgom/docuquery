
import React, { useState, useEffect, useCallback } from 'react';
import { Document, ChatMessage } from './types';
import { api } from './services/api';
import DocumentManager from './components/DocumentManager';
import QueryInterface from './components/QueryInterface';

const App: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const fetchDocuments = useCallback(async () => {
    try {
      const docs = await api.getDocuments();
      setDocuments(docs);
      setError(null);
    } catch (err) {
      console.error(err);
      setError('Could not connect to the document server.');
    }
  }, []);

  useEffect(() => {
    setLoadingDocs(true);
    fetchDocuments().finally(() => setLoadingDocs(false));
  }, [fetchDocuments]);

  useEffect(() => {
    const needsPolling = documents.some(doc => doc.status === 'uploading' || doc.status === 'processing');
    if (!needsPolling) return;

    const interval = setInterval(() => {
      fetchDocuments();
    }, 3000);

    return () => clearInterval(interval);
  }, [documents, fetchDocuments]);

  const handleUpload = async (file: File) => {
    try {
      await api.uploadDocument(file);
      await fetchDocuments();
    } catch (err) {
      setError('Upload failed. Please try again.');
    }
  };

  const handleRename = async (docId: string, newName: string) => {
    try {
      await api.renameDocument(docId, newName);
      await fetchDocuments();
    } catch (err) {
      setError('Failed to rename document.');
    }
  };

  const handleDelete = async (docId: string) => {
    try {
      await api.deleteDocument(docId);
      await fetchDocuments();
    } catch (err) {
      setError('Failed to delete document.');
    }
  };

  const handleNewConversation = () => {
    setChatHistory([]);
  };

  return (
    <div className="flex flex-col md:flex-row h-screen w-full bg-gray-50 overflow-hidden text-gray-900">
      <div className="w-full md:w-80 lg:w-96 flex-shrink-0 border-r border-gray-200 bg-white flex flex-col h-1/2 md:h-full">
        <div className="p-4 border-b border-gray-100 flex items-center justify-between bg-white sticky top-0 z-10">
          <h1 className="text-xl font-bold text-indigo-600 flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/></svg>
            DocuQuery
          </h1>
        </div>
        
        <DocumentManager 
          documents={documents}
          onUpload={handleUpload}
          onRename={handleRename}
          onDelete={handleDelete}
          isLoading={loadingDocs}
          error={error}
        />
      </div>

      <div className="flex-1 flex flex-col h-1/2 md:h-full relative bg-gray-50">
        <QueryInterface 
          documents={documents}
          chatHistory={chatHistory}
          setChatHistory={setChatHistory}
          onNewConversation={handleNewConversation}
        />
      </div>

      {error && (
        <div className="fixed bottom-4 left-1/2 -translate-x-1/2 px-6 py-3 bg-red-600 text-white rounded-lg shadow-xl z-50 flex items-center gap-2 animate-bounce">
          <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          {error}
          <button onClick={() => setError(null)} className="ml-2 hover:text-red-200 text-lg">&times;</button>
        </div>
      )}
    </div>
  );
};

export default App;
