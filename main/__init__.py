import os
from flask import Flask

app = Flask(__name__)

from main import routes

if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
	print("running...")