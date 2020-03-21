import os
import discord
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD = os.getenv("DISCORD_GUILD")
GAME_LOG_CHANNEL = os.getenv("GAME_LOG_CHANNEL")
BOT_NAME = os.getenv("BOT_NAME")

client = discord.Client()

def log_message(msg):
    time_str = "[" + datetime.now().isoformat() + "] Lynx&EagleBot: "
    print(time_str + msg)

@client.event
async def on_message(message):
    if message.channel.name == GAME_LOG_CHANNEL:
        print("[" + datetime.now().isoformat() + "] Lynx&EagleBot: Received Message")
        print(message.content + "\n\tBy: " + message.author.display_name)
        if message.author.display_name == BOT_NAME:
            # Message is from bot, check if winner is 101st or lynx
            if message.content.startswith("[Lynx]") or message.content.startswith("{101st}"):
                print("Woohoo, we won!")
                await message.channel.send(content=":tada: Woohoo, congrats on the win! :tada:", tts=True)


@client.event
async def on_ready():

    for guild in client.guilds:
        print("[" + datetime.now().isoformat() + "] Lynx&EagleBot: Connected")
        if guild.name == GUILD:
            print(
                f"{client.user} is connected to the following guild:\n"
                f"{guild.name}(id: {guild.id})\n"
            )

client.run(TOKEN)