"""Configuration management using environment variables."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # LLM Configuration
    llm_provider: Literal["ollama", "cloud"] = "ollama"
    llm_model: str = "qwen2.5:7b-instruct"
    ollama_host: str = "http://localhost:11434"
    mock_llm: bool = False
    openai_api_key: str = ""
    
    # Embedding Model
    embed_model: str = "BAAI/bge-small-en-v1.5"
    
    # Chunking
    chunk_target_tokens: int = 350
    
    # Retrieval
    retrieval_mode: Literal["dense", "hybrid"] = "hybrid"
    top_k: int = 5
    abstain_tau: float = 0.65
    
    # Storage
    store_dir: Path = Path("./store")
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    admin_token: str = ""
    
    # UI
    ui_port: int = 8501
    api_url: str = "http://localhost:8000"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Ensure store directory exists
settings.store_dir.mkdir(parents=True, exist_ok=True)
(settings.store_dir / "chroma").mkdir(exist_ok=True)
