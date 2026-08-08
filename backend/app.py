# app.py
import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize app
app = Flask(__name__)

# Configuration
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'fallback-secret-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 86400  # 24 hours

# Initialize extensions
jwt = JWTManager(app)
bcrypt = Bcrypt(app)

# CORS
CORS(app, origins=os.environ.get('CORS_ORIGINS', '*'))

# Import routes (with error handling)
try:
    from routes.auth_routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    print("✅ Auth routes loaded")
except ImportError as e:
    print(f"⚠️ Auth routes not loaded: {e}")

try:
    from routes.user_routes import user_bp
    app.register_blueprint(user_bp, url_prefix='/api/users')
    print("✅ User routes loaded")
except ImportError as e:
    print(f"⚠️ User routes not loaded: {e}")

try:
    from routes.course_routes import course_bp
    app.register_blueprint(course_bp, url_prefix='/api/courses')
    print("✅ Course routes loaded")
except ImportError as e:
    print(f"⚠️ Course routes not loaded: {e}")

try:
    from routes.enrollment_routes import enrollment_bp
    app.register_blueprint(enrollment_bp, url_prefix='/api/enrollments')
    print("✅ Enrollment routes loaded")
except ImportError as e:
    print(f"⚠️ Enrollment routes not loaded: {e}")

try:
    from routes.assignment_routes import assignment_bp
    app.register_blueprint(assignment_bp, url_prefix='/api/assignments')
    print("✅ Assignment routes loaded")
except ImportError as e:
    print(f"⚠️ Assignment routes not loaded: {e}")

try:
    from routes.quiz_routes import quiz_bp
    app.register_blueprint(quiz_bp, url_prefix='/api/quiz')
    print("✅ Quiz routes loaded")
except ImportError as e:
    print(f"⚠️ Quiz routes not loaded: {e}")

try:
    from routes.community_routes import community_bp
    app.register_blueprint(community_bp, url_prefix='/api/community')
    print("✅ Community routes loaded")
except ImportError as e:
    print(f"⚠️ Community routes not loaded: {e}")

try:
    from routes.notification_routes import notification_bp
    app.register_blueprint(notification_bp, url_prefix='/api/notifications')
    print("✅ Notification routes loaded")
except ImportError as e:
    print(f"⚠️ Notification routes not loaded: {e}")

try:
    from routes.admin_routes import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    print("✅ Admin routes loaded")
except ImportError as e:
    print(f"⚠️ Admin routes not loaded: {e}")

# Health check
@app.route('/')
def index():
    return jsonify({
        'name': 'LearnSync Pro API',
        'version': '1.0.0',
        'status': 'running',
        'database': 'Google Sheets'
    })

@app.route('/api/health')
def health():
    from services.google_sheets import sheet_service
    return jsonify({
        'status': 'healthy',
        'database': 'Google Sheets',
        'sheets_connected': sheet_service.connected if hasattr(sheet_service, 'connected') else False
    })

# For local development
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)