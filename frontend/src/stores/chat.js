import { ref } from 'vue'
import { defineStore } from 'pinia'
import hebrewRAGApi from '../services/api.js'

export const useChatStore = defineStore('chat', () => {
  const messages = ref([])
  const isLoading = ref(false)
  const hasMessageBeenSent = ref(false)
  const error = ref(null)
  const documentStats = ref({ total_documents: 0, vector_size: 0 })
  const uploadStatus = ref(null)

  // Mock responses for fallback
  const mockResponses = [
    'אני מצטער, אבל אני צריך מסמכים כדי לענות על השאלה שלך. אנא העלה מסמכים תחילה.',
    'לא מצאתי מידע רלוונטי במסמכים שהועלו. אנא נסה לשאול שאלה אחרת.',
    'אני מבוסס על המסמכים שהועלו. אנא ודא שהמסמכים מכילים את המידע הנדרש.',
    'תודה על השאלה. אני מחפש במסמכים שלך...',
    'זו שאלה טובה! הנה מה שמצאתי במסמכים:'
  ]

  // Check system health
  async function checkHealth() {
    try {
      const health = await hebrewRAGApi.checkHealth()
      return health
    } catch (err) {
      console.warn('Health check failed:', err)
      return { status: 'offline', error: err.message }
    }
  }

  // Load document statistics
  async function loadDocumentStats() {
    try {
      error.value = null
      const stats = await hebrewRAGApi.getDocumentStats()
      if (stats.success) {
        documentStats.value = stats.stats
      }
      return stats
    } catch (err) {
      console.warn('Failed to load document stats:', err)
      return { success: false, error: err.message }
    }
  }

  // Upload documents
  async function uploadDocuments(files) {
    try {
      error.value = null
      uploadStatus.value = 'uploading'
      
      const result = await hebrewRAGApi.uploadDocuments(files)
      
      if (result.success) {
        uploadStatus.value = 'success'
        // Refresh document stats
        await loadDocumentStats()
        return {
          success: true,
          message: `הועלו ${result.files_processed} מסמכים בהצלחה (${result.total_chunks} חלקים)`,
          details: result
        }
      } else {
        uploadStatus.value = 'error'
        return {
          success: false,
          message: result.error || 'שגיאה בהעלאת המסמכים',
          details: result
        }
      }
    } catch (err) {
      uploadStatus.value = 'error'
      console.error('Upload error:', err)
      return {
        success: false,
        message: err.message || 'שגיאה בהעלאת המסמכים',
        error: err
      }
    }
  }

  // Clear all documents
  async function clearDocuments() {
    try {
      error.value = null
      const result = await hebrewRAGApi.clearDocuments()
      
      if (result.success) {
        documentStats.value = { total_documents: 0, vector_size: 0 }
        messages.value = []
        hasMessageBeenSent.value = false
        return { success: true, message: 'כל המסמכים נמחקו בהצלחה' }
      } else {
        return { success: false, message: result.error || 'שגיאה במחיקת המסמכים' }
      }
    } catch (err) {
      console.error('Clear documents error:', err)
      return { success: false, message: err.message || 'שגיאה במחיקת המסמכים' }
    }
  }

  // Query documents (send message)
  async function sendMessage(messageContent, useStreaming = true) {
    try {
      error.value = null
      hasMessageBeenSent.value = true
      
      // Add user message immediately
      const userMessage = {
        id: Date.now(),
        content: messageContent,
        sender: 'user',
        timestamp: new Date()
      }
      messages.value.push(userMessage)
      
      // Start loading
      isLoading.value = true
      
      // Create AI message placeholder for streaming
      const aiMessageId = Date.now() + 1
      const aiMessage = {
        id: aiMessageId,
        content: '',
        sender: 'assistant',
        timestamp: new Date(),
        isStreaming: useStreaming
      }
      messages.value.push(aiMessage)
      
      try {
        if (useStreaming) {
          // Try streaming query
          await hebrewRAGApi.queryDocumentsStream(
            messageContent,
            // onChunk callback
            (chunk, fullResponse) => {
              const messageIndex = messages.value.findIndex(msg => msg.id === aiMessageId)
              if (messageIndex !== -1) {
                messages.value[messageIndex].content = fullResponse
              }
            },
            // onComplete callback
            (fullResponse) => {
              const messageIndex = messages.value.findIndex(msg => msg.id === aiMessageId)
              if (messageIndex !== -1) {
                messages.value[messageIndex].content = fullResponse
                messages.value[messageIndex].isStreaming = false
                messages.value[messageIndex].timestamp = new Date()
              }
              isLoading.value = false
            }
          )
        } else {
          // Non-streaming query
          const result = await hebrewRAGApi.queryDocuments(messageContent)
          
          if (result.success) {
            const messageIndex = messages.value.findIndex(msg => msg.id === aiMessageId)
            if (messageIndex !== -1) {
              messages.value[messageIndex].content = result.response
              messages.value[messageIndex].isStreaming = false
              messages.value[messageIndex].timestamp = new Date()
            }
          } else {
            throw new Error(result.error)
          }
          isLoading.value = false
        }
      } catch (apiError) {
        console.warn('API query failed, using mock response:', apiError)
        
        // Fallback to mock response
        const mockResponse = mockResponses[Math.floor(Math.random() * mockResponses.length)]
        
        if (useStreaming) {
          // Simulate streaming
          const words = mockResponse.split(' ')
          let currentResponse = ''
          
          for (let i = 0; i < words.length; i++) {
            await new Promise(resolve => setTimeout(resolve, 100 + Math.random() * 200))
            currentResponse += (i > 0 ? ' ' : '') + words[i]
            
            const messageIndex = messages.value.findIndex(msg => msg.id === aiMessageId)
            if (messageIndex !== -1) {
              messages.value[messageIndex].content = currentResponse
            }
          }
        }
        
        // Complete the response
        const messageIndex = messages.value.findIndex(msg => msg.id === aiMessageId)
        if (messageIndex !== -1) {
          messages.value[messageIndex].content = mockResponse
          messages.value[messageIndex].isStreaming = false
          messages.value[messageIndex].timestamp = new Date()
        }
        isLoading.value = false
      }
      
    } catch (err) {
      error.value = 'Failed to send message'
      console.error('Error sending message:', err)
      
      // Remove the AI message if there was an error
      const aiMessageIndex = messages.value.findIndex(msg => msg.id === aiMessageId && msg.sender === 'assistant')
      if (aiMessageIndex !== -1) {
        messages.value.splice(aiMessageIndex, 1)
      }
      
      isLoading.value = false
      throw err
    }
  }

  // Edit message (re-query with new content)
  async function editMessage(messageId, newContent) {
    try {
      error.value = null
      
      // Find the message to edit
      const messageIndex = messages.value.findIndex(msg => msg.id === messageId)
      if (messageIndex === -1) return

      // Update the message content locally
      messages.value[messageIndex].content = newContent
      messages.value[messageIndex].timestamp = new Date()

      // Remove all messages that came after this message
      messages.value.splice(messageIndex + 1)

      // If this was a user message, send a new query
      if (messages.value[messageIndex].sender === 'user') {
        await sendMessage(newContent, true)
      }
      
    } catch (err) {
      error.value = 'Failed to edit message'
      console.error('Error editing message:', err)
      throw err
    }
  }

  // Clear messages
  async function clearMessages() {
    try {
      messages.value = []
      hasMessageBeenSent.value = false
      isLoading.value = false
      error.value = null
    } catch (err) {
      error.value = 'Failed to clear messages'
      console.error('Error clearing messages:', err)
      throw err
    }
  }

  return {
    // State
    messages,
    isLoading,
    hasMessageBeenSent,
    error,
    documentStats,
    uploadStatus,
    
    // Actions
    checkHealth,
    loadDocumentStats,
    uploadDocuments,
    clearDocuments,
    sendMessage,
    editMessage,
    clearMessages
  }
}) 