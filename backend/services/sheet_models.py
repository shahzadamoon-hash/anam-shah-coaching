# services/sheet_models.py
from .google_sheets import sheet_service
from datetime import datetime
import json

class SheetModel:
    """Base class for sheet-based models"""
    
    def __init__(self, sheet_name, id_field='id'):
        self.sheet_name = sheet_name
        self.id_field = id_field
    
    def get_all(self):
        return sheet_service.get_all_records(self.sheet_name)
    
    def get_by_id(self, id_value):
        return sheet_service.get_record_by_id(self.sheet_name, self.id_field, id_value)
    
    def create(self, data):
        if 'created_at' not in data:
            data['created_at'] = datetime.utcnow().isoformat()
        
        # ✅ Auto-generate ID if not provided or is 0/empty
        if self.id_field not in data or not data.get(self.id_field) or data.get(self.id_field) == 0:
            all_records = self.get_all()
            max_id = 0
            for record in all_records:
                try:
                    rid = int(record.get(self.id_field, 0))
                    if rid > max_id:
                        max_id = rid
                except (ValueError, TypeError):
                    pass
            data[self.id_field] = max_id + 1
        
        return sheet_service.insert_record(self.sheet_name, data)
    
    def update(self, id_value, data):
        if 'updated_at' not in data:
            data['updated_at'] = datetime.utcnow().isoformat()
        return sheet_service.update_record(self.sheet_name, self.id_field, id_value, data)
    
    def delete(self, id_value):
        return sheet_service.delete_record(self.sheet_name, self.id_field, id_value)
    
    def query(self, **kwargs):
        return sheet_service.query_by_fields(self.sheet_name, **kwargs)

# ==================== USER MODELS ====================

class User(SheetModel):
    def __init__(self):
        super().__init__('users', 'user_id')  # ✅ user_id is the ID field
    
    def find_by_email(self, email):
        results = self.query(email=email)
        return results[0] if results else None
    
    def find_by_username(self, username):
        results = self.query(username=username)
        return results[0] if results else None
    
    def to_dict(self, data, include_sensitive=False):
        if not data:
            return None
        
        user_data = {
            'user_id': int(data.get('user_id', 0)) if data.get('user_id') else 0,
            'username': data.get('username', ''),
            'full_name': data.get('full_name', ''),
            'phone': data.get('phone', ''),
            'profile_pic': data.get('profile_pic', ''),
            'bio': data.get('bio', ''),
            'role': data.get('role', 'student'),
            'status': data.get('status', 'active'),
            'created_at': data.get('created_at'),
            'last_login': data.get('last_login')
        }
        
        if include_sensitive:
            user_data['email'] = data.get('email', '')
            user_data['password_hash'] = data.get('password_hash', '')
        
        return user_data

class StudentProfile(SheetModel):
    def __init__(self):
        super().__init__('student_profiles', 'profile_id')
    
    def find_by_user_id(self, user_id):
        results = self.query(user_id=str(user_id))
        return results[0] if results else None
    
    def to_dict(self, data):
        if not data:
            return None
        return {
            'profile_id': int(data.get('profile_id', 0)),
            'user_id': int(data.get('user_id', 0)),
            'date_of_birth': data.get('date_of_birth'),
            'gender': data.get('gender'),
            'address': data.get('address'),
            'city': data.get('city'),
            'state': data.get('state'),
            'country': data.get('country', 'India'),
            'postal_code': data.get('postal_code'),
            'education_level': data.get('education_level'),
            'institution': data.get('institution'),
            'graduation_year': data.get('graduation_year'),
            'exam_target': data.get('exam_target'),
            'preferred_language': data.get('preferred_language', 'English'),
            'learning_goal': data.get('learning_goal')
        }

class InstructorProfile(SheetModel):
    def __init__(self):
        super().__init__('instructor_profiles', 'instructor_id')
    
    def find_by_user_id(self, user_id):
        results = self.query(user_id=str(user_id))
        return results[0] if results else None
    
    def to_dict(self, data):
        if not data:
            return None
        return {
            'instructor_id': int(data.get('instructor_id', 0)),
            'user_id': int(data.get('user_id', 0)),
            'qualification': data.get('qualification'),
            'experience_years': int(data.get('experience_years', 0)),
            'specialization': data.get('specialization'),
            'bio': data.get('bio'),
            'website': data.get('website'),
            'linkedin': data.get('linkedin'),
            'rating': float(data.get('rating', 0)),
            'total_students': int(data.get('total_students', 0)),
            'total_courses': int(data.get('total_courses', 0)),
            'is_verified': data.get('is_verified') == 'true'
        }

