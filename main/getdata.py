import requests, json, datetime, plotly, re
import dateutil.relativedelta
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from sklearn.linear_model import LinearRegression

#request structure
chess_api_url = "https://api.chess.com/pub/player/"

#map meaning of results returned from the API
draw_results = ['agreed', 'repetition', 'stalemate', 'insuficient', '50move', 'timevsinsuficient']
loss_results = ['checkmated', 'resigned', 'lose', 'abandoned']

#make API request
def createRequest(url):
	request = requests.get(url)
	if request.status_code == 404:
		print("404 error")
		return 404
	else:
		response = request.text
		return response

#get all archives available for the user (one per month)
def getArchives(user):
	url = chess_api_url + user + '/games/archives'
	archives_response = createRequest(url)
	if archives_response == 404:
		return 404
	elif archives_response == 500:
		return 500
	archives_list = json.loads(archives_response)['archives']
	return archives_list

#main function to be called by the route
def getData(user, max_games, time_class_list):
	#set all time_classes if no time class was selected by the user 
	if len(time_class_list) == 0:
		time_class_list.append('rapid')
		time_class_list.append('blitz')
		time_class_list.append('bullet')
	
	archives = getArchives(user)
	if archives == 404:
		return 404
	archives = archives[::-1] #Reverse list
	game_list = []
	games_count = 0
	error_count = 0	
	for a in archives:
		#stop requesting archives if the requested number of games has been reached
		if games_count == max_games:
			break
		response_data = createRequest(a)
		if response_data != "error":
			games_data = json.loads(response_data) #load archive into a dict
			for game in games_data['games']:
				#stop loop if number of games is reached
				if games_count == max_games:
					break
				try:
					if game['time_class'] in time_class_list and game['rated'] and game['rules'] == 'chess':			
						#get opening name
						pgn = game['pgn']
						start_string = 'ECOUrl "https://www.chess.com/openings/'
						start = pgn.find(start_string) + len(start_string)
						end = pgn.find('UTCDate') - 4
						opening = pgn[start:end]
						opening = opening.replace('-',' ')
						
						game_dict = {
							'id': game['uuid'],
							'end_time': game['end_time'],
							'rules': game['rules'],
							'time_class': game['time_class'],
							'rated': game['rated'],
							'white_name': game['white']['username'],
							'white_rating': game['white']['rating'],
							'white_result': game['white']['result'],
							'black_name': game['black']['username'],
							'black_rating': game['black']['rating'],
							'black_result': game['black']['result'],
							'opening': opening
						}
						game_list.append(game_dict)
						games_count += 1
					else:
						continue
				except:
					error_count += 1
					print(error_count)
					continue

	qty_div, qly_div, corr_div, white_op_div, black_op_div, insights = createDf(user, game_list)
	data_response = {
		'count': games_count,
		'qty_div':qty_div,
		'qly_div':qly_div,
		'corr_div':corr_div,
		'white_op_div':white_op_div,
		'black_op_div':black_op_div,
		'insights':insights
	}
	return data_response

def createDf(user, archive):
	archive_df = pd.DataFrame(archive)
	archive_df['end_time'] = pd.to_datetime(archive_df['end_time'], unit='s') #change date from epoch value to yyyymmdd hhmmss
	archive_df['day_of_week'] = archive_df['end_time'].dt.day_name() 		  #get day of week
	archive_df['hour'] = archive_df['end_time'].dt.hour  #get hour

	#add time of day
	conditions = [
		(archive_df['hour'] > 5) & (archive_df['hour'] <= 12),
		(archive_df['hour'] > 12) & (archive_df['hour'] <= 20),
		(archive_df['hour'] > 20) | (archive_df['hour'] <= 5)
	]
	choices = ['morning', 'afternoon', 'night']
	archive_df['time_of_day'] = np.select(conditions, choices, default="error")

	archive_df['hour'] = archive_df['end_time'].dt.strftime('%H').add(':00') #set hour to HH:MM format

	archive_df['user_color'] = np.where(archive_df['white_name'] == user, 'white', 'black') #set user color

	#set user result
	archive_df['user_result'] = np.where(archive_df['user_color'] == 'white', archive_df['white_result'], archive_df['black_result'])
	
	archive_df = archive_df.sort_values(by='end_time', ascending = False)
	qty_div = quantityDf(archive_df)
	qly_div = qualityDf(archive_df)
	corr_div = correlationDf(archive_df)
	white_op_div = whiteOpeningsDf(archive_df)
	black_op_div = blackOpeningsDf(archive_df)
	insights = getInsights(archive_df)
	return qty_div, qly_div, corr_div, white_op_div, black_op_div, insights

