"""Graph state definition."""
from typing import List, Dict, Any, Optional, Literal
from datetime import date
from pydantic import BaseModel


class GraphState(BaseModel):
    """State passed through the graph workflow."""
    
    # Input
    question: str
    student_id: Optional[str] = None
    as_of_date: date
    trace_id: str
    
    # Classification
    intent: Optional[str] = None
    needs_personal_data: bool = False
    confidence: float = 0.0
    
    # Retrieval
    retrieved_chunks: List[Dict[str, Any]] = []
    conflicts: List[Dict[str, Any]] = []
    
    # Tool execution
    tools_invoked: List[Dict[str, Any]] = []
    tool_results: Dict[str, Any] = {}
    
    # Rules
    applied_rules: List[Dict[str, Any]] = []
    
    # Generation
    answer: str = ""
    answer_type: Literal[
        'retrieved_fact',
        'calculated',
        'not_found',
        'clarification_needed',
        'refused',
        'conflict_flagged'
    ] = 'not_found'
    citations: List[Dict[str, Any]] = []
    explanation: str = ""
    
    # Control flow
    should_retrieve: bool = False
    should_use_tools: bool = False
    authorized: bool = True
    
    class Config:
        arbitrary_types_allowed = True
