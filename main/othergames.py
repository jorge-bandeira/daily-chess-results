import requests, json
import dateutil.relativedelta
from datetime import date

#request structure
chess_api_url = "https://api.chess.com/pub/player/"

#get a string for every month to consider
def defineMonths(n):
	months = []
	months_to_consider = n - 1
	today = date.today()
	current_month = today.strftime("%Y/%m")
	months.append(current_month)
	i = 1
	while i <= months_to_consider:
		m = today - dateutil.relativedelta.relativedelta(months = i)
		months.append(m.strftime("%Y/%m"))
		i += 1
	return months

#make API request
def createRequest(url):
	request = requests.get(url)
	if request.status_code == 404:
		print("404 error")
		return 'error'
	else:
		response = request.text
		return response

def getData(user, n_months):
	months = defineMonths(n_months)
	archive = []
	for m in months:
		url = chess_api_url + user + "/games/" + m[0:4] + "/" + m[5:7]
		response_data = createRequest(url)
		if response_data != "error":
			games_data = json.loads(response_data)
			for game in games_data['games']:
				game_dict = {
					'id': game['uuid'],
					'end_time': game['end_time'],
					'rules': game['rules'],
					'time_control': game['time_control'],
					'rated': game['rated'],
					'white_name': game['white']['username'],
					'white_rating': game['white']['rating'],
					'white_result': game['white']['result'],
					'black_name': game['black']['username'],
					'black_rating': game['black']['rating'],
					'black_result': game['black']['result']
				}
				archive.append(game_dict)
	# with open("response.txt", "w") as text_file:
	# 	for r in archive:
	# 		print(r, file = text_file)
	return archive