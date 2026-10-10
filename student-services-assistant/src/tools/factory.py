"""Tool factory for registering and invoking tools."""
from typing import Dict, Any, Callable, List
from src.tools.student_tools import (
    get_student_profile,
    get_student_courses,
    get_student_attendance,
    check_exam_eligibility,
    get_cgpa
)


# Tool registry
TOOLS: Dict[str, Dict[str, Any]] = {
    "get_student_profile": {
        "function": get_student_profile,
        "description": "Get student profile information",
        "params": ["student_id"]
    },
    "get_student_courses": {
        "function": get_student_courses,
        "description": "Get courses enrolled by a student",
        "params": ["student_id", "semester"]
    },
    "get_student_attendance": {
        "function": get_student_attendance,
        "description": "Get attendance records for a student",
        "params": ["student_id", "course_code", "as_of_date"]
    },
    "check_exam_eligibility": {
        "function": check_exam_eligibility,
        "description": "Check exam eligibility based on attendance",
        "params": ["student_id", "course_code", "min_attendance_pct", "as_of_date"]
    },
    "get_cgpa": {
        "function": get_cgpa,
        "description": "Calculate CGPA for a student",
        "params": ["student_id"]
    }
}


def get_tool(tool_name: str) -> Callable:
    """Get a tool function by name."""
    if tool_name not in TOOLS:
        raise ValueError(f"Unknown tool: {tool_name}")
    return TOOLS[tool_name]["function"]


def list_tools() -> List[Dict[str, Any]]:
    """List all available tools."""
    return [
        {
            "name": name,
            "description": info["description"],
            "params": info["params"]
        }
        for name, info in TOOLS.items()
    ]


def invoke_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    """Invoke a tool with given parameters."""
    tool_func = get_tool(tool_name)
    return tool_func(**kwargs)
