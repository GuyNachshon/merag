// API service configuration
// Since nginx is proxying /api/ requests, we can use relative URLs
const getApiUrl = () => {
  // If we're running with nginx proxy, use relative URLs
  if (typeof window !== 'undefined') {
    return '';
  }
  
  // Fallback to environment variable or default
  return import.meta.env.VITE_API_URL || '';
};

const API_BASE_URL = getApiUrl();

console.log('Frontend connecting to backend at:', API_BASE_URL);

export const api = {
  // Health check
  async health() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/health`);
      return response.json();
    } catch (error) {
      console.error('Health check failed:', error);
      return { status: 'error', message: error.message };
    }
  },

  // Chat endpoints
  async chat(message, history = []) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          history,
        }),
      });
      return response.json();
    } catch (error) {
      console.error('Chat request failed:', error);
      return { success: false, error: error.message };
    }
  },

  // Streaming chat
  async chatStream(message, history = [], onChunk) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          history,
        }),
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') return;
            
            try {
              const parsed = JSON.parse(data);
              onChunk(parsed);
            } catch (e) {
              console.error('Error parsing chunk:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Streaming chat failed:', error);
      throw error;
    }
  },

  // File upload
  async uploadFile(file) {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_BASE_URL}/api/v1/upload`, {
        method: 'POST',
        body: formData,
      });
      return response.json();
    } catch (error) {
      console.error('File upload failed:', error);
      return { success: false, error: error.message };
    }
  },

  // Transcription
  async transcribeAudio(file) {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_BASE_URL}/api/v1/transcribe`, {
        method: 'POST',
        body: formData,
      });
      return response.json();
    } catch (error) {
      console.error('Transcription failed:', error);
      return { success: false, error: error.message };
    }
  },

  // Get documents
  async getDocuments() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/documents`);
      return response.json();
    } catch (error) {
      console.error('Get documents failed:', error);
      return { success: false, error: error.message };
    }
  },

  // Delete document
  async deleteDocument(docId) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/documents/${docId}`, {
        method: 'DELETE',
      });
      return response.json();
    } catch (error) {
      console.error('Delete document failed:', error);
      return { success: false, error: error.message };
    }
  },
}; 