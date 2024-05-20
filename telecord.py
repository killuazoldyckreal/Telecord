import aiohttp, random
import discord
from discord.ext import tasks, commands
from discord import app_commands, Intents, TextChannel, Message, Interaction, CategoryChannel
import re, time, asyncio
import traceback
import telebot
from typing import Union
from telebot.async_telebot import AsyncTeleBot
from telebot.util import escape
from telebot.types import ReplyParameters
import function as func
from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorCollection,
)
from helper import *

authdict = {}
        
class DiscordBot(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(command_prefix = func.settings.bot_prefix, intents = Intents.all(), help_command= None)
        self.embed_color = func.settings.embed_color
        self.bot_access_user = func.settings.bot_access_user
        self.embed_color = func.settings.embed_color
        self.telegram_bot = None
        self.command_list = [f"{func.settings.bot_prefix}start", f"{func.settings.bot_prefix}unmute", f"{func.settings.bot_prefix}mute", f"{func.settings.bot_prefix}help", f"{func.settings.bot_prefix}ping", f"{func.settings.bot_prefix}end"]
        

    async def setup_hook(self) -> None:
        # Connecting to MongoDB
        await self.connect_db()
        self.reply_dict = await load_user_data("jsonfiles/replydict.json")
        self.message_dict = await load_user_data("jsonfiles/users.json")
        self.activeChannel_dict = await load_user_data("jsonfiles/activechannels.json")

    async def connect_db(self) -> None:
        if not ((db_name := func.tokens.mongodb_name) and (db_url := func.tokens.mongodb_url)):
            raise Exception("MONGODB_NAME and MONGODB_URL can't not be empty in settings.json")

        try:
            func.MONGO_DB = AsyncIOMotorClient(host=db_url)
            await func.MONGO_DB.server_info()
            print("Successfully connected to MongoDB!")

        except Exception as e:
            raise Exception("Not able to connect MongoDB! Reason:", e)
        
        func.telecorddata = func.MONGO_DB[db_name]['telecorddata']
        func.telegramdata = func.MONGO_DB[db_name]['telegramdata']

    async def on_ready(self):
        print("Telecord has connected to Discord!")
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} command(s)")
            self.session = aiohttp.ClientSession()
        except:
            traceback.print_exc()

    async def on_message(self, message):
        if (message.guild and isinstance(message.channel, TextChannel) and not message.author.bot):
            if any(message.content.split(" ",1)[0] == command for command in self.command_list):
                await self.process_commands(message)
            else:
                await save_to_json("jsonfiles/users.json", message.author.id, message.author.name)
                if message.reference:
                    await self.forward_to_telegram(message, message.reference.message_id)
                await self.forward_to_telegram(message)

    async def on_tgmessage(self, message, replied_message):
        try:
            result_telecord = await func.get_db(func.telecorddata, {"useridtg": int(message.from_user.id)})
            if not result_telecord:
                return
            useriddc = result_telecord['useriddc']
            chatid = result_telecord['chatid']
            activeChannelid = self.activeChannel_dict[str(chatid)]['id']
            timestmp = self.activeChannel_dict[str(chatid)]['since']
            if int(time.time()) - timestmp > 600:
                activeChannelid = result_telecord['channelid']
            author = self.message_dict[str(useriddc)]

            # Check if message is a reply
            replied_msgID = None
            if replied_message:
                if replied_message.text:
                    #replied_msgID = int(re.search(r"\b\d+\b(?![\s\S]*\b\d+\b)", replied_message.text).group())
                    last_line = replied_message.text.strip().split("\n")[-1]
                    ids = [int(id.strip()) for id in last_line.split("|")]
                    replied_msgID, channelid = ids
                elif replied_message.caption:
                    #replied_msgID = int(re.search(r"\b\d+\b(?![\s\S]*\b\d+\b)", replied_message.caption).group()) 
                    last_line = replied_message.caption.strip().split("\n")[-1]
                    ids = [int(id.strip()) for id in last_line.split("|")]
                    replied_msgID, channelid = ids          
            
            # Check if message has GIF file
            if message.animation:
                filename, gifname = await getAnimation(self.telegram_bot, message)
                if filename:
                    if replied_msgID:
                        activechannel_data = {'id':channelid,'since':int(time.time())}
                        await save_to_json("jsonfiles/activechannels.json", chatid, activechannel_data)
                        msg_id = await send_gif(self.session, channelid, author, gifname, replied_msgID)
                    else:
                        activechannel_data = {'id':activeChannelid,'since':int(time.time())}
                        await save_to_json("jsonfiles/activechannels.json", chatid, activechannel_data)
                        msg_id = await send_gif(self.session, activeChannelid, author, gifname, replied_msgID)
                    await delete_file(filename)
                    await delete_file(gifname)
                    if msg_id:
                        await save_to_json("jsonfiles/replydict.json", msg_id, message.message_id)
                        return msg_id
                return
            
            if replied_msgID:
                activechannel_data = {'id':channelid,'since':int(time.time())}
                await save_to_json("jsonfiles/activechannels.json", chatid, activechannel_data)
                msg_id = await send_reply(self.session, channelid, message, author, replied_msgID)
            else:
                activechannel_data = {'id':activeChannelid,'since':int(time.time())}
                await save_to_json("jsonfiles/activechannels.json", chatid, activechannel_data)
                msg_id = await send_reply(self.session, activeChannelid, message, author, replied_msgID)
            if msg_id:
                await save_to_json("jsonfiles/replydict.json", msg_id, message.message_id)
        except:
            traceback.print_exc()

    async def forward_to_telegram(self, message: Message, replied_messageid: int = None):
        try:
            result = await func.get_all_db(func.telecorddata)
            if result:
                for result_telecord in result:
                    mutedchannels = result_telecord['mutedchannels']
                    print(mutedchannels)
                    if message.channel.id in mutedchannels:
                        return
                    elif message.channel.category:
                        if message.channel.category.id in mutedchannels:
                            return
                    TELEGRAM_CHAT_ID = result_telecord['chatid']
                    activechannel_data = {'id':message.channel.id,'since':int(time.time())}
                    self.activeChannel_dict[str(TELEGRAM_CHAT_ID)] = {'id':message.channel.id,'since':int(time.time())}
                    await save_to_json("jsonfiles/activechannels.json", TELEGRAM_CHAT_ID, activechannel_data) 
                    header = ""
                    reply_params = None

                    # Get reply params if the message is a reply
                    if replied_messageid:
                        try:
                            tg_msgid = self.reply_dict[str(replied_messageid)]
                            reply_params = ReplyParameters(message_id=tg_msgid)
                        except:
                            pass

                    # Check if user has uploaded any media
                    if message.attachments:
                        adata = [TELEGRAM_CHAT_ID, replied_messageid]
                        response = await sendAttachments(message, self.telegram_bot, adata, reply_params)
                        if response:
                            return 

                    header = header + f"__*{message.author.display_name}* | _#{message.channel.name}_ __\n"

                    # Check if message has any emoji, mentions for channels, roles or members
                    msgcontent = getRtext(message)
                    items = [msgcontent, header, TELEGRAM_CHAT_ID] 

                    # Check if message has any emoji
                    if isinstance(msgcontent, list):
                        await sendEmoji(self.telegram_bot, message, items, reply_params)
                        return 

                    # Check if message has any discord GIF
                    if "gif" in msgcontent and is_valid_url(msgcontent.strip()):
                        await sendAnimation(self.telegram_bot, message, items, reply_params)
                        return 

                    # Frame the message without any attachments
                    text = f"{escape(msgcontent)}\n\n`{message.id}` | `{message.channel.id}`"
                    content = header + text
                    content = escapeMD(content)
                    msg = await self.telegram_bot.send_message(TELEGRAM_CHAT_ID, content, parse_mode="markdownv2", reply_parameters = reply_params)
                    await save_to_json("jsonfiles/replydict.json", message.id, msg.message_id)
        except:
            traceback.print_exc()


