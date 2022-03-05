import json

# Copied from bot.py
def loadFileToJson(filePath):
    with open(filePath, 'r') as reader:
        return json.load(reader)

def dumpJsonToFile(filePath, data):
    with open(filePath, "w") as writer:
        json.dump(data, writer, sort_keys=True, indent=4)

### Switches format for tournaments stored in JSON:
# old: tournamentName-seriesName
# new: seriesName-tournamentName
def swapTournamentNameFormat():
    tournament_ids = loadFileToJson("./files/tournamentIds")
    game_ids = loadFileToJson("./files/gameIds")
    standings = loadFileToJson("./files/standings")
    boots = loadFileToJson("./files/boots")


    # Tournament IDs
    new_tourney_ids = {}
    for tourney_name, id in tournament_ids.items():
        series = tourney_name.split("-")[1]
        tourney = tourney_name.split("-")[0]

        new_tourney_ids["{}-{}".format(series, tourney)] = id
    dumpJsonToFile("./new_files/tournamentIds", new_tourney_ids)


    # Game IDs
    new_game_ids = {}
    for tourney_name, id in game_ids.items():
        series = tourney_name.split("-")[1]
        tourney = tourney_name.split("-")[0]

        new_game_ids["{}-{}".format(series, tourney)] = id
    dumpJsonToFile("./new_files/gameIds", new_game_ids)


    # Standings
    new_standings = {}
    for tourney_name, players in standings.items():
        series = tourney_name.split("-")[1]
        tourney = tourney_name.split("-")[0]

        new_standings["{}-{}".format(series, tourney)] = players
    dumpJsonToFile("./new_files/standings", new_standings)


    # Boots
    new_boots = {}
    for tourney_name, players in boots.items():
        series = tourney_name.split("-")[1]
        tourney = tourney_name.split("-")[0]

        new_boots["{}-{}".format(series, tourney)] = players
    dumpJsonToFile("./new_files/boots", new_boots)

swapTournamentNameFormat()
