import os
import discord
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("DISCORD_GUILD_ID")
ROLES_CHANNEL = os.getenv("ROLES_CHANNEL")

intents = discord.Intents(messages=True, guilds=True, reactions=True, members=True)
client = discord.Client(intents=intents)

general_role_msg = """If you want a role, react any of these:
Picking Competition: 
Warzone: 
Chess: 
Civ 6: 
Catan: 
CSGO: 
L4D2: 
Politics: 
Rocket League: """
emojis = []

emote_to_role = {
    
}

def log_message(msg):
    time_str = "[" + datetime.now().isoformat() + "] Jot: "
    print(time_str + msg)

async def send_init_message(message: discord.message):
    sent_message = await message.channel.send(content=general_role_msg)
    for emoji in emojis:
        await sent_message.add_reaction(emoji)

@client.event
async def on_message(message: discord.message):
    if message.author.display_name == "JustinR17" and message.context == "j!init":
        await message.channel.send(content=":tada: Woohoo, I saw what you said", tts=True)

@client.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    await user.add_roles()
    await reaction.message.channel.send("Found an emote added by {}".format(user.name))
    print("msg: {}".format(reaction.message.content))

@client.event
async def on_reaction_remove(reaction: discord.Reaction, user: discord.User):
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
