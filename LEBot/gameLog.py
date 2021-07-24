import os
import discord
import sys
import json
import requests
from dotenv import load_dotenv
from datetime import datetime
import traceback

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
BOT_NAME = os.getenv("BOT_NAME")
API_EMAIL = os.getenv("API_EMAIL")
API_TOKEN = os.getenv("API_TOKEN")

if (len(sys.argv) > 2 and sys.argv[2] == "live"):
    GUILD = int(os.getenv("DISCORD_GUILD"))
    PR_LOG_CHANNEL = int(os.getenv("PR_LOG_CHANNEL"))
    DEBUG_MODE = False
else:
    GUILD = int(os.getenv("DISCORD_GUILD_TEST"))
    PR_LOG_CHANNEL = int(os.getenv("PR_LOG_CHANNEL_TEST"))    
    DEBUG_MODE = True

finished_games = []
standings_strings = []
boot_string = ""

client = discord.Client()

def log_message(msg, type="check_games"):
    time_str = "[" + datetime.now().isoformat() + "] {}{}: ".format(type, " [TEST]" if DEBUG_MODE else "")
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
        global boot_string
        channel = get_channel()

        for game in finished_games:
            await channel.send(content=format_message(game))
        finished_games = []

        for standing in standings_strings:
            await channel.send(content=standing)
        standings_strings = []

        if boot_string:
            await channel.send(content=boot_string)
        boot_string = ""

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

def loadFileToJson(filePath):
    with open(filePath, 'r') as reader:
        return json.load(reader)

def dumpJsonToFile(filePath, data):
    with open(filePath, "w") as writer:
        json.dump(data, writer, sort_keys=True, indent=4)

def check_games():
    try:
        global finished_games
        finished_games.clear()
        tournament_ids = loadFileToJson("./files/tournamentIds")
        processed_games = loadFileToJson("./files/processedGames")
        standings = loadFileToJson("./files/standings")
        boots = loadFileToJson("./files/boots")

        log_message("Number of already processed games: {} ".format(len(processed_games)))
        game_ids = {}

        for key, val in tournament_ids.items():
            game_ids[key] = send_tournament_query(val)

        for div in game_ids:
            if div not in standings:
                standings[div] = {}
            if div not in boots:
                boots[div] = {}
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

                            # Check if loser booted and add to stats if so
                            if player.get("state") == "Booted":
                                boots[div].setdefault(player.get("id"), {"name": loser, "boots": 0, "links": []})
                                boots[div][player.get("id")]["boots"] += 1
                                boots[div][player.get("id")]["links"].append(game.get("id"))
                    
                    finished_games.append(GameObject(div, winner, loser, game_id))
                    processed_games.append(game_id)
        
        dumpJsonToFile("./files/processedGames", processed_games)
        dumpJsonToFile("./files/standings", standings)
        dumpJsonToFile("./files/boots", boots)
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
    standings = loadFileToJson("./files/standings")
    global standings_strings
    standings_strings.clear()

    for div, players in standings.items():
        player_arr = list(players.values())
        player_arr.sort(key=lambda p: p["wins"], reverse=True)
        player_arr.sort(key=lambda p: p["losses"])

        output_str = "**{}**\n".format(div)
        for i in range(len(player_arr)):
            output_str += "\t{}. {}: {}-{}\n".format(i+1, player_arr[i]["name"], player_arr[i]["wins"], player_arr[i]["losses"])
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

def boot_report():
    boots = loadFileToJson("./files/boots")
    global boot_string
    boot_string = "**Wall of Shame (boots)**\n"

    for div, players in boots.items():
        if len(players):
            boot_string += "{}:\n".format(div)
            for id, player in players.items():
                boot_string += "\t{} boots - {} (ID: {})\n".format(player['boots'], player['name'], id)
    client.run(TOKEN)

def run_boot_report():
    start_time = datetime.utcnow()
    log_message("Started run at {}".format(start_time.isoformat()), "boot_report")
    boot_report()
    run_time = datetime.utcnow() - start_time
    log_message("Ended run at {}".format(datetime.utcnow().isoformat()), "boot_report")
    log_message("Ran for {}".format(str(run_time)), "boot_report")

if len(sys.argv) > 1:
    if sys.argv[1] == "check_games":
        run_check_games_iteration()
    elif sys.argv[1] == "post_standings":
        run_post_standings_iteration()
    elif sys.argv[1] == "boot_report":
        run_boot_report()