#generate heatmap with qty of games per day of week
def quantityDf(df):
	df = df.groupby(['day_of_week', 'hour']).size().reset_index(name='n')
	df['day_of_week'] = pd.Categorical(
		df['day_of_week'],
		categories = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday', 'Sunday'],
		ordered = True
		)
	df = df.sort_values('day_of_week')
	heatmap_quantity = heatmap(df['hour'], df['day_of_week'], df['n'])
	heatmap_quantity.update_layout(
		title = 'Daily chess games',
	    xaxis_title="Hour of Day",
	    xaxis_showgrid = False,
	    yaxis_showgrid = False,
	    xaxis_zeroline = False,
	    yaxis_zeroline = False,
	    paper_bgcolor='rgba(0,0,0,0)',
	    plot_bgcolor='rgba(0,0,0,0)',
	    font = dict(color = 'white'),
	    xaxis_fixedrange = True,
	    yaxis_fixedrange = True
		)
	return plotly.io.to_html(heatmap_quantity, include_plotlyjs=True, full_html=False, config={'displayModeBar': False})

#generate heatmap with win rate per day of week
def qualityDf(df):
	df = df.groupby(['day_of_week', 'hour'], as_index = False).agg({'user_result':[('n','count'),('wins', lambda x:len(x[x == 'win']))]})
	df.columns = df.columns.droplevel()	
	df.columns = ['day_of_week', 'hour', 'n_games', 'n_wins']
	df['win_rate'] = round(df['n_wins'] / df['n_games'],2)
	df['day_of_week'] = pd.Categorical(
		df['day_of_week'],
		categories = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday', 'Sunday'],
		ordered = True
		)
	df = df.sort_values('day_of_week')
	heatmap_quality = heatmap(df['hour'], df['day_of_week'], df['win_rate'])
	heatmap_quality.update_layout(
		title = 'Daily chess win rate',
	    xaxis_title="Hour of Day",
	    xaxis_showgrid = False,
	    yaxis_showgrid = False,
	    xaxis_zeroline = False,
	    yaxis_zeroline = False,
	    paper_bgcolor='rgba(0,0,0,0)',
	    plot_bgcolor='rgba(0,0,0,0)',
	    font = dict(color = 'white'),
	    xaxis_fixedrange = True,
	    yaxis_fixedrange = True
		)
	return plotly.io.to_html(heatmap_quality, include_plotlyjs=True, full_html=False, config={'displayModeBar': False})

def heatmap(x, y, z):
	x_order = ['06:00','07:00','08:00','09:00','10:00','11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00',
			'18:00', '19:00', '20:00', '21:00', '22:00', '23:00', '00:00', '01:00', '02:00', '03:00', '04:00', '05:00']
	heatmap = go.Figure(data=go.Heatmap(x=x, y=y, z=z, colorscale='Viridis', hoverongaps=False))
	heatmap.update_xaxes(categoryarray = x_order)
	return heatmap

