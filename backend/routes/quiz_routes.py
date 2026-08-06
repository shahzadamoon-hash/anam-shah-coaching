# routes/quiz_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.sheet_models import QuizQuestion, QuizAttempt, Enrollment
from utils.auth import instructor_required
from datetime import datetime

quiz_bp = Blueprint('quiz', __name__)
question_model = QuizQuestion()
attempt_model = QuizAttempt()
enrollment_model = Enrollment()

@quiz_bp.route('/lesson/<int:lesson_id>', methods=['GET'])
@jwt_required()
def get_quiz_questions(lesson_id):
    questions = question_model.query(lesson_id=str(lesson_id))
    return jsonify({'questions': questions}), 200

@quiz_bp.route('/lesson/<int:lesson_id>/start', methods=['POST'])
@jwt_required()
def start_quiz(lesson_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Verify enrollment
    enrollment = enrollment_model.get_by_user_and_course(user_id, data.get('course_id'))
    if not enrollment:
        return jsonify({'error': 'Not enrolled'}), 403
    
    # Get questions
    questions = question_model.query(lesson_id=str(lesson_id))
    
    # Create attempt
    attempt = attempt_model.create({
        'enrollment_id': enrollment.get('enrollment_id'),
        'lesson_id': lesson_id,
        'total_questions': len(questions),
        'attempt_date': datetime.utcnow().isoformat()
    })
    
    return jsonify({
        'attempt_id': attempt.get('attempt_id'),
        'questions': questions,
        'total_questions': len(questions)
    }), 200

@quiz_bp.route('/submit', methods=['POST'])
@jwt_required()
def submit_quiz():
    data = request.get_json()
    
    # Calculate score
    correct = 0
    wrong = 0
    unanswered = 0
    
    for answer in data.get('answers', []):
        question = question_model.get_by_id(answer.get('question_id'))
        if not question:
            continue
        if answer.get('selected') == question.get('correct_answer'):
            correct += 1
        elif answer.get('selected'):
            wrong += 1
        else:
            unanswered += 1
    
    total = correct + wrong + unanswered
    score = (correct / total * 100) if total > 0 else 0
    is_passed = score >= 60
    
    attempt_model.update(data.get('attempt_id'), {
        'correct_answers': correct,
        'wrong_answers': wrong,
        'unanswered': unanswered,
        'score': score,
        'is_passed': str(is_passed).lower()
    })
    
    return jsonify({
        'score': score,
        'correct': correct,
        'wrong': wrong,
        'unanswered': unanswered,
        'is_passed': is_passed
    }), 200

@quiz_bp.route('/attempts', methods=['GET'])
@jwt_required()
def get_attempts():
    user_id = get_jwt_identity()
    enrollments = enrollment_model.get_by_user(user_id)
    
    all_attempts = []
    for enrollment in enrollments:
        attempts = attempt_model.query(enrollment_id=str(enrollment.get('enrollment_id')))
        all_attempts.extend(attempts)
    
    return jsonify({'attempts': all_attempts}), 200

@quiz_bp.route('/questions', methods=['POST'])
@jwt_required()
@instructor_required
def create_question():
    data = request.get_json()
    question = question_model.create(data)
    return jsonify({'question': question}), 201

@quiz_bp.route('/questions/<int:question_id>', methods=['PUT'])
@jwt_required()
@instructor_required
def update_question(question_id):
    data = request.get_json()
    question = question_model.update(question_id, data)
    return jsonify({'question': question}), 200

@quiz_bp.route('/questions/<int:question_id>', methods=['DELETE'])
@jwt_required()
@instructor_required
def delete_question(question_id):
    question_model.delete(question_id)
    return jsonify({'message': 'Question deleted'}), 200
