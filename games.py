import requests, ndjson

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

games_request = requests.get(api_url + "Zee_Haddock", headers = headers, params = params).text
gdata = ndjson.loads(games_request)

print(gdata)
