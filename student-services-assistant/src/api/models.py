"""Pydantic models for API contract."""
from datetime import date
from typing import Literal, Optional
from pydantic import BaseModel, Field


# Request Models

class AskRequest(BaseModel):
    """Request model for POST /ask."""
    question: str = Field(min_length=1, max_length=1000)
    as_of_date: Optional[date] = None


class IngestMetadata(BaseModel):
    """Metadata for POST /ingest."""
    doc_id: str
    title: str
    issuer: str
    authority_level: int = Field(ge=1, le=5)
    doc_type: Literal['regulation', 'circular', 'notice', 'faq', 'handbook', 'unofficial']
    version: str
    effective_from: date
    effective_to: Optional[date] = None
    supersedes: str = ''
    scope_programmes: str = 'ALL'
    scope_batches: str = 'ALL'
    provenance: str = ''
    retrieved_on: Optional[date] = None
    synthetic: Literal['Y', 'N'] = 'N'


# Response Models

class Citation(BaseModel):
    """Citation information."""
    doc_id: str
    title: str
    section: Optional[str] = None
    page: Optional[int] = None
    version: str
    effective_from: str


class ToolCall(BaseModel):
    """Tool invocation record."""
    tool: str
    input: dict
    output: dict


class AppliedRule(BaseModel):
    """Rule application record."""
    rule_id: str
    value: str
    source_doc_id: str


class Conflict(BaseModel):
    """Conflict information."""
    docs: list[str]
    summary: str
    resolution: Literal['supersession', 'authority', 'recency', 'unresolved']
    winner_doc_id: Optional[str] = None


class AskResponse(BaseModel):
    """Response model for POST /ask."""
    trace_id: str
    answer: str
    answer_type: Literal[
        'retrieved_fact',
        'calculated',
        'not_found',
        'clarification_needed',
        'refused',
        'conflict_flagged'
    ]
    citations: list[Citation]
    tools_invoked: list[ToolCall]
    applied_rules: list[AppliedRule]
    conflicts_detected: list[Conflict]
    explanation: str
    as_of_date: str


class IngestResponse(BaseModel):
    """Response model for POST /ingest."""
    doc_id: str
    chunks_indexed: int
    status: str
    rules_extracted: int = 0
    ocr_pages: int = 0
    tables: int = 0
    warnings: list[str] = []


class HealthResponse(BaseModel):
    """Response model for GET /health."""
    status: str
    api: str
    chroma: str
    sqlite: str
    llm: str


class SourceInfo(BaseModel):
    """Source register information."""
    doc_id: str
    title: str
    authority_level: int
    doc_type: str
    version: str
    effective_from: str
    effective_to: Optional[str] = None
    chunk_count: int
    rule_count: int
    ingested_at: str
