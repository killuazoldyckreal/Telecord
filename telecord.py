import discord
from discord.ext import commands
from collections import OrderedDict
import asyncio
import traceback
import telebot
from telebot.async_telebot import AsyncTeleBot
from collections import OrderedDict

# Discord Bot Token
DISCORD_TOKEN = "Discord Bot Token"

# Telegram Bot Token
TELEGRAM_TOKEN = "Telegram Bot Token"

class Telecord:
    def __init__(self):
        self.tgbot = AsyncTeleBot(TELEGRAM_TOKEN)
        self.dcbot = commands.Bot(command_prefix="!", help_command=None, intents=discord.Intents.all())
        self.message_dict = OrderedDict()

    async def dcstart(self):
        self.dcbot.add_listener(self.on_ready)
        self.dcbot.add_listener(self.on_message)
        self.dcbot.add_listener(self.on_tgmessage, "on_tgmessage")
        await self.dcbot.start(DISCORD_TOKEN)

    async def on_ready(self):
        print("Telecord has connected to Discord!")
        self.channel = self.dcbot.get_channel(self.channel_id)

    async def on_message(self, message):
        replied_message = None
        if (message.guild and isinstance(message.channel, discord.TextChannel) and not message.author.bot):
            if len(message_dict) >= 100:
                message_dict.popitem(last=False)
            message_dict[message.id] = message
            if message.reference:
                replied_message = await message.channel.fetch_message(
                    message.reference.message_id
                )
            await self.forward_to_telegram(message, replied_message)
        await self.dcbot.process_commands(message)

    async def on_tgmessage(self, message, dcchannel, replied_message):
        try:
            # Check if message is a reply
            rmsg = getReplyMsg(message_dict, dcchannel, replied_message)                

            # Check if message has GIF file
            if message.animation:
                await sendAnimation2DC(self.tgbot, message, dcchannel, rmsg)
                return

            embed = discord.Embed(description=message.text)
            embed.set_author(name=message.from_user.full_name[:25])
            if rmsg:
                await rmsg.reply(embed=embed, allowed_mentions=discord.AllowedMentions.none())
            else:
                await dcchannel.send(embed=embed)
        except:
            traceback.print_exc()

    async def forward_to_telegram(self, TELEGRAM_CHAT_ID: int, message: discord.Message, replied_message: discord.Message = None):
        try:
            header = ""
            if replied_message:
                header = getHeader(replied_message) 
            if message.attachments:
                response = await sendAttachments(message, header, self.tgbot, TELEGRAM_CHAT_ID)
                if response:
                    return 
            header = header + f"__*{message.author.display_name}* | _#{message.channel.name}_ __\n"
            # Check if message has any emoji, mentions for channels, roles or members
            msgcontent = getRtext(message)
            items = [msgcontent, header, TELEGRAM_CHAT_ID] 
            # Check if message has any emoji
            if isinstance(msgcontent, list):
                await sendEmoji(self.tgbot, message, items)
                return 
            # Check if message has any discord GIF
            if "gif" in msgcontent and is_valid_url(msgcontent.strip()):
                await sendAnimation(self.tgbot, message, items)
                return 
            # Frame the message without any attachments
            text = f"{escape(msgcontent)}\n\n`{message.id}`"
            content = header + text
            content = escapeMD(content)
            await self.tgbot.send_message(TELEGRAM_CHAT_ID, content, parse_mode="markdownv2")
        except:
            traceback.print_exc()

    async def tgstart(self):
        print("Telecord has connected to Telegram!")
        self.tgbot.set_update_listener(self.telegram_update_listener)
        await self.tgbot.infinity_polling()

    async def getDCchannel(self, message, replied_message):
        replied_msgID = None
        if replied_message:
            if replied_message.text:
                replied_msgID = int(re.search(r"\b\d+\b(?![\s\S]*\b\d+\b)", replied_message.text).group())
            elif replied_message.caption:
                replied_msgID = int(re.search(r"\b\d+\b(?![\s\S]*\b\d+\b)", replied_message.caption).group())

    # Listener function for Telegram updates
    async def telegram_update_listener(self, messages):
        replied_message = None
        for message in messages:
            if message.chat.id == TELEGRAM_CHAT_ID:
                if message.reply_to_message:
                    replied_message = message.reply_to_message
                # Forward the message from Telegram to Discord
                dcchannel = await self.getDCchannel(message, replied_message)
                await forward_to_discord(message, dcchannel, replied_message)

    async def forward_to_discord(self, message, dcchannel, replied_message):
        # Create the event for sending the message
        telecordDC.dispatch("tgmessage", message, dcchannel, replied_message)