# ==================== COURSE MODELS ====================

class Category(SheetModel):
    def __init__(self):
        super().__init__('categories', 'category_id')
    
    def to_dict(self, data):
        if not data:
            return None
        return {
            'category_id': int(data.get('category_id', 0)),
            'name': data.get('name'),
            'slug': data.get('slug'),
            'icon': data.get('icon'),
            'description': data.get('description'),
            'parent_id': int(data.get('parent_id', 0)) if data.get('parent_id') else None
        }

class Course(SheetModel):
    def __init__(self):
        super().__init__('courses', 'course_id')
    
    def get_published(self):
        all_courses = self.get_all()
        return [c for c in all_courses if c.get('is_published') == 'true']
    
    def get_featured(self):
        all_courses = self.get_all()
        return [c for c in all_courses if c.get('is_featured') == 'true']
    
    def to_dict(self, data):
        if not data:
            return None
        return {
            'course_id': int(data.get('course_id', 0)),
            'instructor_id': int(data.get('instructor_id', 0)),
            'category_id': int(data.get('category_id', 0)) if data.get('category_id') else None,
            'title': data.get('title'),
            'slug': data.get('slug'),
            'description': data.get('description'),
            'short_description': data.get('short_description'),
            'level': data.get('level', 'beginner'),
            'language': data.get('language', 'English'),
            'thumbnail': data.get('thumbnail'),
            'price': float(data.get('price', 0)),
            'discount_price': float(data.get('discount_price', 0)) if data.get('discount_price') else None,
            'is_free': data.get('is_free') == 'true',
            'is_published': data.get('is_published') == 'true',
            'is_featured': data.get('is_featured') == 'true',
            'total_lectures': int(data.get('total_lectures', 0)),
            'total_duration': int(data.get('total_duration', 0)),
            'total_students': int(data.get('total_students', 0)),
            'rating': float(data.get('rating', 0)),
            'rating_count': int(data.get('rating_count', 0)),
            'created_at': data.get('created_at'),
            'requirements': data.get('requirements'),
            'learning_outcomes': data.get('learning_outcomes'),
            'target_audience': data.get('target_audience')
        }

class Section(SheetModel):
    def __init__(self):
        super().__init__('sections', 'section_id')
    
    def get_by_course(self, course_id):
        return self.query(course_id=str(course_id))
    
    def to_dict(self, data):
        if not data:
            return None
        return {
            'section_id': int(data.get('section_id', 0)),
            'course_id': int(data.get('course_id', 0)),
            'title': data.get('title'),
            'description': data.get('description'),
            'order_number': int(data.get('order_number', 0))
        }

class Lesson(SheetModel):
    def __init__(self):
        super().__init__('lessons', 'lesson_id')
    
    def get_by_section(self, section_id):
        return self.query(section_id=str(section_id))
    
    def to_dict(self, data):
        if not data:
            return None
        return {
            'lesson_id': int(data.get('lesson_id', 0)),
            'section_id': int(data.get('section_id', 0)),
            'title': data.get('title'),
            'description': data.get('description'),
            'lesson_type': data.get('lesson_type', 'video'),
            'content': data.get('content'),
            'video_url': data.get('video_url'),
            'video_duration': int(data.get('video_duration', 0)),
            'file_url': data.get('file_url'),
            'file_type': data.get('file_type'),
            'order_number': int(data.get('order_number', 0)),
            'is_preview': data.get('is_preview') == 'true',
            'is_free': data.get('is_free') == 'true',
            'created_at': data.get('created_at')
        }

# ==================== CONTENT MODELS ====================

