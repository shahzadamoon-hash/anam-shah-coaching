// js/api.js
const API_BASE_URL = 'https://anam-shah-coaching-api.vercel.app/api';

// For local development, you can switch to:
// const API_BASE_URL = 'http://localhost:5000/api';

class LearnSyncAPI {
    constructor() {
        this.token = localStorage.getItem('access_token');
        this.user = JSON.parse(localStorage.getItem('user') || 'null');
    }

    // Store token and user
    setAuth(token, user) {
        this.token = token;
        this.user = user;
        localStorage.setItem('access_token', token);
        localStorage.setItem('user', JSON.stringify(user));
    }

    // Clear auth
    clearAuth() {
        this.token = null;
        this.user = null;
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
    }

    // Get headers with authentication
    getHeaders() {
        const headers = {
            'Content-Type': 'application/json',
        };
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        return headers;
    }

    // Generic API request
    async request(endpoint, method = 'GET', data = null) {
        const url = `${API_BASE_URL}${endpoint}`;
        const options = {
            method,
            headers: this.getHeaders(),
        };
        if (data) {
            options.body = JSON.stringify(data);
        }

        try {
            const response = await fetch(url, options);
            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Something went wrong');
            }
            return result;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // ==================== AUTH ENDPOINTS ====================

    // Register a new user
    async register(userData) {
        const result = await this.request('/auth/register', 'POST', userData);
        if (result.user) {
            // Auto-login after registration
            const loginResult = await this.login({
                email: userData.email,
                password: userData.password
            });
            return loginResult;
        }
        return result;
    }

    // Login user
    async login(credentials) {
        const result = await this.request('/auth/login', 'POST', credentials);
        if (result.access_token) {
            this.setAuth(result.access_token, result.user);
        }
        return result;
    }

    // Logout
    logout() {
        this.clearAuth();
        window.location.href = '/';
    }

    // Get current user
    async getCurrentUser() {
        if (!this.token) return null;
        try {
            const result = await this.request('/auth/me', 'GET');
            return result.user;
        } catch (error) {
            this.clearAuth();
            return null;
        }
    }

    // ==================== USER ENDPOINTS ====================

    // Get user profile
    async getProfile() {
        return this.request('/users/profile', 'GET');
    }

    // Update user profile
    async updateProfile(data) {
        return this.request('/users/profile', 'PUT', data);
    }

    // ==================== COURSE ENDPOINTS ====================

    // Get all courses
    async getCourses() {
        return this.request('/courses', 'GET');
    }

    // Get featured courses
    async getFeaturedCourses() {
        return this.request('/courses/featured', 'GET');
    }

    // Get course by ID
    async getCourse(courseId) {
        return this.request(`/courses/${courseId}`, 'GET');
    }

    // ==================== ENROLLMENT ENDPOINTS ====================

    // Get user enrollments
    async getEnrollments() {
        return this.request('/enrollments', 'GET');
    }

    // Enroll in course
    async enrollCourse(courseId) {
        return this.request(`/enrollments/course/${courseId}`, 'POST');
    }

    // ==================== NOTIFICATION ENDPOINTS ====================

    // Get notifications
    async getNotifications() {
        return this.request('/notifications', 'GET');
    }

    // Get unread notifications
    async getUnreadNotifications() {
        return this.request('/notifications/unread', 'GET');
    }

    // Mark notification as read
    async markNotificationRead(notificationId) {
        return this.request(`/notifications/${notificationId}/read`, 'PUT');
    }

    // Mark all notifications as read
    async markAllNotificationsRead() {
        return this.request('/notifications/mark-all-read', 'PUT');
    }

    // ==================== QUIZ ENDPOINTS ====================

    // Get quiz questions
    async getQuizQuestions(lessonId) {
        return this.request(`/quiz/lesson/${lessonId}`, 'GET');
    }

    // Start quiz
    async startQuiz(lessonId, courseId) {
        return this.request(`/quiz/lesson/${lessonId}/start`, 'POST', { course_id: courseId });
    }

    // Submit quiz
    async submitQuiz(attemptId, answers) {
        return this.request('/quiz/submit', 'POST', { attempt_id: attemptId, answers });
    }

    // ==================== ASSIGNMENT ENDPOINTS ====================

    // Get assignments
    async getAssignments(lessonId) {
        return this.request(`/assignments/lesson/${lessonId}`, 'GET');
    }

    // Submit assignment
    async submitAssignment(assignmentId, courseId, answers) {
        return this.request('/assignments/submit', 'POST', {
            assignment_id: assignmentId,
            course_id: courseId,
            answers
        });
    }

    // ==================== COMMUNITY ENDPOINTS ====================

    // Get community posts
    async getCommunityPosts() {
        return this.request('/community/posts', 'GET');
    }

    // Create community post
    async createCommunityPost(data) {
        return this.request('/community/posts', 'POST', data);
    }

    // Like a post
    async likePost(postId) {
        return this.request(`/community/posts/${postId}/like`, 'POST');
    }

    // Add comment to post
    async addComment(postId, content) {
        return this.request(`/community/posts/${postId}/comments`, 'POST', { content });
    }
}

// Create a single instance
const api = new LearnSyncAPI();