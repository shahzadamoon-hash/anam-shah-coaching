# routes/assignment_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.sheet_models import Assignment, AssignmentQuestion, AssignmentSubmission, Enrollment
from utils.auth import instructor_required
from datetime import datetime

assignment_bp = Blueprint('assignment', __name__)
assignment_model = Assignment()
question_model = AssignmentQuestion()
submission_model = AssignmentSubmission()
enrollment_model = Enrollment()

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
    return jsonify({'assignment': assignment}), 200

@assignment_bp.route('/', methods=['POST'])
@jwt_required()
@instructor_required
def create_assignment():
    data = request.get_json()
    assignment = assignment_model.create(data)
    return jsonify({'assignment': assignment}), 201

@assignment_bp.route('/<int:assignment_id>', methods=['PUT'])
@jwt_required()
@instructor_required
def update_assignment(assignment_id):
    data = request.get_json()
    assignment = assignment_model.update(assignment_id, data)
    return jsonify({'assignment': assignment}), 200

@assignment_bp.route('/<int:assignment_id>', methods=['DELETE'])
@jwt_required()
@instructor_required
def delete_assignment(assignment_id):
    assignment_model.delete(assignment_id)
    return jsonify({'message': 'Assignment deleted'}), 200

@assignment_bp.route('/submit', methods=['POST'])
@jwt_required()
def submit_assignment():
    data = request.get_json()
    user_id = get_jwt_identity()

    # Verify enrollment exists
    enrollment = enrollment_model.get_by_user_and_course(user_id, data.get('course_id'))
    if not enrollment:
        return jsonify({'error': 'Not enrolled in this course'}), 403

    submission = submission_model.create({
        'enrollment_id': enrollment.get('enrollment_id'),
        'assignment_id': data.get('assignment_id'),
        'answers': data.get('answers'),
        'time_taken': data.get('time_taken', 0)
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

@assignment_bp.route('/submissions/<int:submission_id>/grade', methods=['PUT'])
@jwt_required()
@instructor_required
def grade_submission(submission_id):
    data = request.get_json()
    submission = submission_model.update(submission_id, {
        'score': data.get('score'),
        'obtained_marks': data.get('obtained_marks'),
        'percentage': data.get('percentage'),
        'is_passed': str(data.get('is_passed', False)).lower(),
        'is_graded': 'true',
        'graded_at': datetime.utcnow().isoformat()
    })
    return jsonify({'submission': submission}), 200

@assignment_bp.route('/upcoming', methods=['GET'])
@jwt_required()
def get_upcoming_assignments():
    user_id = get_jwt_identity()

    # Get user's enrollments
    enrollments = enrollment_model.get_by_user(user_id)
    enrollment_ids = [e.get('enrollment_id') for e in enrollments]

    # Get assignments for enrolled courses
    all_assignments = []
    for enrollment in enrollments:
        course_id = enrollment.get('course_id')
        # Get assignments for this course's lessons
        # This is a simplified version - you might want to add a lesson lookup
        assignments = assignment_model.query(course_id=str(course_id))
        all_assignments.extend(assignments)

    # Sort by due date
    all_assignments.sort(key=lambda x: x.get('due_date', ''), reverse=False)

    # Return upcoming (not overdue)
    from datetime import datetime
    now = datetime.utcnow().isoformat()
    upcoming = [a for a in all_assignments if a.get('due_date', '') >= now or not a.get('due_date')]

    # Add course names
    for assignment in upcoming[:5]:
        course_id = assignment.get('course_id')
        if course_id:
            course = course_model.get_by_id(course_id)
            assignment['course_name'] = course.get('title', 'Course') if course else 'Course'
        assignment['icon'] = 'pencil-alt'

    return jsonify({'assignments': upcoming[:5]}), 200