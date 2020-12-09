from flask import jsonify
from blacklist import BLACKLIST
from flask_jwt_extended import JWTManager, verify_jwt_in_request, get_jwt_claims


def bind_jwt_messages(app):
    """Binds jwt messages to the app.

    Args:
        app: The main app, configured but not started

    Returns:
        JWTManager: The jwt manager bound to the app
    """
    jwt = JWTManager(app)

    @jwt.expired_token_loader
    def expired_token_callback():
        return jsonify({
            "message": "The token has expired",
            "error": "token_expired"
        }), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            "message": "Signature verification failed",
            "error": "invalid_token"
        }), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            "message": "Request does not contain an access token",
            "error": "authorization_required"
        }), 401

    @jwt.needs_fresh_token_loader
    def needs_fresh_token_callback(error):
        return jsonify({
            "message": "The token is not fresh",
            "error": "fresh_token_required"
        }), 401

    @jwt.revoked_token_loader
    def revoked_token_callback():
        return jsonify({
            "message": "The token has been revoked",
            "error": "token_revoked"
        }), 401

    @jwt.token_in_blacklist_loader
    def check_if_token_in_blacklist(decrypted_token):
        return decrypted_token["jti"] in BLACKLIST

    return jwt


def role_required(role="admin"):
    """Custom decorator factory that produces a decorator that verifies if
        the JWT is present in the request, as well as insuring that this
        user has a chosen role in the access token
    """
    def decorator(fn):
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt_claims()
            if claims['role'] != role:
                return {"error": "role_mismatch", "message": f"Wanted '{role}', but got '{claims['role']}'."}, 403
            else:
                return fn(*args, **kwargs)
        return wrapper
    return decorator
