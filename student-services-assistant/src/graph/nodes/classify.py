"""Classification node for intent detection."""
from src.graph.state import GraphState
from src.llm.client import get_llm_client
from src.prompts.templates import get_classifier_prompt


def classify_node(state: GraphState) -> GraphState:
    """
    Classify the query intent and determine routing.
    
    Outputs:
    - intent: Type of query
    - needs_personal_data: Whether student data access is needed
    - should_retrieve: Whether to retrieve from documents
    - should_use_tools: Whether to invoke tools
    """
    llm = get_llm_client()
    
    prompt = get_classifier_prompt(state.question)
    
    try:
        result = llm.generate_json(prompt, temperature=0.0)
        
        state.intent = result.get('intent', 'general_query')
        state.needs_personal_data = result.get('needs_personal_data', False)
        state.confidence = result.get('confidence', 0.5)
        
        # Determine routing
        if state.intent in ['personal_query', 'calculation']:
            state.should_use_tools = True
            state.should_retrieve = True  # May also need policy docs
        else:
            state.should_retrieve = True
            state.should_use_tools = False
        
    except Exception as e:
        # Fallback: assume general query
        state.intent = 'general_query'
        state.needs_personal_data = False
        state.should_retrieve = True
        state.should_use_tools = False
        state.confidence = 0.3
    
    return state
