"""Seed document ingestion script."""
import sys
import csv
from pathlib import Path
from datetime import date

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingestion.pipeline import IngestPipeline
from src.config import settings


def load_source_register(csv_path: Path) -> list:
    """Load source register from CSV."""
    sources = []
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse dates
            row['effective_from'] = date.fromisoformat(row['effective_from'])
            if row['effective_to']:
                row['effective_to'] = date.fromisoformat(row['effective_to'])
            else:
                row['effective_to'] = None
            
            if row['retrieved_on']:
                row['retrieved_on'] = date.fromisoformat(row['retrieved_on'])
            
            # Parse integer
            row['authority_level'] = int(row['authority_level'])
            
            sources.append(row)
    
    return sources


def ingest_documents(docs_dir: Path, source_register: list):
    """Ingest all documents from directory."""
    pipeline = IngestPipeline()
    
    results = []
    
    for source in source_register:
        doc_id = source['doc_id']
        
        # Look for matching file (try different extensions)
        doc_file = None
        for ext in ['.pdf', '.txt', '.PDF']:
            candidate = docs_dir / f"{doc_id}{ext}"
            if candidate.exists():
                doc_file = candidate
                break
        
        if not doc_file:
            print(f"Warning: No file found for {doc_id}, skipping...")
            continue
        
        print(f"Ingesting {doc_id} from {doc_file.name}...")
        
        try:
            # Read file
            with open(doc_file, 'rb') as f:
                file_bytes = f.read()
            
            # Ingest
            result = pipeline.ingest_document(
                file_bytes=file_bytes,
                filename=doc_file.name,
                metadata=source
            )
            
            print(f"  ✓ Indexed {result['chunks_indexed']} chunks")
            print(f"  ✓ Extracted {result['rules_extracted']} rules")
            results.append(result)
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            results.append({
                'doc_id': doc_id,
                'status': 'failed',
                'error': str(e)
            })
    
    return results


def main():
    """Main entry point."""
    print("=" * 60)
    print("Document Ingestion Script")
    print("=" * 60)
    
    # Paths
    data_dir = Path(__file__).parent.parent / "data"
    docs_dir = data_dir / "docs"
    source_csv = data_dir / "source_register.csv"
    
    # Check paths
    if not docs_dir.exists():
        print(f"Error: {docs_dir} does not exist")
        print("Please create data/docs/ and add your PDF documents")
        return 1
    
    if not source_csv.exists():
        print(f"Error: {source_csv} does not exist")
        print("Please create data/source_register.csv")
        return 1
    
    # Load source register
    print(f"\nLoading source register from {source_csv}...")
    sources = load_source_register(source_csv)
    print(f"Found {len(sources)} documents to ingest")
    
    # Ingest documents
    print(f"\nIngesting documents from {docs_dir}...\n")
    results = ingest_documents(docs_dir, sources)
    
    # Summary
    print("\n" + "=" * 60)
    print("Ingestion Summary")
    print("=" * 60)
    
    successful = [r for r in results if r.get('status') == 'completed']
    failed = [r for r in results if r.get('status') == 'failed']
    
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    
    if successful:
        total_chunks = sum(r['chunks_indexed'] for r in successful)
        total_rules = sum(r['rules_extracted'] for r in successful)
        print(f"Total chunks indexed: {total_chunks}")
        print(f"Total rules extracted: {total_rules}")
    
    print(f"\nVector store location: {settings.store_dir / 'chroma'}")
    print(f"SQLite database: {settings.store_dir / 'student_services.db'}")
    
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
