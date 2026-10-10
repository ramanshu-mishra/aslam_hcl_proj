# AI-Powered University Student Services Assistant - MVP

## Overview

This is an MVP implementation of the AI-Powered University Student Services Assistant for the HCLTech Future Ready AI Engineer Hackathon. The system answers student academic service questions using authorized university documents and student data with accurate, grounded, and explainable responses.

## Architecture

- **Single Fixed LangGraph Workflow**: Code handles filtering, precedence, tool execution, thresholds, citations, and auditing
- **Local LLM**: Uses Ollama (qwen2.5:7b-instruct or llama3.1:8b)
- **Vector Store**: ChromaDB (persisted to disk)
- **Structured Data**: SQLite (student data and rule registry)
- **Embeddings**: sentence-transformers (BAAI/bge-small-en-v1.5)
- **API**: FastAPI + Uvicorn with Pydantic v2
- **UI**: Streamlit

## Key Features

- ✅ Grounded answers with citations (document, section, page, version, effective date)
- ✅ No fabrication - returns "not found" when evidence is insufficient
- ✅ Version and conflict resolution using Source Precedence Policy
- ✅ Deterministic tools for calculations and eligibility checks
- ✅ Authorization and privacy controls
- ✅ Live document ingestion (no restart required)
- ✅ Full audit trail with trace IDs

## Prerequisites

1. **Python 3.11+**
2. **Ollama** (for local LLM)
   ```bash
   # Install Ollama from https://ollama.ai
   curl -fsSL https://ollama.com/install.sh | sh
   
   # Pull the model
   ollama pull qwen2.5:7b-instruct
   ```
3. **System Dependencies**
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install -y tesseract-ocr poppler-utils libgl1-mesa-glx
   
   # macOS
   brew install tesseract poppler
   ```

## Quick Start

### 1. Clone and Setup

```bash
cd student-services-assistant

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configuration

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` if needed (defaults should work for local development):
```env
LLM_PROVIDER=ollama
LLM_MODEL=qwen2.5:7b-instruct
OLLAMA_HOST=http://localhost:11434
EMBED_MODEL=BAAI/bge-small-en-v1.5
CHUNK_TARGET_TOKENS=350
RETRIEVAL_MODE=hybrid
TOP_K=5
STORE_DIR=./store
MOCK_LLM=false
```

### 3. Prepare Sample Data

```bash
# Generate synthetic student data
python scripts/generate_data.py

# Validate the data
python scripts/validate_data.py

# Load students into database
python scripts/load_students.py --dir data/test_students/
```

### 4. Ingest Sample Documents

Place your university documents (PDFs) in `data/docs/` and create `data/source_register.csv`:

```csv
doc_id,title,issuer,authority_level,doc_type,version,effective_from,effective_to,supersedes,scope_programmes,scope_batches,provenance,retrieved_on,synthetic
ACAD-REG-2024,Academic Regulations,Dean Academics,1,regulation,1.0,2024-07-01,,,,ALL,ALL,https://university.edu,2024-10-01,N
```

Then run:
```bash
python scripts/ingest_seed.py
```

### 5. Start the API Server

```bash
# Start the FastAPI server
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

### 6. Start the Streamlit UI (Optional)

In a new terminal:
```bash
source venv/bin/activate
streamlit run src/ui/streamlit_app.py
```

The UI will open in your browser at `http://localhost:8501`

## Using Docker Compose (Recommended)

```bash
# Make sure Ollama is installed and the model is pulled
ollama pull qwen2.5:7b-instruct

# Start all services
docker-compose up --build

# Access the services:
# - API: http://localhost:8000
# - UI: http://localhost:8501
# - API Docs: http://localhost:8000/docs
```

To stop:
```bash
docker-compose down
```

## API Usage Examples

### Health Check
```bash
curl http://localhost:8000/health
```

### Ask a Question (General)
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the minimum attendance required to appear for end-semester exams?",
    "as_of_date": "2024-10-10"
  }'
```

### Ask a Personal Question
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -H "X-Student-Id: S1001" \
  -d '{
    "question": "What is my attendance in Data Structures?",
    "as_of_date": "2024-10-10"
  }'
```

