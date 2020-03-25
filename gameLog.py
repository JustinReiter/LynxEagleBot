import os
import discord
import json
import requests
from dotenv import load_dotenv
from datetime import datetime
import traceback

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD = os.getenv("DISCORD_GUILD")
PR_LOG_CHANNEL = os.getenv("PR_LOG_CHANNEL")
BOT_NAME = os.getenv("BOT_NAME")
API_EMAIL = os.getenv("API_EMAIL")
API_TOKEN = os.getenv("API_TOKEN")

client = discord.Client()

def log_message(msg, division=None, game=None):
    time_str = "[" + datetime.now().isoformat() + "] check_games: "
    print(time_str + msg)

def format_message(game):
    return game.winner + " defeats " + game.loser + "\n" + game.division + "\n<https://www.warzone.com/MultiPlayer?GameID=" + game.game_id + ">"

def get_channel():
    for guild in client.guilds:
        if guild.name == GUILD:
            for channel in guild.text_channels:
                if channel.name == PR_LOG_CHANNEL:
                    return channel

@client.event
async def on_ready():
    try:
        global finished_games
        channel = get_channel()
        for game in finished_games:
            await channel.send(content=format_message(game))
        if not client.is_closed():
            await client.logout()
    except Exception as err:
        log_message("ERROR IN ON_READY: {}".format(err.args))
        if not client.is_closed():
            await client.logout()

def send_game_query(game_id):
    url = "https://www.warzone.com/API/GameFeed?GameID=" + str(game_id)
    params = {"Email": API_EMAIL, "APIToken": API_TOKEN}
    return requests.get(url=url, params=params).json()

def send_tournament_query(tournament_id):
    url = "https://www.warzone.com/API/GameIDFeed?TournamentID=" + str(tournament_id)
    params = {"Email": API_EMAIL, "APIToken":API_TOKEN}
    return requests.get(url=url, params=params).json().get("gameIDs", [])

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

def convertListToFile(processedList):
    file_str = ""
    for game_id in processedList:
        file_str += str(game_id) + "\n"
    return file_str

def check_games():
    try:
        processed_games = open("./games/processedGames", "r")
        tournament_ids = open("./games/tournamentIds", "r")
        processed_games = convertFileToList(processed_games)
        tournament_ids = convertFileToDict(tournament_ids)

        log_message("Number of already processed games: {} ".format(len(processed_games)))
        print(tournament_ids)
        game_ids = {}

        for key, val in tournament_ids.items():
            game_ids[key] = send_tournament_query(val)

        for div in game_ids:
            unprocessed_games = list(set(game_ids[div]) - set(processed_games))
            log_message("Number of games in {} to check: {}".format(div, len(unprocessed_games)))
            for game_id in unprocessed_games:
                game = send_game_query(game_id)
                if "error" not in game and game.get("state") == "Finished":
                    log_message("Found finished game in {} with id {}".format(div, game_id))
                    winner = ""
                    loser = ""
                    for player in game.get("players"):
                        if player.get("state") == "Won":
                            winner = player.get("name")
                        else:
                            loser = player.get("name")
                    finished_games.append(GameObject(div, winner, loser, game_id))
                    processed_games.append(game_id)
        
        open("./games/processedGames", "w").write(convertListToFile(processed_games))
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

finished_games = []
start_time = datetime.utcnow()
log_message("Started run at {}".format(start_time.isoformat()))
check_games()
run_time = datetime.utcnow() - start_time
log_message("Ended run at {}".format(datetime.utcnow().isoformat()))
log_message("Ran for {}".format(str(run_time)))