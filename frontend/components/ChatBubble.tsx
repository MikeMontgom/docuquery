
import React from 'react';
import { ChatMessage, Source } from '../types';

interface ChatBubbleProps {
  message: ChatMessage;
  onCitationClick?: (source: Source) => void;
}

const ChatBubble: React.FC<ChatBubbleProps> = ({ message, onCitationClick }) => {
  const isUser = message.role === 'user';

  const parsePageNumber = (sourcePages?: string): number => {
    if (!sourcePages) return 1;
    // source_pages can be "5" or "5-7", take the first page
    const match = sourcePages.match(/^(\d+)/);
    return match ? parseInt(match[1], 10) : 1;
  };

  return (
    <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} gap-1 animate-in fade-in slide-in-from-bottom-2 duration-300`}>
      <div className={`flex items-start gap-3 max-w-[85%] ${isUser ? 'flex-row-reverse' : ''}`}>
        <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 text-sm font-bold shadow-sm
          ${isUser ? 'bg-indigo-600 text-white' : 'bg-white border border-gray-200 text-indigo-600'}`}>
          {isUser ? 'U' : 'AI'}
        </div>

        <div className={`
          p-4 rounded-2xl shadow-sm text-sm leading-relaxed
          ${isUser ? 'bg-indigo-600 text-white rounded-tr-none' : 'bg-white border border-gray-100 text-gray-800 rounded-tl-none'}
        `}>
          <div className="whitespace-pre-wrap font-medium">
            {message.content}
          </div>

          {!isUser && message.sources && message.sources.length > 0 && (
            <div className="mt-4 pt-3 border-t border-gray-50">
              <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-2 flex items-center gap-1">
                <svg xmlns="http://www.w3.org/2000/svg" className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
                Citations
                <span className="text-gray-300 font-normal ml-1">(click to view)</span>
              </p>
              <div className="flex flex-wrap gap-2">
                {message.sources.map((source, idx) => (
                  <button
                    key={idx}
                    onClick={() => onCitationClick?.(source)}
                    className="flex items-center gap-1.5 px-2 py-1 bg-gray-50 hover:bg-indigo-50 rounded border border-gray-100 hover:border-indigo-200 text-[11px] text-gray-500 hover:text-indigo-600 transition-colors cursor-pointer"
                  >
                    <span className="font-bold text-indigo-500">[{idx + 1}]</span>
                    <span className="truncate max-w-[120px]" title={source.doc_name}>{source.doc_name}</span>
                    {source.source_pages && <span className="text-gray-400">p.{source.source_pages}</span>}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      <span className="text-[10px] text-gray-400 px-11 font-medium">
        {isUser ? 'You' : 'Assistant'}
      </span>
    </div>
  );
};

export default ChatBubble;
