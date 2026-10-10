"""Vector store using ChromaDB."""
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from src.config import settings


class VectorStore:
    """ChromaDB vector store wrapper."""
    
    def __init__(self, persist_directory: str = None):
        persist_dir = persist_directory or str(settings.store_dir / "chroma")
        
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_documents(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ):
        """Add documents to the vector store."""
        self.collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
    
    def similarity_search(
        self,
        query_embedding: List[float],
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=filter
        )
        
        # Format results
        documents = []
        if results['ids']:
            for i in range(len(results['ids'][0])):
                doc = {
                    'id': results['ids'][0][i],
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                }
                documents.append(doc)
        
        return documents
    
    def delete_by_doc_id(self, doc_id: str):
        """Delete all chunks for a document."""
        self.collection.delete(where={"doc_id": doc_id})
    
    def count(self) -> int:
        """Get total number of chunks."""
        return self.collection.count()


# Global instance
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get or create global vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
