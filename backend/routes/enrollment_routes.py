from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.sheet_models import Enrollment, Course, LessonProgress, Notification
from datetime import datetime

enrollment_bp = Blueprint('enrollment', __name__)
enrollment_model = Enrollment()
course_model = Course()
progress_model = LessonProgress()
notification_model = Notification()

@enrollment_bp.route('/', methods=['GET'])
@jwt_required()
def get_enrollments():
    user_id = get_jwt_identity()
    enrollments = enrollment_model.get_by_user(user_id)
    
    # Add course details
    for enrollment in enrollments:
        course = course_model.get_by_id(enrollment.get('course_id'))
        if course:
            enrollment['course_title'] = course.get('title')
            enrollment['course_thumbnail'] = course.get('thumbnail')
            enrollment['course_level'] = course.get('level')
    
    return jsonify({'enrollments': enrollments}), 200

@enrollment_bp.route('/course/<int:course_id>', methods=['POST'])
@jwt_required()
def enroll(course_id):
    user_id = get_jwt_identity()
    
    # Check if already enrolled
    existing = enrollment_model.get_by_user_and_course(user_id, course_id)
    if existing:
        return jsonify({'error': 'Already enrolled'}), 400
    
    # Create enrollment
    enrollment = enrollment_model.create({
        'user_id': user_id,
        'course_id': course_id,
        'enrollment_date': datetime.utcnow().isoformat(),
        'status': 'enrolled',
        'progress_percentage': 0
    })
    
    # Create notification
    course = course_model.get_by_id(course_id)
    notification_model.create({
        'user_id': user_id,
        'type': 'enrollment',
        'title': 'Course Enrolled',
        'message': f'You have enrolled in {course.get("title", "Course")}',
        'is_read': 'false',
        'created_at': datetime.utcnow().isoformat()
    })
    
    return jsonify({
        'message': 'Successfully enrolled',
        'enrollment': enrollment
    }), 201

@enrollment_bp.route('/<int:enrollment_id>/progress', methods=['PUT'])
@jwt_required()
def update_progress(enrollment_id):
    data = request.get_json()
    user_id = get_jwt_identity()
    
    # Verify ownership
    enrollment = enrollment_model.get_by_id(enrollment_id)
    if not enrollment or int(enrollment.get('user_id')) != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Update progress
    enrollment_model.update(enrollment_id, {
        'progress_percentage': data.get('progress_percentage'),
        'last_accessed': datetime.utcnow().isoformat()
    })
    
    # Update lesson progress
    if data.get('lesson_id'):
        progress_model.create({
            'enrollment_id': enrollment_id,
            'lesson_id': data.get('lesson_id'),
            'status': data.get('status', 'in_progress'),
            'progress_percentage': data.get('lesson_progress', 0),
            'watch_time': data.get('watch_time', 0),
            'last_accessed': datetime.utcnow().isoformat()
        })
    
    return jsonify({'message': 'Progress updated'}), 200