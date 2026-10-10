"""Generate synthetic student data for testing."""
import random
import csv
from pathlib import Path
from datetime import date


def generate_students(num_students=30):
    """Generate synthetic student records."""
    programmes = ["B.Tech CSE", "B.Tech ECE"]
    batches = [2023, 2024]
    
    students = []
    for i in range(1, num_students + 1):
        student_id = f"S{1000 + i}"
        students.append({
            'student_id': student_id,
            'full_name': f"Student {i}",
            'programme': random.choice(programmes),
            'batch_year': random.choice(batches),
            'current_semester': random.randint(1, 8),
            'cgpa': round(random.uniform(6.0, 9.5), 2),
            'active_backlogs': random.choice([0, 0, 0, 1, 2])
        })
    
    return students


def generate_courses():
    """Generate course records."""
    courses = []
    
    # CSE courses
    cse_courses = [
        ("CS101", "Programming Fundamentals", 1, 4),
        ("CS201", "Data Structures", 3, 4),
        ("CS202", "Algorithms", 4, 4),
        ("CS301", "Database Systems", 5, 3),
        ("CS401", "Machine Learning", 7, 3),
    ]
    
    # ECE courses
    ece_courses = [
        ("EC101", "Circuit Theory", 1, 4),
        ("EC201", "Digital Electronics", 3, 4),
        ("EC202", "Signals and Systems", 4, 4),
    ]
    
    for code, name, sem, credits in cse_courses:
        courses.append({
            'course_code': code,
            'course_name': name,
            'programme': 'B.Tech CSE',
            'semester': sem,
            'credits': credits
        })
    
    for code, name, sem, credits in ece_courses:
        courses.append({
            'course_code': code,
            'course_name': name,
            'programme': 'B.Tech ECE',
            'semester': sem,
            'credits': credits
        })
    
    return courses


def generate_attendance(students, courses):
    """Generate attendance records."""
    attendance = []
    
    for student in students:
        # Get courses for student's programme
        student_courses = [c for c in courses if c['programme'] == student['programme']]
        
        # Generate attendance for 2-3 courses
        for course in random.sample(student_courses, min(3, len(student_courses))):
            held = random.choice([40, 45, 50])
            
            # Create edge cases for some students
            if student['student_id'] in ['S1001', 'S1002']:
                # Exactly at threshold (75%)
                attended = int(held * 0.75)
            elif student['student_id'] == 'S1003':
                # One below threshold
                attended = int(held * 0.75) - 1
            else:
                # Random attendance
                attended = random.randint(int(held * 0.6), held)
            
            attendance.append({
                'student_id': student['student_id'],
                'course_code': course['course_code'],
                'classes_held': held,
                'classes_attended': attended
            })
    
    return attendance


def generate_results(students, courses):
    """Generate result records."""
    results = []
    
    for student in students:
        student_courses = [c for c in courses if c['programme'] == student['programme']]
        
        for course in random.sample(student_courses, min(2, len(student_courses))):
            max_marks = 100
            pass_marks = 40
            
            # Random result
            if random.random() < 0.8:  # 80% pass rate
                internal = random.randint(15, 30)
                external = random.randint(30, 70)
                result = 'PASS'
            else:
                internal = random.randint(10, 25)
                external = random.randint(10, 35)
                result = 'FAIL'
            
            total = internal + external
            
            results.append({
                'student_id': student['student_id'],
                'course_code': course['course_code'],
                'exam_session': '2024-MAY',
                'exam_type': 'REGULAR',
                'internal_marks': internal,
                'external_marks': external,
                'total_marks': total,
                'max_marks': max_marks,
                'result': result
            })
    
    return results


def save_to_csv(data, filename, fieldnames):
    """Save data to CSV file."""
    output_dir = Path('data/test_students')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    print(f"Generated {filename} with {len(data)} records")


def main():
    """Generate all synthetic data."""
    print("Generating synthetic student data...")
    
    # Generate data
    students = generate_students(30)
    courses = generate_courses()
    attendance = generate_attendance(students, courses)
    results = generate_results(students, courses)
    
    # Save to CSV
    save_to_csv(students, 'students.csv', 
                ['student_id', 'full_name', 'programme', 'batch_year', 
                 'current_semester', 'cgpa', 'active_backlogs'])
    
    save_to_csv(courses, 'courses.csv',
                ['course_code', 'course_name', 'programme', 'semester', 'credits'])
    
    save_to_csv(attendance, 'attendance.csv',
                ['student_id', 'course_code', 'classes_held', 'classes_attended'])
    
    save_to_csv(results, 'results.csv',
                ['student_id', 'course_code', 'exam_session', 'exam_type',
                 'internal_marks', 'external_marks', 'total_marks', 'max_marks', 'result'])
    
    print("\nData generation complete!")
    print(f"Generated {len(students)} students, {len(courses)} courses")
    print(f"Generated {len(attendance)} attendance records, {len(results)} results")
    
    # Create data card
    card_path = Path('data/data_card.md')
    with open(card_path, 'w') as f:
        f.write(f"""# Synthetic Data Card

## Purpose
Testing data for the Student Services Assistant MVP.

## Generator
- Method: Python script with random generation
- Date: {date.today()}
- Student Count: {len(students)}
- Course Count: {len(courses)}

## Schema
Follows Annex C schema exactly.

## Edge Cases
- S1001, S1002: Attendance exactly at 75% threshold
- S1003: Attendance one class below threshold
- Random distribution of pass/fail results

## Validation
Run `python scripts/validate_data.py` to validate constraints.
""")
    
    print(f"\nCreated data card at {card_path}")


if __name__ == "__main__":
    main()
