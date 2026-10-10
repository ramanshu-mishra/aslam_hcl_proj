"""Document parsing utilities."""
import PyPDF2
from pathlib import Path
from typing import List, Dict, Any
import io


def extract_text_from_pdf(file_path: Path) -> List[Dict[str, Any]]:
    """
    Extract text from PDF file.
    
    Returns:
        List of page dicts with page_num and text
    """
    pages = []
    
    try:
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            
            for page_num, page in enumerate(pdf_reader.pages, start=1):
                text = page.extract_text()
                pages.append({
                    'page_num': page_num,
                    'text': text,
                    'needs_ocr': len(text.strip()) < 50  # Heuristic for scanned pages
                })
    
    except Exception as e:
        raise RuntimeError(f"Failed to parse PDF: {e}")
    
    return pages


def extract_text_from_bytes(file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
    """Extract text from file bytes."""
    if filename.lower().endswith('.pdf'):
        return _extract_pdf_from_bytes(file_bytes)
    elif filename.lower().endswith('.txt'):
        return [{
            'page_num': 1,
            'text': file_bytes.decode('utf-8'),
            'needs_ocr': False
        }]
    else:
        raise ValueError(f"Unsupported file type: {filename}")


def _extract_pdf_from_bytes(file_bytes: bytes) -> List[Dict[str, Any]]:
    """Extract text from PDF bytes."""
    pages = []
    
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        
        for page_num, page in enumerate(pdf_reader.pages, start=1):
            text = page.extract_text()
            pages.append({
                'page_num': page_num,
                'text': text,
                'needs_ocr': len(text.strip()) < 50
            })
    
    except Exception as e:
        raise RuntimeError(f"Failed to parse PDF bytes: {e}")
    
    return pages


def detect_structure(pages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Detect document structure (sections, headings).
    
    This is a simplified implementation for MVP.
    """
    structure = {
        'sections': [],
        'has_toc': False
    }
    
    # Simple heuristic: lines that are all caps or end with colon are headings
    for page in pages:
        lines = page['text'].split('\n')
        for line in lines:
            line = line.strip()
            if len(line) > 5 and (line.isupper() or line.endswith(':')):
                structure['sections'].append({
                    'title': line,
                    'page': page['page_num']
                })
    
    return structure
