from flask import jsonify, current_app
from flask_jwt_extended import (
    create_access_token, get_jwt_identity, get_jwt,
    JWTManager, jwt_required
)
from datetime import timedelta
from Modules.SQLModels import User
from functools import wraps

jwt = JWTManager()  # Will initialize in server.py with jwt.init_app(app)

# --------------------------
# GEN JWT
# --------------------------
def generate_jwt(user):
    """
    Generate JWT for a SQLAlchemy user object
    """
    return create_access_token(
        identity=user.username,
        additional_claims={
            "role": user.role,
            "id": user.id,
            "email": user.email
        },
        expires_delta=timedelta(hours=1)
    )

# --------------------------
# GET CURRENT USER (from DB)
# --------------------------
def get_current_user():
    username = get_jwt_identity()
    claims = get_jwt()

    user = User.query.filter_by(username=username).first()
    if not user:
        return None

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "nume": user.nume
    }

# --------------------------
# CHECK ROLE (simple)
# --------------------------
def check_role(required_role):
    claims = get_jwt()
    return claims.get("role") == required_role

# --------------------------
# DECORATOR PENTRU ROLURI
# --------------------------
def allowed_users(allowed_roles):
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def decorated(*args, **kwargs):
            user = get_current_user()
            if not user or user["role"] not in allowed_roles:
                return jsonify({"error": "Acces interzis"}), 403
            return fn(*args, **kwargs)  # <- make sure args/kwargs are passed
        return decorated
    return wrapper


# --------------------------
# JWT ERROR HANDLERS
# --------------------------
def init_jwt(app):
    """
    Initialize JWTManager and register error handlers
    """
    jwt.init_app(app)

    @jwt.unauthorized_loader
    def unauthorized_response(msg):
        return jsonify({"error": "Missing Authorization Header", "details": msg}), 401

    @jwt.invalid_token_loader
    def invalid_token_response(msg):
        return jsonify({"error": "Invalid token", "details": msg}), 422

    @jwt.expired_token_loader
    def expired_token_response(header, payload):
        return jsonify({"error": "Token expired"}), 401
