# create_sheets.py
import gspread
from google.oauth2.service_account import Credentials
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to Google Sheets
creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
import json
creds_dict = json.loads(creds_json)
scopes = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
client = gspread.authorize(creds)

# Open your sheet
sheet_id = os.environ.get('GOOGLE_SHEET_ID')
sheet = client.open_by_key(sheet_id)

# Define all sheets with headers
sheets = {
    'users': ['user_id', 'username', 'email', 'password_hash', 'full_name', 'phone', 'profile_pic', 'bio', 'role', 'status', 'created_at', 'last_login'],
    'student_profiles': ['profile_id', 'user_id', 'date_of_birth', 'gender', 'address', 'city', 'state', 'country', 'postal_code', 'education_level', 'institution', 'graduation_year', 'exam_target', 'preferred_language', 'learning_goal'],
    'instructor_profiles': ['instructor_id', 'user_id', 'qualification', 'experience_years', 'specialization', 'bio', 'website', 'linkedin', 'rating', 'total_students', 'total_courses', 'is_verified'],
    'categories': ['category_id', 'name', 'slug', 'icon', 'description', 'parent_id'],
    'courses': ['course_id', 'instructor_id', 'category_id', 'title', 'slug', 'description', 'short_description', 'level', 'language', 'thumbnail', 'price', 'discount_price', 'is_free', 'is_published', 'is_featured', 'total_lectures', 'total_duration', 'total_students', 'rating', 'rating_count', 'requirements', 'learning_outcomes', 'created_at'],
    'sections': ['section_id', 'course_id', 'title', 'description', 'order_number'],
    'lessons': ['lesson_id', 'section_id', 'title', 'description', 'lesson_type', 'content', 'video_url', 'video_duration', 'file_url', 'file_type', 'order_number', 'is_preview', 'is_free', 'created_at'],
    'flashcards': ['flashcard_id', 'lesson_id', 'term', 'definition', 'example', 'category', 'difficulty', 'order_number'],
    'quiz_questions': ['question_id', 'lesson_id', 'question_type', 'question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer', 'explanation', 'marks', 'negative_marks', 'order_number'],
    'assignments': ['assignment_id', 'lesson_id', 'title', 'description', 'instructions', 'assignment_type', 'total_marks', 'passing_marks', 'time_limit', 'due_date', 'is_active'],
    'assignment_questions': ['question_id', 'assignment_id', 'question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer', 'explanation', 'marks', 'order_number'],
    'enrollments': ['enrollment_id', 'user_id', 'course_id', 'enrollment_date', 'status', 'progress_percentage', 'completion_date', 'last_accessed', 'certificate_issued', 'certificate_url'],
    'lesson_progress': ['progress_id', 'enrollment_id', 'lesson_id', 'status', 'progress_percentage', 'watch_time', 'is_completed', 'completed_at', 'last_accessed'],
    'quiz_attempts': ['attempt_id', 'enrollment_id', 'lesson_id', 'score', 'total_questions', 'correct_answers', 'wrong_answers', 'unanswered', 'time_taken', 'is_passed', 'attempt_date'],
    'assignment_submissions': ['submission_id', 'enrollment_id', 'assignment_id', 'answers', 'score', 'total_marks', 'obtained_marks', 'percentage', 'is_passed', 'is_graded', 'graded_by', 'graded_at', 'time_taken', 'submitted_at'],
    'community_posts': ['post_id', 'user_id', 'course_id', 'title', 'content', 'tags', 'status', 'is_announcement', 'view_count', 'like_count', 'comment_count', 'created_at', 'updated_at'],
    'community_comments': ['comment_id', 'post_id', 'user_id', 'content', 'like_count', 'is_approved', 'created_at', 'updated_at'],
    'notifications': ['notification_id', 'user_id', 'type', 'title', 'message', 'link', 'is_read', 'created_at'],
    'user_settings': ['setting_id', 'user_id', 'theme', 'language', 'notifications_enabled', 'email_notifications', 'push_notifications', 'auto_play_videos', 'daily_reminders', 'privacy_profile_visible', 'privacy_activity_status', 'privacy_progress_sharing', 'privacy_data_analytics']
}

# Create each sheet
for name, headers in sheets.items():
    try:
        worksheet = sheet.worksheet(name)
        print(f"✅ Sheet '{name}' already exists")
    except:
        worksheet = sheet.add_worksheet(title=name, rows=1000, cols=len(headers))
        worksheet.append_row(headers)
        print(f"✅ Created sheet: {name}")

print("\n🎉 All sheets created successfully!")
