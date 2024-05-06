import discord
from discord.ext import commands
from telebot.async_telebot import AsyncTeleBot
from telebot.util import escape
import asyncio, traceback, re

# Discord Bot Token
DISCORD_TOKEN = "Discord Bot Token"

# Telegram Bot Token
TELEGRAM_TOKEN = "Telegram Bot Token"

# Discord Channel ID
DISCORD_CHANNEL_ID = 13267468755565765 #Enter your discord channel id

# Telegram Group Chat ID
TELEGRAM_CHAT_ID = 123443464 #Enter you Telegram chat id

# Initialize Discord client
telecordDC = commands.Bot(command_prefix="!", help_command=None, intents = discord.Intents.all())

# Get Discord Channel
dcchannel = None

# Initialize Telegram bot
telecordTG = AsyncTeleBot(TELEGRAM_TOKEN)


# Event handler for Discord bot when it is ready
@telecordDC.event
async def on_ready():
    print(f'{telecordDC.user} has connected to Discord!')
    global dcchannel
    dcchannel = telecordDC.get_channel(DISCORD_CHANNEL_ID)


# Event handler for Discord bot to send message
@telecordDC.event
async def on_tgmessage(message, replied_message):
    try:
        # Get the content of message
        replied_msgID = None
        rmsg = None
        if replied_message:
            replied_msgID = int(re.search(r'\b\d+\b(?![\s\S]*\b\d+\b)', replied_message.text).group())
        if replied_msgID:
            rmsg = await dcchannel.fetch_message(replied_msgID)
        embed = discord.Embed(description=message.text)
        embed.set_author(name= message.from_user.full_name[:25])
        #embed.set_footer(text=message.message_id)
        if rmsg:
            await rmsg.reply(embed=embed)
        else:
            await dcchannel.send(embed=embed)
    except:
        traceback.print_exc()


# Event handler for Discord bot when a message is received
@telecordDC.event
async def on_message(message):
    replied_message = None
    # Check if the message is from a guild TextChannel
    if message.guild and isinstance(message.channel, discord.TextChannel) and not message.author.bot:
        # Forward the message to Telegram
        if message.reference:
            replied_message = await message.channel.fetch_message(message.reference.message_id)
        await forward_to_telegram(message, replied_message)

def escapeMD(text):
    markdown_symbols = ['-', '|', '#', '+']
    escaped_text = ""

    for char in text:
        if char in markdown_symbols:
            escaped_text += '\\' + char
        else:
            escaped_text += char

    return escaped_text

# Function to forward a Discord message to Telegram
async def forward_to_telegram(message, replied_message):
    # Get the content of the message
    try:
        header = ""
        if replied_message:
            if replied_message.embeds:
                embed = replied_message.embeds[0]
                rcontent = embed.description
                if len(rcontent)>60:
                    rcontent = escape(replied_message.content[:50]) + "..."
                author = embed.author.name
            else:
                if len(message.content)>60:
                    rcontent = escape(replied_message.content[:50]) + "..."
                else:
                    rcontent = escape(replied_message.content)
                author = replied_message.author.name
            header = f">*{escape(author)}:* {rcontent}\n⤷ "
        header = header + f"__*{message.author.display_name}* | _#{message.channel.name}_ __\n"

        text = f"{escape(message.content)}\n\n`{message.id}`"
        content = header + text
        content = escapeMD(content)

        # Send the message to the Telegram group chat
        await telecordTG.send_message(TELEGRAM_CHAT_ID, content, parse_mode="markdownv2")
    except:
        traceback.print_exc()


# Start the Discord bot
async def start_discord_bot():
    await telecordDC.start(DISCORD_TOKEN)


# Start Telegram bot polling
async def start_telegram_bot():
    try:
        telecordTG.set_update_listener(telegram_update_listener)
        await telecordTG.infinity_polling()
    except Exception as e:
        print(f"Failed to start Telegram bot: {e}")


# Listener function for Telegram updates
async def telegram_update_listener(messages):
    replied_message = None
    for message in messages:
        if message.chat.id == TELEGRAM_CHAT_ID:
            if message.reply_to_message:
                replied_message = message.reply_to_message
            # Forward the message from Telegram to Discord
            await forward_to_discord(message, replied_message)


# Function to forward a Telegram message to Discord
async def forward_to_discord(message, replied_message):
    # Create the event for sending the message
    telecordDC.dispatch("tgmessage", message, replied_message)


if __name__ == "__main__":
    # Run the bots
    try:
        loop = asyncio.get_event_loop()
        asyncio.gather(start_discord_bot(), start_telegram_bot())
        loop.run_forever()
    except:
        traceback.print_exc()
