import os
import discord
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("DISCORD_GUILD_ID")
ROLES_CHANNEL = os.getenv("ROLES_CHANNEL")
BOT_ID = os.getenv("BOT_ID")

admins = [
    os.getenv("JOI_ID"),
    os.getenv("JUSTIN_ID")
]

intents = discord.Intents(messages=True, guilds=True, reactions=True, members=True)
client = discord.Client(intents=intents)

general_role_msg = """If you want a role, react any of these:
Picking Competition: :x:
Warzone: :regional_indicator_w:
Chess: :chess_pawn:
Civ 6: :regional_indicator_c:
Catan: :farmer:
CSGO: :gun:
L4D2: :zombie:
Politics: :judge:
Rocket League: :red_car:"""
emojis = []

emote_to_role = {
    ":x:": "Picking Competition",
    ":regional_indicator_w:": "Warzone",
    ":chess_pawn:": "Chess",
    ":regional_indicator_c:": "Civ 6",
    ":farmer:": "Catan",
    ":gun:": "CS:GO",
    ":zombie:": "L4D2",
    ":judge:": "Politics",
    ":red_car:": "Rocket League"
}

def log_message(msg):
    time_str = "[" + datetime.now().isoformat() + "] Jot: "
    print(time_str + msg)

async def send_init_message(message: discord.Message):
    sent_message = await message.channel.send(content=general_role_msg)
    for emoji in emojis:
        await sent_message.add_reaction(emoji)

@client.event
async def on_message(message: discord.Message):
    if message.author.id == BOT_ID:
        # Don't process bot messages
        return
    if message.author.id in admins and message.context == "j!init":
        await message.channel.send(content=":tada: Woohoo, I saw what you said", tts=True)
    elif message.author.id in admins and message.context.startswith("j!event"):
        sent_message = await message.channel.send("New picking competition on {}!\n\nIf you are interested in joining, use :judge: to be a judge and :student: to be a contestant.".format(message.context[8:]))
        await sent_message.add_reaction(":judge:")
        await sent_message.add_reaction(":student:")
    

@client.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    if user.id == BOT_ID:
        # Don't process bot actions
        return
    if reaction.message.channel.name == ROLES_CHANNEL:
        await user.add_roles()
        await reaction.message.channel.send("Found an emote added by {}".format(user.name))
        print("msg: {}".format(reaction.message.content))

@client.event
async def on_reaction_remove(reaction: discord.Reaction, user: discord.Member):
    if user.id == BOT_ID:
        # Don't process bot actions
        return
    if reaction.message.channel.name == ROLES_CHANNEL:
        await user.remove_roles()
        await reaction.message.channel.send("Found an emote removed by {}".format(user.name))
        print("msg: {}".format(reaction.message.content))

@client.event
async def on_ready():
    print("Running from bot.py")
    for guild in client.guilds:
        print("[" + datetime.now().isoformat() + "] Jot: Connected")
        if guild.id == GUILD_ID:
            print(
                f"{client.user} is connected to the following guild:\n"
                f"{guild.name}(id: {guild.id})\n"
            )

client.run(TOKEN)
