import os
from flask import Flask

app = Flask(__name__)

if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
	print("running...")