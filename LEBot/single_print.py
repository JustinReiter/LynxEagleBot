import os
import discord
import sys
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if (len(sys.argv) > 1 and sys.argv[1] == "live"):
    GUILD = int(os.getenv("DISCORD_GUILD"))
    CHANNEL = int(os.getenv("CHANNEL"))
else:
    GUILD = int(os.getenv("DISCORD_GUILD_TEST"))
    CHANNEL = int(os.getenv("CHANNEL_TEST"))

client = discord.Client()

def log_message(msg):
    time_str = "[" + datetime.now().isoformat() + "] Lynx&EagleBot: "
    print(time_str + msg)

@client.event
async def on_ready():
    print("Running from bot.py")
    print(CHANNEL)
    print("[" + datetime.now().isoformat() + "] Lynx&EagleBot: Connected")
    channel = await client.fetch_channel(CHANNEL)
    if channel:
        # await (await channel.fetch_message(875780124870606889)).reply(content="You got it boss")

        await channel.send(content="https://tenor.com/view/imback-gif-18241868")
        pass

client.run(TOKEN)

# To msg a user, use: <@!userid>
