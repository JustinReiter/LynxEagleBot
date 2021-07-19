import os
import discord
import sys
import requests
from dotenv import load_dotenv
from datetime import datetime
import traceback

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD = int(os.getenv("DISCORD_GUILD"))
PR_LOG_CHANNEL = int(os.getenv("PR_LOG_CHANNEL"))
BOT_NAME = os.getenv("BOT_NAME")
API_EMAIL = os.getenv("API_EMAIL")
API_TOKEN = os.getenv("API_TOKEN")

finished_games = []
standings_strings = []

client = discord.Client()

def log_message(msg, type="check_games"):
    time_str = "[" + datetime.now().isoformat() + "] {}: ".format(type)
    print(time_str + msg)
    with open("./logs/{}.txt".format(datetime.now().isoformat()[:10]), 'a') as log_writer:
        log_writer.write(time_str + msg + "\n")

def format_message(game):
    return "**" + game.winner + "** defeats **" + game.loser + "**\n" + game.division + "\n<https://www.warzone.com/MultiPlayer?GameID=" + game.game_id + ">"

def get_channel():
    for guild in client.guilds:
        if guild.id == GUILD:
            for channel in guild.text_channels:
                if channel.id == PR_LOG_CHANNEL:
                    return channel

@client.event
async def on_ready():
    try:
        global finished_games
        global standings_strings
        channel = get_channel()

        for game in finished_games:
            await channel.send(content=format_message(game))
        finished_games = []

        for standing in standings_strings:
            await channel.send(content=standing)
        standings_strings = []

        if not client.is_closed():
            await client.close()
    except Exception as err:
        log_message("ERROR IN ON_READY: {}".format(err.args))
        if not client.is_closed():
            await client.close()

def send_game_query(game_id):
    url = "https://www.warzone.com/API/GameFeed?GameID=" + str(game_id)
    params = {"Email": API_EMAIL, "APIToken": API_TOKEN}
    return requests.get(url=url, params=params).json()

def send_tournament_query(tournament_id):
    url = "https://www.warzone.com/API/GameIDFeed?TournamentID=" + str(tournament_id)
    params = {"Email": API_EMAIL, "APIToken":API_TOKEN}
    res = requests.get(url=url, params=params).json()
    if "gameIDs" not in res:
        log_message("Game ids not found for tourney id {}: {}".format(tournament_id, res))
    return res.get("gameIDs")

def convertFileToList(linesIt):
    newList = []
    for line in linesIt:
        newList.append(int(line.strip("\n")))
    return newList

def convertFileToDict(linesIt):
    newDict = {}
    key = ""
    hasSeenKey = False
    for line in linesIt:
        if hasSeenKey:
            newDict[key] = line.strip("\n")
        else:
            key = line.strip("\n")
        hasSeenKey = not hasSeenKey
    return newDict

def getStandingsFromFile():
    # {division: {id: {names, wins, losses}}}
    standings = {}
    with open("./files/standings", "r") as standingsLines:
        for line in standingsLines:
            tokens = line.split("\t")
            if tokens[0] not in standings:
                standings[tokens[0]] = {}
            
            standings[tokens[0]][tokens[1]] = {"name": tokens[2], "wins": int(tokens[3]), "losses": int(tokens[4])}
        standingsLines.close()
    return standings

def writeStandingsToFile(standings):
    try:
        writer = open("./files/standings", "w")
        for div, players in standings.items():
            for id, player in players.items():
                writer.write("{}\t{}\t{}\t{}\t{}\n".format(div, id, player['name'], player['wins'], player['losses']))
    except:
        pass

def convertListToFile(processedList):
    file_str = ""
    for game_id in processedList:
        file_str += str(game_id) + "\n"
    return file_str

def check_games():
    try:
        global finished_games
        finished_games.clear()
        processed_games = open("./files/processedGames", "r")
        tournament_ids = open("./files/tournamentIds", "r")
        processed_games = convertFileToList(processed_games)
        tournament_ids = convertFileToDict(tournament_ids)
        standings = getStandingsFromFile()

        log_message("Number of already processed games: {} ".format(len(processed_games)))
        game_ids = {}

        for key, val in tournament_ids.items():
            game_ids[key] = send_tournament_query(val)

        for div in game_ids:
            if div not in standings:
                standings[div] = {}
            unprocessed_games = list(set(game_ids[div]) - set(processed_games))
            log_message("Number of games in {} to check: {}".format(div, len(unprocessed_games)))
            for game_id in unprocessed_games:
                game = send_game_query(game_id)
                for player in game.get("players", {}):
                    if player.get("id") not in standings[div]:
                        standings[div][player.get("id")] = {"name": player.get("name"), "wins": 0, "losses": 0}

                if "error" not in game and game.get("state") == "Finished":
                    log_message("Found finished game in {} with id {}".format(div, game_id))
                    
                    for player in game.get("players"):
                        if standings[div][player.get("id")]["name"] != player.get("name"):
                            standings[div][player.get("id")]["name"] = player.get("name")

                        if player.get("state") == "Won":
                            winner = player.get("name")
                            playerObj = standings[div][player.get("id")]
                            playerObj["wins"] += 1
                            standings[div].update({player.get("id"): playerObj})
                        else:
                            loser = player.get("name")
                            playerObj = standings[div][player.get("id")]
                            playerObj["losses"] += 1
                            standings[div].update({player.get("id"): playerObj})
                    finished_games.append(GameObject(div, winner, loser, game_id))
                    processed_games.append(game_id)
        
        open("./files/processedGames", "w").write(convertListToFile(processed_games))
        writeStandingsToFile(standings)
        log_message("Number of new finished games: {}".format(len(finished_games)))
        if len(finished_games):
            client.run(TOKEN)
    except Exception as err:
        log_message("ERROR IN CHECK_GAMES: {}".format(err.args))
        traceback.print_exc()


class GameObject:
    def __init__(self, division, winner, loser, game_id):
        self.division = division
        self.winner = winner
        self.loser = loser
        self.game_id = str(game_id)

def run_check_games_iteration():
    start_time = datetime.utcnow()
    log_message("Started run at {}".format(start_time.isoformat()))
    check_games()
    run_time = datetime.utcnow() - start_time
    log_message("Ended run at {}".format(datetime.utcnow().isoformat()))
    log_message("Ran for {}".format(str(run_time)))

def post_standings():
    standings = getStandingsFromFile()
    global standings_strings
    standings_strings.clear()

    for div, players in standings.items():
        player_arr = list(players.values())
        player_arr.sort(key=lambda p: p["wins"], reverse=True)
        player_arr.sort(key=lambda p: p["losses"])

        output_str = "**{}**\n".format(div)
        for i in range(len(player_arr)):
            output_str += "{}. {}: {}-{}\n".format(i+1, player_arr[i]["name"], player_arr[i]["wins"], player_arr[i]["losses"])
        standings_strings.append(output_str)
    if len(standings_strings):
        client.run(TOKEN)


def run_post_standings_iteration():
    start_time = datetime.utcnow()
    log_message("Started run at {}".format(start_time.isoformat()), "post_standings")
    post_standings()
    run_time = datetime.utcnow() - start_time
    log_message("Ended run at {}".format(datetime.utcnow().isoformat()), "post_standings")
    log_message("Ran for {}".format(str(run_time)), "post_standings")

if len(sys.argv) > 1:
    if sys.argv[1] == "check_games":
        run_check_games_iteration()
    elif sys.argv[1] == "post_standings":
        run_post_standings_iteration()
