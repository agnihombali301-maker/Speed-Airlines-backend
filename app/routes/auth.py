from flask import Blueprint, request, jsonify
from app import db
from app.models import User
from app.utils import create_token, require_user
from config import Config

auth_bp = Blueprint('auth', __name__)

SECURITY_QUESTIONS = [
    "What is your mother's maiden name?",
    "What was the name of your first pet?",
    "In which city were you born?",
    "What is your favorite book?",
    "What was your first school name?"
]

@auth_bp.route('/questions', methods=['GET'])
def get_questions():
    return jsonify({'questions': SECURITY_QUESTIONS})

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    username = (data.get('username') or '').strip()
    password = data.get('password')
    q1, q2, q3 = data.get('q1'), data.get('q2'), data.get('q3')
    a1, a2, a3 = data.get('a1'), data.get('a2'), data.get('a3')
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    if not all([q1, q2, q3, a1, a2, a3]):
        return jsonify({'error': 'All 3 security questions and answers required'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 409
    user = User(username=username, role='customer', balance=Config.DEFAULT_CUSTOMER_BALANCE)
    user.set_password(password)
    user.q1, user.q2, user.q3 = SECURITY_QUESTIONS[int(q1)], SECURITY_QUESTIONS[int(q2)], SECURITY_QUESTIONS[int(q3)]
    user.set_answer(1, a1)
    user.set_answer(2, a2)
    user.set_answer(3, a3)
    db.session.add(user)
    db.session.commit()
    token = create_token(user)
    return jsonify({'message': 'Account created', 'token': token, 'user': user.to_dict()}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = (data.get('username') or '').strip()
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid credentials'}), 401
    token = create_token(user)
    return jsonify({'token': token, 'user': user.to_dict()})

@auth_bp.route('/forgot-password-questions', methods=['GET'])
def forgot_password_questions():
    """Return the 3 security questions for the given username (customer only)."""
    username = (request.args.get('username') or '').strip()
    if not username:
        return jsonify({'error': 'Username required'}), 400
    user = User.query.filter_by(username=username, role='customer').first()
    if not user or not user.q1 or not user.q2 or not user.q3:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'questions': [user.q1, user.q2, user.q3]})

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    username = (data.get('username') or '').strip()
    a1, a2, a3 = data.get('a1'), data.get('a2'), data.get('a3')
    if not username or not all([a1, a2, a3]):
        return jsonify({'error': 'Username and all 3 answers required'}), 400
    user = User.query.filter_by(username=username, role='customer').first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    if not (user.check_answer(1, a1) and user.check_answer(2, a2) and user.check_answer(3, a3)):
        return jsonify({'error': 'Incorrect answers to security questions'}), 401
    token = create_token(user, extra={'reset': True})
    return jsonify({'message': 'Answers verified. Use this token to set new password.', 'token': token, 'user': user.to_dict()})

@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    user, payload, err = require_user()
    if err:
        return err[0], err[1]
    data = request.get_json() or {}
    new_pass = data.get('new_password')
    target_username = data.get('target_username')
    if payload.get('reset'):
        if not new_pass:
            return jsonify({'error': 'New password required'}), 400
        user.set_password(new_pass)
        db.session.commit()
        return jsonify({'message': 'Password updated. You can now sign in.'})
    if payload.get('role') == 'admin' and target_username:
        target = User.query.filter_by(username=target_username).first()
        if not target:
            return jsonify({'error': 'Target user not found'}), 404
        if not new_pass:
            return jsonify({'error': 'New password required'}), 400
        target.set_password(new_pass)
        db.session.commit()
        return jsonify({'message': f'Password updated for {target_username}'})
    # Changing own password: only new password required (no current password)
    if not new_pass:
        return jsonify({'error': 'New password required'}), 400
    user.set_password(new_pass)
    db.session.commit()
    return jsonify({'message': 'Password updated'})

@auth_bp.route('/me', methods=['GET', 'POST'])
def me():
    user, _, err = require_user()
    if err:
        return err[0], err[1]
    return jsonify(user.to_dict())