### Ingest a New Document
```bash
curl -X POST http://localhost:8000/ingest \
  -F "file=@data/docs/circular.pdf" \
  -F 'metadata={
    "doc_id": "CIRC-2024-01",
    "title": "Attendance Policy Update",
    "issuer": "Dean Academics",
    "authority_level": 2,
    "doc_type": "circular",
    "version": "1.0",
    "effective_from": "2024-08-01",
    "scope_programmes": "ALL",
    "scope_batches": "ALL",
    "synthetic": "N"
  }'
```

### Get Audit Trail
```bash
curl http://localhost:8000/audit/{trace_id}
```

### List All Sources
```bash
curl http://localhost:8000/sources
```

## Project Structure

```
student-services-assistant/
├── src/
│   ├── api/              # FastAPI routes and models
│   ├── graph/            # LangGraph workflow and nodes
│   ├── ingestion/        # Document parsing and chunking
│   ├── retrieval/        # Hybrid search (dense + BM25)
│   ├── precedence/       # Annex A conflict resolution
│   ├── tools/            # Deterministic tools for student data
│   ├── rules/            # Rule registry and resolver
│   ├── llm/              # Ollama client with fallback
│   ├── prompts/          # Versioned prompt templates
│   ├── db/               # SQLite schema and queries
│   └── ui/               # Streamlit interface
├── scripts/              # Data generation and loading
├── data/                 # Documents and student data
├── eval/                 # Evaluation set and metrics
├── tests/                # Unit, contract, and E2E tests
├── docker/               # Dockerfiles
├── store/                # Persistent data (Chroma, SQLite)
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Running Tests

```bash
# Run all tests
pytest tests/

# Run unit tests only
pytest tests/unit/

# Run with coverage
pytest --cov=src tests/
```

## Running Evaluation

```bash
# Run the evaluation set
python eval/run_eval.py

# View the report
cat eval/report.md
```

## Key Design Decisions

1. **Single Fixed Graph**: Simplest architecture that meets requirements - no unnecessary agents
2. **Code Decides, LLM Explains**: All authoritative results computed in Python
3. **Metadata-Driven**: No hardcoded document IDs, thresholds, or course codes
4. **Identity from Header Only**: LLM never chooses whose data to read
5. **Reproducible Responses**: Every response traceable from audit record

## Answer Types

- `retrieved_fact`: Answer from cited document text
- `calculated`: Result from deterministic tool
- `not_found`: Not in authorized sources
- `clarification_needed`: Ambiguous question
- `refused`: Not allowed (privacy violation)
- `conflict_flagged`: Unresolvable conflict between sources

## Limitations and Known Issues

- Local 7B models may occasionally return invalid JSON (fallback handles this)
- Rule extraction has <100% recall (retrieval path still works)
- OCR quality depends on scan quality
- CPU-only latency can reach 5-10 seconds per question
- No CGPA recalculation for what-if (assumption stated in answer)

## Configuration Options

See `.env.example` for all configuration options including:
- LLM provider and model selection
- Embedding model choice
- Retrieval mode (dense vs hybrid)
- Chunking parameters
- Mock mode for testing

## Troubleshooting

### Ollama Connection Issues
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
systemctl restart ollama  # Linux
# Or restart from System Preferences on macOS
```

### Slow Performance
- Ensure Ollama model is downloaded: `ollama pull qwen2.5:7b-instruct`
- Use GPU if available (CUDA/Metal)
- Reduce `TOP_K` in `.env`
- Enable `keep_alive` in Ollama settings

### Memory Issues
- Reduce batch size for data generation
- Use smaller embedding model
- Reduce chunk context size

## Development

### Adding New Tools
1. Create tool function in `src/tools/`
2. Add to tool catalogue in `src/tools/factory.py`
3. Update intent routing in `src/graph/nodes/route.py`

### Adding New Document Types
1. Add parser in `src/ingestion/parse.py`
2. Update structure detection in `src/ingestion/structure.py`
3. Test with sample documents

### Modifying Prompts
1. Update prompt files in `src/prompts/`
2. Increment version number
3. Test with mock mode first

## Team Contributions

This MVP implements the core architecture from the design document focusing on:
- **Ingestion & Chunking**: Document parsing, OCR, structure detection
- **Retrieval & Precedence**: Hybrid search, Annex A resolution
- **Tools & Safety**: Deterministic calculations, authorization controls
- **API & Evaluation**: FastAPI endpoints, metrics, Docker setup

## License

This project is for the HCLTech Future Ready AI Engineer Hackathon.

## Contact

For questions about this implementation, refer to the design document or hackathon guidelines.