class Flashcard(SheetModel):
    def __init__(self):
        super().__init__('flashcards', 'flashcard_id')
    
    def get_by_lesson(self, lesson_id):
        return self.query(lesson_id=str(lesson_id))
    
    def to_dict(self, data):
        if not data:
            return None
        return {
            'flashcard_id': int(data.get('flashcard_id', 0)),
            'lesson_id': int(data.get('lesson_id', 0)),
            'term': data.get('term'),
            'definition': data.get('definition'),
            'example': data.get('example'),
            'category': data.get('category'),
            'difficulty': data.get('difficulty', 'medium'),
            'order_number': int(data.get('order_number', 0))
        }

class QuizQuestion(SheetModel):
    def __init__(self):
        super().__init__('quiz_questions', 'question_id')
    
    def get_by_lesson(self, lesson_id):
        return self.query(lesson_id=str(lesson_id))
    
    def to_dict(self, data):
        if not data:
            return None
        return {
            'question_id': int(data.get('question_id', 0)),
            'lesson_id': int(data.get('lesson_id', 0)),
            'question_type': data.get('question_type', 'mcq'),
            'question_text': data.get('question_text'),
            'options': {
                'A': data.get('option_a'),
                'B': data.get('option_b'),
                'C': data.get('option_c'),
                'D': data.get('option_d')
            } if data.get('option_a') else None,
            'correct_answer': data.get('correct_answer'),
            'explanation': data.get('explanation'),
            'marks': int(data.get('marks', 1)),
            'negative_marks': int(data.get('negative_marks', 0)),
            'order_number': int(data.get('order_number', 0))
        }

# ==================== ASSIGNMENT MODELS ====================

class Assignment(SheetModel):
    def __init__(self):
        super().__init__('assignments', 'assignment_id')
    
    def get_by_lesson(self, lesson_id):
        return self.query(lesson_id=str(lesson_id))
    
    def to_dict(self, data):
        if not data:
            return None
        return {
            'assignment_id': int(data.get('assignment_id', 0)),
            'lesson_id': int(data.get('lesson_id', 0)),
            'title': data.get('title'),
            'description': data.get('description'),
            'instructions': data.get('instructions'),
            'assignment_type': data.get('assignment_type', 'practice'),
            'total_marks': int(data.get('total_marks', 100)),
            'passing_marks': int(data.get('passing_marks', 40)),
            'time_limit': int(data.get('time_limit', 0)) if data.get('time_limit') else None,
            'due_date': data.get('due_date'),
            'is_active': data.get('is_active') == 'true'
        }

class AssignmentQuestion(SheetModel):
    def __init__(self):
        super().__init__('assignment_questions', 'question_id')
    
    def get_by_assignment(self, assignment_id):
        return self.query(assignment_id=str(assignment_id))
    
    def to_dict(self, data):
        if not data:
            return None
        return {
            'question_id': int(data.get('question_id', 0)),
            'assignment_id': int(data.get('assignment_id', 0)),
            'question_text': data.get('question_text'),
            'options': {
                'A': data.get('option_a'),
                'B': data.get('option_b'),
                'C': data.get('option_c'),
                'D': data.get('option_d')
            } if data.get('option_a') else None,
            'correct_answer': data.get('correct_answer'),
            'explanation': data.get('explanation'),
            'marks': int(data.get('marks', 1)),
            'order_number': int(data.get('order_number', 0))
        }

class AssignmentSubmission(SheetModel):
    def __init__(self):
        super().__init__('assignment_submissions', 'submission_id')
    
    def get_by_enrollment(self, enrollment_id):
        return self.query(enrollment_id=str(enrollment_id))
    
    def to_dict(self, data):
        if not data:
            return None
        return {
            'submission_id': int(data.get('submission_id', 0)),
            'enrollment_id': int(data.get('enrollment_id', 0)),
            'assignment_id': int(data.get('assignment_id', 0)),
            'answers': json.loads(data.get('answers', '{}')) if data.get('answers') else None,
            'score': float(data.get('score', 0)) if data.get('score') else None,
            'total_marks': int(data.get('total_marks', 0)),
            'obtained_marks': int(data.get('obtained_marks', 0)),
            'percentage': float(data.get('percentage', 0)) if data.get('percentage') else None,
            'is_passed': data.get('is_passed') == 'true',
            'is_graded': data.get('is_graded') == 'true',
            'graded_at': data.get('graded_at'),
            'time_taken': int(data.get('time_taken', 0)),
            'submitted_at': data.get('submitted_at')
        }

