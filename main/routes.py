from main import app
from flask import render_template

@app.route('/')
@app.route('/home')
def home():
	print("home")
	return render_template('home.html')

@app.route('/results')
def results():
	print("results")
	return render_template('results.html')
