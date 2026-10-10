"""Authorization node for access control."""
from src.graph.state import GraphState


def authorize_node(state: GraphState) -> GraphState:
    """
    Check authorization for personal data access.
    
    Rule: If query needs personal data, student_id MUST be in header.
    LLM cannot choose whose data to access.
    """
    if state.needs_personal_data:
        if not state.student_id:
            state.authorized = False
            state.answer_type = 'refused'
            state.answer = "This question requires authentication. Please provide your student ID."
            state.explanation = "Personal data access denied: no student_id in request header"
            return state
    
    state.authorized = True
    return state
