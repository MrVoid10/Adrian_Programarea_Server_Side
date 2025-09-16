from flask import Flask, request, render_template
from flask_jwt_extended import JWTManager
from Modules.misc import SSL_CONTEXT,JWT_SECRET_KEY
from Modules.api import api
from Modules.Auth import auth

app = Flask(__name__)
#CORS(app)
app.config['DEBUG'] = False

app.register_blueprint(api, url_prefix="/")
app.register_blueprint(auth, url_prefix="/")

app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY 
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600  # o ora
jwt = JWTManager(app)

@app.route('/')
@app.route('/home')
def home():
  if request.method == 'GET':
    return render_template('index.html')

if __name__ == '__main__':
  app.run(ssl_context=SSL_CONTEXT)