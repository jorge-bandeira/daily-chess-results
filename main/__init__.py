import os
from flask import Flask

app = Flask(__name__)

secret_key = os.urandom(32)
app.config['SECRET_KEY'] = secret_key

from main import routes

if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
	print("running...")