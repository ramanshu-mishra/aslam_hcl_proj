"""Validate synthetic student data against schema constraints."""
import csv
from pathlib import Path
import re


def validate_students(file_path):
    """Validate students.csv."""
    errors = []
    
    with open(file_path) as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            # Check student_id format
            if not re.match(r'^S\d{4}$', row['student_id']):
                errors.append(f"Line {i}: Invalid student_id format: {row['student_id']}")
            
            # Check reserved range
            sid_num = int(row['student_id'][1:])
            if 9000 <= sid_num <= 9999:
                errors.append(f"Line {i}: Student ID in reserved range: {row['student_id']}")
            
            # Check semester range
            sem = int(row['current_semester'])
            if not (1 <= sem <= 10):
                errors.append(f"Line {i}: Semester out of range: {sem}")
            
            # Check CGPA range
            cgpa = float(row['cgpa'])
            if not (0 <= cgpa <= 10):
                errors.append(f"Line {i}: CGPA out of range: {cgpa}")
            
            # Check backlogs
            backlogs = int(row['active_backlogs'])
            if backlogs < 0:
                errors.append(f"Line {i}: Negative backlogs: {backlogs}")
    
    return errors


def validate_courses(file_path):
    """Validate courses.csv."""
    errors = []
    
    with open(file_path) as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            # Check reserved course codes
            if row['course_code'].startswith('JDG'):
                errors.append(f"Line {i}: Course code in reserved range: {row['course_code']}")
            
            # Check credits
            credits = int(row['credits'])
            if credits <= 0:
                errors.append(f"Line {i}: Invalid credits: {credits}")
    
    return errors


def validate_attendance(file_path):
    """Validate attendance.csv."""
    errors = []
    
    with open(file_path) as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            held = int(row['classes_held'])
            attended = int(row['classes_attended'])
            
            # Check held > 0
            if held <= 0:
                errors.append(f"Line {i}: classes_held must be > 0: {held}")
            
            # Check attended <= held
            if attended > held:
                errors.append(f"Line {i}: Attended ({attended}) > Held ({held})")
            
            # Check attended >= 0
            if attended < 0:
                errors.append(f"Line {i}: Negative attendance: {attended}")
    
    return errors


def validate_results(file_path):
    """Validate results.csv."""
    errors = []
    
    with open(file_path) as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            # Check exam_type
            if row['exam_type'] not in ['REGULAR', 'SUPPLEMENTARY']:
                errors.append(f"Line {i}: Invalid exam_type: {row['exam_type']}")
            
            # Check result
            if row['result'] not in ['PASS', 'FAIL', 'ABSENT', 'DETAINED']:
                errors.append(f"Line {i}: Invalid result: {row['result']}")
            
            # Check marks consistency (if not ABSENT)
            if row['result'] != 'ABSENT':
                if row['internal_marks'] and row['external_marks'] and row['total_marks']:
                    internal = int(row['internal_marks'])
                    external = int(row['external_marks'])
                    total = int(row['total_marks'])
                    
                    if internal + external != total:
                        errors.append(f"Line {i}: Marks mismatch: {internal}+{external}≠{total}")
    
    return errors


def main():
    """Run all validations."""
    data_dir = Path('data/test_students')
    
    if not data_dir.exists():
        print(f"Error: {data_dir} does not exist")
        print("Run generate_data.py first")
        return 1
    
    print("Validating synthetic student data...\n")
    
    all_errors = []
    
    # Validate each file
    files = {
        'students.csv': validate_students,
        'courses.csv': validate_courses,
        'attendance.csv': validate_attendance,
        'results.csv': validate_results
    }
    
    for filename, validator in files.items():
        file_path = data_dir / filename
        
        if not file_path.exists():
            print(f"❌ {filename}: File not found")
            continue
        
        errors = validator(file_path)
        
        if errors:
            print(f"❌ {filename}: {len(errors)} errors found")
            for error in errors:
                print(f"   - {error}")
            all_errors.extend(errors)
        else:
            print(f"✅ {filename}: All constraints satisfied")
    
    print(f"\n{'='*60}")
    
    if all_errors:
        print(f"❌ Validation FAILED: {len(all_errors)} total errors")
        return 1
    else:
        print("✅ Validation PASSED: All data is valid")
        return 0


if __name__ == "__main__":
    exit(main())
