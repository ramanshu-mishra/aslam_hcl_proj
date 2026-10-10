"""Test script to verify setup and basic functionality."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        from src.config import settings
        print("  ✓ Config")
        
        from src.db.connection import get_db
        print("  ✓ Database")
        
        from src.llm.client import get_llm_client
        print("  ✓ LLM Client")
        
        from src.retrieval.embeddings import get_embeddings
        print("  ✓ Embeddings")
        
        from src.retrieval.vector_store import get_vector_store
        print("  ✓ Vector Store")
        
        from src.ingestion.pipeline import IngestPipeline
        print("  ✓ Ingestion Pipeline")
        
        from src.tools.factory import list_tools
        print("  ✓ Tools")
        
        from src.precedence.engine import PrecedenceEngine
        print("  ✓ Precedence Engine")
        
        from src.graph.workflow import create_workflow
        print("  ✓ Graph Workflow")
        
        print("\n✓ All imports successful!")
        return True
        
    except Exception as e:
        print(f"\n✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database():
    """Test database connection."""
    print("\nTesting database...")
    
    try:
        from src.db.connection import get_db
        
        db = get_db()
        with db.transaction() as conn:
            cursor = conn.execute("SELECT COUNT(*) as count FROM students")
            count = cursor.fetchone()['count']
            print(f"  ✓ Database connected ({count} students)")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Database test failed: {e}")
        return False


def test_llm():
    """Test LLM connection."""
    print("\nTesting LLM...")
    
    try:
        from src.llm.client import get_llm_client
        from src.config import settings
        
        llm = get_llm_client()
        
        if settings.mock_llm:
            print("  ⚠ Mock mode enabled")
            return True
        
        # Try health check
        if llm.health_check():
            print("  ✓ LLM connected")
            return True
        else:
            print("  ⚠ LLM not accessible (may need to start Ollama)")
            return True  # Don't fail on this
            
    except Exception as e:
        print(f"  ✗ LLM test failed: {e}")
        return False


def test_embeddings():
    """Test embedding model."""
    print("\nTesting embeddings...")
    
    try:
        from src.retrieval.embeddings import get_embeddings
        
        embeddings = get_embeddings()
        
        # Test embedding
        test_text = "This is a test sentence."
        embedding = embeddings.embed_query(test_text)
        
        print(f"  ✓ Embeddings working (dimension: {len(embedding)})")
        return True
        
    except Exception as e:
        print(f"  ✗ Embeddings test failed: {e}")
        return False


def test_vector_store():
    """Test vector store."""
    print("\nTesting vector store...")
    
    try:
        from src.retrieval.vector_store import get_vector_store
        
        vs = get_vector_store()
        count = vs.count()
        
        print(f"  ✓ Vector store connected ({count} chunks)")
        return True
        
    except Exception as e:
        print(f"  ✗ Vector store test failed: {e}")
        return False


def test_tools():
    """Test tool functions."""
    print("\nTesting tools...")
    
    try:
        from src.tools.factory import list_tools, invoke_tool
        
        tools = list_tools()
        print(f"  ✓ {len(tools)} tools available")
        
        # Try to get a student profile
        result = invoke_tool('get_student_profile', student_id='S1001')
        if 'error' not in result:
            print(f"  ✓ Tool execution works (found: {result.get('name', 'N/A')})")
        else:
            print(f"  ⚠ No test data loaded yet")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Tools test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Setup Verification Tests")
    print("=" * 60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Database", test_database()))
    results.append(("LLM", test_llm()))
    results.append(("Embeddings", test_embeddings()))
    results.append(("Vector Store", test_vector_store()))
    results.append(("Tools", test_tools()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name:20s} {status}")
    
    all_passed = all(passed for _, passed in results)
    
    if all_passed:
        print("\n✓ All tests passed! System is ready.")
        return 0
    else:
        print("\n⚠ Some tests failed. Check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
