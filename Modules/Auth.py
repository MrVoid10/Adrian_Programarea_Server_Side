from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
# from Modules.misc import users, add_user
from datetime import timedelta
import re
from Modules.SQLModels import User
from Modules.DBConn import db

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
    nume = data.get('nume') or data.get('name') or ''
    email = data.get('email', '')

    if not username or not password:
        return jsonify({'message': 'Username și parola sunt necesare'}), 400

    if email and not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
        return jsonify({'message': 'Email invalid'}), 400

    # verificăm dacă userul există
    existing_user = User.query.filter(
        (User.username == username) | (User.email == email)
    ).first()

    if existing_user:
        return jsonify({'message': 'Username-ul sau email-ul există deja'}), 409

    # hash parola
    hashed_pw = generate_password_hash(password)

    new_user = User(
        id=None,  # dacă e IDENTITY în SQL, poți lăsa None
        username=username,
        nume=nume,
        email=email,
        password=hashed_pw,
        role="Client",
        is_active=True
    )

    db.session.add(new_user)
    db.session.commit()

    access_token = create_access_token(
        identity=new_user.username,
        expires_delta=timedelta(hours=1)
    )

    return jsonify({
        'message': 'User înregistrat cu succes!',
        'access_token': access_token,
        'name': new_user.nume,
        'role': new_user.role
    }), 201

# --------------------------
# LOGIN
# --------------------------
@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username și parola sunt necesare'}), 400

    # căutăm userul în DB
    user = User.query.filter_by(username=username).first()

    if not user or not check_password_hash(user.password, password):
        return jsonify({'message': 'Credențiale invalide'}), 401

    if not user.is_active:
        return jsonify({'message': 'Contul este dezactivat'}), 403

    access_token = create_access_token(
        identity=user.username,
        expires_delta=timedelta(hours=1)
    )

    return jsonify({
        'message': f'Bine ai venit, {user.nume}!',
        'access_token': access_token,
        'name': user.nume,
        'role': user.role
    }), 200
