import requests, ndjson, plotly
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

#request structure
api_url = "https://lichess.org/api/games/user/"

headers = {
	"Accept": "application/x-ndjson"
}

def getData(user, max, time_control):
	time_control_string = ','.join(time_control)
	params = {
	"max": str(max),
	"rated": "true",
	"perfType": time_control_string,
	"pgnInJson": "false"
	}
	url = api_url + user
	games_response = createRequest(url, headers, params)
	if games_response == 'error':
		return 'error', 'error', 'error'
	else:
		gdata = ndjson.loads(games_response)
		games = getGames(gdata)
		df = createDf(games, user)
		games_count = len(df.index)
		rating_div = createRateDiffDf(df)
		num_div = createGamesNumDf(df)
		scatter_div = createScatterDf(df)
		insights = getInsights(df)
		return rating_div, num_div, scatter_div, games_count, insights

#api request
def createRequest(url, headers, params):
	r = requests.get(url, headers = headers, params = params)
	if r.status_code == 404:
		print('404 error')
		return 'error'
	else:
		games_response = r.text
		return games_response
	

#create list of games
def getGames(data):
	games = []
	for g in data:
		try:
			gdict = {
			"id": g['id'],
			"rated": g['rated'],
			"variant": g['variant'],
			"speed": g['speed'],
			"date": g['createdAt'],
			"white": g['players']['white']['user']['name'],
			"black": g['players']['black']['user']['name'],
			"white_rating": g['players']['white']['rating'],
			"white_rating_diff": g['players']['white']['ratingDiff'],
			"black_rating": g['players']['black']['rating'],
			"black_rating_diff": g['players']['black']['ratingDiff'],
			"status": g['status']
			}
			games.append(gdict)
		except:
			print("data error")
			continue
	return games	

#create pandas dataframe
def createDf(games, user):
	df_games = pd.DataFrame(games)

	#change date format
	df_games['date'] = pd.to_datetime(df_games['date'], unit="ms")
	df_games['day_of_week'] = df_games['date'].dt.day_name()
	df_games['hour'] = df_games['date'].dt.hour

	#add morning 6 - 12 / afternoon 12 - 20 / night 20 - 5
	conditions = [
		(df_games['hour'] > 5) & (df_games['hour'] <= 12),
		(df_games['hour'] > 12) & (df_games['hour'] <= 20),
		(df_games['hour'] > 20)
	]
	choices = ['morning', 'afternoon', 'night']
	df_games['time_of_day'] = np.select(conditions, choices, default='error')

	#add user result
	df_games['user_color'] = np.where(df_games['white'] == user, "white", "black")
	df_games['user_rate_diff'] = np.where(df_games['white'] == user, df_games['white_rating_diff'], df_games['black_rating_diff'])
	return df_games

#rating heatmap
def createRateDiffDf(df):
	heatMap_df = df[['day_of_week', 'hour', 'user_rate_diff']]
	heatMap_df = heatMap_df.groupby(['day_of_week', 'hour'])['user_rate_diff'].sum().reset_index()
	heatMap_df['day_of_week'] = pd.Categorical(
		heatMap_df['day_of_week'],
		categories = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday', 'Sunday'],
		ordered = True
		)
	heatMap_df = heatMap_df.sort_values('day_of_week')
	x = heatMap_df['hour']
	y = heatMap_df['day_of_week']
	z = heatMap_df['user_rate_diff']
	heatMap_fig = go.Figure(data=go.Heatmap(x=x, y=y, z=z, colorscale='Viridis', hoverongaps=False))
	heatMap_fig.update_layout(
		title = 'Daily Chess Rating Change',
	    xaxis_title="Hour of Day",
	    xaxis_showgrid = False,
	    yaxis_showgrid = False,
	    xaxis_zeroline = False,
	    yaxis_zeroline = False,
	    paper_bgcolor='rgba(0,0,0,0)',
	    plot_bgcolor='rgba(0,0,0,0)',
	    font = dict(color = 'white')
		)
	heatMap_fig.update_xaxes(type='category', autorange='reversed')
	plot_div = plotly.io.to_html(heatMap_fig, include_plotlyjs=True, full_html=False)
	return plot_div

