import discord
from discord.ext import commands
import telebot
from telebot.async_telebot import AsyncTeleBot
from telebot.util import escape
import asyncio, traceback, re
from telebot import types
from collections import OrderedDict
from moviepy.editor import VideoFileClip
from helper import *
from telecord import Telecord


# Discord Bot Token
DISCORD_TOKEN = "Discord Bot Token"

# Telegram Bot Token
TELEGRAM_TOKEN = "Telegram Bot Token"

# Discord Channel ID
DISCORD_CHANNEL_ID = 13267468755565765 #Enter your discord channel id

# Telegram Group Chat ID
TELEGRAM_CHAT_ID = 123443464 #Enter you Telegram chat id

# Initialize Discord client
telecordDC = commands.Bot(
    command_prefix="!", help_command=None, intents=discord.Intents.all()
)

# Get Discord Channel
dcchannel = None

message_dict = OrderedDict()
# Initialize Telegram bot
telecordTG = AsyncTeleBot(TELEGRAM_TOKEN)


# Event handler for Discord bot when it is ready
@telecordDC.event
async def on_ready():
    print(f"{telecordDC.user} has connected to Discord!")
    global dcchannel
    dcchannel = telecordDC.get_channel(DISCORD_CHANNEL_ID)


# Event handler for Discord bot to send message
@telecordDC.event


if __name__ == "__main__":
    # Run the bots
    try:
        loop = asyncio.get_event_loop()
        # Initialize the bot class
        telecord = Telecord()

        # Start the bot
        asyncio.gather(telecord.dcstart(), telecord.tgstart())
        loop.run_forever()
    except:
        traceback.print_exc()
