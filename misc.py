# misc.py
import json

with open('settings.json', 'r') as f:
  config = json.load(f)
SSL_CONTEXT = (config['ssl_context']['cert'], config['ssl_context']['key'])
ALLOWED_TERMS = config['allowed_terms']