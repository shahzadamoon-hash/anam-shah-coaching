from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.sheet_models import User, StudentProfile

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
    
    # Update user
    user_model.update(user_id, {
        'full_name': data.get('full_name'),
        'phone': data.get('phone'),
        'bio': data.get('bio')
    })
    
    # Update student profile
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