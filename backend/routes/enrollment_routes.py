from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.sheet_models import Enrollment, Course, Notification, LessonProgress
from datetime import datetime

enrollment_bp = Blueprint('enrollment', __name__)
enrollment_model = Enrollment()
course_model = Course()
notification_model = Notification()

@enrollment_bp.route('', methods=['GET'])
@jwt_required()
def get_enrollments():
    user_id = get_jwt_identity()
    
    try:
        # Get all enrollments for this user
        enrollments = enrollment_model.get_by_user(user_id)
        
        # Add course details and progress
        for enrollment in enrollments:
            course = course_model.get_by_id(enrollment.get('course_id'))
            if course:
                enrollment['course_title'] = course.get('title')
                enrollment['course_thumbnail'] = course.get('thumbnail')
                enrollment['course_level'] = course.get('level')
                enrollment['total_lectures'] = int(course.get('total_lectures', 0))
                enrollment['total_duration'] = int(course.get('total_duration', 0))
            
            # Calculate actual progress from lesson_progress
            enrollment_id = enrollment.get('enrollment_id')
            progress_records = LessonProgress().get_by_enrollment(enrollment_id)
            
            if progress_records:
                completed = [p for p in progress_records if p.get('is_completed') == 'true']
                total = len(progress_records)
                enrollment['progress_percentage'] = int((len(completed) / total) * 100) if total > 0 else 0
                enrollment['completed_lessons'] = len(completed)
                enrollment['total_lessons'] = total
            else:
                enrollment['progress_percentage'] = int(enrollment.get('progress_percentage', 0))
                enrollment['completed_lessons'] = 0
                enrollment['total_lessons'] = 0
        
        return jsonify({
            'enrollments': enrollments,
            'count': len(enrollments)
        }), 200
        
    except Exception as e:
        print(f"Error fetching enrollments: {e}")
        return jsonify({'error': 'Failed to fetch enrollments', 'enrollments': []}), 500


@enrollment_bp.route('/course/<int:course_id>', methods=['POST'])
@jwt_required()
def enroll(course_id):
    user_id = get_jwt_identity()
    
    try:
        # Check if course exists
        course = course_model.get_by_id(course_id)
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        
        # Check if already enrolled
        existing = enrollment_model.get_by_user_and_course(user_id, course_id)
        if existing:
            return jsonify({'error': 'Already enrolled', 'enrollment': existing}), 400
        
        # Create enrollment with date
        now = datetime.utcnow().isoformat()
        enrollment = enrollment_model.create({
            'user_id': user_id,
            'course_id': course_id,
            'enrollment_date': now,
            'status': 'enrolled',
            'progress_percentage': 0,
            'last_accessed': now
        })
        
        # Create notification
        course_title = course.get('title', 'Course')
        notification_model.create({
            'user_id': user_id,
            'type': 'enrollment',
            'title': '🎉 Course Enrolled!',
            'message': f'You have successfully enrolled in "{course_title}". Start learning now!',
            'link': f'/course-content.html?course={course_id}',
            'is_read': 'false',
            'created_at': now
        })
        
        return jsonify({
            'message': 'Successfully enrolled',
            'enrollment': enrollment
        }), 201
        
    except Exception as e:
        print(f"Error enrolling: {e}")
        return jsonify({'error': 'Failed to enroll'}), 500


@enrollment_bp.route('/<int:enrollment_id>', methods=['GET'])
@jwt_required()
def get_enrollment(enrollment_id):
    user_id = get_jwt_identity()
    
    try:
        enrollment = enrollment_model.get_by_id(enrollment_id)
        if not enrollment:
            return jsonify({'error': 'Enrollment not found'}), 404
        
        # Check if enrollment belongs to this user
        if str(enrollment.get('user_id')) != str(user_id):
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Add course details
        course = course_model.get_by_id(enrollment.get('course_id'))
        if course:
            enrollment['course_title'] = course.get('title')
            enrollment['course_description'] = course.get('description')
            enrollment['course_thumbnail'] = course.get('thumbnail')
        
        # Get lesson progress
        progress_records = LessonProgress().get_by_enrollment(enrollment_id)
        enrollment['lesson_progress'] = progress_records
        
        return jsonify({'enrollment': enrollment}), 200
        
    except Exception as e:
        print(f"Error fetching enrollment: {e}")
        return jsonify({'error': 'Failed to fetch enrollment'}), 500


@enrollment_bp.route('/<int:enrollment_id>/progress', methods=['PUT'])
@jwt_required()
def update_progress(enrollment_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    
    try:
        # Check if enrollment belongs to this user
        enrollment = enrollment_model.get_by_id(enrollment_id)
        if not enrollment:
            return jsonify({'error': 'Enrollment not found'}), 404
        
        if str(enrollment.get('user_id')) != str(user_id):
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Update progress
        progress_percentage = data.get('progress_percentage')
        lesson_id = data.get('lesson_id')
        
        # Update lesson progress
        if lesson_id:
            lesson_progress = LessonProgress().get_by_enrollment_and_lesson(enrollment_id, lesson_id)
            if lesson_progress:
                LessonProgress().update(lesson_progress.get('progress_id'), {
                    'status': data.get('status', 'in_progress'),
                    'progress_percentage': data.get('lesson_progress', 0),
                    'watch_time': data.get('watch_time', 0),
                    'is_completed': data.get('is_completed', 'false'),
                    'last_accessed': datetime.utcnow().isoformat()
                })
            else:
                LessonProgress().create({
                    'enrollment_id': enrollment_id,
                    'lesson_id': lesson_id,
                    'status': data.get('status', 'in_progress'),
                    'progress_percentage': data.get('lesson_progress', 0),
                    'watch_time': data.get('watch_time', 0),
                    'is_completed': data.get('is_completed', 'false'),
                    'last_accessed': datetime.utcnow().isoformat()
                })
        
        # Update enrollment progress
        if progress_percentage is not None:
            enrollment_model.update(enrollment_id, {
                'progress_percentage': progress_percentage,
                'last_accessed': datetime.utcnow().isoformat()
            })
        
        # Check if course is complete (100%)
        if progress_percentage and progress_percentage >= 100:
            enrollment_model.update(enrollment_id, {
                'status': 'completed',
                'completion_date': datetime.utcnow().isoformat()
            })
        
        return jsonify({'message': 'Progress updated successfully'}), 200
        
    except Exception as e:
        print(f"Error updating progress: {e}")
        return jsonify({'error': 'Failed to update progress'}), 500