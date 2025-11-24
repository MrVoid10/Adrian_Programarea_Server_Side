# DBConn.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from colorama import init, Fore
from Modules.misc import get_setting

db = SQLAlchemy()

# Inițializează colorama
init(autoreset=True)

def init_db(app):
    # Preluăm setările din settings.json
    NUME = get_setting('db.username')
    PAROLA = get_setting('db.password')
    DBNUME = get_setting('db.database')
    SERVER = get_setting('db.server')

    DATABASE_URI = f'mssql+pyodbc://{NUME}:{PAROLA}@{SERVER}/{DBNUME}?driver=ODBC+Driver+17+for+SQL+Server'
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    try:
        engine = create_engine(DATABASE_URI)
        connection = engine.connect()
        connection.close()
        print(Fore.GREEN + "Conexiunea la baza de date a fost realizată cu succes.")
    except OperationalError as e:
        print(Fore.RED + f"Nu s-a putut conecta la baza de date: {e}")

    db.init_app(app)
