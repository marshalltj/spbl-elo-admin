import http.client
import json

server = "localhost:5000"
jsonHeader = {'Content-type': 'application/json'}

def returnRequestAsJson(method, path):
	connection = http.client.HTTPConnection(server)
	connection.request(method, path)
	response = connection.getresponse()
	resp = json.loads(response.read().decode())
	connection.close()
	return resp['data']

def addPlayerToGame(player, game, team):
	body = {'historical_elo': player['elo'], 'name':player['name']}
	jsonBody = json.dumps(body)

	connection = http.client.HTTPConnection(server)
	connection.request("POST", "/teams/" + team + "/games/" + game, jsonBody, jsonHeader)
	response = connection.getresponse()
	print(response.read().decode())
	connection.close()

def updatePlayer(player):
	body = {'elo': player['elo'], 'wins': player['wins'], 'losses':player['losses']}
	jsonBody = json.dumps(body)

	connection = http.client.HTTPConnection(server)
	connection.request("PUT", "/players/" + player['name'], jsonBody, jsonHeader)
	response = connection.getresponse()
	print(response.read().decode())
	connection.close()

def updateGame(game):
	body = {'win_team':game['win_team'], 'elo_score':game['elo_score'], 
	'map':game['map'], 'round':game['round'], 'emp_team_elo':game['emp_team_elo'], 'nr_team_elo':game['nr_team_elo']}
	jsonBody = json.dumps(body)
	
	connection = http.client.HTTPConnection(server)
	connection.request("PUT", "/events/games/" + str(game['id']), jsonBody, jsonHeader)
	response = connection.getresponse()
	print(response.read().decode())
	connection.close()

def getPlayersForTeam(team):
	players = returnRequestAsJson("GET", "/teams/" + team + "/players")
	print("\nPlayers for ", players[0]['team_name'], ":", sep="")
	for i in range(len(players)):
		print("IDX:", i, "|| Name:", players[i]['name'], "|| Elo:", players[i]['elo'])
	return players 

def getEvents():
	events = returnRequestAsJson("GET", "/events")
	print("\nEvents:")
	for event in events:
		print("Event ID:", event['id'], "|| Name:", event['name'], "|| Date:", event['date'])
	return events 

def getTeamsForEvent(event):
	teams = returnRequestAsJson("GET", "/events/" + event + "/teams/")
	print("\nTeams:")
	for team in teams:
		print("Team ID:", team['id'], "Name:", team['team_name'], "|| Captain:", team['captain'])
	return teams

def getGamesForEvent(event):
	games = returnRequestAsJson("GET", "/events/" + event + "/games")
	print("\nOutstanding Results:")
	for i in range(len(games)):
		if games[i]['elo_score'] == 0:
			print("IDX:", i, "|| Game ID:", games[i]['id'], "|| NR team:", games[i]['nr_team'], "|| Emp team:", games[i]['emp_team'])
	return games

def getTeamGameRoster(team):
	roster = getPlayersForTeam(team)
	rosterIn = ""
	print("Remove idx of players from roster to match players that played. Enter 99 when finished")
	while rosterIn != 99:
		rosterIn = int(input())
		if rosterIn != 99:
			print("Player", roster.pop(rosterIn)['name'], "removed")

	return roster

def calculateTeamElo(roster):
	sum = 0
	for player in roster:
		sum += player['elo']
	avg = round(sum / len(roster))
	print(roster[0]['team_name'], "average elo:", avg)
	return avg

def calculateEloChange(winnerElo, loserElo):
	winChance = 1.0 /(1 + 10**((loserElo - winnerElo)/400.0))  
	delta = round(32 * (1 - winChance))
	print("Elo change of team rated", winnerElo, "beating team rated", loserElo, "is:", delta)
	return delta

def addGameResults():
	events = getEvents()
	event = input("\nEnter ID to get games teams and games from event: ")
	getTeamsForEvent(event)
	games = getGamesForEvent(event)
	gameIdx = int(input("\nEnter idx of game to post results for: "))
	game = games[gameIdx]
	print("Modifying Game ID:",game['id'])
	winner = input("Enter winning team ID: ")
	gameRound = int(input("Enter round #: "))
	gameMap = input("Enter map: ")

	loser = ""
	if int(winner) == game['nr_team']:
		loser = game['emp_team']
		
	else:
		loser = game['nr_team']

	print("Losing team ID:", loser, "Winning team ID:", winner)
	winningTeamRoster = getTeamGameRoster(winner)
	losingTeamRoster = getTeamGameRoster(str(loser))

	winningTeamAvgElo = calculateTeamElo(winningTeamRoster)
	losingTeamAvgElo = calculateTeamElo(losingTeamRoster)
	eloChange = calculateEloChange(winningTeamAvgElo, losingTeamAvgElo)

	warning = input("WARNING: Please check above output. If something is off, type QUIT to cancel this operation before sending changes to the database")
	if warning == "QUIT":
		return
		
	for player in winningTeamRoster:
		addPlayerToGame(player, str(game['id']), str(winner))
		player['wins'] += 1
		player['elo'] += eloChange
		updatePlayer(player)

	for player in losingTeamRoster:
		addPlayerToGame(player, str(game['id']), str(loser))
		player['losses'] += 1
		player['elo'] -= eloChange
		updatePlayer(player)

	game['win_team'] = int(winner)
	game['elo_score'] = eloChange
	game['round'] = gameRound
	game['map'] = gameMap
	if int(winner) == game['nr_team']:
		game['nr_team_elo'] = winningTeamAvgElo
		game['emp_team_elo'] = losingTeamAvgElo
	else:
		game['nr_team_elo'] = losingTeamAvgElo
		game['emp_team_elo'] = winningTeamAvgElo

	updateGame(game)


def getCommand():
	usrIn = input().lower()
	if usrIn == "post results":
		addGameResults()
	print("\n")
	return usrIn

def main():
	usrIn = ""
	while(usrIn!="q"):
		print("ADMIN MENU")
		print("'post results' - Add Game Results")
		print("'q' - quit")
		usrIn = getCommand()

main()