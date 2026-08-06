# routes/notification_routes.py
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.sheet_models import Notification

notification_bp = Blueprint('notification', __name__)
notification_model = Notification()

@notification_bp.route('/', methods=['GET'])
@jwt_required()
def get_notifications():
    user_id = get_jwt_identity()
    notifications = notification_model.get_by_user(user_id)
    return jsonify({'notifications': notifications}), 200

@notification_bp.route('/unread', methods=['GET'])
@jwt_required()
def get_unread():
    user_id = get_jwt_identity()
    notifications = notification_model.query(user_id=str(user_id), is_read='false')
    return jsonify({'notifications': notifications}), 200

@notification_bp.route('/<int:notification_id>/read', methods=['PUT'])
@jwt_required()
def mark_read(notification_id):
    notification_model.update(notification_id, {'is_read': 'true'})
    return jsonify({'message': 'Marked as read'}), 200

@notification_bp.route('/mark-all-read', methods=['PUT'])
@jwt_required()
def mark_all_read():
    user_id = get_jwt_identity()
    notifications = notification_model.query(user_id=str(user_id), is_read='false')
    for notification in notifications:
        notification_model.update(notification.get('notification_id'), {'is_read': 'true'})
    return jsonify({'message': 'All notifications marked as read'}), 200

@notification_bp.route('/<int:notification_id>', methods=['DELETE'])
@jwt_required()
def delete_notification(notification_id):
    notification_model.delete(notification_id)
    return jsonify({'message': 'Notification deleted'}), 200

@notification_bp.route('/clear', methods=['DELETE'])
@jwt_required()
def clear_notifications():
    user_id = get_jwt_identity()
    notifications = notification_model.get_by_user(user_id)
    for notification in notifications:
        notification_model.delete(notification.get('notification_id'))
    return jsonify({'message': 'All notifications cleared'}), 200
