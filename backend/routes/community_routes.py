from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.sheet_models import CommunityPost, CommunityComment, Like, User
from datetime import datetime
import json

community_bp = Blueprint('community', __name__)
post_model = CommunityPost()
comment_model = CommunityComment()
like_model = Like()
user_model = User()

@community_bp.route('/posts', methods=['GET'])
def get_posts():
    posts = post_model.query(status='published')
    return jsonify({'posts': posts}), 200

@community_bp.route('/posts/feed', methods=['GET'])
@jwt_required()
def get_feed():
    posts = post_model.get_all()
    return jsonify({'posts': posts}), 200

@community_bp.route('/posts', methods=['POST'])
@jwt_required()
def create_post():
    data = request.get_json()
    user_id = get_jwt_identity()
    
    post = post_model.create({
        'user_id': user_id,
        'title': data.get('title'),
        'content': data.get('content'),
        'tags': json.dumps(data.get('tags', [])),
        'course_id': data.get('course_id'),
        'status': 'published',
        'created_at': datetime.utcnow().isoformat()
    })
    
    return jsonify({'post': post}), 201

@community_bp.route('/posts/<int:post_id>/like', methods=['POST'])
@jwt_required()
def like_post(post_id):
    user_id = get_jwt_identity()
    
    # Check if already liked
    existing = like_model.query(user_id=str(user_id), post_id=str(post_id))
    if existing:
        like_model.delete(existing[0].get('like_id'))
        post = post_model.get_by_id(post_id)
        post_model.update(post_id, {'like_count': max(0, int(post.get('like_count', 0)) - 1)})
        return jsonify({'message': 'Unliked'}), 200
    
    like_model.create({
        'user_id': user_id,
        'post_id': post_id,
        'created_at': datetime.utcnow().isoformat()
    })
    
    post = post_model.get_by_id(post_id)
    post_model.update(post_id, {'like_count': int(post.get('like_count', 0)) + 1})
    
    return jsonify({'message': 'Liked'}), 200

@community_bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    users = user_model.get_all()
    enrollments = []
    
    # Get enrollments for each user (simplified)
    from services.sheet_models import Enrollment
    enrollment_model = Enrollment()
    
    leaders = []
    for user in users[:20]:
        user_id = user.get('user_id')
        user_enrollments = enrollment_model.get_by_user(user_id)
        
        # Calculate XP
        total_courses = len(user_enrollments)
        completed = len([e for e in user_enrollments if e.get('status') in ['completed', 'finished']])
        total_xp = (total_courses * 10) + (completed * 15)
        streak_days = 3 if total_courses > 0 else 0
        
        leaders.append({
            'user_id': user_id,
            'username': user.get('username'),
            'full_name': user.get('full_name'),
            'total_xp': total_xp,
            'course_count': total_courses,
            'streak_days': streak_days
        })
    
    # Sort by XP descending
    leaders.sort(key=lambda x: x['total_xp'], reverse=True)
    
    return jsonify({'leaders': leaders[:10]}), 200

@community_bp.route('/posts/<int:post_id>/comments', methods=['POST'])
@jwt_required()
def add_comment(post_id):
    data = request.get_json()
    user_id = get_jwt_identity()
    
    comment = comment_model.create({
        'post_id': post_id,
        'user_id': user_id,
        'content': data.get('content'),
        'created_at': datetime.utcnow().isoformat()
    })
    
    post = post_model.get_by_id(post_id)
    post_model.update(post_id, {'comment_count': int(post.get('comment_count', 0)) + 1})
    
    return jsonify({'comment': comment}), 201