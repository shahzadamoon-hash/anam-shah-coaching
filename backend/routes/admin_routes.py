# routes/admin_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.sheet_models import User, Course, Enrollment
from utils.auth import admin_required

admin_bp = Blueprint('admin', __name__)
user_model = User()
course_model = Course()
enrollment_model = Enrollment()

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required
def get_all_users():
    users = user_model.get_all()
    return jsonify({'users': users}), 200

@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
@admin_required
def get_user(user_id):
    user = user_model.get_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'user': user}), 200

@admin_bp.route('/users/<int:user_id>/status', methods=['PUT'])
@jwt_required()
@admin_required
def update_user_status(user_id):
    data = request.get_json()
    user_model.update(user_id, {'status': data.get('status')})
    return jsonify({'message': 'Status updated'}), 200

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_user(user_id):
    user_model.delete(user_id)
    return jsonify({'message': 'User deleted'}), 200

@admin_bp.route('/courses', methods=['GET'])
@jwt_required()
@admin_required
def get_all_courses():
    courses = course_model.get_all()
    return jsonify({'courses': courses}), 200

@admin_bp.route('/courses/<int:course_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_course(course_id):
    data = request.get_json()
    course_model.update(course_id, data)
    return jsonify({'message': 'Course updated'}), 200

@admin_bp.route('/courses/<int:course_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_course(course_id):
    course_model.delete(course_id)
    return jsonify({'message': 'Course deleted'}), 200

@admin_bp.route('/analytics', methods=['GET'])
@jwt_required()
@admin_required
def get_analytics():
    users = user_model.get_all()
    courses = course_model.get_all()
    enrollments = enrollment_model.get_all()
    
    return jsonify({
        'total_users': len(users),
        'total_courses': len(courses),
        'total_enrollments': len(enrollments),
        'active_users': len([u for u in users if u.get('status') == 'active'])
    }), 200