#generate plot with win rate and games played by date and time control
def correlationDf(df): 
	df['date'] = df['end_time'].dt.date
	df = df.groupby(['date', 'time_class'], as_index = False).agg({'user_result':[('n','count'),('wins', lambda x:len(x[x == 'win']))]})
	df.columns = df.columns.droplevel()	
	df.columns = ['date', 'time_class', 'n_games', 'n_wins']
	df['win_rate'] = round(df['n_wins'] / df['n_games'],2)
	
	#convert date to timestamps so the linear regression can be applied
	df['timestamp'] = pd.to_datetime(df['date']).astype(np.int64) / 10**9
	
	#separate df per time class for linear regression data	
	bulletDf = df[df['time_class'] == 'bullet']
	blitzDf = df[df['time_class'] == 'blitz']
	rapidDf = df[df['time_class'] == 'rapid']

	#Linear regression model for win rate trendline
	bulletCheck = bulletDf.shape[0]
	model_bullet = None
	if bulletCheck > 0:
		x_bullet = bulletDf['timestamp'].values.reshape(-1,1)
		y_bullet = bulletDf['win_rate']
		model_bullet = LinearRegression().fit(x_bullet,y_bullet)

	blitzCheck = blitzDf.shape[0]
	model_blitz = None
	if blitzCheck > 0:
		x_blitz = blitzDf['timestamp'].values.reshape(-1,1)
		y_blitz = blitzDf['win_rate']
		model_blitz = LinearRegression().fit(x_blitz,y_blitz)

	rapidCheck = rapidDf.shape[0]
	model_rapid = None
	if rapidCheck > 0:
		x_rapid = rapidDf['timestamp'].values.reshape(-1,1)
		y_rapid = rapidDf['win_rate']
		model_rapid = LinearRegression().fit(x_rapid,y_rapid)

	corrFig = px.scatter(df, x='date', 
		y='win_rate', 
		color='time_class', 
		size='n_games', 
		color_discrete_map={'bullet':'#00CC96', 'blitz':'#4E57BA', 'rapid':'#B04535'})
	
	if model_bullet != None:
		corrFig.add_shape(
			type = 'line',
			x0=bulletDf['date'].min(),
	    	x1=bulletDf['date'].max(),
	    	y0=model_bullet.intercept_ + model_bullet.coef_[0] * bulletDf['timestamp'].min(),
	    	y1=model_bullet.intercept_ + model_bullet.coef_[0] * bulletDf['timestamp'].max(),
	    	yref='y',
	    	line=dict(
	    		color = '#00CC96',
	    		dash = 'dash'
	    		)
			)

	if model_blitz != None:
		corrFig.add_shape(
			type = 'line',
			x0=blitzDf['date'].min(),
	    	x1=blitzDf['date'].max(),
	    	y0=model_blitz.intercept_ + model_blitz.coef_[0] * blitzDf['timestamp'].min(),
	    	y1=model_blitz.intercept_ + model_blitz.coef_[0] * blitzDf['timestamp'].max(),
	    	yref='y',
	    	line=dict(
	    		color = '#4E57BA',
	    		dash = 'dash'
	    		)
			)
	if model_rapid != None:
		corrFig.add_shape(
			type = 'line',
			x0=rapidDf['date'].min(),
	    	x1=rapidDf['date'].max(),
	    	y0=model_rapid.intercept_ + model_rapid.coef_[0] * rapidDf['timestamp'].min(),
	    	y1=model_rapid.intercept_ + model_rapid.coef_[0] * rapidDf['timestamp'].max(),
	    	yref='y',
	    	line=dict(
	    		color = '#B04535',
	    		dash = 'dash'
	    		)
			)
	corrFig.update_layout(
		title = 'Win rate and games played by date and time control',
		xaxis_title = 'Date',
		yaxis_title = 'Win rate',
		legend_title = '',
		xaxis_showgrid = False,
	    yaxis_showgrid = False,
	    xaxis_zeroline = False,
	    yaxis_zeroline = False,
		paper_bgcolor='rgba(0,0,0,0)',
	    plot_bgcolor='rgba(0,0,0,0)',
	    font = dict(color = 'white'),
	    xaxis_fixedrange = True,
	    yaxis_fixedrange = True
		)
	corrFig.update_coloraxes(showscale=True)
	corr_div = plotly.io.to_html(corrFig, include_plotlyjs=True, full_html=False, config={'displayModeBar': False})
	return corr_div

#generate bar plot with top 10 openings played as white
def whiteOpeningsDf(df):
	color_filter = df['user_color'] == 'white'
	df = df[color_filter]
	df['opening'] = df['opening'].apply(lambda x: ' '.join(x.split()[:2]))
	df = df.groupby(['opening']).agg({'user_result':[
		('n', 'count'),
		('wins', lambda x:len(x[x=='win'])),
		('draws', lambda x:len(x[x.isin(draw_results)])),
		('losses', lambda x:len(x[x.isin(loss_results)]))
		]}).sort_values(('user_result','n'), ascending=False)

	df = df.reset_index().loc[0:9]
	df.drop(('user_result','n'), axis = 1, inplace = True)
	df.columns = df.columns.droplevel()	
	df.columns = ['opening', 'wins', 'draws', 'losses']
	df = pd.melt(df, id_vars = 'opening', var_name = 'result', value_name = 'count')
	
	fig = px.bar(df, x = df['opening'], y = df['count'], color = df['result'])
	fig.update_layout(
		title = 'Top 10 openings played with white',
		xaxis_title = 'Opening',
		yaxis_title = '',
		legend_title = '',
		xaxis_showgrid = False,
	    yaxis_showgrid = False,
	    xaxis_zeroline = False,
	    yaxis_zeroline = False,
		paper_bgcolor='rgba(0,0,0,0)',
	    plot_bgcolor='rgba(0,0,0,0)',
	    font = dict(color = 'white'),
	    xaxis_fixedrange = True,
	    yaxis_fixedrange = True
		)
	div = plotly.io.to_html(fig, include_plotlyjs=True, full_html=False, config={'displayModeBar': False})
	return div

