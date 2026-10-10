"""Hybrid retriever combining dense and sparse search."""
from typing import List, Dict, Any, Optional
from datetime import date
from src.retrieval.embeddings import get_embeddings
from src.retrieval.vector_store import get_vector_store
from src.config import settings


class HybridRetriever:
    """Hybrid retriever with dense (vector) and sparse (BM25) search."""
    
    def __init__(self):
        self.embeddings = get_embeddings()
        self.vector_store = get_vector_store()
        self.mode = settings.retrieval_mode
        self.top_k = settings.top_k
    
    def retrieve(
        self,
        query: str,
        as_of_date: date,
        filter_metadata: Optional[Dict[str, Any]] = None,
        k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks for a query.
        
        Args:
            query: User query
            as_of_date: Date for filtering valid documents
            filter_metadata: Additional metadata filters
            k: Number of results (defaults to settings.top_k)
        
        Returns:
            List of retrieved chunks with metadata
        """
        k = k or self.top_k
        
        if self.mode == "dense":
            return self._dense_retrieve(query, as_of_date, filter_metadata, k)
        elif self.mode == "hybrid":
            return self._hybrid_retrieve(query, as_of_date, filter_metadata, k)
        else:
            raise ValueError(f"Unknown retrieval mode: {self.mode}")
    
    def _dense_retrieve(
        self,
        query: str,
        as_of_date: date,
        filter_metadata: Optional[Dict[str, Any]],
        k: int
    ) -> List[Dict[str, Any]]:
        """Dense retrieval using embeddings."""
        # Embed query
        query_embedding = self.embeddings.embed_query(query)
        
        # Search vector store
        # Note: ChromaDB filtering for date ranges is limited in simple setup
        # For MVP, we retrieve more and filter in Python
        results = self.vector_store.similarity_search(
            query_embedding,
            k=k * 2,  # Get more for filtering
            filter=filter_metadata
        )
        
        # Filter by date validity
        valid_results = []
        for result in results:
            if self._is_valid_on_date(result['metadata'], as_of_date):
                valid_results.append(result)
                if len(valid_results) >= k:
                    break
        
        return valid_results
    
    def _hybrid_retrieve(
        self,
        query: str,
        as_of_date: date,
        filter_metadata: Optional[Dict[str, Any]],
        k: int
    ) -> List[Dict[str, Any]]:
        """
        Hybrid retrieval combining dense and sparse (simplified for MVP).
        
        For a full implementation, this would use BM25 + dense retrieval
        with reciprocal rank fusion. For MVP, we use dense only.
        """
        # For MVP, fall back to dense retrieval
        # Full implementation would add BM25 here
        return self._dense_retrieve(query, as_of_date, filter_metadata, k)
    
    def _is_valid_on_date(self, metadata: Dict[str, Any], as_of_date: date) -> bool:
        """Check if a document is valid on the given date."""
        effective_from = metadata.get('effective_from')
        effective_to = metadata.get('effective_to')
        
        if not effective_from:
            return True
        
        # Parse dates
        try:
            if isinstance(effective_from, str):
                if not effective_from:
                    eff_from = date.min
                else:
                    eff_from = date.fromisoformat(effective_from)
            else:
                eff_from = effective_from
            
            if effective_to and isinstance(effective_to, str) and effective_to:
                eff_to = date.fromisoformat(effective_to)
            else:
                eff_to = date.max
        except:
            return True  # If parsing fails, include the doc
        
        return eff_from <= as_of_date < eff_to
