#!/bin/bash
# Quick start script for setting up and running the Student Services Assistant

set -e

# Change to project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "=========================================="
echo "Student Services Assistant - Quick Start"
echo "=========================================="
echo ""
echo "Project directory: $PROJECT_ROOT"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip > /dev/null
pip install -r requirements.txt > /dev/null

echo "✓ Dependencies installed"
echo ""

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "✓ .env file created"
else
    echo "✓ .env file exists"
fi
echo ""

# Create store directory
echo "Creating storage directories..."
mkdir -p store/chroma
echo "✓ Storage directories created"
echo ""

# Check if database exists, if not initialize it
if [ ! -f "store/student_services.db" ]; then
    echo "Initializing database..."
    python3 -c "
from src.db.connection import get_db
db = get_db()
print('✓ Database initialized')
"
fi
echo ""

# Run setup test
echo "Running setup tests..."
python scripts/test_setup.py
echo ""

# Check if Ollama is running
echo "Checking Ollama..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✓ Ollama is running"
    
    # Check if model is pulled
    if curl -s http://localhost:11434/api/tags | grep -q "qwen2.5:7b-instruct"; then
        echo "✓ Model qwen2.5:7b-instruct is available"
    else
        echo "⚠ Model not found. Pulling qwen2.5:7b-instruct..."
        echo "  This may take several minutes..."
        ollama pull qwen2.5:7b-instruct
    fi
else
    echo "⚠ Ollama is not running"
    echo "  Please start Ollama first:"
    echo "  - Install from: https://ollama.ai"
    echo "  - Run: ollama serve"
    echo "  - Pull model: ollama pull qwen2.5:7b-instruct"
fi
echo ""

# Ask if user wants to load sample data
echo "=========================================="
echo "Sample Data Setup"
echo "=========================================="
echo ""

read -p "Do you want to generate and load sample student data? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Generating sample data..."
    python scripts/generate_data.py
    
    echo "Validating data..."
    python scripts/validate_data.py
    
    echo "Loading students into database..."
    python scripts/load_students.py --dir data/test_students/
    
    echo "✓ Sample data loaded"
fi
echo ""

read -p "Do you want to ingest sample documents? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Ingesting documents..."
    python scripts/ingest_seed.py
    
    echo "✓ Documents ingested"
fi
echo ""

echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "To start the services:"
echo ""
echo "  1. API Server:"
echo "     uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "  2. UI (in another terminal):"
echo "     streamlit run src/ui/streamlit_app.py"
echo ""
echo "Or use Docker Compose:"
echo "     docker-compose up --build"
echo ""
echo "API will be available at: http://localhost:8000"
echo "UI will be available at: http://localhost:8501"
echo "API Docs will be at: http://localhost:8000/docs"
echo ""
