from main import app, games, othergames
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
		
		num_div, rating_div_avg, scatter_div, count, insights = games.getData(user, max_games, time_control)
		
		if num_div == 'error':
			return render_template('error.html')
		else:
			return render_template('results.html',
			 user = user,
			 max_games = max_games,
			 num_div = num_div,
			 rating_div_avg = rating_div_avg,
			 scatter_div = scatter_div,
			 count = count,
			 insights = insights
			)
	else:
		return render_template('error.html')

@app.route('/report', methods = ['POST'])
def report():
	form = MainForm()
	print(form.errors)
	user = None
	if form.validate_on_submit():
		user = form.user.data
		max_games = form.max_games.data
		print(max_games)
		qty_div, qly_div, count = othergames.getData(user, max_games)
		if qly_div == 'error':
			return render_template('error.html')
		else:
			return render_template('report.html',
				user = user,
				qty_div = qty_div,
				qly_div = qly_div,
				count = count
				)