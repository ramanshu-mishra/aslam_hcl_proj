"""Tool execution node."""
from src.graph.state import GraphState
from src.tools.factory import invoke_tool


def execute_tools_node(state: GraphState) -> GraphState:
    """
    Execute deterministic tools for calculations and data access.
    """
    if not state.should_use_tools or not state.authorized:
        return state
    
    # Determine which tools to call based on intent
    if state.intent == 'personal_query':
        # Example: attendance query
        if 'attendance' in state.question.lower():
            result = invoke_tool(
                'get_student_attendance',
                student_id=state.student_id,
                as_of_date=state.as_of_date
            )
            state.tools_invoked.append({
                'tool': 'get_student_attendance',
                'input': {'student_id': state.student_id},
                'output': result
            })
            state.tool_results['attendance'] = result
        
        elif 'cgpa' in state.question.lower() or 'grade' in state.question.lower():
            result = invoke_tool('get_cgpa', student_id=state.student_id)
            state.tools_invoked.append({
                'tool': 'get_cgpa',
                'input': {'student_id': state.student_id},
                'output': result
            })
            state.tool_results['cgpa'] = result
        
        elif 'course' in state.question.lower():
            result = invoke_tool('get_student_courses', student_id=state.student_id)
            state.tools_invoked.append({
                'tool': 'get_student_courses',
                'input': {'student_id': state.student_id},
                'output': result
            })
            state.tool_results['courses'] = result
    
    elif state.intent == 'calculation':
        # Example: eligibility check
        if 'eligible' in state.question.lower() or 'exam' in state.question.lower():
            # This would need more sophisticated parsing to extract course_code
            # For MVP, we return a generic message
            state.tool_results['message'] = "Eligibility check requires course code specification"
    
    return state
