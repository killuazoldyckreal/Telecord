import discord
from discord.ext import commands
import telebot
from telebot.async_telebot import AsyncTeleBot
from telebot.util import escape
import asyncio, traceback, re
from telebot import types
from collections import OrderedDict
from moviepy.editor import VideoFileClip

# Discord Bot Token
DISCORD_TOKEN = "BTOKEN"

# Telegram Bot Token
TELEGRAM_TOKEN = "TOKENTG"

# Discord Channel ID
DISCORD_CHANNEL_ID = 123737867671471016

# Telegram Group Chat ID
TELEGRAM_CHAT_ID = 1737657820  # Enter you Telegram chat id

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
async def on_tgmessage(message, replied_message):
    try:
        replied_msgID = None
        rmsg = None

        # Check if message is a reply
        if replied_message:
            if replied_message.text:
                replied_msgID = int(
                    re.search(
                        r"\b\d+\b(?![\s\S]*\b\d+\b)", replied_message.text
                    ).group()
                )
            elif replied_message.caption:
                replied_msgID = int(
                    re.search(
                        r"\b\d+\b(?![\s\S]*\b\d+\b)", replied_message.caption
                    ).group()
                )
        if replied_msgID:
            try:
                rmsg = message_dict[replied_msgID]
            except KeyError:
                if not rmsg:
                    try:
                        rmsg = await dcchannel.fetch_message(replied_msgID)
                    except discord.errors.NotFound:
                        pass

        # Check if message has GIF file
        if message.animation:
            file_info = await telecordTG.get_file(message.animation.file_id)
            file_content = await telecordTG.download_file(file_info.file_path)
            with open("image.mp4", "wb") as f:
                f.write(file_content)
            videoClip = VideoFileClip("image.mp4")
            videoClip.write_gif("image.gif")
            embed = discord.Embed()
            embed.set_author(name=message.from_user.full_name[:25])
            file = discord.File("image.gif")
            await delete_file("image.mp4")
            embed.set_image(url="attachment://image.gif")
            if rmsg:
                await rmsg.reply(
                    embed=embed,
                    file=file,
                    allowed_mentions=discord.AllowedMentions.none(),
                )
                await delete_file("image.gif")
            else:
                await dcchannel.send(embed=embed, file=file)
                await delete_file("image.gif")
            return

        embed = discord.Embed(description=message.text)
        embed.set_author(name=message.from_user.full_name[:25])
        if rmsg:
            await rmsg.reply(
                embed=embed, allowed_mentions=discord.AllowedMentions.none()
            )
        else:
            await dcchannel.send(embed=embed)
    except:
        traceback.print_exc()


# Event handler for Discord bot when a message is received
@telecordDC.event
async def on_message(message):
    replied_message = None
    if (
        message.guild
        and isinstance(message.channel, discord.TextChannel)
        and not message.author.bot
    ):
        if len(message_dict) >= 100:
            message_dict.popitem(last=False)
        message_dict[message.id] = message
        if message.reference:
            replied_message = await message.channel.fetch_message(
                message.reference.message_id
            )
        await forward_to_telegram(message, replied_message)


# Function to forward a Discord message to Telegram
async def forward_to_telegram(message, replied_message):
    try:
        header = ""

        # Check if message is a reply
        if replied_message:
            if replied_message.embeds:
                embed = replied_message.embeds[0]
                rcontent = embed.description
                if len(rcontent) > 60:
                    rcontent = escape(replied_message.content[:50]) + "..."
                author = embed.author.name
            else:
                if len(replied_message.content) > 60:
                    rcontent = escape(replied_message.content[:50]) + "..."
                else:
                    rcontent = escape(replied_message.content)
                author = replied_message.author.name
            header = f">*{escape(author)}:* {rcontent}\n⤷ "

        # Check if message has any photos, videos, etc
        if message.attachments:
            media_group = []
            try:
                for attachment in message.attachments:
                    if ".pdf" in attachment.url:
                        media_group.append(types.InputMediaDocument(attachment.url))
                    elif ".mp3" in attachment.url or ".m4a" in attachment.url:
                        media_group.append(types.InputMediaAudio(attachment.url))
                    elif ".mp4" in attachment.url:
                        media_group.append(types.InputMediaVideo(attachment.url))
                    elif ".jpeg" in attachment.url or ".jpg" in attachment.url:
                        media_group.append(types.InputMediaPhoto(attachment.url))
                    elif ".png" in attachment.url:
                        media_group.append(types.InputMediaPhoto(attachment.url))
                    elif ".gif" in attachment.url:
                        media_group.append(types.InputMediaAnimation(attachment.url))
                    else:
                        media_group.append(types.InputMediaDocument(attachment.url))
                content = escapeMD(header)
                await telecordTG.send_message(
                    TELEGRAM_CHAT_ID, content, parse_mode="markdownv2"
                )
                await telecordTG.send_media_group(TELEGRAM_CHAT_ID, media_group)
                return
            except:
                traceback.print_exc()
                pass

        # Continue framing the message if it don't have any attachments
        header = (
            header
            + f"__*{message.author.display_name}* | _#{message.channel.name}_ __\n"
        )

        # Check if message has any emoji, mentions for channels, roles or members
        msgcontent = getRtext(message)

        # Check if message has any emoji
        if isinstance(msgcontent, list):

            # Check if message has single emoji
            if len(msgcontent) == 1:
                header = header + f"\n`{message.id}`"
                caption = escapeMD(header)
                if ".png" in msgcontent[0]:
                    await telecordTG.send_photo(
                        TELEGRAM_CHAT_ID,
                        msgcontent[0],
                        caption=caption,
                        parse_mode="markdownv2",
                    )
                elif ".gif" in msgcontent[0]:
                    await telecordTG.send_animation(
                        TELEGRAM_CHAT_ID,
                        msgcontent[0],
                        caption=caption,
                        parse_mode="markdownv2",
                    )
                return

            # Send multiple emojis as an album
            media_group = []
            for url in msgcontent:
                if ".png" in url:
                    media_group.append(types.InputMediaPhoto(url))
                elif ".gif" in url:
                    media_group.append(types.InputMediaAnimation(url))
            header = header + f"\n`{message.id}`"
            content = escapeMD(header)
            await telecordTG.send_message(
                TELEGRAM_CHAT_ID, content, parse_mode="markdownv2"
            )
            await telecordTG.send_media_group(TELEGRAM_CHAT_ID, media_group)
            return

        # Check if message has any discord GIF
        if "gif" in msgcontent and is_valid_url(msgcontent.strip()):
            if "tenor" in msgcontent:
                msgcontent = await get_direct_gif_url(msgcontent.strip())
            header = header + f"\n`{message.id}`"
            caption = escapeMD(header)
            await telecordTG.send_animation(
                TELEGRAM_CHAT_ID, msgcontent, caption=caption, parse_mode="markdownv2"
            )
            return

        # Frame the message without any attachments
        text = f"{escape(msgcontent)}\n\n`{message.id}`"
        content = header + text
        content = escapeMD(content)
        await telecordTG.send_message(
            TELEGRAM_CHAT_ID, content, parse_mode="markdownv2"
        )
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
