"""Text chunking with semantic awareness."""
from typing import List, Dict, Any
import re


def chunk_text(
    pages: List[Dict[str, Any]],
    target_tokens: int = 350,
    overlap_tokens: int = 50
) -> List[Dict[str, Any]]:
    """
    Chunk text from pages into smaller segments.
    
    Args:
        pages: List of page dicts with text
        target_tokens: Target size per chunk (approximate)
        overlap_tokens: Overlap between chunks
    
    Returns:
        List of chunk dicts with text and metadata
    """
    chunks = []
    chunk_id = 0
    
    for page in pages:
        text = page['text']
        page_num = page['page_num']
        
        # Split into sentences (simple approach)
        sentences = _split_sentences(text)
        
        current_chunk = []
        current_tokens = 0
        
        for sentence in sentences:
            sentence_tokens = _estimate_tokens(sentence)
            
            if current_tokens + sentence_tokens > target_tokens and current_chunk:
                # Save current chunk
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    'chunk_id': f"chunk_{chunk_id}",
                    'text': chunk_text,
                    'page_num': page_num,
                    'token_count': current_tokens
                })
                chunk_id += 1
                
                # Start new chunk with overlap
                overlap_sentences = current_chunk[-2:] if len(current_chunk) >= 2 else current_chunk
                current_chunk = overlap_sentences.copy()
                current_tokens = sum(_estimate_tokens(s) for s in current_chunk)
            
            current_chunk.append(sentence)
            current_tokens += sentence_tokens
        
        # Save remaining chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append({
                'chunk_id': f"chunk_{chunk_id}",
                'text': chunk_text,
                'page_num': page_num,
                'token_count': current_tokens
            })
            chunk_id += 1
    
    return chunks


def _split_sentences(text: str) -> List[str]:
    """Split text into sentences."""
    # Simple sentence splitter
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def _estimate_tokens(text: str) -> int:
    """Estimate token count (rough approximation)."""
    # Rough estimate: 1 token ~= 4 characters
    return len(text) // 4
