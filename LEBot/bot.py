import os
import discord
import sys
import json
import requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv
from datetime import datetime
import traceback

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
BOT_NAME = os.getenv("BOT_NAME")
API_EMAIL = os.getenv("API_EMAIL")
API_TOKEN = os.getenv("API_TOKEN")
MY_DISCORD_ID = int(os.getenv("DISCORD_ID"))

if (len(sys.argv) > 1 and sys.argv[1] == "live"):
    GUILD = int(os.getenv("DISCORD_GUILD"))
    PR_LOG_CHANNEL = int(os.getenv("PR_LOG_CHANNEL"))
    DEBUG_MODE = False
else:
    GUILD = int(os.getenv("DISCORD_GUILD_TEST"))
    PR_LOG_CHANNEL = int(os.getenv("PR_LOG_CHANNEL_TEST"))    
    DEBUG_MODE = True

client = discord.Client()

#########################
######## HELPERS ########
#########################

def log_message(msg: str, type="check_games"):
    time_str = "[" + datetime.now().isoformat() + "] {}{}: ".format(type, " [TEST]" if DEBUG_MODE else "")
    print(time_str + msg)
    with open("./logs/{}.txt".format(datetime.now().isoformat()[:10]), 'a') as log_writer:
        log_writer.write(time_str + msg + "\n")

def log_exception(msg: str):
    time_str = "[" + datetime.now().isoformat() + "] {}{}: ".format(type, " [TEST]" if DEBUG_MODE else "")
    print(time_str + msg)
    with open("./logs/{}.txt".format(datetime.now().isoformat()[:10]), 'a') as log_writer:
        log_writer.write(time_str + msg + "\n")
    with open("./errors/{}.txt".format(datetime.now().isoformat()[:10]), 'a') as log_writer:
        log_writer.write(time_str + msg + "\n")

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

def get_top_players_mtl():
    return requests.get(url="http://md-ladder.cloudapp.net/api/v1.0/players/?topk=50").json()

def loadFileToJson(filePath):
    with open(filePath, 'r') as reader:
        return json.load(reader)

def dumpJsonToFile(filePath, data):
    with open(filePath, "w") as writer:
        json.dump(data, writer, sort_keys=True, indent=4)

def format_message(game):
    return "**" + ", ".join(game.winner) + "** defeats **" + ", ".join(game.loser) + "**\n" + game.division + "\n" + game.league + "\n<https://www.warzone.com/MultiPlayer?GameID=" + game.game_id + ">"

def get_channel():
    for guild in client.guilds:
        if guild.id == GUILD:
            for channel in guild.text_channels:
                if channel.id == PR_LOG_CHANNEL:
                    return channel

#########################
######### OBJS ##########
#########################

class GameObject:
    def __init__(self, division, game_id):
        self.division = division.split("-")[0]
        self.league = division.split("-")[1]
        self.winner = []
        self.loser = []
        self.game_id = str(game_id)


#########################
######### FUNCS #########
#########################

async def check_games():
    try:
        finished_games = []
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
                        if "team" in player:
                            standings[div][player.get("id")]["team"] = player.get("team")

                if "error" not in game and game.get("state") == "Finished":
                    log_message("Found finished game in {} with id {}".format(div, game_id))
                    new_game_obj = GameObject(div, game_id)

                    for player in game.get("players"):
                        if standings[div][player.get("id")]["name"] != player.get("name"):
                            standings[div][player.get("id")]["name"] = player.get("name")

                        if player.get("state") == "Won":
                            new_game_obj.winner.append(player.get("name"))
                            playerObj = standings[div][player.get("id")]
                            playerObj["wins"] += 1
                            standings[div].update({player.get("id"): playerObj})
                        else:
                            new_game_obj.loser.append(player.get("name"))
                            playerObj = standings[div][player.get("id")]
                            playerObj["losses"] += 1
                            standings[div].update({player.get("id"): playerObj})

                            # Check if loser booted and add to stats if so
                            if player.get("state") == "Booted":
                                boots[div].setdefault(player.get("id"), {"name": player.get("name"), "boots": 0, "links": []})
                                boots[div][player.get("id")]["boots"] += 1
                                boots[div][player.get("id")]["links"].append(game.get("id"))
                    
                    finished_games.append(new_game_obj)
                    processed_games.append(game_id)
        
        dumpJsonToFile("./files/processedGames", processed_games)
        dumpJsonToFile("./files/standings", standings)
        dumpJsonToFile("./files/boots", boots)
        log_message("Number of new finished games: {}".format(len(finished_games)))
        if len(finished_games):
            channel = get_channel()

            for game in finished_games:
                await channel.send(content=format_message(game))
    except Exception as err:
        log_exception("ERROR IN CHECK_GAMES: {}".format(err.args))
        traceback.print_exc()


