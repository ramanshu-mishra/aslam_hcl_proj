"""FastAPI application entry point."""
from fastapi import FastAPI, HTTPException, Header, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import uuid
from datetime import datetime, date as date_type

from src.api.models import (
    AskRequest, AskResponse, IngestResponse, HealthResponse,
    SourceInfo, Citation
)
from src.config import settings
from src.db.connection import get_db

app = FastAPI(
    title="AI-Powered University Student Services Assistant",
    description="Grounded, accurate, and explainable answers to student queries",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    db = get_db()
    
    # Check API
    api_status = "ok"
    
    # Check SQLite
    try:
        with db.transaction() as conn:
            conn.execute("SELECT 1").fetchone()
        sqlite_status = "ok"
    except Exception:
        sqlite_status = "error"
    
    # Check Chroma (simplified for MVP)
    chroma_status = "ok"  # TODO: Implement actual check
    
    # Check LLM (simplified for MVP)
    llm_status = "ok" if not settings.mock_llm else "mock"
    
    overall = "ok" if all(
        s == "ok" for s in [api_status, sqlite_status, chroma_status]
    ) or llm_status == "mock" else "degraded"
    
    return HealthResponse(
        status=overall,
        api=api_status,
        chroma=chroma_status,
        sqlite=sqlite_status,
        llm=llm_status
    )


@app.post("/ask", response_model=AskResponse)
async def ask_question(
    request: AskRequest,
    x_student_id: Optional[str] = Header(None)
):
    """Ask a question to the assistant."""
    from src.graph.workflow import run_workflow
    import json
    
    trace_id = uuid.uuid4().hex[:8]
    as_of_date = request.as_of_date or date_type.today()
    
    try:
        # Run the workflow
        result = run_workflow(
            question=request.question,
            student_id=x_student_id,
            as_of_date=as_of_date,
            trace_id=trace_id
        )
        
        # Format conflicts
        conflicts = []
        for conflict in result.get('conflicts', []):
            conflicts.append({
                'docs': conflict.get('docs', []),
                'summary': conflict.get('summary', ''),
                'resolution': 'authority',  # Simplified for MVP
                'winner_doc_id': conflict['docs'][0] if conflict.get('docs') else None
            })
        
        # Store audit record
        db = get_db()
        with db.transaction() as conn:
            audit_record = {
                'trace_id': trace_id,
                'question': request.question,
                'student_id': x_student_id,
                'answer': result['answer'],
                'answer_type': result['answer_type'],
                'citations': result.get('citations', []),
                'tools_invoked': result.get('tools_invoked', []),
                'timestamp': datetime.now().isoformat(),
                'as_of_date': str(as_of_date)
            }
            
            conn.execute(
                """
                INSERT INTO audit_log (trace_id, question, student_id, record_json, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    trace_id,
                    request.question,
                    x_student_id or '',
                    json.dumps(audit_record),
                    datetime.now().isoformat()
                )
            )
        
        # Build response
        return AskResponse(
            trace_id=trace_id,
            answer=result['answer'],
            answer_type=result['answer_type'],
            citations=result.get('citations', []),
            tools_invoked=result.get('tools_invoked', []),
            applied_rules=result.get('applied_rules', []),
            conflicts_detected=conflicts,
            explanation=result.get('explanation', ''),
            as_of_date=str(as_of_date)
        )
    
    except Exception as e:
        # Log error and return graceful response
        print(f"Error processing question: {e}")
        import traceback
        traceback.print_exc()
        
        return AskResponse(
            trace_id=trace_id,
            answer="I encountered an error processing your question. Please try again.",
            answer_type="not_found",
            citations=[],
            tools_invoked=[],
            applied_rules=[],
            conflicts_detected=[],
            explanation=f"Error: {str(e)}",
            as_of_date=str(as_of_date)
        )


@app.post("/ingest", response_model=IngestResponse)
async def ingest_document(
    file: UploadFile = File(...),
    metadata: str = Form(...)
):
    """Ingest a new document."""
    from src.ingestion.pipeline import IngestPipeline
    import json
    from datetime import date as date_type
    
    try:
        # Parse metadata
        metadata_dict = json.loads(metadata)
        
        # Parse dates
        if isinstance(metadata_dict['effective_from'], str):
            metadata_dict['effective_from'] = date_type.fromisoformat(metadata_dict['effective_from'])
        
        if metadata_dict.get('effective_to'):
            if isinstance(metadata_dict['effective_to'], str):
                metadata_dict['effective_to'] = date_type.fromisoformat(metadata_dict['effective_to'])
        
        if metadata_dict.get('retrieved_on'):
            if isinstance(metadata_dict['retrieved_on'], str):
                metadata_dict['retrieved_on'] = date_type.fromisoformat(metadata_dict['retrieved_on'])
        
        # Read file
        file_bytes = await file.read()
        
        # Ingest
        pipeline = IngestPipeline()
        result = pipeline.ingest_document(
            file_bytes=file_bytes,
            filename=file.filename,
            metadata=metadata_dict
        )
        
        return IngestResponse(
            doc_id=result['doc_id'],
            chunks_indexed=result['chunks_indexed'],
            status=result['status'],
            rules_extracted=result.get('rules_extracted', 0),
            warnings=[]
        )
    
    except Exception as e:
        print(f"Error ingesting document: {e}")
        import traceback
        traceback.print_exc()
        
        return IngestResponse(
            doc_id=metadata_dict.get('doc_id', 'UNKNOWN'),
            chunks_indexed=0,
            status="failed",
            warnings=[f"Error: {str(e)}"]
        )


@app.get("/sources")
async def list_sources():
    """List all ingested documents."""
    db = get_db()
    
    with db.transaction() as conn:
        cursor = conn.execute("""
            SELECT doc_id, title, authority_level, doc_type, version,
                   effective_from, effective_to, chunk_count, rule_count, ingested_at
            FROM source_register
            ORDER BY ingested_at DESC
        """)
        sources = [dict(row) for row in cursor.fetchall()]
    
    return {"sources": sources}


@app.get("/audit/{trace_id}")
async def get_audit(
    trace_id: str,
    x_student_id: Optional[str] = Header(None)
):
    """Get audit record for a specific trace ID."""
    db = get_db()
    
    with db.transaction() as conn:
        cursor = conn.execute(
            "SELECT * FROM audit_log WHERE trace_id = ?",
            (trace_id,)
        )
        record = cursor.fetchone()
    
    if not record:
        raise HTTPException(status_code=404, detail="Trace ID not found")
    
    record_dict = dict(record)
    
    # Check authorization if header provided
    if x_student_id and record_dict.get('student_id') != x_student_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    import json
    return json.loads(record_dict['record_json'])


@app.get("/rules")
async def list_rules(parameter: Optional[str] = None):
    """List rules from the registry."""
    db = get_db()
    
    query = """
        SELECT rule_id, description, parameter, operator, value,
               scope_programmes, scope_batches, effective_from, effective_to,
               source_doc_id, source_section, status
        FROM rule_registry
    """
    
    params = ()
    if parameter:
        query += " WHERE parameter = ?"
        params = (parameter,)
    
    query += " ORDER BY effective_from DESC"
    
    with db.transaction() as conn:
        cursor = conn.execute(query, params)
        rules = [dict(row) for row in cursor.fetchall()]
    
    return {"rules": rules}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
