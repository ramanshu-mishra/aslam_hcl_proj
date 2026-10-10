"""Deterministic tools for student data operations."""
from datetime import date
from typing import Dict, Any, List, Optional
from src.db.connection import get_db


def get_student_profile(student_id: str) -> Dict[str, Any]:
    """Get student profile information."""
    db = get_db()
    
    with db.transaction() as conn:
        cursor = conn.execute(
            """
            SELECT student_id, name, programme, batch, email, phone, 
                   advisor_name, status
            FROM students
            WHERE student_id = ?
            """,
            (student_id,)
        )
        row = cursor.fetchone()
    
    if not row:
        return {"error": f"Student {student_id} not found"}
    
    return dict(row)


def get_student_courses(student_id: str, semester: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get courses enrolled by a student."""
    db = get_db()
    
    query = """
        SELECT e.course_code, c.course_name, c.credits, 
               e.semester, e.grade, e.grade_points
        FROM enrollments e
        JOIN courses c ON e.course_code = c.course_code
        WHERE e.student_id = ?
    """
    
    params = [student_id]
    if semester:
        query += " AND e.semester = ?"
        params.append(semester)
    
    query += " ORDER BY e.semester DESC, e.course_code"
    
    with db.transaction() as conn:
        cursor = conn.execute(query, params)
        courses = [dict(row) for row in cursor.fetchall()]
    
    return courses


def get_student_attendance(
    student_id: str,
    course_code: Optional[str] = None,
    as_of_date: Optional[date] = None
) -> Dict[str, Any]:
    """Get attendance information for a student."""
    db = get_db()
    as_of_date = as_of_date or date.today()
    
    query = """
        SELECT course_code, total_classes, attended_classes,
               excused_absences, last_updated
        FROM attendance
        WHERE student_id = ? AND last_updated <= ?
    """
    
    params = [student_id, as_of_date.isoformat()]
    
    if course_code:
        query += " AND course_code = ?"
        params.append(course_code)
    
    with db.transaction() as conn:
        cursor = conn.execute(query, params)
        records = [dict(row) for row in cursor.fetchall()]
    
    if not records:
        return {"error": f"No attendance records found for {student_id}"}
    
    # Calculate percentages
    for record in records:
        record['percentage'] = calculate_attendance_percentage(
            record['attended_classes'],
            record['total_classes']
        )
    
    if course_code:
        return records[0] if records else {}
    
    return {"courses": records, "as_of_date": as_of_date.isoformat()}


def calculate_attendance_percentage(attended: int, total: int) -> float:
    """Calculate attendance percentage."""
    if total == 0:
        return 0.0
    return round((attended / total) * 100, 2)


def check_exam_eligibility(
    student_id: str,
    course_code: str,
    min_attendance_pct: float = 75.0,
    as_of_date: Optional[date] = None
) -> Dict[str, Any]:
    """
    Check if a student is eligible for exams based on attendance.
    
    Args:
        student_id: Student identifier
        course_code: Course code
        min_attendance_pct: Minimum required attendance percentage
        as_of_date: Date for checking eligibility
    
    Returns:
        Eligibility information with status and details
    """
    attendance = get_student_attendance(student_id, course_code, as_of_date)
    
    if 'error' in attendance:
        return {
            "eligible": False,
            "reason": attendance['error'],
            "attendance_percentage": 0.0,
            "required_percentage": min_attendance_pct
        }
    
    current_pct = attendance['percentage']
    eligible = current_pct >= min_attendance_pct
    
    result = {
        "eligible": eligible,
        "attendance_percentage": current_pct,
        "required_percentage": min_attendance_pct,
        "attended_classes": attendance['attended_classes'],
        "total_classes": attendance['total_classes'],
        "course_code": course_code,
        "as_of_date": (as_of_date or date.today()).isoformat()
    }
    
    if not eligible:
        shortage = min_attendance_pct - current_pct
        result["reason"] = f"Attendance shortage of {shortage:.2f}%"
    
    return result


def get_cgpa(student_id: str) -> Dict[str, Any]:
    """Calculate CGPA for a student."""
    db = get_db()
    
    with db.transaction() as conn:
        cursor = conn.execute(
            """
            SELECT e.grade_points, c.credits
            FROM enrollments e
            JOIN courses c ON e.course_code = c.course_code
            WHERE e.student_id = ? AND e.grade_points IS NOT NULL
            """,
            (student_id,)
        )
        records = cursor.fetchall()
    
    if not records:
        return {"error": f"No grade records found for {student_id}"}
    
    total_points = 0.0
    total_credits = 0.0
    
    for row in records:
        grade_points = row['grade_points']
        credits = row['credits']
        total_points += grade_points * credits
        total_credits += credits
    
    if total_credits == 0:
        cgpa = 0.0
    else:
        cgpa = round(total_points / total_credits, 2)
    
    return {
        "student_id": student_id,
        "cgpa": cgpa,
        "total_credits": total_credits
    }
