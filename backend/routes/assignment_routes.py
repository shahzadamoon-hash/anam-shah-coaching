from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.sheet_models import Assignment, AssignmentQuestion, AssignmentSubmission, Enrollment, Course
from utils.auth import instructor_required
from datetime import datetime

assignment_bp = Blueprint('assignment', __name__)
assignment_model = Assignment()
question_model = AssignmentQuestion()
submission_model = AssignmentSubmission()
enrollment_model = Enrollment()
course_model = Course()

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


# ============================================================
# ✅ NEW: GET UPCOMING ASSIGNMENTS (for dashboard)
# ============================================================

@assignment_bp.route('/upcoming', methods=['GET'])
@jwt_required()
def get_upcoming_assignments():
    """Get upcoming assignments for the current user's enrolled courses"""
    user_id = get_jwt_identity()
    
    try:
        # Get user's enrollments
        enrollments = enrollment_model.get_by_user(user_id)
        course_ids = [int(e.get('course_id')) for e in enrollments if e.get('course_id')]
        
        if not course_ids:
            return jsonify({
                'assignments': [],
                'message': 'No courses enrolled'
            }), 200
        
        # Get all assignments
        all_assignments = assignment_model.get_all()
        
        # Filter: only assignments for user's courses, not submitted, and due in future
        upcoming = []
        now = datetime.utcnow().isoformat()
        
        for assignment in all_assignments:
            # Check if assignment belongs to user's enrolled courses
            assignment_course_id = int(assignment.get('course_id', 0))
            if assignment_course_id not in course_ids:
                continue
            
            # Check if already submitted by this user
            submitted = submission_model.query(
                assignment_id=assignment.get('assignment_id'),
                enrollment_id__in=[e.get('enrollment_id') for e in enrollments]
            )
            
            # If submitted, skip (or mark as completed)
            if submitted:
                continue
            
            # Check if due date is in future (or no due date)
            due_date = assignment.get('due_date')
            if due_date and due_date < now:
                continue  # Past due, skip
            
            # Add course name
            course = course_model.get_by_id(assignment_course_id)
            assignment['course_name'] = course.get('title') if course else 'Unknown Course'
            
            # Add icon based on assignment type
            assignment_type = assignment.get('assignment_type', 'practice')
            icons = {
                'practice': 'pencil-alt',
                'graded': 'star',
                'quiz': 'question-circle',
                'project': 'code'
            }
            assignment['icon'] = icons.get(assignment_type, 'file')
            
            upcoming.append(assignment)
        
        # Sort by due date (soonest first)
        upcoming.sort(key=lambda x: x.get('due_date', '9999-12-31'))
        
        return jsonify({
            'assignments': upcoming[:5],  # Return top 5
            'count': len(upcoming)
        }), 200
        
    except Exception as e:
        print(f"Error fetching upcoming assignments: {e}")
        return jsonify({
            'assignments': [],
            'error': 'Failed to fetch assignments'
        }), 200


# ============================================================
# ✅ NEW: GET ASSIGNMENT DETAILS WITH QUESTIONS
# ============================================================

@assignment_bp.route('/<int:assignment_id>/details', methods=['GET'])
@jwt_required()
def get_assignment_details(assignment_id):
    """Get assignment with all questions"""
    user_id = get_jwt_identity()
    
    try:
        # Get assignment
        assignment = assignment_model.get_by_id(assignment_id)
        if not assignment:
            return jsonify({'error': 'Assignment not found'}), 404
        
        # Check if user is enrolled in the course
        course_id = int(assignment.get('course_id', 0))
        enrollment = enrollment_model.get_by_user_and_course(user_id, course_id)
        if not enrollment:
            return jsonify({'error': 'Not enrolled in this course'}), 403
        
        # Get questions
        questions = question_model.get_by_assignment(assignment_id)
        
        # Return assignment with questions
        return jsonify({
            'assignment': assignment,
            'questions': questions,
            'total_questions': len(questions)
        }), 200
        
    except Exception as e:
        print(f"Error fetching assignment details: {e}")
        return jsonify({'error': 'Failed to fetch assignment'}), 500


# ============================================================
# ✅ NEW: GET ASSIGNMENT RESULTS (for student)
# ============================================================

@assignment_bp.route('/<int:assignment_id>/results', methods=['GET'])
@jwt_required()
def get_assignment_results(assignment_id):
    """Get results for a specific assignment submission"""
    user_id = get_jwt_identity()
    
    try:
        # Get user's enrollments
        enrollments = enrollment_model.get_by_user(user_id)
        enrollment_ids = [e.get('enrollment_id') for e in enrollments]
        
        # Find submission for this assignment
        submissions = submission_model.query(
            assignment_id=str(assignment_id)
        )
        
        # Filter by user's enrollments
        user_submissions = [
            s for s in submissions 
            if s.get('enrollment_id') in enrollment_ids
        ]
        
        if not user_submissions:
            return jsonify({
                'submission': None,
                'message': 'No submission found'
            }), 200
        
        # Get the latest submission
        submission = user_submissions[-1]
        
        # Get assignment details
        assignment = assignment_model.get_by_id(assignment_id)
        
        return jsonify({
            'submission': submission,
            'assignment': assignment
        }), 200
        
    except Exception as e:
        print(f"Error fetching results: {e}")
        return jsonify({'error': 'Failed to fetch results'}), 500