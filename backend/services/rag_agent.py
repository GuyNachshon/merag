import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
import asyncio

from agno.agent import Agent
from agno.knowledge.langchain import LangChainKnowledgeBase
from agno.models.ollama import Ollama
from langchain_core.documents import Document

from config import settings
from services.vector_store_service import vector_service
from services.llm_service import hebrew_llm_service
from services.document_processor import document_processor

logger = logging.getLogger(__name__)

class HebrewRAGAgent:
    """Hebrew Agentic RAG system using Agno framework"""
    
    def __init__(self):
        self.agent = None
        self.knowledge_base = None
        self.initialized = False
        
    async def initialize(self):
        """Initialize the RAG agent and all dependencies"""
        if self.initialized:
            return
            
        try:
            logger.info("Initializing Hebrew RAG Agent...")
            
            # Initialize all services
            await vector_service.initialize()
            await hebrew_llm_service.initialize()
            await document_processor.initialize()
            
            # Create knowledge base from vector store
            retriever = vector_service.vector_store.as_retriever(
                search_kwargs={
                    "k": 5,  # Return top 5 relevant chunks
                    "score_threshold": 0.5
                }
            )
            
            self.knowledge_base = LangChainKnowledgeBase(retriever=retriever)
            
            # Create the Agno agent with Hebrew configuration
            self.agent = Agent(
                model=Ollama(
                    id=settings.llm_model,
                    host=settings.ollama_host
                ),
                knowledge=self.knowledge_base,
                description="""
אתה עוזר AI מתמחה בעיבוד מסמכים בעברית.
אתה עונה על שאלות בהתבסס על המסמכים שהועלו למערכת.
תמיד תענה בעברית בצורה ברורה ומדויקת.
אם אין לך מספיק מידע לענות על השאלה, אמור זאת בבירור.
                """.strip(),
                instructions=[
                    "השתמש במידע מבסיס הנתונים כדי לענות על שאלות",
                    "תענה תמיד בעברית",
                    "אם אין לך מספיק מידע, אמור זאת בבירור",
                    "תן מקורות למידע שאתה משתמש בו",
                    "תהיה מדויק ולא תמציא מידע"
                ],
                markdown=True,
                search_knowledge=True,
                show_tool_calls=False,
                debug_mode=False
            )
            
            self.initialized = True
            logger.info("Hebrew RAG Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG agent: {e}")
            raise
    
    async def add_documents(self, documents: List[Document]) -> Dict[str, Any]:
        """Add documents to the knowledge base"""
        if not self.initialized:
            await self.initialize()
        
        try:
            logger.info(f"Adding {len(documents)} documents to knowledge base")
            
            # Add documents to vector store
            document_ids = await vector_service.add_documents(documents)
            
            # Get updated stats
            stats = await vector_service.get_collection_stats()
            
            return {
                "success": True,
                "documents_added": len(documents),
                "document_ids": document_ids,
                "total_documents": stats.get("total_documents", 0),
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            return {
                "success": False,
                "documents_added": 0,
                "document_ids": [],
                "total_documents": 0,
                "error": str(e)
            }
    
    async def process_and_add_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """Process files and add them to knowledge base"""
        if not self.initialized:
            await self.initialize()
        
        try:
            # Process documents
            processing_result = await document_processor.process_multiple_documents(file_paths)
            
            if not processing_result["successful"]:
                return {
                    "success": False,
                    "error": "No documents were successfully processed",
                    "processing_details": processing_result
                }
            
            # Collect all document chunks
            all_documents = []
            for result in processing_result["successful"]:
                all_documents.extend(result["documents"])
            
            # Add to knowledge base
            add_result = await self.add_documents(all_documents)
            
            return {
                "success": add_result["success"],
                "files_processed": len(processing_result["successful"]),
                "files_failed": len(processing_result["failed"]),
                "total_chunks": len(all_documents),
                "documents_added": add_result["documents_added"],
                "total_documents": add_result["total_documents"],
                "processing_details": processing_result,
                "error": add_result["error"]
            }
            
        except Exception as e:
            logger.error(f"Failed to process and add files: {e}")
            return {
                "success": False,
                "error": str(e),
                "files_processed": 0,
                "files_failed": len(file_paths),
                "total_chunks": 0,
                "documents_added": 0
            }
    
    async def query(self, question: str, stream: bool = False) -> Dict[str, Any]:
        """Query the RAG agent"""
        if not self.initialized:
            await self.initialize()
        
        try:
            logger.info(f"Processing query: {question[:100]}...")
            
            if stream:
                # Return streaming response generator
                return {
                    "success": True,
                    "response_generator": self._stream_response(question),
                    "error": None
                }
            else:
                # Get complete response
                response = self.agent.run(question)
                
                return {
                    "success": True,
                    "response": response.content,
                    "error": None,
                    "metadata": {
                        "model_used": settings.llm_model,
                        "search_performed": True
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to process query: {e}")
            return {
                "success": False,
                "response": None,
                "error": str(e)
            }
    
    async def _stream_response(self, question: str) -> AsyncGenerator[str, None]:
        """Generate streaming response"""
        try:
            # Use the actual LLM service for streaming
            from services.llm_service import hebrew_llm_service
            
            # Get relevant documents from vector store
            relevant_docs = await vector_service.search_similar(question, k=5)
            
            # Create context from relevant documents
            context = "\n\n".join([doc.page_content for doc in relevant_docs])
            
            # Stream response using the LLM service
            async for token in hebrew_llm_service.generate_hebrew_response_stream(
                query=question,
                context=context
            ):
                yield token
                
        except Exception as e:
            logger.error(f"Failed to stream response: {e}")
            yield f"שגיאה: {str(e)}"
    
    async def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base"""
        if not self.initialized:
            await self.initialize()
        
        try:
            stats = await vector_service.get_collection_stats()
            return {
                "success": True,
                "stats": stats,
                "error": None
            }
        except Exception as e:
            logger.error(f"Failed to get knowledge base stats: {e}")
            return {
                "success": False,
                "stats": {},
                "error": str(e)
            }
    
    async def clear_knowledge_base(self) -> Dict[str, Any]:
        """Clear all documents from the knowledge base"""
        if not self.initialized:
            await self.initialize()
        
        try:
            await vector_service.delete_collection()
            # Reinitialize to recreate the collection
            await vector_service.initialize()
            
            return {
                "success": True,
                "message": "Knowledge base cleared successfully",
                "error": None
            }
        except Exception as e:
            logger.error(f"Failed to clear knowledge base: {e}")
            return {
                "success": False,
                "message": None,
                "error": str(e)
            }

class RAGService:
    """Service wrapper for the Hebrew RAG Agent"""
    
    def __init__(self):
        self.rag_agent = HebrewRAGAgent()
        
    async def initialize(self):
        """Initialize the RAG service"""
        await self.rag_agent.initialize()
        logger.info("RAG Service initialized")
    
    async def add_documents_from_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """Add documents from file paths"""
        return await self.rag_agent.process_and_add_files(file_paths)
    
    async def query_documents(self, question: str, stream: bool = False) -> Dict[str, Any]:
        """Query the document collection"""
        return await self.rag_agent.query(question, stream)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        return await self.rag_agent.get_knowledge_base_stats()
    
    async def clear_documents(self) -> Dict[str, Any]:
        """Clear all documents"""
        return await self.rag_agent.clear_knowledge_base()

# Global RAG service instance
rag_service = RAGService()