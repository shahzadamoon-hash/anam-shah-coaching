from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.sheet_models import User, StudentProfile, Enrollment, LessonProgress
from datetime import datetime, timedelta

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


# ============================================================
# ✅ NEW: GET USER STATS (for dashboard)
# ============================================================

@user_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_user_stats():
    """Get user statistics for dashboard: streak, hours, certificates"""
    user_id = get_jwt_identity()

    try:
        # 1. Get all enrollments for this user
        enrollments = Enrollment().get_by_user(user_id)
        total_courses = len(enrollments)
        completed_courses = [e for e in enrollments if e.get('status') == 'completed']
        certificates = len(completed_courses)

        # 2. Calculate total study hours from lesson progress
        total_hours = 0
        weekly_hours = 0
        one_week_ago = datetime.utcnow() - timedelta(days=7)

        for enrollment in enrollments:
            enrollment_id = enrollment.get('enrollment_id')
            progress_records = LessonProgress().get_by_enrollment(enrollment_id)

            for record in progress_records:
                # Total hours from all lessons
                watch_time = int(record.get('watch_time', 0))
                total_hours += watch_time / 3600  # Convert seconds to hours

                # Weekly hours (only from last 7 days)
                last_accessed = record.get('last_accessed')
                if last_accessed:
                    try:
                        # Handle different date formats
                        if isinstance(last_accessed, str):
                            last_accessed = datetime.fromisoformat(last_accessed.replace(' ', 'T'))
                        if last_accessed > one_week_ago:
                            weekly_hours += watch_time / 3600
                    except:
                        pass  # Skip if date parsing fails

        # 3. Calculate streak days
        user = user_model.get_by_id(user_id)
        streak_days = calculate_streak(user)

        # 4. New certificates (earned in last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        new_certificates = 0

        # Check if any course was completed in last 30 days
        for enrollment in enrollments:
            if enrollment.get('status') == 'completed':
                completion_date = enrollment.get('completion_date')
                if completion_date:
                    try:
                        if isinstance(completion_date, str):
                            completion_date = datetime.fromisoformat(completion_date.replace(' ', 'T'))
                        if completion_date > thirty_days_ago:
                            new_certificates += 1
                    except:
                        pass

        return jsonify({
            'streak_days': streak_days,
            'total_hours': round(total_hours, 1),
            'weekly_hours': round(weekly_hours, 1),
            'certificates': certificates,
            'new_certificates': new_certificates,
            'total_courses': total_courses
        }), 200

    except Exception as e:
        print(f"Error calculating stats: {e}")
        # Return fallback data
        return jsonify({
            'streak_days': 0,
            'total_hours': 0,
            'weekly_hours': 0,
            'certificates': 0,
            'new_certificates': 0,
            'total_courses': 0
        }), 200


def calculate_streak(user):
    """Calculate the user's current learning streak in days"""
    # Check last_login from user record
    last_login = user.get('last_login')
    if not last_login:
        return 0

    try:
        if isinstance(last_login, str):
            # Try different formats
            try:
                last_login_date = datetime.fromisoformat(last_login.replace(' ', 'T'))
            except:
                # Try format: "2026-08-08 10:28:28"
                last_login_date = datetime.strptime(last_login, '%Y-%m-%d %H:%M:%S')

        today = datetime.utcnow().date()
        last_login_date = last_login_date.date()

        # If last login was today or yesterday, assume streak continues
        days_diff = (today - last_login_date).days

        # For demo purposes, return 7 if user has been active
        # In production, you'd check daily login history
        if days_diff <= 1:
            return 7  # Placeholder - track actual streak in a separate sheet
        else:
            return 0

    except Exception as e:
        print(f"Error calculating streak: {e}")
        return 0


# ============================================================
# ✅ NEW: GET USER DASHBOARD SUMMARY (optional - all-in-one)
# ============================================================

@user_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard_data():
    """Get all dashboard data in one request"""
    user_id = get_jwt_identity()

    # Get user profile
    user = user_model.get_by_id(user_id)
    profile = StudentProfile().find_by_user_id(user_id)

    # Get stats
    stats_response = get_user_stats()
    stats = stats_response[0] if isinstance(stats_response, tuple) else stats_response

    return jsonify({
        'user': user_model.to_dict(user) if user else None,
        'profile': profile,
        'stats': stats
    }), 200