LEAGUES_TO_POST_STANDINGS = [
    "101/Python Annual Championship 2021",
    "Python/101st P/R League"
]

async def post_standings():
    try:
        standings = loadFileToJson("./files/standings")
        standings_strings = []

        league = ""

        for div, players in standings.items():
            if div.split("-")[1] not in LEAGUES_TO_POST_STANDINGS:
                continue
            if div.split("-")[1] != league:
                league = div.split("-")[1]
                standings_strings.append("**{}**".format(league))

            player_arr = list(players.values())

            # Sort by best potential
            player_arr.sort(key=lambda p: p["wins"], reverse=True)
            player_arr.sort(key=lambda p: len(player_arr)-1 + int(p["wins"]) - int(p["losses"]), reverse=True)

            # Sort by most wins
            # player_arr.sort(key=lambda p: p["losses"])
            # player_arr.sort(key=lambda p: p["wins"], reverse=True)

            output_str = "{}\n```".format(div.split("-")[0])
            for i in range(len(player_arr)):
                output_str += "\t{}. {}: {}-{}\n".format(i+1, player_arr[i]["name"], player_arr[i]["wins"], player_arr[i]["losses"])
            output_str += "```"
            standings_strings.append(output_str)
        if len(standings_strings):
            channel = get_channel()
            for standing in standings_strings:
                await channel.send(content=standing)
    except Exception as err:
        log_exception("ERROR IN post_standings: {}".format(err.args))
        traceback.print_exc()

async def boot_report(channel: discord.TextChannel):
    try:
        boots = loadFileToJson("./files/boots")
        boot_string = "**Wall of Shame (boots)**\n```"

        for div, players in boots.items():
            if len(players):
                boot_string += "{}:\n".format(" - ".join(div.split("-")[::-1]))
                for id, player in players.items():
                    boot_string += "\t{} boot{} - {} (ID: {})\n".format(player['boots'], "s" if int(player['boots']) > 1 else " ", player['name'], id)
        boot_string += "```"
        
        if boot_string:
                await channel.send(content=boot_string)
    except Exception as err:
        log_exception("ERROR IN boot_report: {}".format(err.args))

async def mtl_players(channel: discord.TextChannel):
    try:
        players = get_top_players_mtl()

        output = "**Players in top 50:**\n"
        for player in players["players"]:
            if "clan_id" not in player or player["clan_id"] not in [7, 489]:
                continue
            output += "{:>2}. {:>4} - {} {}\n".format(player["rank"], player["displayed_rating"], ("<:101st:925466598784004126>" if player["clan_id"] == 7 else "<:python:925466546602643527>"), player["player_name"])

        await channel.send(content=output)
    except Exception as err:
        log_exception("ERROR IN mtl_players: {}".format(err.args))

#########################
######### Tasks #########
#########################

async def run_check_games_job():
    start_time = datetime.utcnow()
    log_message("Started run at {}".format(start_time.isoformat()))
    await check_games()
    run_time = datetime.utcnow() - start_time
    log_message("Ran for {}".format(str(run_time)))

