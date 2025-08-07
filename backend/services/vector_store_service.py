import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from qdrant_client.http.exceptions import UnexpectedResponse
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

try:
    from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
    FASTEMBED_AVAILABLE = True
except ImportError:
    FASTEMBED_AVAILABLE = False
    FastEmbedEmbeddings = None

from config import settings

logger = logging.getLogger(__name__)

class MockEmbeddings(Embeddings):
    """Mock embeddings for when sentence-transformers is not available"""
    
    def __init__(self, model_name: str = None, **kwargs):
        super().__init__()
        self.model_name = model_name or "mock-embeddings"
        logger.info(f"Using MockEmbeddings for {self.model_name}")
        
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Mock document embedding"""
        import random
        random.seed(42)  # For consistent results
        return [[random.random() for _ in range(1024)] for _ in texts]
    
    def embed_query(self, text: str) -> List[float]:
        """Mock query embedding"""
        import random
        random.seed(42)  # For consistent results
        return [random.random() for _ in range(1024)]

class HebrewEmbeddingService:
    """Service for generating embeddings optimized for Hebrew text using FastEmbed"""
    
    def __init__(self):
        # Use multilingual-e5-large for excellent Hebrew support
        self.model_name = "intfloat/multilingual-e5-large"
        self.langchain_embeddings = None
        
    async def initialize(self):
        """Initialize the FastEmbed embedding model"""
        try:
            logger.info(f"Loading FastEmbed model: {self.model_name}")
            
            if not FASTEMBED_AVAILABLE:
                logger.warning("FastEmbed not available, using mock embeddings")
                self.langchain_embeddings = MockEmbeddings(self.model_name)
                return
            
            # Initialize FastEmbed embeddings - designed specifically for retrieval
            try:
                self.langchain_embeddings = FastEmbedEmbeddings(
                    model_name=self.model_name,
                    max_length=512,  # Good for document chunks
                    doc_embed_type="passage",  # Optimized for document embedding
                    cache_dir="./storage/fastembed_cache"
                )
                logger.info("FastEmbed model initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize FastEmbed: {e}, using mock embeddings")
                self.langchain_embeddings = MockEmbeddings(self.model_name)
            
        except Exception as e:
            logger.error(f"Failed to initialize embedding service: {e}")
            # Use mock as fallback
            self.langchain_embeddings = MockEmbeddings(self.model_name)
    
    def preprocess_hebrew_text(self, text: str) -> str:
        """Preprocess Hebrew text for better embedding quality"""
        # Basic Hebrew text preprocessing
        # Remove extra whitespace, normalize direction markers, etc.
        cleaned_text = ' '.join(text.split())
        
        # Add query prefix for e5 models (improves retrieval quality)
        if not cleaned_text.startswith("query:") and not cleaned_text.startswith("passage:"):
            # For queries, we'll add "query:" prefix in the retrieval method
            # For documents, we'll add "passage:" prefix
            pass
            
        return cleaned_text

class QdrantVectorService:
    """Service for managing Qdrant vector storage"""
    
    def __init__(self):
        self.client = None
        self.collection_name = settings.qdrant_collection_name
        self.embedding_service = HebrewEmbeddingService()
        self.vector_store = None
        
    async def initialize(self):
        """Initialize Qdrant client and collection"""
        try:
            # Initialize embedding service
            await self.embedding_service.initialize()
            
            # Initialize Qdrant client
            logger.info(f"Connecting to Qdrant at {settings.qdrant_path}")
            self.client = QdrantClient(path=settings.qdrant_path)
            
            # Create collection if it doesn't exist
            await self._ensure_collection_exists()
            
            # Initialize LangChain vector store
            if self.embedding_service.langchain_embeddings is None:
                logger.error("No embeddings available, cannot initialize vector store")
                raise RuntimeError("Embedding service initialization failed")
            
            try:
                self.vector_store = QdrantVectorStore(
                    client=self.client,
                    collection_name=self.collection_name,
                    embedding=self.embedding_service.langchain_embeddings
                )
            except Exception as e:
                if "dimensions" in str(e).lower():
                    logger.warning(f"Vector dimension mismatch: {e}")
                    logger.info("Recreating collection with correct dimensions...")
                    
                    # Delete and recreate collection
                    try:
                        self.client.delete_collection(self.collection_name)
                    except:
                        pass  # Collection might not exist
                    
                    # Recreate collection with correct dimensions
                    await self._ensure_collection_exists()
                    
                    # Try again
                    self.vector_store = QdrantVectorStore(
                        client=self.client,
                        collection_name=self.collection_name,
                        embedding=self.embedding_service.langchain_embeddings
                    )
                else:
                    raise
            
            logger.info("Qdrant vector service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant service: {e}")
            raise
    
    async def _ensure_collection_exists(self):
        """Create collection if it doesn't exist"""
        try:
            collection_info = self.client.get_collection(collection_name=self.collection_name)
            logger.info(f"Collection '{self.collection_name}' already exists")
        except (UnexpectedResponse, ValueError):
            logger.info(f"Creating collection '{self.collection_name}'")
            # Get the actual dimension from the embedding model
            embedding_dim = 1024  # multilingual-e5-large uses 1024 dimensions
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=embedding_dim,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Collection '{self.collection_name}' created successfully")
    
    async def add_documents(
        self, 
        documents: List[Document], 
        batch_size: int = 100
    ) -> List[str]:
        """Add documents to the vector store"""
        if self.vector_store is None:
            raise RuntimeError("Vector store not initialized")
        
        try:
            logger.info(f"Adding {len(documents)} documents to vector store")
            
            # Process documents in batches
            document_ids = []
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                batch_ids = self.vector_store.add_documents(batch)
                document_ids.extend(batch_ids)
                logger.info(f"Processed batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}")
            
            logger.info(f"Successfully added {len(documents)} documents")
            return document_ids
            
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise
    
    async def search_similar(
        self, 
        query: str, 
        k: int = 5,
        score_threshold: float = 0.5
    ) -> List[Document]:
        """Search for similar documents"""
        if self.vector_store is None:
            raise RuntimeError("Vector store not initialized")
        
        try:
            logger.info(f"Searching for documents similar to query (k={k})")
            
            # Use the vector store's similarity search
            retriever = self.vector_store.as_retriever(
                search_kwargs={
                    "k": k,
                    "score_threshold": score_threshold
                }
            )
            
            results = retriever.get_relevant_documents(query)
            logger.info(f"Found {len(results)} similar documents")
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search documents: {e}")
            raise
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        if self.client is None:
            raise RuntimeError("Qdrant client not initialized")
        
        try:
            collection_info = self.client.get_collection(self.collection_name)
            return {
                "total_documents": collection_info.points_count,
                "vector_size": collection_info.config.params.vectors.size,
                "distance_metric": collection_info.config.params.vectors.distance.value
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {}
    
    async def delete_collection(self):
        """Delete the entire collection"""
        if self.client is None:
            raise RuntimeError("Qdrant client not initialized")
        
        try:
            self.client.delete_collection(self.collection_name)
            logger.info(f"Collection '{self.collection_name}' deleted")
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            raise

# Global vector service instance
vector_service = QdrantVectorService()