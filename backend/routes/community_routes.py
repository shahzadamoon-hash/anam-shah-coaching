from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.sheet_models import CommunityPost, CommunityComment, Like, User, Enrollment, Course, LessonProgress, QuizAttempt
from datetime import datetime, timedelta
import json

community_bp = Blueprint('community', __name__)
post_model = CommunityPost()
comment_model = CommunityComment()
like_model = Like()
user_model = User()
enrollment_model = Enrollment()
course_model = Course()
lesson_progress_model = LessonProgress()
quiz_attempt_model = QuizAttempt()


# ============================================================
# 📊 LEADERBOARD ENDPOINT (for dashboard)
# ============================================================

@community_bp.route('/leaderboard', methods=['GET'])
@jwt_required()
def get_leaderboard():
    """Get top learners with XP scores for the dashboard"""
    current_user_id = get_jwt_identity()
    
    try:
        # Get all users
        all_users = user_model.get_all()
        
        # Calculate XP for each user
        leaderboard = []
        
        for user in all_users:
            user_id = user.get('user_id')
            
            # Skip inactive users
            if user.get('status') != 'active':
                continue
            
            # Calculate XP from various sources
            total_xp = 0
            course_count = 0
            streak_days = 0
            
            # 1. XP from enrolled courses
            enrollments = enrollment_model.get_by_user(user_id)
            course_count = len(enrollments)
            
            for enrollment in enrollments:
                # XP for progress (10 XP per 10% progress)
                progress = int(enrollment.get('progress_percentage', 0))
                total_xp += (progress // 10) * 10
                
                # XP for completed courses (bonus 50 XP)
                if enrollment.get('status') == 'completed':
                    total_xp += 50
                    total_xp += 100  # Extra bonus for completion
            
            # 2. XP from lesson progress
            for enrollment in enrollments:
                progress_records = lesson_progress_model.get_by_enrollment(
                    enrollment.get('enrollment_id')
                )
                for record in progress_records:
                    if record.get('is_completed') == 'true':
                        total_xp += 5  # 5 XP per completed lesson
            
            # 3. XP from quiz attempts
            for enrollment in enrollments:
                quiz_attempts = quiz_attempt_model.get_by_enrollment(
                    enrollment.get('enrollment_id')
                )
                for attempt in quiz_attempts:
                    score = float(attempt.get('score', 0))
                    total_xp += int(score // 10)  # 1 XP per 10% score
            
            # 4. XP from community participation
            posts = post_model.query(user_id=str(user_id))
            total_xp += len(posts) * 10  # 10 XP per post
            
            comments = comment_model.query(user_id=str(user_id))
            total_xp += len(comments) * 3  # 3 XP per comment
            
            likes_received = 0
            for post in posts:
                likes_received += int(post.get('like_count', 0))
            total_xp += likes_received * 1  # 1 XP per like received
            
            # 5. Calculate streak (from last_login)
            last_login = user.get('last_login')
            if last_login:
                try:
                    if isinstance(last_login, str):
                        last_login_date = datetime.fromisoformat(last_login.replace(' ', 'T'))
                    else:
                        last_login_date = last_login
                    
                    today = datetime.utcnow().date()
                    last_login_date = last_login_date.date()
                    days_diff = (today - last_login_date).days
                    
                    # Simplified streak: if active in last 7 days
                    if days_diff <= 1:
                        streak_days = 7  # Placeholder - use actual streak tracking
                    elif days_diff <= 3:
                        streak_days = 3
                    else:
                        streak_days = 0
                except:
                    streak_days = 0
            
            # Determine if this is the current user
            is_you = (str(user_id) == str(current_user_id))
            
            # Get user's full name or username
            full_name = user.get('full_name') or user.get('username', 'User')
            
            leaderboard.append({
                'user_id': int(user_id),
                'username': user.get('username', ''),
                'full_name': full_name,
                'total_xp': total_xp,
                'course_count': course_count,
                'streak_days': streak_days,
                'is_you': is_you,
                'profile_pic': user.get('profile_pic', '')
            })
        
        # Sort by XP descending (highest first)
        leaderboard.sort(key=lambda x: x['total_xp'], reverse=True)
        
        # Add rank to each entry (for top 3 display with emojis)
        for idx, entry in enumerate(leaderboard):
            entry['rank'] = idx + 1
        
        return jsonify({
            'leaders': leaderboard[:10],  # Top 10
            'total_users': len(leaderboard),
            'current_user_rank': next(
                (i + 1 for i, u in enumerate(leaderboard) if u.get('is_you')),
                None
            )
        }), 200
        
    except Exception as e:
        print(f"Error generating leaderboard: {e}")
        # Return fallback data with at least the current user
        return jsonify({
            'leaders': [
                {
                    'user_id': int(current_user_id),
                    'username': 'you',
                    'full_name': 'You',
                    'total_xp': 0,
                    'course_count': 0,
                    'streak_days': 0,
                    'is_you': True,
                    'rank': 1
                }
            ],
            'total_users': 1,
            'current_user_rank': 1
        }), 200


# ============================================================
# 📝 COMMUNITY POSTS ENDPOINTS
# ============================================================

@community_bp.route('/posts', methods=['GET'])
@jwt_required()
def get_posts():
    """Get all community posts with user details"""
    user_id = get_jwt_identity()
    
    # Get query parameters
    course_id = request.args.get('course_id')
    limit = int(request.args.get('limit', 20))
    
    try:
        # Get posts
        if course_id:
            posts = post_model.query(course_id=str(course_id))
        else:
            posts = post_model.get_all()
        
        # Sort by created_at (newest first)
        posts.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Add user details to each post
        for post in posts[:limit]:
            poster = user_model.get_by_id(post.get('user_id'))
            if poster:
                post['poster_name'] = poster.get('full_name') or poster.get('username', 'Unknown')
                post['poster_avatar'] = poster.get('profile_pic', '')
            else:
                post['poster_name'] = 'Unknown'
                post['poster_avatar'] = ''
            
            # Check if current user liked this post
            existing_like = like_model.query(
                user_id=str(user_id),
                post_id=str(post.get('post_id'))
            )
            post['user_liked'] = len(existing_like) > 0
        
        return jsonify({
            'posts': posts[:limit],
            'count': len(posts)
        }), 200
        
    except Exception as e:
        print(f"Error fetching posts: {e}")
        return jsonify({'posts': [], 'error': 'Failed to fetch posts'}), 200


@community_bp.route('/posts', methods=['POST'])
@jwt_required()
def create_post():
    """Create a new community post"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    try:
        # Prepare tags
        tags = data.get('tags', [])
        if isinstance(tags, list):
            tags = json.dumps(tags)
        
        post = post_model.create({
            'user_id': user_id,
            'course_id': data.get('course_id'),
            'title': data.get('title'),
            'content': data.get('content'),
            'tags': tags,
            'status': 'published',
            'is_announcement': 'false',
            'view_count': 0,
            'like_count': 0,
            'comment_count': 0,
            'created_at': datetime.utcnow().isoformat()
        })
        
        return jsonify({
            'message': 'Post created successfully',
            'post': post
        }), 201
        
    except Exception as e:
        print(f"Error creating post: {e}")
        return jsonify({'error': 'Failed to create post'}), 500


@community_bp.route('/posts/<int:post_id>', methods=['GET'])
@jwt_required()
def get_post(post_id):
    """Get a single post with comments"""
    user_id = get_jwt_identity()
    
    try:
        post = post_model.get_by_id(post_id)
        if not post:
            return jsonify({'error': 'Post not found'}), 404
        
        # Increment view count
        post_model.update(post_id, {
            'view_count': int(post.get('view_count', 0)) + 1
        })
        
        # Get post author
        poster = user_model.get_by_id(post.get('user_id'))
        if poster:
            post['poster_name'] = poster.get('full_name') or poster.get('username', 'Unknown')
            post['poster_avatar'] = poster.get('profile_pic', '')
        
        # Get comments
        comments = comment_model.query(post_id=str(post_id))
        
        # Add user details to comments
        for comment in comments:
            commenter = user_model.get_by_id(comment.get('user_id'))
            if commenter:
                comment['commenter_name'] = commenter.get('full_name') or commenter.get('username', 'Unknown')
                comment['commenter_avatar'] = commenter.get('profile_pic', '')
            
            # Check if current user liked this comment
            existing_like = like_model.query(
                user_id=str(user_id),
                comment_id=str(comment.get('comment_id'))
            )
            comment['user_liked'] = len(existing_like) > 0
        
        # Check if current user liked the post
        existing_like = like_model.query(
            user_id=str(user_id),
            post_id=str(post_id)
        )
        post['user_liked'] = len(existing_like) > 0
        
        return jsonify({
            'post': post,
            'comments': comments,
            'comment_count': len(comments)
        }), 200
        
    except Exception as e:
        print(f"Error fetching post: {e}")
        return jsonify({'error': 'Failed to fetch post'}), 500


@community_bp.route('/posts/<int:post_id>/comment', methods=['POST'])
@jwt_required()
def add_comment(post_id):
    """Add a comment to a post"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    try:
        # Check if post exists
        post = post_model.get_by_id(post_id)
        if not post:
            return jsonify({'error': 'Post not found'}), 404
        
        # Create comment
        comment = comment_model.create({
            'post_id': post_id,
            'user_id': user_id,
            'content': data.get('content'),
            'like_count': 0,
            'is_approved': 'true',
            'created_at': datetime.utcnow().isoformat()
        })
        
        # Update post comment count
        post_model.update(post_id, {
            'comment_count': int(post.get('comment_count', 0)) + 1
        })
        
        return jsonify({
            'message': 'Comment added successfully',
            'comment': comment
        }), 201
        
    except Exception as e:
        print(f"Error adding comment: {e}")
        return jsonify({'error': 'Failed to add comment'}), 500


@community_bp.route('/like', methods=['POST'])
@jwt_required()
def toggle_like():
    """Like or unlike a post or comment"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    post_id = data.get('post_id')
    comment_id = data.get('comment_id')
    
    try:
        if post_id:
            # Check if already liked
            existing = like_model.query(
                user_id=str(user_id),
                post_id=str(post_id)
            )
            
            if existing:
                # Unlike
                like_model.delete(existing[0].get('like_id'))
                post = post_model.get_by_id(post_id)
                post_model.update(post_id, {
                    'like_count': max(0, int(post.get('like_count', 0)) - 1)
                })
                return jsonify({'message': 'Unliked', 'liked': False}), 200
            else:
                # Like
                like_model.create({
                    'user_id': user_id,
                    'post_id': post_id,
                    'created_at': datetime.utcnow().isoformat()
                })
                post = post_model.get_by_id(post_id)
                post_model.update(post_id, {
                    'like_count': int(post.get('like_count', 0)) + 1
                })
                return jsonify({'message': 'Liked', 'liked': True}), 200
        
        elif comment_id:
            # Check if already liked
            existing = like_model.query(
                user_id=str(user_id),
                comment_id=str(comment_id)
            )
            
            if existing:
                like_model.delete(existing[0].get('like_id'))
                comment = comment_model.get_by_id(comment_id)
                comment_model.update(comment_id, {
                    'like_count': max(0, int(comment.get('like_count', 0)) - 1)
                })
                return jsonify({'message': 'Unliked', 'liked': False}), 200
            else:
                like_model.create({
                    'user_id': user_id,
                    'comment_id': comment_id,
                    'created_at': datetime.utcnow().isoformat()
                })
                comment = comment_model.get_by_id(comment_id)
                comment_model.update(comment_id, {
                    'like_count': int(comment.get('like_count', 0)) + 1
                })
                return jsonify({'message': 'Liked', 'liked': True}), 200
        
        return jsonify({'error': 'Post ID or Comment ID required'}), 400
        
    except Exception as e:
        print(f"Error toggling like: {e}")
        return jsonify({'error': 'Failed to toggle like'}), 500