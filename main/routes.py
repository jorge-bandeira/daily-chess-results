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
		time_control = []
		if form.classical.data:
			time_control.append('classical')
		if form.rapid.data:
			time_control.append('rapid')
		if form.blitz.data:
			time_control.append('blitz')
		if form.bullet.data:
			time_control.append('bullet')
		
		if len(time_control) == 0:
			noControl = True
			return render_template('home.html', noControl = noControl)
		else:
			rating_div, num_div, scatter_div, count = games.getData(user, max_games, time_control)
			if rating_div == 'error':
				return render_template('error.html')
			else:
				return render_template('results.html',
				 user = user,
				 max_games = max_games,
				 rating_div = rating_div,
				 num_div = num_div,
				 scatter_div = scatter_div,
				 count = count)
	else:
		return render_template('error.html')