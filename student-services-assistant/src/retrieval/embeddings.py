"""Embedding model wrapper."""
from typing import List
from sentence_transformers import SentenceTransformer
from src.config import settings


class EmbeddingModel:
    """Wrapper for sentence-transformers embeddings."""
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.embed_model
        self.model = SentenceTransformer(self.model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query text."""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents."""
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return [emb.tolist() for emb in embeddings]


# Global instance
_embeddings: EmbeddingModel = None


def get_embeddings() -> EmbeddingModel:
    """Get or create global embeddings instance."""
    global _embeddings
    if _embeddings is None:
        _embeddings = EmbeddingModel()
    return _embeddings
