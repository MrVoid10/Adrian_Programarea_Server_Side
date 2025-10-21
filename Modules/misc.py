# misc.py
import json
from werkzeug.security import generate_password_hash
from functools import wraps
from copy import deepcopy

with open('Modules/settings.json', 'r') as f:
  config = json.load(f)
  SSL_CONTEXT = (config['ssl_context']['cert'], config['ssl_context']['key'])
  ALLOWED_TERMS = config['allowed_terms']
  JWT_SECRET_KEY = config['jwt_secret_key']
  STATIC_FRONTEND_FOLDER = config['static_frontend_folder']
  del config

with open('Prototip/products.json', 'r') as f:
  products= json.load(f)["products"]

with open('Prototip/stock.json', 'r') as f:
  stock= json.load(f)["stock"]

with open('Prototip/users.json', 'r') as f:
  users= json.load(f)["users"]

with open('Prototip/orders.json', 'r') as f:
  orders= json.load(f)["orders"]

with open('Prototip/camere.json', 'r') as f:
  camere= json.load(f)["camere"]

with open('Prototip/detalii_camera.json', 'r') as f:
  detalii_camera= json.load(f)["detalii_camera"]


TABLE_SCHEMAS = {
  "products": {
    "id": 0,
    "nume": "",
    "brand": "",
    "model": "",
    "descriere": "",
    "pret": 0.0,
    "categorie": "",
    "garantie": 0,
    "imagine": "",
    "data_adaugare": ""
  },
  "stock": {
    "produs_id": 0,
    "cantitate": 0,
    "depozit": ""
  },
  "orders": {
    "id": 0,
    "client_id": 0,
    "data_comanda": "",
    "status": "",
    "produse": []
  },
  "users": {
    "id": 0,
    "username": "",
    "nume": "",
    "email": "",
    "password": "",
    "role": "Client",
    "is_active": True
  }
}

def add_user(username, password, nume="", email="", role="Client"):
  # Verificăm dacă username există deja
  if any(u['username'] == username for u in users):
    raise ValueError("Username-ul există deja")

  # Creăm ID nou
  new_id = max(u['id'] for u in users) + 1 if users else 1

  new_user = {
    "id": new_id,
    "username": username,
    "nume": nume,
    "email": email,
    "password": password,
    "role": role
  }

  users.append(new_user)

  # Scriem înapoi în users.json
  with open('Prototip/users.json', 'w') as f:
    json.dump({"users": users}, f, indent=2)

  return new_user

def change_user_role(user, target_username, new_role):
    target_user = next((u for u in users if u['username'] == target_username), None)
    if not target_user:
        raise ValueError("Utilizatorul țintă nu există")

    if not user.get("is_active", True):
        raise PermissionError("Utilizatorul nu este activ")

    if user["role"] == "Client":
        raise PermissionError("Clientul nu are permisiunea de a modifica roluri")

    if user["role"] == "Angajat" and target_user["role"] != "Client":
        raise PermissionError("Angajatul poate modifica doar rolul utilizatorilor cu rol Client")

    target_user["role"] = new_role

    with open('Prototip/users.json', 'w') as f:
        json.dump({"users": users}, f, indent=2)

    return target_user

def load_table(table_name):
    path = f"Prototip/{table_name}.json"
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get(table_name, [])
    except FileNotFoundError:
        return []
  
def save_table(table_name, data):
  path = f"Prototip/{table_name}.json"
  with open(path, "w", encoding="utf-8") as f:
    json.dump({table_name : data}, f, indent=2)

def capitalize_name(f):
  @wraps(f)
  def decorated(*args, **kwargs):
    users_copy = deepcopy(users)
    for u in users_copy:
      if "nume" in u and isinstance(u["nume"], str):
        u["nume"] = u["nume"].upper()
    return f(users_copy, *args, **kwargs)
  return decorated

# ? #