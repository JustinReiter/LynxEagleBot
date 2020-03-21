import os
import discord
import json
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD = os.getenv("DISCORD_GUILD")
PR_LOG_CHANNEL = os.getenv("PR_LOG_CHANNEL")
BOT_NAME = os.getenv("BOT_NAME")
API_EMAIL = os.getenv("API_EMAIL")
API_TOKEN = os.getenv("API_TOKEN")

client = discord.Client()

def format_message(game):
    return game["winner"] + " defeats " + game["loser"] + "\n" + game["division"] + "\nhttps://www.warzone.com/MultiPlayer?GameID=" + game["game_id"]

def get_channel():
    for guild in client.guilds:
        if guild.name == GUILD:
            for channel in guild.text_channels:
                if channel.name == PR_LOG_CHANNEL:
                    return channel

@client.event
async def on_ready():
    global finished_games
    channel = get_channel()
    for game in finished_games:
        await channel.send(content=format_message(game))

def send_game_query(game_id):
    url = "https://www.warzone.com/API/GameFeed?GameID=" + game_id
    params = {"Email": API_EMAIL, "APIToken":API_TOKEN}
    return requests.get(url=url, params=params)

def send_tournament_query(tournament_id):
    url = "https://www.warzone.com/API/GameIDFeed?TournamentID=" + tournament_id
    params = {"Email": API_EMAIL, "APIToken":API_TOKEN}
    return requests.get(url=url, params=params).json().get("gameIDs", [])

def check_games():
    processed_games = open("./games/processedGames", "r").read()
    processed_games = json.loads(processed_games)

    tournament_ids = open("./games/tournamentIds", "r").read()
    tournament_ids = json.loads(processed_games)

    game_ids = {}

    for key, val in tournament_ids.items():
        game_ids[key] = send_tournament_query(val)

    for div in game_ids:
        unprocessed_games = list(set(game_ids[div]) - set(processed_games))
        for game_id in unprocessed_games:
            game = send_game_query(game_id)
            if not "error" in game and game.get("state") == "Finished":
                winner = ""
                loser = ""
                for player in game.get("players"):
                    if player.get("state") == "Won":
                        winner = player.get("name")
                    else:
                        loser = player.get("name")
                finished_games.append(GameObject(div, winner, loser, game_id))
                processed_games.append(game_id)
    
    open("./games/processedGames", "w").write([json.dumps(processed_games)])
    client.run(TOKEN)


class GameObject:
    def __init__(self, division, winner, loser, game_id):
        self.division = division
        self.winner = winner
        self.loser = loser
        self.game_id = game_id

finished_games = []
check_games()