import requests
import dateutil.relativedelta
from datetime import date

#request structure
chess_api_url = "https://api.chess.com/pub/player/"

def defineMonths():
	months = []
	months_to_consider = 3
	today = date.today()
	current_month = today.strftime("%Y/%m")
	months.append(current_month)
	i = 1
	while i <= months_to_consider:
		m = today - dateutil.relativedelta.relativedelta(months = i)
		months.append(m.strftime("%Y/%m"))
		i += 1
	print(months)
	return months

def getData(user, max, time_control):
	url = chess_api_url + user
