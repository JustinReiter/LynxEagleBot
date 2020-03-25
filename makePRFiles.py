import os
import discord
import json



print("PR Setup by JustinR17\n")

division_count = int(input("Number of divisions: "))

divisions = ""
for i in range(division_count):
    divisions += input("Division name: ") + "\n"
    divisions += input("Division id: ") + "\n"
open("./games/tournamentIds", "w").write(divisions)
open("./games/processedGames", "w").write("")