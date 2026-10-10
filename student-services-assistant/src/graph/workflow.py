"""Main LangGraph workflow definition."""
from datetime import date
from typing import Dict, Any, Optional
import uuid

from langgraph.graph import StateGraph, END
from src.graph.state import GraphState
from src.graph.nodes.classify import classify_node
from src.graph.nodes.authorize import authorize_node
from src.graph.nodes.retrieve import retrieve_node
from src.graph.nodes.execute_tools import execute_tools_node
from src.graph.nodes.generate import generate_node


def create_workflow() -> StateGraph:
    """
    Create the LangGraph workflow.
    
    Flow:
    1. Classify query intent
    2. Authorize access (if personal data needed)
    3. Retrieve relevant documents
    4. Execute tools (if needed)
    5. Generate answer
    """
    workflow = StateGraph(GraphState)
    
    # Add nodes
    workflow.add_node("classify", classify_node)
    workflow.add_node("authorize", authorize_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("execute_tools", execute_tools_node)
    workflow.add_node("generate", generate_node)
    
    # Set entry point
    workflow.set_entry_point("classify")
    
    # Add edges
    workflow.add_edge("classify", "authorize")
    
    # Conditional edge from authorize
    def should_continue(state: GraphState) -> str:
        if not state.authorized:
            return "end"
        return "retrieve"
    
    workflow.add_conditional_edges(
        "authorize",
        should_continue,
        {
            "retrieve": "retrieve",
            "end": END
        }
    )
    
    workflow.add_edge("retrieve", "execute_tools")
    workflow.add_edge("execute_tools", "generate")
    workflow.add_edge("generate", END)
    
    return workflow.compile()


def run_workflow(
    question: str,
    student_id: Optional[str] = None,
    as_of_date: Optional[date] = None,
    trace_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run the workflow for a question.
    
    Args:
        question: User question
        student_id: Student ID from header (if authenticated)
        as_of_date: Date for query context
        trace_id: Trace ID for audit
    
    Returns:
        Final state as dict
    """
    # Create initial state
    initial_state = GraphState(
        question=question,
        student_id=student_id,
        as_of_date=as_of_date or date.today(),
        trace_id=trace_id or uuid.uuid4().hex[:8]
    )
    
    # Create and run workflow
    workflow = create_workflow()
    final_state = workflow.invoke(initial_state)
    
    # Convert to dict for response
    return final_state.model_dump()
