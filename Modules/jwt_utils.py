from flask_jwt_extended import create_access_token, get_jwt_identity, get_jwt
from datetime import timedelta
from Modules.misc import users

# --------------------------
# GEN JWT
# --------------------------
def generate_jwt(user):
    return create_access_token(
        identity=user["username"],  # username devine identitatea
        additional_claims={
            "role": user["role"],
            "id": user["id"],
            "email": user["email"]
        },
        expires_delta=timedelta(hours=1)
    )

# --------------------------
# GET CURRENT USER
# --------------------------
def get_current_user():
    username = get_jwt_identity()
    claims = get_jwt()

    # căutăm în lista de useri
    user = next((u for u in users if u["username"] == username), None)
    if not user:
        return None

    # completăm cu claims (ca fallback)
    user_info = {
        "id": claims.get("id", user["id"]),
        "username": username,
        "email": claims.get("email", user["email"]),
        "role": claims.get("role", user["role"]),
        "nume": user.get("nume")
    }
    return user_info

# --------------------------
# CHECK ROLE
# --------------------------
def check_role(required_role):
    claims = get_jwt()
    role = claims.get("role")
    return role == required_role

from flask import jsonify, request
from Modules.jwt_utils import get_current_user
from Modules.misc import load_table, save_table, TABLE_SCHEMAS

# --------------------------
# DECORATOR PENTRU ROLURI
# --------------------------
from functools import wraps
from flask_jwt_extended import jwt_required

def allowed_users(allowed_roles):
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def decorated(*args, **kwargs):
            user = get_current_user()
            if not user or user["role"] not in allowed_roles:
                return jsonify({"error": "Acces interzis"}), 403
            return fn(*args, **kwargs)
        return decorated
    return wrapper

# --------------------------
# ROUTA /ADD
# --------------------------

