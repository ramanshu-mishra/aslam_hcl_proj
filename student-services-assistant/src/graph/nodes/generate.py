"""Answer generation node."""
import re
from src.graph.state import GraphState
from src.llm.client import get_llm_client
from src.prompts.templates import get_generator_prompt


def generate_node(state: GraphState) -> GraphState:
    """
    Generate the final answer using LLM.
    """
    # Check if we should skip generation
    if not state.authorized or state.answer:
        return state
    
    # Build context from retrieved chunks
    context_parts = []
    for i, chunk in enumerate(state.retrieved_chunks):
        doc_id = chunk['metadata'].get('doc_id', 'unknown')
        page = chunk['metadata'].get('page_num', 'unknown')
        text = chunk.get('text', '')
        context_parts.append(f"[{doc_id}] (Page {page}):\n{text}\n")
    
    context = "\n".join(context_parts) if context_parts else "No relevant documents found."
    
    # Build tool results summary
    tool_results_str = ""
    if state.tool_results:
        import json
        tool_results_str = json.dumps(state.tool_results, indent=2)
    else:
        tool_results_str = "No tool results."
    
    # Generate answer
    llm = get_llm_client()
    prompt = get_generator_prompt(state.question, context, tool_results_str)
    
    try:
        answer = llm.generate(prompt, temperature=0.1, max_tokens=512)
        state.answer = answer.strip()
        
        # Extract citations
        citations = extract_citations(answer, state.retrieved_chunks)
        state.citations = citations
        
        # Determine answer type
        if state.tool_results:
            state.answer_type = 'calculated'
        elif citations:
            state.answer_type = 'retrieved_fact'
        elif "don't have" in answer.lower() or "not found" in answer.lower():
            state.answer_type = 'not_found'
        else:
            state.answer_type = 'retrieved_fact'
        
        # Generate explanation
        state.explanation = generate_explanation(state)
        
    except Exception as e:
        state.answer = "I encountered an error processing your question."
        state.answer_type = 'not_found'
        state.explanation = f"Error: {str(e)}"
    
    return state


def extract_citations(answer: str, chunks: list) -> list:
    """Extract citation information from answer."""
    citations = []
    
    # Find all [doc_id] patterns in answer
    doc_ids = re.findall(r'\[([^\]]+)\]', answer)
    
    # Build citation info
    seen = set()
    for chunk in chunks:
        metadata = chunk.get('metadata', {})
        doc_id = metadata.get('doc_id')
        
        if doc_id and doc_id in doc_ids and doc_id not in seen:
            citations.append({
                'doc_id': doc_id,
                'title': metadata.get('title', ''),
                'section': None,
                'page': metadata.get('page_num'),
                'version': metadata.get('version', ''),
                'effective_from': metadata.get('effective_from', '')
            })
            seen.add(doc_id)
    
    return citations


def generate_explanation(state: GraphState) -> str:
    """Generate explanation of how answer was derived."""
    parts = []
    
    if state.retrieved_chunks:
        parts.append(f"Retrieved {len(state.retrieved_chunks)} relevant document chunks")
    
    if state.conflicts:
        parts.append(f"Resolved {len(state.conflicts)} conflicts using precedence rules")
    
    if state.tools_invoked:
        tool_names = [t['tool'] for t in state.tools_invoked]
        parts.append(f"Used tools: {', '.join(tool_names)}")
    
    if not parts:
        parts.append("No authoritative sources found")
    
    return ". ".join(parts) + "."
