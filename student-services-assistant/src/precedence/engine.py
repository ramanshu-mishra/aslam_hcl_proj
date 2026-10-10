"""Precedence engine implementing Annex A conflict resolution logic."""
from datetime import date
from typing import List, Dict, Any, Optional, Literal


class PrecedenceEngine:
    """
    Implements the Source Precedence Policy (Annex A) for resolving conflicts.
    
    Priority order:
    1. Supersession (effective_to/supersedes)
    2. Authority Level (1 > 2 > 3 > 4 > 5)
    3. Recency (newer effective_from wins)
    """
    
    def resolve(
        self,
        chunks: List[Dict[str, Any]],
        as_of_date: date
    ) -> List[Dict[str, Any]]:
        """
        Resolve conflicts among chunks using precedence rules.
        
        Args:
            chunks: List of chunk dicts with metadata
            as_of_date: Date for validity checking
            
        Returns:
            Filtered list of chunks with conflicts resolved
        """
        if len(chunks) <= 1:
            return chunks
        
        # Step 1: Filter by validity (effective_from <= as_of_date < effective_to)
        valid_chunks = [
            chunk for chunk in chunks
            if self._is_valid_on_date(chunk, as_of_date)
        ]
        
        if len(valid_chunks) <= 1:
            return valid_chunks
        
        # Step 2: Group by topic (if multiple docs discuss same thing)
        # For MVP, we assume conflicts are between chunks from different docs
        docs = set(chunk['doc_id'] for chunk in valid_chunks)
        
        if len(docs) == 1:
            # All from same doc - no conflict
            return valid_chunks
        
        # Step 3: Apply precedence rules
        resolved = self._apply_precedence(valid_chunks)
        
        return resolved
    
    def detect_conflicts(
        self,
        chunks: List[Dict[str, Any]],
        as_of_date: date
    ) -> List[Dict[str, Any]]:
        """
        Detect conflicts without resolving them.
        
        Returns:
            List of conflict descriptions
        """
        valid_chunks = [
            chunk for chunk in chunks
            if self._is_valid_on_date(chunk, as_of_date)
        ]
        
        if len(valid_chunks) <= 1:
            return []
        
        docs = set(chunk['doc_id'] for chunk in valid_chunks)
        if len(docs) == 1:
            return []
        
        # Build conflict info
        conflicts = []
        doc_groups = {}
        
        for chunk in valid_chunks:
            doc_id = chunk['doc_id']
            if doc_id not in doc_groups:
                doc_groups[doc_id] = []
            doc_groups[doc_id].append(chunk)
        
        if len(doc_groups) > 1:
            conflict = {
                'docs': list(doc_groups.keys()),
                'summary': f"Multiple sources found: {', '.join(doc_groups.keys())}",
                'chunk_count': {doc_id: len(chunks) for doc_id, chunks in doc_groups.items()}
            }
            conflicts.append(conflict)
        
        return conflicts
    
    def _is_valid_on_date(self, chunk: Dict[str, Any], as_of_date: date) -> bool:
        """Check if chunk is valid on the given date."""
        effective_from = chunk.get('effective_from')
        effective_to = chunk.get('effective_to')
        
        if not effective_from:
            return True
        
        # Parse dates if they're strings
        if isinstance(effective_from, str):
            effective_from = date.fromisoformat(effective_from)
        if effective_to and isinstance(effective_to, str):
            effective_to = date.fromisoformat(effective_to)
        
        # Check validity window
        if effective_from > as_of_date:
            return False
        
        if effective_to and effective_to <= as_of_date:
            return False
        
        return True
    
    def _apply_precedence(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply precedence rules to resolve conflicts.
        
        Annex A rules:
        1. Supersession: If doc B supersedes doc A, only keep B
        2. Authority: Lower authority_level wins (1 > 2 > 3 > 4 > 5)
        3. Recency: Newer effective_from wins
        """
        # Rule 1: Check supersession
        superseded_docs = set()
        for chunk in chunks:
            supersedes = chunk.get('supersedes', '')
            if supersedes:
                superseded_docs.add(supersedes)
        
        if superseded_docs:
            chunks = [c for c in chunks if c['doc_id'] not in superseded_docs]
        
        if len(chunks) <= 1:
            return chunks
        
        # Rule 2: Authority level (lower is better)
        min_authority = min(chunk.get('authority_level', 5) for chunk in chunks)
        chunks = [c for c in chunks if c.get('authority_level', 5) == min_authority]
        
        if len(chunks) <= 1:
            return chunks
        
        # Rule 3: Recency (newer effective_from)
        chunks_with_dates = []
        for chunk in chunks:
            eff_from = chunk.get('effective_from')
            if isinstance(eff_from, str):
                eff_from = date.fromisoformat(eff_from)
            chunks_with_dates.append((chunk, eff_from or date.min))
        
        max_date = max(d for _, d in chunks_with_dates)
        chunks = [c for c, d in chunks_with_dates if d == max_date]
        
        return chunks
    
    def get_resolution_type(
        self,
        before_count: int,
        after_count: int,
        conflicts: List[Dict[str, Any]]
    ) -> Literal['supersession', 'authority', 'recency', 'unresolved']:
        """Determine how conflicts were resolved."""
        if after_count == before_count:
            return 'unresolved'
        
        # This is a simplified heuristic
        if conflicts and 'supersedes' in str(conflicts):
            return 'supersession'
        
        # Could enhance this by tracking the actual resolution path
        return 'authority'
