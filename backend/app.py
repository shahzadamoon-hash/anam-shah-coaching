import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
from config import config

# Load environment variables
load_dotenv()

# Initialize app
app = Flask(__name__)

# Configuration
app.config['JWT_SECRET_KEY'] = config.JWT_SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = config.JWT_ACCESS_TOKEN_EXPIRES

# Initialize extensions
jwt = JWTManager(app)
bcrypt = Bcrypt(app)

# CORS
CORS(app, origins=config.CORS_ORIGINS)

# Import routes
from routes.auth_routes import auth_bp
from routes.user_routes import user_bp
from routes.course_routes import course_bp
from routes.enrollment_routes import enrollment_bp
from routes.assignment_routes import assignment_bp
from routes.quiz_routes import quiz_bp
from routes.community_routes import community_bp
from routes.notification_routes import notification_bp
from routes.admin_routes import admin_bp

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(user_bp, url_prefix='/api/users')
app.register_blueprint(course_bp, url_prefix='/api/courses')
app.register_blueprint(enrollment_bp, url_prefix='/api/enrollments')
app.register_blueprint(assignment_bp, url_prefix='/api/assignments')
app.register_blueprint(quiz_bp, url_prefix='/api/quiz')
app.register_blueprint(community_bp, url_prefix='/api/community')
app.register_blueprint(notification_bp, url_prefix='/api/notifications')
app.register_blueprint(admin_bp, url_prefix='/api/admin')

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
    return jsonify({
        'status': 'healthy',
        'database': 'Google Sheets',
        'environment': config.ENV
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=config.DEBUG)