class TelegramBot(AsyncTeleBot):
    def __init__(self, token, discord_bot=None):
        super().__init__(token)
        self.discord_bot = discord_bot

        @self.message_handler(commands=['start'])
        async def send_welcome(message):
            await self.reply_to(message, f"Hello\! This is your User ID: `{message.from_user.id}`\nThis is your Chat ID: `{message.chat.id}`", parse_mode="markdownv2")

        @self.message_handler(commands=['help'])
        async def send_help(message):
            await self.reply_to(message, "This is help!")

        @self.message_handler(commands=['userid'])
        async def send_chatid(message):
            await self.reply_to(message, f"User ID: `{message.from_user.id}`", parse_mode="markdownv2")

        @self.message_handler(commands=['chatid'])
        async def send_chatid(message):
            await self.reply_to(message, f"Chat ID: `{message.chat.id}`", parse_mode="markdownv2")

        @self.message_handler(func=lambda message: True, content_types=['photo', 'text', 'sticker', 'animation'])
        async def echo_all(message):
            replied_message = None
            if message.reply_to_message:
                replied_message = message.reply_to_message
            
            # Forward the message from Telegram to Discord
            await self.forward_to_discord(message, replied_message)
    
    async def forward_to_discord(self, message, replied_message):
        # Create the event for sending the message
        self.discord_bot.dispatch("tgmessage", message, replied_message)

    
