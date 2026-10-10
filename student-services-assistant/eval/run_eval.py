"""Evaluation script for testing the assistant."""
import sys
from pathlib import Path
import json
from datetime import date

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.graph.workflow import run_workflow


# Evaluation questions
EVAL_SET = [
    {
        "id": "Q1",
        "question": "What is the minimum attendance required for exams?",
        "type": "policy",
        "expected_answer_type": "retrieved_fact",
        "requires_auth": False
    },
    {
        "id": "Q2",
        "question": "What is my attendance?",
        "type": "personal",
        "expected_answer_type": "calculated",
        "requires_auth": True,
        "test_student_id": "S1001"
    },
    {
        "id": "Q3",
        "question": "What is the grading scale?",
        "type": "policy",
        "expected_answer_type": "retrieved_fact",
        "requires_auth": False
    },
    {
        "id": "Q4",
        "question": "What is my CGPA?",
        "type": "personal",
        "expected_answer_type": "calculated",
        "requires_auth": True,
        "test_student_id": "S1001"
    },
    {
        "id": "Q5",
        "question": "What are the credit requirements for graduation?",
        "type": "policy",
        "expected_answer_type": "retrieved_fact",
        "requires_auth": False
    },
]


def run_evaluation():
    """Run evaluation on the question set."""
    print("=" * 80)
    print("Running Evaluation")
    print("=" * 80)
    
    results = []
    
    for question_data in EVAL_SET:
        print(f"\n[{question_data['id']}] {question_data['question']}")
        print("-" * 80)
        
        try:
            # Run workflow
            student_id = question_data.get('test_student_id') if question_data['requires_auth'] else None
            
            result = run_workflow(
                question=question_data['question'],
                student_id=student_id,
                as_of_date=date.today()
            )
            
            # Check results
            answer_type = result['answer_type']
            answer = result['answer']
            citations = result.get('citations', [])
            tools = result.get('tools_invoked', [])
            
            print(f"Answer Type: {answer_type}")
            print(f"Answer: {answer[:200]}..." if len(answer) > 200 else f"Answer: {answer}")
            print(f"Citations: {len(citations)}")
            print(f"Tools Used: {len(tools)}")
            
            # Evaluate
            correct_type = answer_type == question_data['expected_answer_type']
            has_answer = len(answer) > 10 and answer != "I don't have this information"
            
            score = 1.0 if (correct_type and has_answer) else 0.5 if has_answer else 0.0
            
            print(f"Score: {score:.1f}/1.0")
            
            results.append({
                'question_id': question_data['id'],
                'question': question_data['question'],
                'expected_type': question_data['expected_answer_type'],
                'actual_type': answer_type,
                'answer': answer,
                'citations': len(citations),
                'tools': len(tools),
                'score': score
            })
            
        except Exception as e:
            print(f"ERROR: {e}")
            results.append({
                'question_id': question_data['id'],
                'question': question_data['question'],
                'error': str(e),
                'score': 0.0
            })
    
    # Summary
    print("\n" + "=" * 80)
    print("Evaluation Summary")
    print("=" * 80)
    
    total_score = sum(r['score'] for r in results)
    max_score = len(results)
    accuracy = (total_score / max_score) * 100
    
    print(f"Total Score: {total_score:.1f}/{max_score}")
    print(f"Accuracy: {accuracy:.1f}%")
    
    # Save results
    output_file = Path(__file__).parent / "eval_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            'total_score': total_score,
            'max_score': max_score,
            'accuracy': accuracy,
            'results': results
        }, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    
    # Generate report
    generate_report(results, total_score, max_score, accuracy)
    
    return 0 if accuracy >= 50 else 1


def generate_report(results, total_score, max_score, accuracy):
    """Generate markdown report."""
    report_file = Path(__file__).parent / "report.md"
    
    with open(report_file, 'w') as f:
        f.write("# Evaluation Report\n\n")
        f.write(f"**Date:** {date.today().isoformat()}\n\n")
        f.write(f"**Total Score:** {total_score:.1f}/{max_score}\n\n")
        f.write(f"**Accuracy:** {accuracy:.1f}%\n\n")
        
        f.write("## Results by Question\n\n")
        
        for r in results:
            f.write(f"### {r['question_id']}: {r['question']}\n\n")
            f.write(f"- **Expected Type:** {r.get('expected_type', 'N/A')}\n")
            f.write(f"- **Actual Type:** {r.get('actual_type', 'N/A')}\n")
            f.write(f"- **Citations:** {r.get('citations', 0)}\n")
            f.write(f"- **Tools Used:** {r.get('tools', 0)}\n")
            f.write(f"- **Score:** {r['score']:.1f}/1.0\n")
            
            if 'error' in r:
                f.write(f"- **Error:** {r['error']}\n")
            else:
                answer = r.get('answer', '')[:150]
                f.write(f"- **Answer:** {answer}...\n")
            
            f.write("\n")
    
    print(f"Report saved to: {report_file}")


if __name__ == "__main__":
    sys.exit(run_evaluation())
