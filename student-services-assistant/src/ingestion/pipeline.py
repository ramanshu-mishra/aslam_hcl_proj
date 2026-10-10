"""Main ingestion pipeline."""
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, date
import json

from src.ingestion.parse import extract_text_from_bytes, detect_structure
from src.ingestion.chunker import chunk_text
from src.retrieval.embeddings import get_embeddings
from src.retrieval.vector_store import get_vector_store
from src.db.connection import get_db
from src.config import settings


class IngestPipeline:
    """Pipeline for ingesting documents into the system."""
    
    def __init__(self):
        self.db = get_db()
        self.vector_store = get_vector_store()
        self.embeddings = get_embeddings()
    
    def ingest_document(
        self,
        file_bytes: bytes,
        filename: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Ingest a document through the full pipeline.
        
        Args:
            file_bytes: Raw file bytes
            filename: Original filename
            metadata: Document metadata (doc_id, title, etc.)
        
        Returns:
            Ingestion result with statistics
        """
        doc_id = metadata['doc_id']
        
        # Step 1: Parse document
        pages = extract_text_from_bytes(file_bytes, filename)
        
        # Step 2: Detect structure
        structure = detect_structure(pages)
        
        # Step 3: Chunk text
        chunks = chunk_text(pages, target_tokens=settings.chunk_target_tokens)
        
        # Step 4: Generate embeddings
        chunk_texts = [chunk['text'] for chunk in chunks]
        embeddings = self.embeddings.embed_documents(chunk_texts)
        
        # Step 5: Store in vector database
        chunk_ids = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_id = f"{doc_id}_chunk_{i}"
            chunk_ids.append(chunk_id)
            
            # Add metadata to chunk
            chunk_metadata = {
                'doc_id': doc_id,
                'chunk_id': chunk_id,
                'page_num': chunk['page_num'],
                'title': metadata['title'],
                'authority_level': metadata['authority_level'],
                'doc_type': metadata['doc_type'],
                'version': metadata['version'],
                'effective_from': str(metadata['effective_from']),
                'effective_to': str(metadata.get('effective_to', '')),
                'supersedes': metadata.get('supersedes', ''),
            }
            
            self.vector_store.add_documents(
                texts=[chunk['text']],
                embeddings=[embedding],
                metadatas=[chunk_metadata],
                ids=[chunk_id]
            )
        
        # Step 6: Register in source_register
        self._register_source(metadata, len(chunks))
        
        # Step 7: Extract rules (simplified for MVP)
        rules_extracted = self._extract_rules(chunks, metadata)
        
        return {
            'doc_id': doc_id,
            'chunks_indexed': len(chunks),
            'rules_extracted': len(rules_extracted),
            'pages': len(pages),
            'status': 'completed'
        }
    
    def _register_source(self, metadata: Dict[str, Any], chunk_count: int):
        """Register document in source_register table."""
        with self.db.transaction() as conn:
            # Check if already exists
            cursor = conn.execute(
                "SELECT doc_id FROM source_register WHERE doc_id = ?",
                (metadata['doc_id'],)
            )
            
            if cursor.fetchone():
                # Update existing
                conn.execute(
                    """
                    UPDATE source_register
                    SET chunk_count = ?, ingested_at = ?
                    WHERE doc_id = ?
                    """,
                    (chunk_count, datetime.now().isoformat(), metadata['doc_id'])
                )
            else:
                # Insert new
                conn.execute(
                    """
                    INSERT INTO source_register (
                        doc_id, title, issuer, authority_level, doc_type,
                        version, effective_from, effective_to, supersedes,
                        scope_programmes, scope_batches, provenance,
                        retrieved_on, synthetic, chunk_count, rule_count, ingested_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        metadata['doc_id'],
                        metadata['title'],
                        metadata['issuer'],
                        metadata['authority_level'],
                        metadata['doc_type'],
                        metadata['version'],
                        str(metadata['effective_from']),
                        str(metadata.get('effective_to', '')),
                        metadata.get('supersedes', ''),
                        metadata.get('scope_programmes', 'ALL'),
                        metadata.get('scope_batches', 'ALL'),
                        metadata.get('provenance', ''),
                        str(metadata.get('retrieved_on', date.today())),
                        metadata.get('synthetic', 'N'),
                        chunk_count,
                        0,  # Will be updated after rule extraction
                        datetime.now().isoformat()
                    )
                )
    
    def _extract_rules(
        self,
        chunks: List[Dict[str, Any]],
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extract rules from chunks (simplified for MVP).
        
        This is a basic pattern-matching approach. Full implementation
        would use LLM-based extraction.
        """
        rules = []
        
        # Simple patterns for common rules
        patterns = [
            (r'minimum.*?(\d+)%.*?attendance', 'min_attendance_pct'),
            (r'CGPA.*?(\d+\.?\d*)', 'min_cgpa'),
            (r'(\d+).*?credits?.*?required', 'required_credits'),
        ]
        
        import re
        
        for chunk in chunks:
            text = chunk['text']
            
            for pattern, param in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    rule = {
                        'parameter': param,
                        'value': match,
                        'source_doc_id': metadata['doc_id'],
                        'source_section': f"Page {chunk['page_num']}",
                        'effective_from': str(metadata['effective_from']),
                        'effective_to': str(metadata.get('effective_to', ''))
                    }
                    rules.append(rule)
        
        # Store rules in database
        if rules:
            with self.db.transaction() as conn:
                for rule in rules:
                    rule_id = f"{metadata['doc_id']}_{rule['parameter']}_{hash(rule['value']) % 10000}"
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO rule_registry (
                            rule_id, description, parameter, operator, value,
                            scope_programmes, scope_batches, effective_from,
                            effective_to, source_doc_id, source_section, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            rule_id,
                            f"Extracted from {metadata['title']}",
                            rule['parameter'],
                            '>=',
                            rule['value'],
                            'ALL',
                            'ALL',
                            rule['effective_from'],
                            rule['effective_to'],
                            rule['source_doc_id'],
                            rule['source_section'],
                            'active'
                        )
                    )
                
                # Update rule count
                conn.execute(
                    "UPDATE source_register SET rule_count = ? WHERE doc_id = ?",
                    (len(rules), metadata['doc_id'])
                )
        
        return rules
