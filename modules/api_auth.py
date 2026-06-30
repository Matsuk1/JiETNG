"""Authentication and permission helpers for JiETNG HTTP APIs."""

from functools import wraps

from flask import jsonify, request

from modules.devtoken_manager import load_dev_tokens, verify_dev_token
from modules.import_token_manager import verify_import_token
from modules.user_db import get_user, get_user_field


MAIMAI_SESSION_CORS_ORIGINS = {
    "https://maimaidx.jp",
    "https://maimaidx-eng.com",
    "https://dxrating.net",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
}


def maimai_session_cors(response):
    origin = request.headers.get("Origin")
    if origin in MAIMAI_SESSION_CORS_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response


def require_dev_token(f):
    """Verify developer Bearer token and attach request.token_info."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return jsonify({
                "error": "No authorization header",
                "message": "Authorization header is required",
            }), 401

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({
                "error": "Invalid authorization header",
                "message": "Authorization header must be in format: Bearer <token>",
            }), 401

        token_info = verify_dev_token(parts[1])
        if not token_info:
            return jsonify({
                "error": "Invalid token",
                "message": "Token is invalid or has been revoked",
            }), 401

        request.token_info = token_info
        return f(*args, **kwargs)

    return decorated_function


def require_import_token(f):
    """Verify user import token and attach request.import_token_info."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == "OPTIONS":
            return f(*args, **kwargs)

        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return maimai_session_cors(jsonify({
                "error": "No authorization header",
                "message": "Authorization header is required",
            })), 401

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return maimai_session_cors(jsonify({
                "error": "Invalid authorization header",
                "message": "Authorization header must be in format: Bearer <token>",
            })), 401

        token_info = verify_import_token(parts[1])
        if not token_info:
            return maimai_session_cors(jsonify({
                "error": "Invalid token",
                "message": "Import token is invalid or has been revoked",
            })), 401

        request.import_token_info = token_info
        return f(*args, **kwargs)

    return decorated_function


def check_user_permission(user_id, token_id):
    """Return (True, user_data) if token can access user_id, else an error response."""
    user_data = get_user(user_id)

    if not user_data:
        return False, (jsonify({
            "error": "User not found",
            "message": f"User {user_id} does not exist",
        }), 404)

    if user_data.get("registered_via_token") == token_id:
        return True, user_data

    dev_tokens = load_dev_tokens()
    if token_id in dev_tokens:
        allowed_users = dev_tokens[token_id].get("allowed_users", [])
        if user_id in allowed_users:
            return True, user_data

    return False, (jsonify({
        "error": "Permission denied",
        "message": f"Token does not have permission to access user {user_id}",
    }), 403)


def require_user_permission(f):
    """Require request.token_info to have access to URL kwarg user_id."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = kwargs.get("user_id")
        if not user_id:
            return jsonify({
                "error": "Missing parameter",
                "message": "user_id is required",
            }), 400

        token_id = request.token_info["token_id"]
        has_permission, result = check_user_permission(user_id, token_id)
        if not has_permission:
            return result

        return f(*args, **kwargs)

    return decorated_function


def require_owner_permission(f):
    """Require request.token_info to be the owner token for URL kwarg user_id."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = kwargs.get("user_id")
        if not user_id:
            return jsonify({
                "error": "Missing parameter",
                "message": "user_id is required",
            }), 400

        token_id = request.token_info["token_id"]
        owner_token = get_user_field(user_id, "registered_via_token")
        if owner_token is None:
            return jsonify({
                "error": "User not found",
                "message": f"User {user_id} does not exist",
            }), 404

        if owner_token != token_id:
            return jsonify({
                "error": "Forbidden",
                "message": "Only the owner token (creator) can perform this operation",
            }), 403

        return f(*args, **kwargs)

    return decorated_function
