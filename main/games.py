import requests, ndjson
import pandas as pd
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
print(df_games)
# print(gdata[0]['pgn'])
