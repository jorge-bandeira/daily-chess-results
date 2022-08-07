import requests, ndjson
import pandas as pd
import numpy as np
from local_settings import user

#request structure
api_url = "https://lichess.org/api/games/user/"

headers = {
	"Accept": "application/x-ndjson"
}

params = {
	"max": "50",
	"rated": "true",
	"perfType": "rapid",
	"pgnInJson": "true"
}

#api request
games_request = requests.get(api_url + user, headers = headers, params = params).text
gdata = ndjson.loads(games_request)

#create list of games
games = []
for g in gdata:
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

#create pandas dataframe
df_games = pd.DataFrame(games)

#change date format
df_games['date'] = pd.to_datetime(df_games['date'], unit="ms")
df_games['day_of_week'] = df_games['date'].dt.day_name()

#add user result
df_games['user_color'] = np.where(df_games['white'] == user, "white", "black")
df_games['user_rate_diff'] = np.where(df_games['white'] == user, df_games['white_rating_diff'], df_games['black_rating_diff'])

print(df_games.head())