# ==================== ENROLLMENT MODELS ====================

class Enrollment(SheetModel):
    def __init__(self):
        super().__init__('enrollments', 'enrollment_id')
    
    def get_by_user(self, user_id):
        return self.query(user_id=str(user_id))
    
    def get_by_course(self, course_id):
        return self.query(course_id=str(course_id))
    
    def get_by_user_and_course(self, user_id, course_id):
        results = self.query(user_id=str(user_id), course_id=str(course_id))
        return results[0] if results else None
    
    def to_dict(self, data):
        if not data:
            return None
        return {
            'enrollment_id': int(data.get('enrollment_id', 0)),
            'user_id': int(data.get('user_id', 0)),
            'course_id': int(data.get('course_id', 0)),
            'enrollment_date': data.get('enrollment_date'),
            'status': data.get('status', 'enrolled'),
            'progress_percentage': int(data.get('progress_percentage', 0)),
            'completion_date': data.get('completion_date'),
            'last_accessed': data.get('last_accessed'),
            'certificate_issued': data.get('certificate_issued') == 'true',
            'certificate_url': data.get('certificate_url')
        }

class LessonProgress(SheetModel):
    def __init__(self):
        super().__init__('lesson_progress', 'progress_id')
    
    def get_by_enrollment(self, enrollment_id):
        return self.query(enrollment_id=str(enrollment_id))
    
    def get_by_enrollment_and_lesson(self, enrollment_id, lesson_id):
        results = self.query(enrollment_id=str(enrollment_id), lesson_id=str(lesson_id))
        return results[0] if results else None
    
    def to_dict(self, data):
        if not data:
            return None
        return {
            'progress_id': int(data.get('progress_id', 0)),
            'enrollment_id': int(data.get('enrollment_id', 0)),
            'lesson_id': int(data.get('lesson_id', 0)),
            'status': data.get('status', 'not_started'),
            'progress_percentage': int(data.get('progress_percentage', 0)),
            'watch_time': int(data.get('watch_time', 0)),
            'is_completed': data.get('is_completed') == 'true',
            'completed_at': data.get('completed_at'),
            'last_accessed': data.get('last_accessed')
        }

# ==================== QUIZ ATTEMPT MODELS ====================

class QuizAttempt(SheetModel):
    def __init__(self):
        super().__init__('quiz_attempts', 'attempt_id')
    
    def get_by_enrollment(self, enrollment_id):
        return self.query(enrollment_id=str(enrollment_id))
    
    def to_dict(self, data):
        if not data:
            return None
        total_q = int(data.get('total_questions', 0))
        correct = int(data.get('correct_answers', 0))
        return {
            'attempt_id': int(data.get('attempt_id', 0)),
            'enrollment_id': int(data.get('enrollment_id', 0)),
            'lesson_id': int(data.get('lesson_id', 0)),
            'score': float(data.get('score', 0)),
            'total_questions': total_q,
            'correct_answers': correct,
            'wrong_answers': int(data.get('wrong_answers', 0)),
            'unanswered': int(data.get('unanswered', 0)),
            'time_taken': int(data.get('time_taken', 0)),
            'is_passed': data.get('is_passed') == 'true',
            'attempt_date': data.get('attempt_date'),
            'percentage': round((correct / total_q * 100) if total_q > 0 else 0, 2)
        }

# ==================== COMMUNITY MODELS ====================

class CommunityPost(SheetModel):
    def __init__(self):
        super().__init__('community_posts', 'post_id')
    
    def to_dict(self, data):
        if not data:
            return None
        tags = data.get('tags')
        if tags:
            try:
                tags = json.loads(tags)
            except:
                tags = [tags] if tags else []
        else:
            tags = []
        return {
            'post_id': int(data.get('post_id', 0)),
            'user_id': int(data.get('user_id', 0)),
            'course_id': int(data.get('course_id', 0)) if data.get('course_id') else None,
            'title': data.get('title'),
            'content': data.get('content'),
            'tags': tags,
            'status': data.get('status', 'published'),
            'is_announcement': data.get('is_announcement') == 'true',
            'view_count': int(data.get('view_count', 0)),
            'like_count': int(data.get('like_count', 0)),
            'comment_count': int(data.get('comment_count', 0)),
            'created_at': data.get('created_at'),
            'updated_at': data.get('updated_at')
        }