bot = DiscordBot()
telegram_bot = TelegramBot(token = func.tokens.tgtoken, discord_bot = bot)
bot.telegram_bot = telegram_bot

@bot.hybrid_command(name="unmute", description="Unmute incoming messages from a channel.", with_app_command = True)
@app_commands.describe(channel="Select channel that you want to unmute")
async def unmute_command(ctx: commands.Context, channel: Union[CategoryChannel, TextChannel]):
    try:
        if ctx.interaction:
            interaction : discord.Interaction = ctx.interaction
            userid = interaction.user.id
            await interaction.response.defer()
            sendmessage = ctx.interaction.followup
        else:
            userid = ctx.author.id
            sendmessage = ctx
        result_telecord = await func.get_db(func.telecorddata, {"useriddc": userid})
        if not result_telecord:
            await sendmessage.send("<a:pending:1241031324119072789> You are not a registered user! Use /start to get started.")
            return
        filter_telecord = {"useriddc": userid}
        update_telecord = { "$pull": { "mutedchannels": channel.id } }
        updated = await func.update_db(func.telecorddata, filter_telecord, update_telecord)
        if updated:
            await sendmessage.send(f"<a:chk:1241031331756904498> {channel.mention} unmuted successfully!")
        else:
            await sendmessage.send("<a:pending:1241031324119072789> Oops something went wrong! Contact support if the error persists.")
    except:
        traceback.print_exc()

@bot.hybrid_command(name="mute", description="Mute incoming messages from a channel.", with_app_command = True)
@app_commands.describe(channel="Select channel that you want to mute")
async def mute_command(ctx: commands.Context, channel: Union[CategoryChannel, TextChannel]):
    try:
        if ctx.interaction:
            interaction : discord.Interaction = ctx.interaction
            userid = interaction.user.id
            await interaction.response.defer()
            sendmessage = ctx.interaction.followup
        else:
            userid = ctx.author.id
            sendmessage = ctx
        result_telecord = await func.get_db(func.telecorddata, {"useriddc": userid})
        if not result_telecord:
            await sendmessage.send("<a:pending:1241031324119072789> You are not a registered user! Use /start to get started.")
            return
        filter_telecord = {"useriddc": userid}
        update_telecord = { "$addToSet": { "mutedchannels": channel.id } }
        updated = await func.update_db(func.telecorddata, filter_telecord, update_telecord)
        if updated:
            await sendmessage.send(f"<a:chk:1241031331756904498> {channel.mention} muted successfully!")
        else:
            await sendmessage.send("<a:pending:1241031324119072789> Oops something went wrong! Contact support if the error persists.")
    except:
        traceback.print_exc()
        
        
@bot.hybrid_command(name="help", description="Show guide to how to get started.", with_app_command = True)
async def send_bot_help(ctx: commands.Context):
    embed = discord.Embed(title="How to get started!", color=func.settings.embed_color)
    embed.description = f"Get you telegram userid and chat id from [here](https://telegram.me/discordmessenger_bot)\nUse /start command and choose your primary discord chatting channel\n\n\nNOTE: You can send messages from Telegram to only 1 discord channel, however you can reply to the messages from different channels by selecting them.\nTo stop recieving message from a specific server/channel use /mute command.\n\n**Tip**: `Use {func.settings.bot_prefix}prefix commands instead of /slash commands to avoid timeout issues`"
    embed.add_field(name="/help", value="Guide to how to get started", inline=False)
    embed.add_field(name="/ping", value="Checks bot latency with discord API", inline=False)
    embed.add_field(name="/start", value="Setup discord-telegram connection", inline=False)
    embed.add_field(name="/end", value="Ends a discord-telegram connection", inline=False)
    embed.add_field(name="/mute", value="Mute incoming messages from a channel", inline=False)
    embed.add_field(name="/unmute", value="Unmute incoming messages from a channel", inline=False)
    await ctx.send(embed=embed)
        
    
