from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from Modules.misc import users, add_user
from datetime import timedelta

auth = Blueprint("auth", __name__)

# --------------------------
# REGISTER / SIGNUP
# --------------------------
@auth.route('/signup', methods=['POST'])
@auth.route('/register', methods=['POST'])
def register():
    data = request.get_json() if request.is_json else request.args

    username = data.get('username')
    password = data.get('password')
    nume = data.get('nume', '')
    email = data.get('email', '')

    if not username or not password:
        return jsonify({'message': 'Username și parola sunt necesare'}), 400

    if any(u['username'] == username for u in users):
        return jsonify({'message': 'Username-ul există deja'}), 409

    hashed_password = generate_password_hash(password)

    new_user = add_user(
        username=username,
        password=hashed_password,
        nume=nume,
        email=email
    )

    access_token = create_access_token(
        identity=new_user['username'],
        expires_delta=timedelta(hours=1)
    )

    return jsonify({'message': 'User înregistrat cu succes!', 'access_token': access_token}), 201


# --------------------------
# LOGIN
# --------------------------
@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json() if request.is_json else request.args

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username și parola sunt necesare'}), 400

    user = next((u for u in users if u['username'] == username), None)
    if not user or not check_password_hash(user['password'], password):
        return jsonify({'message': 'Credențiale invalide'}), 401

    access_token = create_access_token(
        identity=user['username'],
        expires_delta=timedelta(hours=1)
    )

    return jsonify({
        'message': f'Bine ai venit, {user["nume"]}!',
        'access_token': access_token
    }), 200
