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