@bot.hybrid_command(name="start", description="Setup your discord-telegram chat.", with_app_command = True)
@app_commands.describe(
    channel="Discord channel in which you want to chat",
    telegram_chat_id="Enter your Telegram chat ID received by /start in telegram",
    telegram_user_id="Enter your Telegram user ID received by /start in telegram"
)
async def start_command(ctx: commands.Context, channel: TextChannel, telegram_chat_id: int, telegram_user_id: int):
    try:
        if ctx.interaction:
            interaction : discord.Interaction = ctx.interaction
            await interaction.response.defer()
            sendmessage = ctx.interaction.followup
        else:
            sendmessage = ctx
        response = await is_valid_user(telegram_bot, telegram_chat_id, telegram_user_id)
        if response:
            query = {
                "$or": [
                    {"useridtg": telegram_user_id},
                    {"useriddc": ctx.author.id},
                    {"chatid": telegram_chat_id}
                ]
            }
            response = await func.get_any(func.telecorddata, query)
            if response:
                await sendmessage.send("<a:pending:1241031324119072789> You are already a registered user!")
                return
            otp = "".join([str(random.randint(0, 9)) for _ in range(6)])
            authdict[telegram_user_id] = {'id': ctx.author.id, 'code': otp, 'since': int(time.time())}
            await telegram_bot.send_message(telegram_chat_id, f"This is your Telecord authentication code:\n `{otp}`", parse_mode="markdownv2")
            await sendmessage.send("<a:pending:1241031324119072789> Type the code sent by the bot in telegram to verify yourself in 2min")

            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel and re.match(r'^\d{6}$', m.content.strip())
            
            try:
                # Wait for a message from the same user in the same channel for 120 seconds
                reply = await bot.wait_for('message', timeout=120, check=check)
            except asyncio.TimeoutError:
                await sendmessage.send("You didn't reply within 2 minutes.")
                return
            authcode = int(reply.content.strip())
            if int(otp) == authcode:
                insert_telecord = {"useriddc": ctx.author.id, "useridtg": telegram_user_id, "channelid": channel.id, "chatid": telegram_chat_id, "mutedchannels":[]}
                response = await func.insert_db(func.telecorddata, insert_telecord)
                if response:
                    await sendmessage.send("<a:chk:1241031331756904498> Your setup completed successfully!")
                    return
                await sendmessage.send("<a:crs:1241031335250755746> Setup failed! Try again or contact support.")
                return
            await sendmessage.send("<a:crs:1241031335250755746> Setup failed! Invalid code.")
            return
        await sendmessage.send("<a:crs:1241031335250755746> Setup failed! Invalid chatID or userID.")
    except:
        traceback.print_exc()

@bot.hybrid_command(name="end", description="Disconnect your discord-telegram chat.", with_app_command = True)
async def end_command(ctx: commands.Context):
    try:
        if ctx.interaction:
            interaction : discord.Interaction = ctx.interaction
            await interaction.response.defer()
            sendmessage = ctx.interaction.followup
        else:
            sendmessage = ctx
        response = await func.delete_db(func.telecorddata, {"useriddc": ctx.author.id})
        if response:
            await sendmessage.send("<a:chk:1241031331756904498> You are disconnected from Telecord successfully!")
            return
        await sendmessage.send("<a:pending:1241031324119072789> You are not a registered user! Use /start to get started.")
    except:
        traceback.print_exc()

@bot.hybrid_command(name="ping", description="Checks bot latency with discord API.", with_app_command = True)
async def ping_command(ctx:commands.Context):
    try:
        if round(bot.latency * 1000) <= 50:
            embed=discord.Embed(title="PING", description=f"<a:ping:1241838037290188860> Pong! Latency: **{round(bot.latency *1000)}** ms!", color=0x44ff44)
        elif round(bot.latency * 1000) <= 100:
            embed=discord.Embed(title="PING", description=f"<a:ping:1241838037290188860> Pong! Latency: **{round(bot.latency *1000)}** ms!", color=0xffd000)
        elif round(bot.latency * 1000) <= 200:
            embed=discord.Embed(title="PING", description=f"<a:ping:1241838037290188860> Pong! Latency: **{round(bot.latency *1000)}** ms!", color=0xff6600)
        else:
            embed=discord.Embed(title="PING", description=f"<a:ping:1241838037290188860> Pong! Latency: **{round(bot.latency *1000)}** ms!", color=0x990000)
        await ctx.send(embed=embed)
    except:
        traceback.print_exc()
            
class Telecord:
    def __init__(self):
        self.dctoken = func.tokens.dctoken
        self.discord_bot = bot
        self.telegram_bot = telegram_bot

    async def dcstart(self):
        try:
        	await self.discord_bot.start(self.dctoken)
        except:
            traceback.print_exc()

    async def tgstart(self):
        print("Telecord has connected to Telegram!")
        await self.telegram_bot.infinity_polling()