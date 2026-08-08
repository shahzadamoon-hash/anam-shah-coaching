from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.sheet_models import User, StudentProfile, Enrollment, Course

user_bp = Blueprint('user', __name__)
user_model = User()

@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    user = user_model.get_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    profile = StudentProfile().find_by_user_id(user_id)

    return jsonify({
        'user': user_model.to_dict(user),
        'profile': profile
    }), 200

@user_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    data = request.get_json()

    user_model.update(user_id, {
        'full_name': data.get('full_name'),
        'phone': data.get('phone'),
        'bio': data.get('bio')
    })

    profile = StudentProfile().find_by_user_id(user_id)
    if profile:
        StudentProfile().update(profile['profile_id'], {
            'date_of_birth': data.get('date_of_birth'),
            'gender': data.get('gender'),
            'address': data.get('address'),
            'city': data.get('city'),
            'state': data.get('state'),
            'country': data.get('country'),
            'education_level': data.get('education_level'),
            'institution': data.get('institution'),
            'exam_target': data.get('exam_target'),
            'preferred_language': data.get('preferred_language'),
            'learning_goal': data.get('learning_goal')
        })

    return jsonify({'message': 'Profile updated successfully'}), 200

@user_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_user_stats():
    user_id = get_jwt_identity()

    enrollment_model = Enrollment()
    course_model = Course()

    enrollments = enrollment_model.get_by_user(user_id)

    total_courses = len(enrollments)
    completed_courses = len([e for e in enrollments if e.get('status') in ['completed', 'finished']])

    # Calculate study hours from progress
    total_hours = 0
    for enrollment in enrollments:
        progress = int(enrollment.get('progress_percentage', 0))
        total_hours += int((progress / 100) * 15)

    weekly_hours = min(total_hours // 2, 15) if total_hours > 0 else 0
    streak_days = 7 if total_courses > 0 else 0
    certificates = completed_courses
    new_certificates = min(completed_courses, 2)

    return jsonify({
        'total_courses': total_courses,
        'completed_courses': completed_courses,
        'streak_days': streak_days,
        'total_hours': total_hours,
        'weekly_hours': weekly_hours,
        'certificates': certificates,
        'new_certificates': new_certificates
    }), 200