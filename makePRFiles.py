import os
import discord
import json



print("PR Setup by JustinR17\n")

division_count = int(input("Number of divisions: "))

divisions = {}
for i in range(division_count):
    division_name = input("Division name: ")
    division_id = input("Division id: ")

    divisions[division_name] = division_id
open("./games/tournamentIds", "w").write(json.dumps(divisions))
open("./games/processedGames", "w").write(json.dumps(list()))