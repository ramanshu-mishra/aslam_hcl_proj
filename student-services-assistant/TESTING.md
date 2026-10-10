# Testing Guide

This document describes how to test the Student Services Assistant MVP.

## Prerequisites

1. Complete the setup from README.md
2. Load sample data (students and documents)
3. Start the API server

## Quick Test

Run the automated test suite:

```bash
# Test basic setup
python scripts/test_setup.py

# Run evaluation
python eval/run_eval.py
```

## Manual API Testing

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "ok",
  "api": "ok",
  "chroma": "ok",
  "sqlite": "ok",
  "llm": "ok"
}
```

### 2. General Question (No Auth Required)

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the minimum attendance required for exams?",
    "as_of_date": "2024-10-10"
  }'
```

Expected:
- `answer_type`: "retrieved_fact"
- `citations`: List of sources
- `answer`: Should mention "75%"

### 3. Personal Question (Auth Required)

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -H "X-Student-Id: S1001" \
  -d '{
    "question": "What is my attendance in Data Structures?",
    "as_of_date": "2024-10-10"
  }'
```

Expected:
- `answer_type`: "calculated"
- `tools_invoked`: Should include "get_student_attendance"
- `answer`: Specific attendance data

### 4. Unauthorized Personal Question

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is my CGPA?"
  }'
```

Expected:
- `answer_type`: "refused"
- `answer`: Error message about authentication

### 5. List Sources

```bash
curl http://localhost:8000/sources
```

Expected: List of ingested documents

### 6. Ingest New Document

```bash
curl -X POST http://localhost:8000/ingest \
  -F "file=@data/docs/ACAD-REG-2024.txt" \
  -F 'metadata={
    "doc_id": "TEST-DOC-001",
    "title": "Test Document",
    "issuer": "Test Issuer",
    "authority_level": 3,
    "doc_type": "notice",
    "version": "1.0",
    "effective_from": "2024-10-01",
    "scope_programmes": "ALL",
    "scope_batches": "ALL",
    "synthetic": "Y"
  }'
```

Expected:
- `status`: "completed"
- `chunks_indexed`: Number > 0

## UI Testing

1. Start Streamlit: `streamlit run src/ui/streamlit_app.py`
2. Open browser to http://localhost:8501
3. Test each tab:

### Ask Tab
- Enter a general question
- Check response quality
- Verify citations appear
- Try a personal question (enter student ID)

### Ingest Tab
- Upload a test PDF/TXT file
- Fill in metadata
- Click "Ingest Document"
- Verify success message

### Audit Tab
- Enter a trace_id from previous query
- Verify full audit record displays

## Test Scenarios

### Scenario 1: Policy Query
**Question:** "What are the credit requirements for graduation?"

**Expected:**
- Retrieves from ACAD-REG-2024
- Cites specific sections
- Mentions 120 credits for 3-year, 160 for 4-year

### Scenario 2: Personal Data Query
**Question:** "What courses am I enrolled in?"
**Header:** X-Student-Id: S1001

**Expected:**
- Uses get_student_courses tool
- Returns student's course list
- No document citations needed

### Scenario 3: Calculation Query
**Question:** "Am I eligible for exams in Operating Systems?"
**Header:** X-Student-Id: S1001

**Expected:**
- Uses check_exam_eligibility tool
- Retrieves attendance rules from documents
- Provides clear yes/no answer with reasoning

### Scenario 4: Conflicting Documents
(Requires two docs with different rules)

**Expected:**
- Detects conflict
- Applies precedence rules
- Returns winner and explanation in conflicts_detected

### Scenario 5: Missing Information
**Question:** "What is the hostel allocation policy?"

**Expected:**
- answer_type: "not_found"
- Answer indicates no information available
- Empty citations list

## Performance Testing

### Load Test with Artillery

Install artillery:
```bash
npm install -g artillery
```

Create `loadtest.yml`:
```yaml
config:
  target: "http://localhost:8000"
  phases:
    - duration: 60
      arrivalRate: 5
scenarios:
  - flow:
      - post:
          url: "/ask"
          json:
            question: "What is minimum attendance?"
            as_of_date: "2024-10-10"
```

Run:
```bash
artillery run loadtest.yml
```

## Evaluation Metrics

The evaluation script (`eval/run_eval.py`) checks:

1. **Answer Type Accuracy**: Does answer_type match expected?
2. **Citation Presence**: Are sources cited when needed?
3. **Tool Usage**: Are correct tools invoked?
4. **Response Quality**: Is answer length reasonable?

Target metrics:
- Accuracy: >80%
- Citation recall: >90% for policy questions
- Tool precision: 100% (correct tool used)

## Troubleshooting

### LLM Returns Invalid JSON
- Check Ollama is running: `curl http://localhost:11434/api/tags`
- Try mock mode: Set `MOCK_LLM=true` in .env
- Use a different model with better JSON support

### No Documents Retrieved
- Check vector store: `python -c "from src.retrieval.vector_store import get_vector_store; print(get_vector_store().count())"`
- Re-run ingestion: `python scripts/ingest_seed.py`
- Check ChromaDB directory: `ls -la store/chroma/`

### Database Errors
- Check database exists: `ls -la store/student_services.db`
- Re-initialize: `rm store/student_services.db && python scripts/load_students.py`

### Tool Execution Fails
- Verify student data loaded: `python -c "from src.tools.factory import invoke_tool; print(invoke_tool('get_student_profile', student_id='S1001'))"`
- Check database has data: `sqlite3 store/student_services.db "SELECT COUNT(*) FROM students;"`

## Continuous Testing

Add to CI/CD:

```bash
#!/bin/bash
set -e

# Setup
python scripts/test_setup.py

# Generate data
python scripts/generate_data.py
python scripts/load_students.py --dir data/test_students/

# Ingest docs
python scripts/ingest_seed.py

# Run evaluation
python eval/run_eval.py

# Check results
if [ $? -eq 0 ]; then
  echo "✓ All tests passed"
  exit 0
else
  echo "✗ Tests failed"
  exit 1
fi
```

## Next Steps

After basic testing works:

1. Add more diverse evaluation questions
2. Test edge cases (very long questions, special characters)
3. Test with real university documents
4. Measure latency under load
5. Test with different LLM models
6. Add integration tests for all endpoints
7. Test error recovery and fallback scenarios