class CommunityComment(SheetModel):
    def __init__(self):
        super().__init__('community_comments', 'comment_id')
    
    def to_dict(self, data):
        if not data:
            return None
        return {
            'comment_id': int(data.get('comment_id', 0)),
            'post_id': int(data.get('post_id', 0)),
            'user_id': int(data.get('user_id', 0)),
            'content': data.get('content'),
            'like_count': int(data.get('like_count', 0)),
            'is_approved': data.get('is_approved') == 'true',
            'created_at': data.get('created_at'),
            'updated_at': data.get('updated_at')
        }

class Like(SheetModel):
    def __init__(self):
        super().__init__('likes', 'like_id')
    
    def to_dict(self, data):
        if not data:
            return None
        return {
            'like_id': int(data.get('like_id', 0)),
            'user_id': int(data.get('user_id', 0)),
            'post_id': int(data.get('post_id', 0)) if data.get('post_id') else None,
            'comment_id': int(data.get('comment_id', 0)) if data.get('comment_id') else None,
            'created_at': data.get('created_at')
        }

# ==================== NOTIFICATION MODELS ====================

class Notification(SheetModel):
    def __init__(self):
        super().__init__('notifications', 'notification_id')
    
    def get_by_user(self, user_id):
        return self.query(user_id=str(user_id))
    
    def get_unread_by_user(self, user_id):
        return self.query(user_id=str(user_id), is_read='false')
    
    def to_dict(self, data):
        if not data:
            return None
        return {
            'notification_id': int(data.get('notification_id', 0)),
            'user_id': int(data.get('user_id', 0)),
            'type': data.get('type', 'system'),
            'title': data.get('title'),
            'message': data.get('message'),
            'link': data.get('link'),
            'is_read': data.get('is_read') == 'true',
            'created_at': data.get('created_at')
        }

# ==================== ACHIEVEMENT MODELS ====================

class Achievement(SheetModel):
    def __init__(self):
        super().__init__('achievements', 'achievement_id')
    
    def to_dict(self, data):
        if not data:
            return None
        return {
            'achievement_id': int(data.get('achievement_id', 0)),
            'name': data.get('name'),
            'description': data.get('description'),
            'icon': data.get('icon'),
            'category': data.get('category'),
            'points': int(data.get('points', 0))
        }

class UserAchievement(SheetModel):
    def __init__(self):
        super().__init__('user_achievements', 'user_achievement_id')
    
    def get_by_user(self, user_id):
        return self.query(user_id=str(user_id))
    
    def to_dict(self, data):
        if not data:
            return None
        return {
            'user_achievement_id': int(data.get('user_achievement_id', 0)),
            'user_id': int(data.get('user_id', 0)),
            'achievement_id': int(data.get('achievement_id', 0)),
            'earned_at': data.get('earned_at')
        }

# ==================== USER SETTINGS ====================

class UserSetting(SheetModel):
    def __init__(self):
        super().__init__('user_settings', 'setting_id')
    
    def get_by_user(self, user_id):
        results = self.query(user_id=str(user_id))
        return results[0] if results else None
    
    def to_dict(self, data):
        if not data:
            return None
        return {
            'setting_id': int(data.get('setting_id', 0)),
            'user_id': int(data.get('user_id', 0)),
            'theme': data.get('theme', 'light'),
            'language': data.get('language', 'en'),
            'notifications_enabled': data.get('notifications_enabled') == 'true',
            'email_notifications': data.get('email_notifications') == 'true',
            'push_notifications': data.get('push_notifications') == 'true',
            'auto_play_videos': data.get('auto_play_videos') == 'true',
            'daily_reminders': data.get('daily_reminders') == 'true',
            'privacy_profile_visible': data.get('privacy_profile_visible') == 'true',
            'privacy_activity_status': data.get('privacy_activity_status') == 'true',
            'privacy_progress_sharing': data.get('privacy_progress_sharing') == 'true',
            'privacy_data_analytics': data.get('privacy_data_analytics') == 'true'
        }
