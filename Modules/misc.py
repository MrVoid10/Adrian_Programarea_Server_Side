# misc.py
import json
from werkzeug.security import generate_password_hash


with open('Modules/settings.json', 'r') as f:
  config = json.load(f)
  SSL_CONTEXT = (config['ssl_context']['cert'], config['ssl_context']['key'])
  ALLOWED_TERMS = config['allowed_terms']
  JWT_SECRET_KEY = config['jwt_secret_key']
  del config

with open('Prototip/products.json', 'r') as f:
  products= json.load(f)["products"]

with open('Prototip/stock.json', 'r') as f:
  stock= json.load(f)["stock"]

with open('Prototip/users.json', 'r') as f:
  users= json.load(f)["users"]

with open('Prototip/orders.json', 'r') as f:
  orders= json.load(f)["orders"]



def add_user(username, password, nume="", email="", role="Client"):
  # Verificăm dacă username există deja
  if any(u['username'] == username for u in users):
    raise ValueError("Username-ul există deja")

  # Creăm ID nou
  new_id = max(u['id'] for u in users) + 1 if users else 1

  # Hash parola
  hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

  new_user = {
    "id": new_id,
    "username": username,
    "nume": nume,
    "email": email,
    "password": hashed_password,
    "role": role
  }

  users.append(new_user)

  # Scriem înapoi în users.json
  with open('Prototip/users.json', 'w') as f:
    json.dump({"users": users}, f, indent=2)

  return new_user