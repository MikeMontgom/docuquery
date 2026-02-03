export type DocStatus = 'uploading' | 'ready' | 'error';

export type ModelType = 'gpt-4o' | 'gpt-4o-mini' | 'gemini-3';

export interface Document {
  doc_id: string;
  name: string;
  status: DocStatus;
  total_chunks?: number;
  total_pages?: number;
  upload_date?: string;
}

export interface Source {
  doc_name: string;
  doc_id: string;
  chunk_sequence: number;
  heading_path: string;
  source_pages?: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
}

export interface QueryResponse {
  answer: string;
  sources: Source[];
}

export interface UploadResponse {
  doc_id: string;
  name: string;
  status: DocStatus;
}
