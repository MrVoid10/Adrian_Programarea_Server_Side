from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from Modules.misc import SSL_CONTEXT,JWT_SECRET_KEY
from Modules.api import api
from Modules.Auth import auth
from Modules.frontend_site import frontend_site
from Modules.file_IO import CSV_IO
from Modules.DBConn import init_db
from Modules.jwt_utils import init_jwt
app = Flask(__name__)
CORS(app)
app.config['DEBUG'] = False

app.register_blueprint(api, url_prefix="/")
app.register_blueprint(auth, url_prefix="/")
app.register_blueprint(frontend_site, url_prefix="/data")
app.register_blueprint(CSV_IO, url_prefix="/csv")

app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY 
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600  # o ora
jwt = JWTManager(app)
init_db(app)
init_jwt(app)
if __name__ == '__main__':
  app.run(ssl_context=SSL_CONTEXT)