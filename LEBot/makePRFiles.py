import json



print("PR Setup by JustinR17\n")

division_count = int(input("Number of divisions: "))

divisions = {}
for i in range(division_count):
    divisions[input("Division name: ")] = input("Division id: ")

with open("./games/tournamentIds", "w") as writer:
    json.dump(divisions, writer, sort_keys=True, indent=4)
with open("./games/processedGames", "w") as writer:
    json.dump([], writer, sort_keys=True, indent=4)
