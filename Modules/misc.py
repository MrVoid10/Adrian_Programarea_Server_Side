# misc.py
import json
from pathlib import Path

SETTINGS_FILE = Path('Modules/settings.json')


def load_settings() -> dict:
    """Load settings from the JSON file."""
    if not SETTINGS_FILE.exists():
        raise FileNotFoundError(f"{SETTINGS_FILE} not found")
    with SETTINGS_FILE.open('r', encoding='utf-8') as f:
        return json.load(f)


def save_settings(settings: dict):
    """Save settings back to the JSON file."""
    with SETTINGS_FILE.open('w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)


def get_setting(key: str, default=None):
    """Get a single setting by key, supports nested keys via dots."""
    settings = load_settings()
    keys = key.split(".")
    val = settings
    for k in keys:
        if isinstance(val, dict):
            val = val.get(k, default)
        else:
            return default
    return val


def change_setting(key: str, value):
    """Change a single setting by key and save to file, supports nested keys via dots."""
    settings = load_settings()
    keys = key.split(".")
    target = settings
    for k in keys[:-1]:
        if k not in target or not isinstance(target[k], dict):
            target[k] = {}
        target = target[k]
    target[keys[-1]] = value
    save_settings(settings)


# Shortcut variables (optional)
settings = load_settings()
SSL_CONTEXT = (get_setting('ssl_context.cert'), get_setting('ssl_context.key'))
# ALLOWED_TERMS = get_setting('allowed_terms')
JWT_SECRET_KEY = get_setting('jwt_secret_key')
# STATIC_FRONTEND_FOLDER = get_setting('static_frontend_folder')

###############
# OLD SUPPORT #
###############
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
    "status": "",
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

SENSITIVE_FIELDS = {
    "users": ["password", "email"],
    "products": ["imagine"], 
    "orders": ["produse"]
}
