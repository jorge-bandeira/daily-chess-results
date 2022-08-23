from main import app, games
from main.forms import MainForm
from flask import render_template

@app.context_processor
def base():
	form = MainForm()
	return dict(form=form)

@app.route('/')
@app.route('/home')
def home():
	return render_template('home.html')

@app.route('/results', methods = ['POST'])
def results():
	form = MainForm()
	print(form.errors)
	user = None
	if form.validate_on_submit():
		user = form.user.data
		max_games = form.max_games.data
		form.user.data = ''
		games.getData(user, max_games)
		return render_template('results.html', user = user, max_games = max_games)
	else:
		return render_template('error.html')