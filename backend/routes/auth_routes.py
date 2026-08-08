# routes/auth_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_bcrypt import Bcrypt
from datetime import datetime
from services.sheet_models import User, StudentProfile

auth_bp = Blueprint('auth', __name__)
user_model = User()

# ✅ Initialize bcrypt (or import from app)
bcrypt = Bcrypt()

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    # Validate
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400

    if not data.get('username') or not data.get('full_name'):
        return jsonify({'error': 'Username and full name required'}), 400

    # Check if user exists
    if user_model.find_by_email(data['email']):
        return jsonify({'error': 'Email already registered'}), 400

    if user_model.find_by_username(data['username']):
        return jsonify({'error': 'Username already taken'}), 400

    # ✅ Hash password using Flask-Bcrypt
    password_hash = bcrypt.generate_password_hash(data['password']).decode('utf-8')

    # Create user
    user = user_model.create({
        'username': data['username'],
        'email': data['email'],
        'password_hash': password_hash,
        'full_name': data['full_name'],
        'phone': data.get('phone', ''),
        'role': data.get('role', 'student'),
        'status': 'active'
    })

    # Create student profile if role is student
    if data.get('role', 'student') == 'student':
        StudentProfile().create({
            'user_id': user.get('user_id'),
            'country': 'India',
            'preferred_language': 'English'
        })

    return jsonify({
        'message': 'User registered successfully',
        'user': user_model.to_dict(user)
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400

    user = user_model.find_by_email(data['email'])
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401

    # ✅ Verify password using Flask-Bcrypt
    if not bcrypt.check_password_hash(user.get('password_hash', ''), data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    if user.get('status') == 'inactive':
        return jsonify({'error': 'Account is inactive'}), 401
    
    if user.get('status') == 'suspended':
        return jsonify({'error': 'Account is suspended'}), 401
    
    # Update last login
    user_model.update(user['user_id'], {
        'last_login': datetime.utcnow().isoformat()
    })
    
    access_token = create_access_token(identity=user['user_id'])
    
    return jsonify({
        'message': 'Login successful',
        'access_token': access_token,
        'user': user_model.to_dict(user, include_sensitive=True)
    }), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = user_model.get_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'user': user_model.to_dict(user, include_sensitive=True)
    }), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    return jsonify({'message': 'Logged out successfully'}), 200