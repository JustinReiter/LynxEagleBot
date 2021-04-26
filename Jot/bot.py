import os
import discord
from dotenv import load_dotenv
from datetime import datetime
from discord.utils import get
import random

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("DISCORD_GUILD_ID")
ROLES_CHANNEL = os.getenv("ROLES_CHANNEL")
BOT_ID = int(os.getenv("BOT_ID"))

admins = [
    int(os.getenv("JOI_ID")),
    int(os.getenv("JUSTIN_ID"))
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
Politics: :office_worker:
Rocket League: :red_car:"""
emojis = ["❌", "🇼", "♟️", "🇨", "🧑‍🌾", "🔫", "🧟", "🧑‍💼", "🚗"]

emote_to_role = {
    "❌": "Picking Competition",
    "🇼": "Warzone",
    "♟️": "Chess",
    "🇨": "Civ 6",
    "🧑‍🌾": "Catan",
    "🔫": "CS:GO",
    "🧟": "L4D2",
    "🧑‍💼": "Politics",
    "🚗": "Rocket League",
    "🧑‍⚖️": "Judge",
    "🧑‍🎓": "Contestant"
}

quotes = [
    '"you cant be more motivated than my motivation to not be motivated"',
    '"From a scale of \'Total Noob\' to \'Noob\' they are \'Free Win\'"',
    '"our entire pick set was basicly counter them... we failed misserably getting 1-6"',
    '"ah [he] is a nub \*hides the fakt i lost to him\*"',
    '"every thing is going absolutly fine. i only kicked 2 people for no reason so far"'
]

def log_message(msg):
    time_str = "[" + datetime.now().isoformat() + "] Jot: "

    fw = open("logs/" + str(datetime.now().date()).replace("-", ""), 'a')
    fw.write("{}\n".format(time_str + msg))
    fw.close()
    print(time_str + msg)

async def send_init_message(message: discord.Message):
    log_message("Sending init message for roles")
    sent_message = await message.channel.send(content=general_role_msg)
    for emoji in emojis:
        print(emoji)
        await sent_message.add_reaction(emoji)

@client.event
async def on_message(message: discord.Message):
    if message.author.id == BOT_ID:
        # Don't process bot messages
        return
    if message.author.id in admins and message.content == "j!init":
        await send_init_message(message)
    elif message.author.id in admins and message.content.startswith("j!event"):
        # New event message
        log_message("Started new picking competition event on {}".format(message.content[8:]))
        sent_message = await message.channel.send("New picking competition on {}!\n\nIf you are interested in joining, use :judge: to be a judge and :student: to be a contestant.".format(message.content[8:]))
        await sent_message.add_reaction("🧑‍⚖️")
        await sent_message.add_reaction("🧑‍🎓")
    elif message.content == "j!quote":
        # Quotes easter egg
        quote = random.choice(quotes)
        await message.channel.send(quote)
        log_message("{} requested quote {} in {}".format(message.author.name + message.author.discriminator, quotes.index(quote), message.channel.name))
    elif message.content == "j!links":
        # Links to youtube/twitch
        await message.channel.send("Links:\nYoutube: <https://www.youtube.com/channel/UCzVdEwv0OYkXtoh5eOw0Tyw>\nTwitch: <https://www.twitch.tv/joir179>")
        log_message("{} requested Joi links in {}".format(message.author.name + message.author.discriminator, message.channel.name))
    

@client.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    channel = await client.fetch_channel(payload.channel_id)
    user = await channel.guild.fetch_member(payload.user_id)

    if user.id == BOT_ID:
        # Don't process bot actions
        return
    if channel.name == ROLES_CHANNEL and payload.emoji.name in emote_to_role:
        await user.add_roles(get(channel.guild.roles, name=emote_to_role[payload.emoji.name]))
        log_message("Added {} role for {}".format(emote_to_role[payload.emoji.name], user.name + user.discriminator))

@client.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    channel = await client.fetch_channel(payload.channel_id)
    user = await channel.guild.fetch_member(payload.user_id)

    if user.id == BOT_ID:
        # Don't process bot actions
        return
    if channel.name == ROLES_CHANNEL and payload.emoji.name in emote_to_role:
        await user.remove_roles(get(channel.guild.roles, name=emote_to_role[payload.emoji.name]))
        log_message("Removed {} role from {}".format(emote_to_role[payload.emoji.name], user.name + user.discriminator))

@client.event
async def on_ready():
    log_message("Bot is online")

@client.event
async def on_disconnect():
    log_message("Bot has disconnected")

client.run(TOKEN)
