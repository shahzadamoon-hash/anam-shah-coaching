# routes/community_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.sheet_models import CommunityPost, CommunityComment, Like
from datetime import datetime
import json

community_bp = Blueprint('community', __name__)
post_model = CommunityPost()
comment_model = CommunityComment()
like_model = Like()

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
        'course_id': data.get('course_id')
    })
    
    return jsonify({'post': post}), 201

@community_bp.route('/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    post = post_model.get_by_id(post_id)
    if not post:
        return jsonify({'error': 'Post not found'}), 404
    
    # Increment view count
    post_model.update(post_id, {'view_count': int(post.get('view_count', 0)) + 1})
    
    return jsonify({'post': post}), 200

@community_bp.route('/posts/<int:post_id>', methods=['PUT'])
@jwt_required()
def update_post(post_id):
    data = request.get_json()
    user_id = get_jwt_identity()
    
    post = post_model.get_by_id(post_id)
    if not post or int(post.get('user_id')) != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    post_model.update(post_id, {
        'title': data.get('title'),
        'content': data.get('content'),
        'tags': json.dumps(data.get('tags', [])),
        'updated_at': datetime.utcnow().isoformat()
    })
    
    return jsonify({'message': 'Post updated'}), 200

@community_bp.route('/posts/<int:post_id>', methods=['DELETE'])
@jwt_required()
def delete_post(post_id):
    user_id = get_jwt_identity()
    
    post = post_model.get_by_id(post_id)
    if not post or int(post.get('user_id')) != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    post_model.delete(post_id)
    return jsonify({'message': 'Post deleted'}), 200

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
        'post_id': post_id
    })
    
    post = post_model.get_by_id(post_id)
    post_model.update(post_id, {'like_count': int(post.get('like_count', 0)) + 1})
    
    return jsonify({'message': 'Liked'}), 200

@community_bp.route('/posts/<int:post_id>/comments', methods=['GET'])
def get_comments(post_id):
    comments = comment_model.query(post_id=str(post_id))
    return jsonify({'comments': comments}), 200

@community_bp.route('/posts/<int:post_id>/comments', methods=['POST'])
@jwt_required()
def add_comment(post_id):
    data = request.get_json()
    user_id = get_jwt_identity()
    
    comment = comment_model.create({
        'post_id': post_id,
        'user_id': user_id,
        'content': data.get('content')
    })
    
    post = post_model.get_by_id(post_id)
    post_model.update(post_id, {'comment_count': int(post.get('comment_count', 0)) + 1})
    
    return jsonify({'comment': comment}), 201

@community_bp.route('/comments/<int:comment_id>', methods=['DELETE'])
@jwt_required()
def delete_comment(comment_id):
    user_id = get_jwt_identity()
    
    comment = comment_model.get_by_id(comment_id)
    if not comment or int(comment.get('user_id')) != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    comment_model.delete(comment_id)
    return jsonify({'message': 'Comment deleted'}), 200

@community_bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    # Get all users
    user_model = User()
    users = user_model.get_all()

    # Get enrollments for each user
    enrollment_model = Enrollment()

    leaders = []
    for user in users[:20]:  # Limit to 20 users
        user_id = user.get('user_id')
        enrollments = enrollment_model.get_by_user(user_id)

        # Calculate XP (simplified: 10 XP per course + 5 XP per completed course)
        total_courses = len(enrollments)
        completed = len([e for e in enrollments if e.get('status') in ['completed', 'finished']])
        total_xp = (total_courses * 10) + (completed * 5)

        # Get streak (simulate)
        streak_days = 3 if total_courses > 0 else 0

        leaders.append({
            'user_id': user_id,
            'username': user.get('username'),
            'full_name': user.get('full_name'),
            'total_xp': total_xp,
            'course_count': total_courses,
            'streak_days': streak_days,
            'is_you': False  # Will be set client-side
        })

    # Sort by XP descending
    leaders.sort(key=lambda x: x['total_xp'], reverse=True)

    return jsonify({'leaders': leaders[:10]}), 200