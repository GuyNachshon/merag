// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

// Hebrew RAG API Service
class HebrewRAGApiService {
  constructor() {
    this.baseURL = API_BASE_URL
  }

  // Health check
  async checkHealth() {
    try {
      const response = await fetch(`${this.baseURL}/health`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      return data
    } catch (error) {
      console.error('Error checking health:', error)
      throw error
    }
  }

  // Get document statistics
  async getDocumentStats() {
    try {
      const response = await fetch(`${this.baseURL}/documents/stats`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      return data
    } catch (error) {
      console.error('Error getting document stats:', error)
      throw error
    }
  }

  // Query documents with regular response
  async queryDocuments(question) {
    try {
      const response = await fetch(`${this.baseURL}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: question,
          stream: false
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      return data
    } catch (error) {
      console.error('Error querying documents:', error)
      throw error
    }
  }

  // Query documents with streaming response
  async queryDocumentsStream(question, onChunk = null, onComplete = null) {
    try {
      const response = await fetch(`${this.baseURL}/query/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: question,
          stream: true
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      // Handle streaming response
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let fullResponse = ''

      while (true) {
        const { done, value } = await reader.read()
        
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            
            if (data === '[DONE]') {
              if (onComplete) onComplete(fullResponse)
              return fullResponse
            }
            
            if (data.startsWith('[ERROR]')) {
              const error = data.slice(8)
              throw new Error(error)
            }

            // For Hebrew RAG, the chunk is just the text content
            fullResponse += data
            if (onChunk) onChunk(data, fullResponse)
          }
        }
      }

      if (onComplete) onComplete(fullResponse)
      return fullResponse
    } catch (error) {
      console.error('Error streaming query:', error)
      throw error
    }
  }

  // Upload documents
  async uploadDocuments(files) {
    try {
      const formData = new FormData()
      
      // Add multiple files
      files.forEach((file, index) => {
        formData.append('files', file)
      })

      const response = await fetch(`${this.baseURL}/documents/upload`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      return data
    } catch (error) {
      console.error('Error uploading documents:', error)
      throw error
    }
  }

  // Clear all documents
  async clearDocuments() {
    try {
      const response = await fetch(`${this.baseURL}/documents/clear`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      return data
    } catch (error) {
      console.error('Error clearing documents:', error)
      throw error
    }
  }
}

// Transcription API methods
export const transcriptionApi = {
  async transcribeAudio(file, language = 'he', task = 'transcribe', outputFormat = 'text') {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('language', language)
    formData.append('task', task)
    formData.append('output_format', outputFormat)

    const response = await fetch(`${API_BASE_URL}/transcribe/audio`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Transcription failed')
    }

    return await response.json()
  },

  async getTranscriptionStatus() {
    const response = await fetch(`${API_BASE_URL}/transcribe/status`)
    
    if (!response.ok) {
      throw new Error('Failed to get transcription status')
    }

    return await response.json()
  }
}

// Create singleton instance
const hebrewRAGApi = new HebrewRAGApiService()

export default hebrewRAGApi 