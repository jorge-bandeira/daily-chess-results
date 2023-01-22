from main import app, getdata
from main.forms import MainForm
from flask import render_template, abort

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
		data_response = getdata.getData(user, max_games, time_class_list)
		if data_response == 404:
			abort(404)
		count = data_response['count']
		if count == 0:
			return render_template('nogames.html')
		return render_template('report.html',
			user = user,
			qty_div = data_response['qty_div'],
			qly_div = data_response['qly_div'],
			corr_div = data_response['corr_div'],
			white_op_div = data_response['white_op_div'],
			black_op_div = data_response['black_op_div'],
			count = count,
			insights = data_response['insights']
			)

@app.errorhandler(404)
def page_not_found(error):
	return render_template('error.html'), 404