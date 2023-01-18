import requests, json, datetime, plotly
import dateutil.relativedelta
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

#request structure
chess_api_url = "https://api.chess.com/pub/player/"

draw_results = ['agreed', 'repetition', 'stalemate', 'insuficient', '50move', 'timevsinsuficient']
loss_results = ['checkmated', 'resigned', 'lose', 'abandoned']

#get a string for every month to consider
# def defineMonths(n):
# 	months = []
# 	months_to_consider = n - 1
# 	today = datetime.date.today()
# 	current_month = today.strftime("%Y/%m")
# 	months.append(current_month)
# 	i = 1
# 	while i <= months_to_consider:
# 		m = today - dateutil.relativedelta.relativedelta(months = i)
# 		months.append(m.strftime("%Y/%m"))
# 		i += 1
# 	return months

#make API request
def createRequest(url):
	request = requests.get(url)
	if request.status_code == 404:
		print("404 error")
		return 'error'
	else:
		response = request.text
		return response

def getArchives(user):
	url = chess_api_url + user + '/games/archives'
	archives_response = createRequest(url)
	archives_list = json.loads(archives_response)['archives']
	return archives_list

def getData(user, max_games, time_class_list):
	if len(time_class_list) == 0:
		time_class_list.append('rapid')
		time_class_list.append('blitz')
		time_class_list.append('bullet')
	archives = getArchives(user)
	archives = archives[::-1] #Reverse list
	game_list = []
	games_count = 0
	error_count = 0	
	for a in archives:
		if games_count == max_games:
			break
		response_data = createRequest(a)
		if response_data != "error":
			games_data = json.loads(response_data)
			for game in games_data['games']:
				if games_count == max_games:
					break
				try:
					if game['time_class'] in time_class_list and game['rated'] and game['rules'] == 'chess':			
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
						print(games_count)
					else:
						continue
				except:
					error_count += 1
					print(error_count)
					continue
	# with open("response.txt", "w") as text_file:
	# 	for r in archive:
	# 		print(r, file = text_file)
	qty_div, qly_div, corr_div, white_op_div, black_op_div = createDf(user, game_list)
	return qty_div, qly_div, corr_div, white_op_div, black_op_div, games_count

def createDf(user, archive):
	archive_df = pd.DataFrame(archive)
	archive_df['end_time'] = pd.to_datetime(archive_df['end_time'], unit='s') #change date from epoch value to yyyymmdd hhmmss
	archive_df['day_of_week'] = archive_df['end_time'].dt.day_name() 		  #get day of week
	archive_df['hour'] = archive_df['end_time'].dt.strftime('%H').add(':00')  #get hour
	archive_df['user_color'] = np.where(archive_df['white_name'] == user, 'white', 'black') #set user color
	archive_df['user_result'] = np.where(archive_df['user_color'] == 'white', archive_df['white_result'], archive_df['black_result'])
	archive_df = archive_df.sort_values(by='end_time', ascending = False)
	# archive_df.to_csv('chess_data.csv', encoding = 'utf-8', index = False)
	qty_div = quantityDf(archive_df)
	qly_div = qualityDf(archive_df)
	corr_div = correlationDf(archive_df)
	white_op_div = whiteOpeningsDf(archive_df)
	black_op_div = blackOpeningsDf(archive_df)
	return qty_div, qly_div, corr_div, white_op_div, black_op_div

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
		title = 'Daily Chess Games',
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
		title = 'Daily Chess Win Rate',
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

def correlationDf(df):
	df['date'] = df['end_time'].dt.date
	df = df.groupby(['date'], as_index = False).agg({'user_result':[('n','count'),('wins', lambda x:len(x[x == 'win']))]})
	df.columns = df.columns.droplevel()	
	df.columns = ['date', 'n_games', 'n_wins']
	df['win_rate'] = round(df['n_wins'] / df['n_games'],2)
	corrFig = px.scatter(df, x='n_games', y='win_rate', color='win_rate', color_continuous_scale=px.colors.sequential.Viridis, trendline='ols')
	corrFig.update_layout(
		title = 'Win Rate vs Games Played',
		xaxis_title = 'Number of games',
		yaxis_title = 'Win rate',
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
	corrFig.update_coloraxes(showscale=False)
	corr_div = plotly.io.to_html(corrFig, include_plotlyjs=True, full_html=False, config={'displayModeBar': False})
	return corr_div

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
	# df['win_rate'] = round(df['user_result']['wins'] / df['user_result']['n'] * 100, 2)
	# df['draw_rate'] = round(df['user_result']['draws'] / df['user_result']['n'] * 100, 2)
	# df['lose_rate'] = round(df['user_result']['losses'] / df['user_result']['n'] * 100, 2)
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
	# df['win_rate'] = round(df['user_result']['wins'] / df['user_result']['n'] * 100, 2)
	# df['draw_rate'] = round(df['user_result']['draws'] / df['user_result']['n'] * 100, 2)
	# df['lose_rate'] = round(df['user_result']['losses'] / df['user_result']['n'] * 100, 2)
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