from main import app
from flask import render_template

@app.route('/')
@app.route('/home')
def home():
	print("home")
	return render_template('home.html')
