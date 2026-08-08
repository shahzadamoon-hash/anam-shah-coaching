from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.sheet_models import Assignment, AssignmentQuestion, AssignmentSubmission, Enrollment, Course
from datetime import datetime

assignment_bp = Blueprint('assignment', __name__)
assignment_model = Assignment()
question_model = AssignmentQuestion()
submission_model = AssignmentSubmission()
enrollment_model = Enrollment()
course_model = Course()

@assignment_bp.route('/upcoming', methods=['GET'])
@jwt_required()
def get_upcoming_assignments():
    user_id = get_jwt_identity()

    # Get user's enrollments
    enrollments = enrollment_model.get_by_user(user_id)

    # Get assignments for enrolled courses
    all_assignments = []
    for enrollment in enrollments:
        course_id = enrollment.get('course_id')
        # Get assignments for this course
        assignments = assignment_model.query(course_id=str(course_id))
        for assignment in assignments:
            assignment['course_name'] = course_model.get_by_id(course_id).get('title', 'Course') if course_id else 'Course'
            assignment['icon'] = 'pencil-alt'
            all_assignments.append(assignment)

    # Sort by due date
    all_assignments.sort(key=lambda x: x.get('due_date', ''), reverse=False)

    # Return upcoming (not overdue)
    now = datetime.utcnow().isoformat()
    upcoming = [a for a in all_assignments if a.get('due_date', '') >= now or not a.get('due_date')]

    return jsonify({'assignments': upcoming[:5]}), 200

@assignment_bp.route('/lesson/<int:lesson_id>', methods=['GET'])
@jwt_required()
def get_assignments_by_lesson(lesson_id):
    assignments = assignment_model.query(lesson_id=str(lesson_id))
    return jsonify({'assignments': assignments}), 200

@assignment_bp.route('/<int:assignment_id>', methods=['GET'])
@jwt_required()
def get_assignment(assignment_id):
    assignment = assignment_model.get_by_id(assignment_id)
    if not assignment:
        return jsonify({'error': 'Assignment not found'}), 404

    # Get questions
    questions = question_model.get_by_assignment(assignment_id)
    assignment['questions'] = questions

    return jsonify({'assignment': assignment}), 200

@assignment_bp.route('/submit', methods=['POST'])
@jwt_required()
def submit_assignment():
    data = request.get_json()
    user_id = get_jwt_identity()

    # Verify enrollment exists
    enrollment = enrollment_model.get_by_user_and_course(user_id, data.get('course_id'))
    if not enrollment:
        return jsonify({'error': 'Not enrolled in this course'}), 403

    # Calculate score
    assignment_id = data.get('assignment_id')
    questions = question_model.get_by_assignment(assignment_id)
    answers = data.get('answers', {})

    correct = 0
    total = len(questions)

    for q in questions:
        q_id = str(q.get('question_id'))
        if q_id in answers and answers[q_id] == q.get('correct_answer'):
            correct += 1

    score = round((correct / total * 100) if total > 0 else 0, 2)
    is_passed = score >= 60

    submission = submission_model.create({
        'enrollment_id': enrollment.get('enrollment_id'),
        'assignment_id': assignment_id,
        'answers': json.dumps(answers),
        'score': score,
        'total_marks': total,
        'obtained_marks': correct,
        'percentage': score,
        'is_passed': str(is_passed).lower(),
        'is_graded': 'true',
        'graded_at': datetime.utcnow().isoformat(),
        'time_taken': data.get('time_taken', 0),
        'submitted_at': datetime.utcnow().isoformat()
    })

    return jsonify({'submission': submission}), 201

@assignment_bp.route('/submissions', methods=['GET'])
@jwt_required()
def get_submissions():
    user_id = get_jwt_identity()
    enrollments = enrollment_model.get_by_user(user_id)

    all_submissions = []
    for enrollment in enrollments:
        submissions = submission_model.query(enrollment_id=str(enrollment.get('enrollment_id')))
        all_submissions.extend(submissions)

    return jsonify({'submissions': all_submissions}), 200