from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.sheet_models import Course, Enrollment

course_bp = Blueprint('course', __name__)
course_model = Course()
enrollment_model = Enrollment()

@course_bp.route('/', methods=['GET'])
@jwt_required(optional=True)
def get_courses():
    # Get all published courses
    courses = course_model.get_published()

    # If user is authenticated, add enrollment status
    user_id = get_jwt_identity()
    if user_id:
        enrollments = enrollment_model.get_by_user(user_id)
        enrolled_ids = [str(e.get('course_id')) for e in enrollments]

        for course in courses:
            course['is_enrolled'] = str(course.get('course_id')) in enrolled_ids

    return jsonify({'courses': courses}), 200

@course_bp.route('/featured', methods=['GET'])
def get_featured():
    courses = course_model.get_featured()
    return jsonify({'courses': courses}), 200

@course_bp.route('/<int:course_id>', methods=['GET'])
def get_course(course_id):
    course = course_model.get_by_id(course_id)
    if not course:
        return jsonify({'error': 'Course not found'}), 404
    return jsonify({'course': course}), 200

@course_bp.route('/search', methods=['GET'])
def search_courses():
    query = request.args.get('q', '').lower()

    if not query:
        return jsonify({'courses': []}), 200

    all_courses = course_model.get_all()

    # Search in title, description, and category
    results = []
    for course in all_courses:
        title = str(course.get('title', '')).lower()
        description = str(course.get('description', '')).lower()
        short_desc = str(course.get('short_description', '')).lower()

        if query in title or query in description or query in short_desc:
            results.append(course)

    return jsonify({'courses': results[:10]}), 200