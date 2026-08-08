# routes/course_routes.py
from flask import Blueprint, jsonify
from services.sheet_models import Course

course_bp = Blueprint('course', __name__)
course_model = Course()

@course_bp.route('/', methods=['GET'])
def get_courses():
    courses = course_model.get_published()
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
        title = course.get('title', '').lower()
        description = course.get('description', '').lower()
        category = course.get('category_name', '').lower()

        if query in title or query in description or query in category:
            results.append(course)

    return jsonify({'courses': results}), 200