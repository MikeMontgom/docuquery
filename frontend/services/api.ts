import { Document, QueryResponse, UploadResponse, ChatMessage, ModelType } from '../types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = {
  async getDocuments(): Promise<Document[]> {
    const res = await fetch(`${API_BASE}/api/documents`);
    if (!res.ok) {
      throw new Error('Failed to fetch documents');
    }
    return res.json();
  },

  async uploadDocument(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${API_BASE}/api/documents/upload`, {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      throw new Error('Failed to upload document');
    }
    return res.json();
  },

  async renameDocument(docId: string, name: string): Promise<UploadResponse> {
    const res = await fetch(`${API_BASE}/api/documents/${docId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ name })
    });

    if (!res.ok) {
      throw new Error('Failed to rename document');
    }
    return res.json();
  },

  async deleteDocument(docId: string): Promise<{ success: boolean }> {
    const res = await fetch(`${API_BASE}/api/documents/${docId}`, {
      method: 'DELETE'
    });

    if (!res.ok) {
      throw new Error('Failed to delete document');
    }
    return res.json();
  },

  async query(
    question: string,
    history: ChatMessage[],
    model: ModelType = 'gpt-4o'
  ): Promise<QueryResponse> {
    const res = await fetch(`${API_BASE}/api/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        question,
        conversation_history: history.map(msg => ({
          role: msg.role,
          content: msg.content
        })),
        model
      })
    });

    if (!res.ok) {
      throw new Error('Failed to query documents');
    }
    return res.json();
  },

  async getPdfUrl(docId: string): Promise<{ url: string; name: string; total_pages: number }> {
    const res = await fetch(`${API_BASE}/api/documents/${docId}/pdf`);
    if (!res.ok) {
      throw new Error('Failed to get PDF URL');
    }
    return res.json();
  }
};