#generate bar plot with top 10 openings played as black
def blackOpeningsDf(df):
	color_filter = df['user_color'] == 'black'
	df = df[color_filter]
	df['opening'] = df['opening'].apply(lambda x: ' '.join(x.split()[:2]))
	df = df.groupby(['opening']).agg({'user_result':[
		('n', 'count'),
		('wins', lambda x:len(x[x=='win'])),
		('draws', lambda x:len(x[x.isin(draw_results)])),
		('losses', lambda x:len(x[x.isin(loss_results)]))
		]}).sort_values(('user_result','n'), ascending=False)

	df = df.reset_index().loc[0:9]
	df.drop(('user_result','n'), axis = 1, inplace = True)
	df.columns = df.columns.droplevel()	
	df.columns = ['opening', 'wins', 'draws', 'losses']
	df = pd.melt(df, id_vars = 'opening', var_name = 'result', value_name = 'count')
	
	fig = px.bar(df, x = df['opening'], y = df['count'], color = df['result'])
	fig.update_layout(
		title = 'Top 10 openings played with black',
		xaxis_title = 'Opening',
		yaxis_title = '',
		legend_title = '',
		xaxis_showgrid = False,
	    yaxis_showgrid = False,
	    xaxis_zeroline = False,
	    yaxis_zeroline = False,
		paper_bgcolor='rgba(0,0,0,0)',
	    plot_bgcolor='rgba(0,0,0,0)',
	    font = dict(color = 'white'),
	    xaxis_fixedrange = True,
	    yaxis_fixedrange = True
		)
	div = plotly.io.to_html(fig, include_plotlyjs=True, full_html=False, config={'displayModeBar': False})
	return div

def getInsights(df):
	weekend_count = df[(df.day_of_week == "Saturday") | (df.day_of_week == "Sunday")].count()["id"]
	weekend_count_wins = df[(df.user_result == "win")][(df.day_of_week == "Saturday") | (df.day_of_week == "Sunday")].count()["id"]
	weekend_performance = round(weekend_count_wins / weekend_count, 2)

	week_count = df[(df.day_of_week != "Saturday") & (df.day_of_week != "Sunday")].count()["id"]
	week_count_wins = df[(df.user_result == "win")][(df.day_of_week != "Saturday") | (df.day_of_week != "Sunday")].count()["id"]
	week_performance = round(week_count_wins / week_count, 2)

	max_count, min_count = getMaxGames(df)
	best_time, worst_time = getBestGames(df)	

	insights = {
			'max_count':max_count,
			'min_count':min_count,
			'best_time':best_time,
			'worst_time':worst_time,
			'week_performance':week_performance,
			'weekend_performance':weekend_performance
	}
	return insights

def getMaxGames(df):
	df = df.groupby(['day_of_week', 'time_of_day']).count()
	max_count = ' '.join(df.idxmax()['id']).lower()
	min_count = ' '.join(df.idxmin()['id']).lower()
	return max_count, min_count

def getBestGames(df):
	df = df[['day_of_week', 'time_of_day', 'user_result']]
	df = df.groupby(['day_of_week', 'time_of_day']).agg({'user_result': [('n', 'count'),('wins', lambda x:len(x[x=='win']))]})
	df['win_rate'] = round(df['user_result']['wins'] / df['user_result']['n'] * 100, 2)
	best_time = ' '.join(map(str, df.idxmax()['win_rate']))
	best_time = re.sub(r'[^\w\s]','',best_time).lower()
	worst_time = ' '.join(map(str, df.idxmin()['win_rate']))
	worst_time = re.sub(r'[^\w\s]','',worst_time).lower()
	return best_time, worst_time