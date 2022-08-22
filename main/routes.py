from main import app
from main.forms import MainForm
from flask import render_template

@app.route('/')
@app.route('/home', methods=['GET', 'POST'])
def home():
	user = None
	form = MainForm()
	if form.validate_on_submit():
		user = form.user.data
		form.user.data = ''
	print("home")
	return render_template('home.html', user = user, form = form)

@app.route('/results')
def results():
	print("results")
	return render_template('results.html')
