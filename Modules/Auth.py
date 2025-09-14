from flask import Blueprint, jsonify, request, abort
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from Modules.misc import users, add_user
from datetime import timedelta

auth = Blueprint("auth", __name__)

@auth.route('/signup', methods=['POST'])
@auth.route('/register', methods=['POST'])
def register():
  data = request.get_json() if request.is_json else request.args

  username = data.get('username')
  password = data.get('password')
  nume = data.get('nume', '')
  email = data.get('email', '')
  role = data.get('role', 'Client')  # default role

  if not username or not password:
    return jsonify({'message': 'Username și parola sunt necesare'}), 400

  if any(u['username'] == username for u in users):
    return jsonify({'message': 'Username-ul există deja'}), 409

  # Folosim funcția add_user din misc.py
  new_user = add_user(username=username, password=password, nume=nume, email=email, role=role)

  # Creăm token JWT cu expirare 1 oră
  access_token = create_access_token(identity=new_user['id'], expires_delta=timedelta(hours=1))

  return jsonify({'message': 'User înregistrat cu succes!', 'access_token': access_token}), 201

# Login
@auth.route('/login', methods=['POST'])
def login():
  data = request.get_json() if request.is_json else request.args

  username = data.get('username')
  password = data.get('password')

  if not username or not password:
    return jsonify({'message': 'Username și parola sunt necesare'}), 400

  # Varianta simplă fără hash
  user = next((u for u in users if u['username'] == username and u['password'] == password), None)

  # Comentariu pentru hash:
  # from werkzeug.security import check_password_hash
  # user = next((u for u in users if u['username'] == username and check_password_hash(u['password'], password)), None)

  if not user:
    return jsonify({'message': 'Credențiale invalide'}), 401

  # Creare token JWT cu expirare de 1 oră
  access_token = create_access_token(identity=user['id'], expires_delta=timedelta(hours=1))

  return jsonify({
    'message': f'Bine ai venit, {user["nume"]}!',
    'access_token': access_token
  }), 200
