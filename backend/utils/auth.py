from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from services.sheet_models import User

def get_user_id_from_jwt():
    """
    Get the user ID as an integer from the JWT identity.
    Returns None if the identity is invalid.
    """
    identity = get_jwt_identity()
    if identity is None:
        return None
    try:
        return int(str(identity))
    except (ValueError, TypeError):
        return None

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()

        # ✅ FIX: Convert identity to integer
        user_id = get_user_id_from_jwt()
        if user_id is None:
            return jsonify({'error': 'Invalid user identity'}), 401

        user = User().get_by_id(user_id)
        if not user or user.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return fn(*args, **kwargs)
    return wrapper

def instructor_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()

        # ✅ FIX: Convert identity to integer
        user_id = get_user_id_from_jwt()
        if user_id is None:
            return jsonify({'error': 'Invalid user identity'}), 401

        user = User().get_by_id(user_id)
        if not user or user.get('role') not in ['instructor', 'admin']:
            return jsonify({'error': 'Instructor access required'}), 403
        return fn(*args, **kwargs)
    return wrapper

# Optional: A helper for routes to get user ID safely
def get_current_user_id():
    """
    Get the current user ID as an integer.
    Raises ValueError if invalid.
    """
    user_id = get_user_id_from_jwt()
    if user_id is None:
        raise ValueError("Invalid user identity")
    return user_id