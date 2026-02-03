
import React, { useState, useRef, useEffect } from 'react';
import { Document, ChatMessage, ModelType, Source } from '../types';
import { api } from '../services/api';
import ChatBubble from './ChatBubble';
import PdfViewer from './PdfViewer';

interface QueryInterfaceProps {
  documents: Document[];
  chatHistory: ChatMessage[];
  setChatHistory: React.Dispatch<React.SetStateAction<ChatMessage[]>>;
  onNewConversation: () => void;
}

const MODELS: { label: string; value: ModelType }[] = [
  { label: 'GPT-4o', value: 'gpt-4o' },
  { label: 'GPT-4o mini', value: 'gpt-4o-mini' },
  { label: 'Gemini 3', value: 'gemini-3' },
];

const QueryInterface: React.FC<QueryInterfaceProps> = ({
  documents,
  chatHistory,
  setChatHistory,
  onNewConversation
}) => {
  const [input, setInput] = useState('');
  const [isQuerying, setIsQuerying] = useState(false);
  const [selectedModel, setSelectedModel] = useState<ModelType>('gpt-4o');
  const [pdfSource, setPdfSource] = useState<Source | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const hasDocuments = documents.some(d => d.status === 'ready');
  const isEmpty = chatHistory.length === 0;

  const handleCitationClick = (source: Source) => {
    setPdfSource(source);
  };

  const parsePageNumber = (sourcePages?: string): number => {
    if (!sourcePages) return 1;
    const match = sourcePages.match(/^(\d+)/);
    return match ? parseInt(match[1], 10) : 1;
  };

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, isQuerying]);

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim() || isQuerying || !hasDocuments) return;

    const userMessage: ChatMessage = { role: 'user', content: input };
    setChatHistory(prev => [...prev, userMessage]);
    setInput('');
    setIsQuerying(true);

    try {
      const response = await api.query(input, chatHistory, selectedModel);
      const assistantMessage: ChatMessage = { 
        role: 'assistant', 
        content: response.answer,
        sources: response.sources 
      };
      setChatHistory(prev => [...prev, assistantMessage]);
    } catch (err) {
      const errorMessage: ChatMessage = { 
        role: 'assistant', 
        content: "I'm sorry, I encountered an error while processing your request. Please try again later." 
      };
      setChatHistory(prev => [...prev, errorMessage]);
    } finally {
      setIsQuerying(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="flex flex-col h-full w-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-100 flex items-center justify-between bg-white z-10 shadow-sm">
        <div>
          <h2 className="text-sm font-semibold text-gray-700">Query Assistant</h2>
          <p className="text-[10px] text-gray-400 uppercase tracking-widest font-bold">Document context active</p>
        </div>
        <button 
          onClick={onNewConversation}
          className="px-3 py-1.5 text-xs font-medium text-gray-600 hover:text-indigo-600 hover:bg-indigo-50 rounded-md transition-colors flex items-center gap-1.5 border border-gray-200"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
          New Conversation
        </button>
      </div>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 bg-gray-50/50">
        {isEmpty ? (
          <div className="h-full flex flex-col items-center justify-center text-center max-w-sm mx-auto space-y-4 opacity-60">
            <div className="p-8 rounded-3xl bg-white shadow-sm border border-gray-100">
              <div className="w-16 h-16 bg-indigo-50 rounded-2xl flex items-center justify-center mx-auto mb-4 text-indigo-500">
                <svg xmlns="http://www.w3.org/2000/svg" className="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
              </div>
              <h3 className="text-lg font-bold text-gray-800">Start a conversation</h3>
              <p className="text-sm text-gray-500 mt-2">
                {hasDocuments 
                  ? "Ask any question about your uploaded documents and I'll find the answer for you."
                  : "Please upload and process a document in the left panel to begin querying."}
              </p>
            </div>
          </div>
        ) : (
          <>
            {chatHistory.map((msg, idx) => (
              <ChatBubble key={idx} message={msg} onCitationClick={handleCitationClick} />
            ))}
            {isQuerying && (
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 flex-shrink-0 animate-pulse">
                   <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2v4"/><path d="m16.2 7.8 2.9-2.9"/><path d="M18 12h4"/><path d="m16.2 16.2 2.9 2.9"/><path d="M12 18v4"/><path d="m4.9 19.1 2.9-2.9"/><path d="M2 12h4"/><path d="m4.9 4.9 2.9 2.9"/></svg>
                </div>
                <div className="bg-white border border-gray-100 rounded-2xl rounded-tl-none p-4 shadow-sm">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                    <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '200ms' }}></span>
                    <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '400ms' }}></span>
                  </div>
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </>
        )}
      </div>

      {/* Input Area */}
      <div className="p-4 bg-white border-t border-gray-100">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto relative group">
          <div className="relative bg-gray-50 border border-gray-200 rounded-2xl transition-all focus-within:ring-2 focus-within:ring-indigo-500/20 focus-within:border-indigo-500 overflow-hidden">
            {/* Model Selector within Query Box */}
            <div className="px-3 pt-2 flex items-center gap-2 border-b border-gray-100 bg-white/50">
               <span className="text-[10px] font-bold text-gray-400 uppercase tracking-tighter">Model:</span>
               <select 
                 value={selectedModel}
                 onChange={(e) => setSelectedModel(e.target.value as ModelType)}
                 className="text-[11px] font-bold text-indigo-600 bg-transparent border-none p-0 pr-6 focus:ring-0 cursor-pointer appearance-none hover:text-indigo-700"
               >
                 {MODELS.map(m => (
                   <option key={m.value} value={m.value}>{m.label}</option>
                 ))}
               </select>
               <div className="flex-1"></div>
            </div>

            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={hasDocuments ? "Ask anything about your docs..." : "Upload a document to get started"}
              disabled={isQuerying || !hasDocuments}
              rows={2}
              className={`
                w-full bg-transparent border-none py-3 pl-5 pr-14 focus:ring-0 focus:outline-none transition-all resize-none min-h-[80px]
                ${!hasDocuments ? 'cursor-not-allowed opacity-50' : ''}
              `}
            />
            
            <button
              type="submit"
              disabled={isQuerying || !input.trim() || !hasDocuments}
              className={`
                absolute right-2.5 bottom-2.5 p-2 rounded-xl transition-all
                ${!input.trim() || isQuerying || !hasDocuments ? 'text-gray-300 bg-gray-100' : 'text-white bg-indigo-600 hover:bg-indigo-700 shadow-lg shadow-indigo-600/20'}
              `}
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
            </button>
          </div>
        </form>
        <div className="mt-2 text-center">
          <p className="text-[10px] text-gray-400 font-medium">DocuQuery uses secure RAG context with your chosen model logic.</p>
        </div>
      </div>

      {/* PDF Viewer Modal */}
      {pdfSource && (
        <PdfViewer
          docId={pdfSource.doc_id}
          docName={pdfSource.doc_name}
          initialPage={parsePageNumber(pdfSource.source_pages)}
          onClose={() => setPdfSource(null)}
        />
      )}
    </div>
  );
};

export default QueryInterface;
