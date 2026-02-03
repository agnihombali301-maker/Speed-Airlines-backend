"""
Single auth layer: create tokens with PyJWT and require_user() that reads token
from body, query, or header. No Flask-JWT-Extended so no proxy/header/sub issues.
"""
from flask import request, jsonify, current_app
import jwt as pyjwt
from app.models import User


def create_token(user, extra=None):
    """Build JWT with sub=str(user.id) and role. No expiry for demo. Optional extra claims."""
    payload = {'sub': str(user.id), 'role': user.role}
    if extra:
        payload.update(extra)
    return pyjwt.encode(
        payload,
        current_app.config['JWT_SECRET_KEY'],
        algorithm='HS256'
    )


def require_user():
    """
    Get JWT from (1) JSON body 'token', (2) query ?token=, (3) Authorization Bearer, (4) X-Auth-Token.
    Decode with PyJWT, return (user, payload, None) or (None, None, error_response).
    """
    token = None
    data = request.get_json(silent=True, force=True) or {}
    token = (data.get('token') or '').strip()
    if not token:
        token = (request.args.get('token') or '').strip()
    if not token:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:].strip()
    if not token:
        token = (request.headers.get('X-Auth-Token') or '').strip()
    if not token:
        return None, None, (jsonify({'error': 'Authorization required. Please sign in again.'}), 401)
    try:
        payload = pyjwt.decode(
            token,
            current_app.config['JWT_SECRET_KEY'],
            algorithms=['HS256'],
            options={'verify_exp': False}
        )
        sub = payload.get('sub')
        if sub is None:
            return None, None, (jsonify({'error': 'Invalid token. Please sign in again.'}), 401)
        try:
            uid = int(sub)
        except (TypeError, ValueError):
            return None, None, (jsonify({'error': 'Invalid token. Please sign in again.'}), 401)
        user = User.query.get(uid)
        if not user:
            return None, None, (jsonify({'error': 'User not found'}), 404)
        return user, payload, None
    except pyjwt.ExpiredSignatureError:
        return None, None, (jsonify({'error': 'Token expired. Please sign in again.'}), 401)
    except pyjwt.InvalidTokenError:
        return None, None, (jsonify({'error': 'Invalid token. Please sign in again.'}), 401)
