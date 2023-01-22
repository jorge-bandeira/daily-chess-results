from main import app, getdata
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

@app.route('/report', methods = ['POST'])
def report():
	form = MainForm()
	print(form.errors)
	user = None
	if form.validate_on_submit():
		user = form.user.data
		max_games = form.max_games.data
		time_class_list = []
		if form.rapid.data:
			time_class_list.append('rapid')
		if form.blitz.data:
			time_class_list.append('blitz')
		if form.bullet.data:
			time_class_list.append('bullet')
		qty_div, qly_div, corr_div, white_op_div, black_op_div, count, insights = getdata.getData(user, max_games, time_class_list)
		if qly_div == 'error':
			return render_template('error.html')
		else:
			return render_template('report.html',
				user = user,
				qty_div = qty_div,
				qly_div = qly_div,
				corr_div = corr_div,
				white_op_div = white_op_div,
				black_op_div = black_op_div,
				count = count,
				insights = insights
				)