async def run_post_standings_job():
    start_time = datetime.utcnow()
    log_message("Started run at {}".format(start_time.isoformat()), "post_standings")
    await post_standings()
    run_time = datetime.utcnow() - start_time
    log_message("Ran for {}".format(str(run_time)), "post_standings")

async def run_boot_report(channel: discord.TextChannel):
    start_time = datetime.utcnow()
    log_message("Started run at {}".format(start_time.isoformat()), "boot_report")
    await boot_report(channel)
    run_time = datetime.utcnow() - start_time
    log_message("Ran for {}".format(str(run_time)), "boot_report")

#########################
######### Events ########
#########################

are_events_scheduled = False

HELP_MESSAGE = """**Biggus Help**
`b!boot_report` - Post the wall of shame (boots) for all events
`b!standings` - Post standings of internal events
`b!links` - Post relevant clan links
`b!mtl` - Show 101st & Python players on the MTL
`b!msg <channel> <msg>` - Sorry, this is Justin's command only
"""

LINKS_MESSAGE = """**Links**
Python <https://www.warzone.com/Clans/?ID=489>
Eagles <https://www.warzone.com/Clans/?ID=7>
CL Sheet <https://docs.google.com/spreadsheets/d/1DAeG0gE0QXSE_JYEH6prEH7mCe-ey6pKFANY7_7Qlf0/edit#gid=1014622740>
"""

@client.event
async def on_message(message: discord.Message):
    try:
        if message.content.lower() == "b!boot_report":
            log_message("{}#{} called boot_report".format(message.author.name, message.author.discriminator), "on_message")
            await run_boot_report(message.channel)
        elif message.content.lower() == "b!help":
            log_message("{}#{} called help".format(message.author.name, message.author.discriminator), "on_message")
            await message.reply(content=HELP_MESSAGE, mention_author=False)
        elif message.content.lower() == "b!mtl":
            log_message("{}#{} called mtl".format(message.author.name, message.author.discriminator), "on_message")
            await mtl_players(message.channel)
        elif message.content.lower() == "b!links":
            log_message("{}#{} called links".format(message.author.name, message.author.discriminator), "on_message")
            await message.channel.send(content=LINKS_MESSAGE)
        # Below are admin commands
        elif "b!standings" in message.content.lower() and message.author.id == MY_DISCORD_ID:
            log_message("{}#{} called standings".format(message.author.name, message.author.discriminator), "on_message")
            await run_post_standings_job();
        elif "b!msg" in message.content.lower() and message.author.id == MY_DISCORD_ID:
            log_message("{}#{} called msg".format(message.author.name, message.author.discriminator), "on_message")

            channel = discord.utils.find(lambda channel: channel.id == int(message.content.split(" ")[1]), client.get_all_channels()) 
            await channel.send(content=" ".join(message.content.split(" ")[2:]))
        elif "b!kys" in message.content.lower() and message.author.id == MY_DISCORD_ID:
            await message.channel.send(content="Ok, I leave now :(")
            await client.close()
        elif "b!cg" in message.content.lower() and message.author.id == MY_DISCORD_ID:
            log_message("{}#{} called cg".format(message.author.name, message.author.discriminator), "on_message")
            await run_check_games_job()

    except Exception as err:
        log_exception("ERROR IN post_standings: {}".format(err.args))
        traceback.print_exc()
        await message.channel.send("Error occurred in on_message. What are you doing?")

@client.event
async def on_ready():
    log_message("Bot is connected", "on_ready")
    global are_events_scheduled
    
    # Start schedulers (only on first run)
    if not are_events_scheduled:
        scheduler = AsyncIOScheduler()
        scheduler.add_job(run_check_games_job, CronTrigger(hour="*", minute="0", second="0"))
        # scheduler.add_job(run_post_standings_job, CronTrigger(day="*", hour="0", minute="5", second="0"))
        scheduler.start()
        log_message("Bot started scheduled tasks", "on_ready")
        are_events_scheduled = True

client.run(TOKEN)

# To msg a user, use: <@!userid>
