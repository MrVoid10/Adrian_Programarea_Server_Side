import json
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from colorama import init, Fore


db = SQLAlchemy()

# Inițializează colorama
init(autoreset=True)

# Citește setările din fișierul settings.json
with open('settings.json', 'r') as f:
  config = json.load(f)

NUME = config['username']
PAROLA = config['password']
DBNUME = config['database']
SERVER = config['server']

def init_db(app):
  DATABASE_URI = f'mssql+pyodbc://{NUME}:{PAROLA}@{SERVER}/{DBNUME}?driver=ODBC+Driver+17+for+SQL+Server'
  app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
  app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

  try:
    # Testarea conexiunii
    engine = create_engine(DATABASE_URI)
    connection = engine.connect()
    connection.close()
    print(Fore.GREEN + "Conexiunea la baza de date a fost realizată cu succes.")
  except OperationalError as e:
    print(Fore.RED + f"Nu s-a putut conecta la baza de date: {e}")

  db.init_app(app)