#number of games heatmap
def createGamesNumDf(df):
	heatMap_n_df = df[['day_of_week', 'hour', 'user_rate_diff']]
	heatMap_n_df = heatMap_n_df.groupby(['day_of_week', 'hour'])['user_rate_diff'].count().reset_index()
	heatMap_n_df['day_of_week'] = pd.Categorical(
		heatMap_n_df['day_of_week'],
		categories = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday', 'Sunday'],
		ordered = True
		)
	heatMap_n_df = heatMap_n_df.sort_values('day_of_week')
	heatMap_n_df.rename(columns = {'user_rate_diff':'num_games'}, inplace=True )
	x = heatMap_n_df['hour']
	y = heatMap_n_df['day_of_week']
	z = heatMap_n_df['num_games']
	heatMap_n_fig = go.Figure(data=go.Heatmap(x=x, y=y, z=z, colorscale='Viridis', hoverongaps=False))
	heatMap_n_fig.update_layout(
		title = 'Daily Chess Games',
	    xaxis_title="Hour of Day",
	    xaxis_showgrid = False,
	    yaxis_showgrid = False,
	    xaxis_zeroline = False,
	    yaxis_zeroline = False,
	    paper_bgcolor='rgba(0,0,0,0)',
	    plot_bgcolor='rgba(0,0,0,0)',
	    font = dict(color = 'white')
		)
	heatMap_n_fig.update_xaxes(type='category', autorange='reversed')
	plot_div_n = plotly.io.to_html(heatMap_n_fig, include_plotlyjs=True, full_html=False)
	return plot_div_n

#number of games vs rating diff
def createScatterDf(df):
	scatterDf = df
	scatterDf['day'] = df['date'].dt.date
	scatterDf = scatterDf[['day', 'user_rate_diff']]
	scatterDf = scatterDf.groupby('day').agg({'user_rate_diff':['count', 'sum']})
	scatterDf.columns = ['games_num', 'rating_change']
	scatterDf = scatterDf.reset_index()
	correlation = scatterDf['games_num'].corr(scatterDf['rating_change'])
	scatterFig = px.scatter(scatterDf, x='games_num', y='rating_change', color='rating_change', color_continuous_scale=px.colors.sequential.Viridis)
	scatterFig.update_layout(
		title = 'Rating Change vs Number of Games',
		xaxis_title = 'Number of games',
		yaxis_title = 'Rating change',
		xaxis_showgrid = False,
	    yaxis_showgrid = False,
	    xaxis_zeroline = False,
	    yaxis_zeroline = False,
		paper_bgcolor='rgba(0,0,0,0)',
	    plot_bgcolor='rgba(0,0,0,0)',
	    font = dict(color = 'white')
		)
	scatterFig.update_coloraxes(showscale=False)
	scatter_div = plotly.io.to_html(scatterFig, include_plotlyjs=True, full_html=False)
	return scatter_div

def getInsights(df):
	weekend_num = df[(df.day_of_week == "Saturday") | (df.day_of_week == "Sunday")].count()["id"]
	week_num = df[(df.day_of_week != "Saturday") & (df.day_of_week != "Sunday")].count()["id"]
	weekend_rate_diff = df[(df.day_of_week == "Saturday") | (df.day_of_week == "Sunday")].sum()["user_rate_diff"]
	week_rate_diff = df[(df.day_of_week != "Saturday") & (df.day_of_week != "Sunday")].sum()["user_rate_diff"]
	
	morning_num = df[df.time_of_day == "morning"].count()["id"]
	afternoon_num = df[df.time_of_day != "afternoon"].count()["id"]
	night_num = df[df.time_of_day != "night"].count()["id"]
	
	morning_rate_diff = df[df.time_of_day == "morning"].sum()["user_rate_diff"]
	afternoon_rate_diff = df[df.time_of_day != "afternoon"].sum()["user_rate_diff"]
	night_rate_diff = df[df.time_of_day != "night"].sum()["user_rate_diff"]

	performance_weekend = weekend_rate_diff / weekend_num
	performance_week = week_rate_diff / week_num
	
	performance_morning = morning_rate_diff / morning_num
	performance_afternoon = afternoon_rate_diff / afternoon_num
	performance_night = night_rate_diff / night_num

	max_day = getMaxGames(df)
	best_day = getBestDay(df)

	insights = {
		'performance_week': round(performance_week, 2),
		'performance_weekend': round(performance_weekend,2),
		'performance_morning': round(performance_morning,2),
		'performance_afternoon': round(performance_afternoon,2),
		'performance_night': round(performance_night,2),
		'max_day': max_day,
		'best_day': best_day
	}
	return insights

def getMaxGames(df):
	max_n_df = df[['day_of_week','user_rate_diff']]
	max_n_df = max_n_df.groupby(['day_of_week'])['user_rate_diff'].count().reset_index()
	max_n_df = max_n_df.loc[max_n_df['user_rate_diff'].idxmax()]
	max_day = max_n_df['day_of_week']
	return max_day

def getBestDay(df):
	best_df = df[['day_of_week','user_rate_diff']]
	best_df = best_df.groupby(['day_of_week'])['user_rate_diff'].sum().reset_index()
	best_df = best_df.loc[best_df['user_rate_diff'].idxmax()]
	best_day = best_df['day_of_week']
	return best_day