# Installation Guide

Follow these steps to set up the Student Services Assistant MVP.

## Prerequisites

1. **Python 3.11+**
   ```bash
   python3 --version  # Should be 3.11 or higher
   ```

2. **Ollama** (for local LLM)
   ```bash
   # Install Ollama
   curl -fsSL https://ollama.com/install.sh | sh
   
   # Pull the model
   ollama pull qwen2.5:7b-instruct
   ```

## Step-by-Step Installation

### 1. Navigate to Project Directory

```bash
cd /home/ramanshu/projects/aslam_hcl/student-services-assistant
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will install all necessary packages including:
- FastAPI and Uvicorn (API server)
- LangGraph (workflow orchestration)
- ChromaDB (vector store)
- Sentence Transformers (embeddings)
- Streamlit (UI)
- and all other dependencies

### 4. Create Environment File

```bash
cp .env.example .env
```

The defaults in `.env` should work for local development. No changes needed unless you want to customize settings.

### 5. Initialize Database

The database will be created automatically when you first run the application. To verify setup:

```bash
python -c "from src.db.connection import get_db; db = get_db(); print('Database initialized successfully')"
```

### 6. Load Sample Data (Optional but Recommended)

```bash
# Generate synthetic student data
python scripts/generate_data.py

# Validate the generated data
python scripts/validate_data.py

# Load students into database
python scripts/load_students.py --dir data/test_students/
```

### 7. Ingest Sample Documents (Optional)

```bash
# This will ingest the sample documents from data/docs/
python scripts/ingest_seed.py
```

### 8. Verify Setup

```bash
python scripts/test_setup.py
```

This will check that all components are working correctly.

## Running the Application

### Option 1: API Server Only

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

Access the API at: http://localhost:8000  
API Documentation: http://localhost:8000/docs

### Option 2: Streamlit UI (in addition to API)

In a new terminal (keep the API server running):

```bash
cd /home/ramanshu/projects/aslam_hcl/student-services-assistant
source venv/bin/activate
streamlit run src/ui/streamlit_app.py
```

Access the UI at: http://localhost:8501

### Option 3: Using Docker Compose

```bash
# Make sure Ollama is running and model is pulled
ollama pull qwen2.5:7b-instruct

# Start all services
docker-compose up --build
```

## Quick Test

Once the API is running, test with:

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the minimum attendance required?",
    "as_of_date": "2024-10-10"
  }'
```

## Troubleshooting

### ImportError: No module named 'X'

Make sure you activated the virtual environment:
```bash
source venv/bin/activate
```

Then reinstall requirements:
```bash
pip install -r requirements.txt
```

### Cannot connect to Ollama

Check if Ollama is running:
```bash
curl http://localhost:11434/api/tags
```

If not working, start Ollama:
```bash
ollama serve
```

### Port already in use

Change the port in the command:
```bash
uvicorn src.api.main:app --port 8001
```

Or kill the process using the port:
```bash
lsof -ti:8000 | xargs kill -9
```

### Database errors

Remove and reinitialize:
```bash
rm store/student_services.db
python scripts/load_students.py --dir data/test_students/
```

## Next Steps

After installation:

1. Read [README.md](README.md) for usage instructions
2. Read [TESTING.md](TESTING.md) for testing guide
3. Read [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
4. Read [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment

## Uninstall

To remove the installation:

```bash
# Deactivate virtual environment
deactivate

# Remove virtual environment
rm -rf venv

# Remove generated data (optional)
rm -rf store/
rm -rf data/test_students/
```
