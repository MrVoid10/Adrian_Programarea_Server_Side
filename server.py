from flask import Flask, request, render_template
from auth_jwt import init_jwt
from misc import SSL_CONTEXT
app = Flask(__name__)
#CORS(app)
app.config['DEBUG'] = True

@app.route('/')
@app.route('/home')
def home():
  if request.method == 'GET':
    return render_template('index.html')

if __name__ == '__main__':
  app.run(ssl_context=SSL_CONTEXT)