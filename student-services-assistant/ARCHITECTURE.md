# Architecture Documentation

This document describes the technical architecture of the AI-Powered University Student Services Assistant.

## Table of Contents

1. [System Overview](#system-overview)
2. [Design Principles](#design-principles)
3. [Component Architecture](#component-architecture)
4. [Data Flow](#data-flow)
5. [Database Schema](#database-schema)
6. [API Contract](#api-contract)
7. [LangGraph Workflow](#langgraph-workflow)
8. [Security Model](#security-model)

## System Overview

The Student Services Assistant is a RAG (Retrieval-Augmented Generation) system that provides grounded, accurate answers to student queries using authorized university documents and student data.

### Key Components

```
┌─────────────────────────────────────────────────────────────┐
│                        Streamlit UI                          │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP
┌─────────────────────────▼───────────────────────────────────┐
│                       FastAPI Server                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              LangGraph Workflow                       │  │
│  │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  │  │
│  │  │Class │─▶│Auth  │─▶│Retr  │─▶│Tools │─▶│Gen   │  │  │
│  │  │ify   │  │orize │  │ieve  │  │      │  │erate │  │  │
│  │  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────┬─────────────────────────┬─────────────────────┘
              │                         │
    ┌─────────▼────────┐    ┌───────────▼──────────┐
    │   ChromaDB       │    │      SQLite          │
    │ (Vector Store)   │    │ (Student Data/Rules) │
    └──────────────────┘    └──────────────────────┘
              │
    ┌─────────▼────────┐
    │   Ollama LLM     │
    │ (Local Inference)│
    └──────────────────┘
```

## Design Principles

### 1. Single Fixed Graph
- No multiple agents or dynamic routing
- Fixed LangGraph workflow handles all query types
- Simpler to debug, maintain, and audit

### 2. Code Decides, LLM Explains
- Deterministic operations in Python code
- LLM used only for:
  - Intent classification
  - Answer generation
  - Natural language explanations
- Critical decisions (precedence, authorization) are in code

### 3. Identity from Header Only
- Student ID comes from X-Student-Id header
- LLM never chooses whose data to access
- Authorization check is deterministic

### 4. Metadata-Driven
- No hardcoded document IDs
- No hardcoded thresholds
- All rules come from source_register and rule_registry
- Extensible without code changes

### 5. Grounded Responses
- Every fact must be traceable to a source
- Citations include doc_id, page, version, effective_date
- "Not found" when evidence is insufficient
- No fabrication or hallucination

## Component Architecture

### 1. API Layer (`src/api/`)

**main.py** - FastAPI application with endpoints:
- `POST /ask` - Main query endpoint
- `POST /ingest` - Document ingestion
- `GET /sources` - List documents
- `GET /audit/{trace_id}` - Audit trail
- `GET /health` - Health check

**models.py** - Pydantic models for request/response validation

### 2. Graph Workflow (`src/graph/`)

**workflow.py** - LangGraph orchestration
- Defines node sequence
- Handles conditional routing
- Manages state transitions

**state.py** - Graph state definition
- Input: question, student_id, as_of_date
- Output: answer, citations, tools, rules, conflicts

**nodes/** - Individual processing nodes:
- `classify.py` - Intent detection
- `authorize.py` - Access control
- `retrieve.py` - Document retrieval
- `execute_tools.py` - Tool invocation
- `generate.py` - Answer generation

### 3. Ingestion Pipeline (`src/ingestion/`)

**pipeline.py** - Main ingestion orchestrator

**parse.py** - Document parsing:
- PDF text extraction
- OCR for scanned pages
- Structure detection

**chunker.py** - Text chunking:
- Semantic-aware splitting
- Target size: ~350 tokens
- Overlap for context preservation

### 4. Retrieval System (`src/retrieval/`)

**retriever.py** - Hybrid search:
- Dense retrieval (embeddings)
- Sparse retrieval (BM25) - planned
- Result fusion

**embeddings.py** - Sentence-transformers wrapper:
- Model: BAAI/bge-small-en-v1.5
- Dimension: 384
- Cached for performance

**vector_store.py** - ChromaDB interface:
- Persistent storage
- Cosine similarity search
- Metadata filtering

### 5. Precedence Engine (`src/precedence/`)

**engine.py** - Conflict resolution:
- Implements Annex A policy
- Priority: supersession > authority > recency
- Date-based validity filtering

### 6. Tools (`src/tools/`)

**student_tools.py** - Deterministic functions:
- `get_student_profile()`
- `get_student_attendance()`
- `check_exam_eligibility()`
- `get_cgpa()`

**factory.py** - Tool registry and invocation

### 7. LLM Client (`src/llm/`)

**client.py** - Ollama wrapper:
- JSON parsing with fallback
- Mock mode for testing
- Error handling and retries

### 8. Rules (`src/rules/`)

**resolver.py** - Rule registry queries:
- Scope matching (programme, batch)
- Date-based filtering
- Default value fallback

### 9. Database (`src/db/`)

**connection.py** - SQLite wrapper:
- Transaction support
- Connection pooling
- WAL mode for concurrency

**schema.sql** - Database schema (Annex C)

### 10. Prompts (`src/prompts/`)

**templates.py** - LLM prompts:
- Classifier prompt
- Generator prompt
- Verifier prompt (future)

## Data Flow

### Query Processing Flow

```
1. User Question
   ↓
2. API receives request + optional X-Student-Id header
   ↓
3. Create initial GraphState
   ↓
4. CLASSIFY NODE
   - LLM determines intent
   - Sets needs_personal_data flag
   - Sets routing flags
   ↓
5. AUTHORIZE NODE
   - If needs_personal_data and no student_id → REFUSE
   - Otherwise → ALLOW
   ↓
6. RETRIEVE NODE (if authorized)
   - Embed query
   - Search vector store
   - Filter by as_of_date
   - Detect conflicts
   - Apply precedence rules
   ↓
7. EXECUTE TOOLS NODE
   - If intent requires tools
   - Call appropriate student data functions
   - Store results in state
   ↓
8. GENERATE NODE
   - Build context from retrieved chunks
   - Build tool results summary
   - LLM generates answer
   - Extract citations
   - Generate explanation
   ↓
9. Store audit record
   ↓
10. Return AskResponse
```

### Document Ingestion Flow

```
1. Upload file + metadata
   ↓
2. Parse document (extract text)
   ↓
3. Detect structure (sections, headings)
   ↓
4. Chunk text (~350 tokens with overlap)
   ↓
5. Generate embeddings for chunks
   ↓
6. Store in ChromaDB with metadata
   ↓
7. Register in source_register table
   ↓
8. Extract rules (pattern matching + LLM)
   ↓
9. Store rules in rule_registry
   ↓
10. Return IngestResponse
```

## Database Schema

### Students Table
```sql
student_id TEXT PRIMARY KEY
name TEXT
programme TEXT
batch TEXT
email TEXT
phone TEXT
advisor_name TEXT
status TEXT
```

### Enrollments Table
```sql
student_id TEXT
course_code TEXT
semester TEXT
grade TEXT
grade_points REAL
PRIMARY KEY (student_id, course_code, semester)
```

### Attendance Table
```sql
student_id TEXT
course_code TEXT
total_classes INTEGER
attended_classes INTEGER
excused_absences INTEGER
last_updated TEXT
PRIMARY KEY (student_id, course_code)
```

### Source Register Table
```sql
doc_id TEXT PRIMARY KEY
title TEXT
issuer TEXT
authority_level INTEGER
doc_type TEXT
version TEXT
effective_from TEXT
effective_to TEXT
supersedes TEXT
scope_programmes TEXT
scope_batches TEXT
chunk_count INTEGER
rule_count INTEGER
ingested_at TEXT
```

### Rule Registry Table
```sql
rule_id TEXT PRIMARY KEY
description TEXT
parameter TEXT
operator TEXT
value TEXT
scope_programmes TEXT
scope_batches TEXT
effective_from TEXT
effective_to TEXT
source_doc_id TEXT
source_section TEXT
status TEXT
```

### Audit Log Table
```sql
trace_id TEXT PRIMARY KEY
question TEXT
student_id TEXT
record_json TEXT
timestamp TEXT
```

## API Contract

### POST /ask

**Request:**
```json
{
  "question": "string",
  "as_of_date": "2024-10-10"  // optional
}
```

**Headers:**
```
X-Student-Id: S1001  // optional, for personal queries
```

**Response:**
```json
{
  "trace_id": "abc123",
  "answer": "string",
  "answer_type": "retrieved_fact | calculated | not_found | ...",
  "citations": [
    {
      "doc_id": "ACAD-REG-2024",
      "title": "Academic Regulations",
      "section": "Section 1.1",
      "page": 3,
      "version": "1.0",
      "effective_from": "2024-07-01"
    }
  ],
  "tools_invoked": [
    {
      "tool": "get_student_attendance",
      "input": {"student_id": "S1001"},
      "output": {"percentage": 85.5}
    }
  ],
  "applied_rules": [],
  "conflicts_detected": [],
  "explanation": "string",
  "as_of_date": "2024-10-10"
}
```

## LangGraph Workflow

### State Machine

```
START
  ↓
classify
  ↓
authorize
  ↓
[authorized?]─No→ END
  │
  Yes
  ↓
retrieve
  ↓
execute_tools
  ↓
generate
  ↓
END
```

### Node Details

**classify:**
- Input: question
- Output: intent, needs_personal_data, confidence
- Logic: LLM classification

**authorize:**
- Input: needs_personal_data, student_id
- Output: authorized flag
- Logic: Deterministic check

**retrieve:**
- Input: question, as_of_date
- Output: retrieved_chunks, conflicts
- Logic: Hybrid search + precedence resolution

**execute_tools:**
- Input: intent, student_id
- Output: tool_results, tools_invoked
- Logic: Conditional tool execution

**generate:**
- Input: question, chunks, tool_results
- Output: answer, citations, explanation
- Logic: LLM generation with grounding

## Security Model

### Authorization Levels

1. **Public Information**
   - No authentication required
   - General policy questions
   - Document listings

2. **Personal Information**
   - Requires X-Student-Id header
   - Access only to own data
   - Audit logged

3. **Admin Operations**
   - Requires admin token (future)
   - Document ingestion
   - User management

### Privacy Controls

1. **Identity Verification**
   - Student ID from trusted header
   - Never from user input or LLM

2. **Data Segregation**
   - Tools enforce student_id filtering
   - No cross-student data access

3. **Audit Trail**
   - Every query logged with trace_id
   - Includes student_id, question, answer
   - Retrievable for compliance

### Attack Mitigation

1. **Prompt Injection**
   - LLM used for classification/generation only
   - Critical logic in deterministic code
   - No LLM-based routing or authorization

2. **Data Exfiltration**
   - Tools enforce access controls
   - No "list all students" functionality
   - Rate limiting (to be added)

3. **Document Poisoning**
   - Source register with authority levels
   - Precedence rules enforce trust hierarchy
   - Ingestion restricted (admin only)

## Performance Characteristics

### Latency Targets

- Health check: <100ms
- General query: <3s
- Personal query: <5s
- Document ingestion: <30s per doc

### Scalability

- API: Stateless, horizontally scalable
- Database: SQLite for MVP, migrate to PostgreSQL for scale
- Vector Store: Single ChromaDB instance supports ~1M chunks
- LLM: Bottleneck, consider GPU or cloud LLM

### Resource Usage

- Memory: ~2GB (embeddings + model)
- Disk: Grows with documents (~50MB per 100 pages)
- CPU: High during ingestion and query processing

## Extension Points

1. **New Tools**
   - Add to `src/tools/student_tools.py`
   - Register in `factory.py`
   - Update routing in `execute_tools.py`

2. **New Document Types**
   - Add parser in `parse.py`
   - Update structure detection
   - Test with sample docs

3. **Different LLM**
   - Update `src/llm/client.py`
   - Add provider-specific logic
   - Test JSON parsing

4. **Additional Precedence Rules**
   - Update `src/precedence/engine.py`
   - Add rule type to resolution logic
   - Document in Annex A

5. **Advanced Retrieval**
   - Implement BM25 in `retriever.py`
   - Add fusion logic
   - Benchmark improvements

## Future Enhancements

1. **Authentication**
   - OAuth2/SAML integration
   - JWT tokens
   - Role-based access control

2. **Caching**
   - Cache frequent queries
   - Cache embeddings
   - Redis integration

3. **Monitoring**
   - Prometheus metrics
   - Grafana dashboards
   - Distributed tracing

4. **Advanced Features**
   - Multi-turn conversations
   - Query clarification
   - Proactive notifications

5. **ML Improvements**
   - Fine-tune embeddings
   - Train custom classifiers
   - Active learning for rules
