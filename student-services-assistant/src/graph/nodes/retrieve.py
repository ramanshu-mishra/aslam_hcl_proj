"""Retrieval node for finding relevant documents."""
from src.graph.state import GraphState
from src.retrieval.retriever import HybridRetriever
from src.precedence.engine import PrecedenceEngine


def retrieve_node(state: GraphState) -> GraphState:
    """
    Retrieve relevant chunks and resolve conflicts.
    """
    if not state.should_retrieve:
        return state
    
    retriever = HybridRetriever()
    precedence = PrecedenceEngine()
    
    # Retrieve chunks
    chunks = retriever.retrieve(
        query=state.question,
        as_of_date=state.as_of_date,
        k=5
    )
    
    if not chunks:
        state.answer_type = 'not_found'
        return state
    
    # Detect conflicts
    conflicts = precedence.detect_conflicts(chunks, state.as_of_date)
    state.conflicts = conflicts
    
    # Resolve conflicts
    resolved_chunks = precedence.resolve(chunks, state.as_of_date)
    state.retrieved_chunks = resolved_chunks
    
    return state
