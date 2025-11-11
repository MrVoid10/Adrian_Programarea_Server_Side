from flask import Flask, request, send_from_directory
from flask_jwt_extended import JWTManager
from Modules.misc import SSL_CONTEXT,JWT_SECRET_KEY,STATIC_FRONTEND_FOLDER
from Modules.api import api
from Modules.Auth import auth
from Modules.frontend_site import frontend_site
from Modules.file_IO import CSV_IO

app = Flask(__name__, static_folder=STATIC_FRONTEND_FOLDER,static_url_path='')
#CORS(app)
app.config['DEBUG'] = False

app.register_blueprint(api, url_prefix="/")
app.register_blueprint(auth, url_prefix="/")
app.register_blueprint(frontend_site, url_prefix="/data")
app.register_blueprint(CSV_IO, url_prefix="/csv")

app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY 
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600  # o ora
jwt = JWTManager(app)

@app.route('/')
@app.route('/home')
@app.route('/')
def serve_index():
  return send_from_directory(app.static_folder, 'index.html')

@app.errorhandler(404)
def handle_404(e):
  return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
  app.run(ssl_context=SSL_CONTEXT)