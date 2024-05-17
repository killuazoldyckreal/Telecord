import aiohttp, random
from discord.ext import tasks, commands
from discord import app_commands, Intents, TextChannel, Message, Interaction
import re, time, asyncio
import traceback
import telebot
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
        super().__init__(command_prefix = func.settings.bot_prefix, intents = Intents.all())
        self.tree.command(
            name="start",
            description="Setup your discord-telegram chat."
        )(self.start_command)
        self.embed_color = func.settings.embed_color
        self.bot_access_user = func.settings.bot_access_user
        self.embed_color = func.settings.embed_color
        self.telegram_bot = None
        self.my_loop1 = tasks.loop(minutes=4)(self.my_task)
        self.my_loop2 = tasks.loop(seconds=300)(self.load_data_task)
        
        # Add before_loop hooks
        self.my_loop1.before_loop(self.before_my_loop)
        self.my_loop2.before_loop(self.before_my_loop)
        

    async def setup_hook(self) -> None:
        await self.tree.sync()
        # Connecting to MongoDB
        await self.connect_db()
        
    async def my_task(self):
        for key, value in self.activeChannel_dict.items():
            if int(time.time()) - value['since'] > 600:
                result = await func.get_db(func.telecorddata, {"chatid": int(key)})
                primarychannel = result['channelid']
                if value['id']!=primarychannel:
                    data = {'id':primarychannel, 'since': int(time.time())}
                    await save_to_json("jsonfiles/activechannels.json", key, data)
    
    async def load_data_task(self):
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
            self.message_dict = await load_user_data("jsonfiles/users.json")
            self.reply_dict = await load_user_data("jsonfiles/replydict.json")
            self.reply_dict = await load_user_data("jsonfiles/activechannels.json")
            self.my_loop1.start()
            self.my_loop2.start()
            self.session = aiohttp.ClientSession()
        except:
            traceback.print_exc()
        
    async def before_my_loop(self):
        await self.wait_until_ready()

    async def on_message(self, message):
        if (message.guild and isinstance(message.channel, TextChannel) and not message.author.bot):
            await save_to_json("jsonfiles/users.json", message.author.id, message.author.name)
            if message.reference:
                await self.forward_to_telegram(message, message.reference.message_id)
            await self.forward_to_telegram(message)
        await self.process_commands(message)

    async def on_tgmessage(self, message, replied_message):
        try:
            result_telecord = await func.get_db(func.telecorddata, {"useridtg": int(message.from_user.id)})
            dcchannel_id = result_telecord['channelid']
            useriddc = result_telecord['useriddc']
            chatid = result_telecord['chatid']
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
                        activechannel_data = {'id':dcchannel_id,'since':int(time.time())}
                        await save_to_json("jsonfiles/activechannels.json", chatid, activechannel_data)
                        msg_id = await send_gif(self.session, dcchannel_id, author, gifname, replied_msgID)
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
                activechannel_data = {'id':dcchannel_id,'since':int(time.time())}
                await save_to_json("jsonfiles/activechannels.json", chatid, activechannel_data)
                msg_id = await send_reply(self.session, dcchannel_id, message, author, replied_msgID)
            if msg_id:
                await save_to_json("jsonfiles/replydict.json", msg_id, message.message_id)
        except:
            traceback.print_exc()

    async def forward_to_telegram(self, message: Message, replied_messageid: int = None):
        try:
            result_telecord = await func.get_db(func.telecorddata, {"useriddc": int(message.author.id)})
            if result_telecord:
                TELEGRAM_CHAT_ID = result_telecord['chatid']
                activechannel_data = {'id':message.channel.id,'since':int(time.time())}
                await save_to_json("jsonfiles/activechannels.json", TELEGRAM_CHAT_ID, activechannel_data) 
                header = ""
                reply_params = None
                if replied_messageid:
                    try:
                        tg_msgid = self.reply_dict[str(replied_messageid)]
                        reply_params = ReplyParameters(message_id=tg_msgid)
                    except:
                        pass
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
            
    @app_commands.describe(
        channel="Discord channel in which you want to chat",
        telegram_chat_id="Enter your Telegram chat ID received by /start in telegram",
        telegram_user_id="Enter your Telegram user ID received by /start in telegram"
    )
    async def start_command(self, interaction: Interaction, channel: TextChannel, telegram_chat_id: int, telegram_user_id: int):
        try:
            await interaction.response.defer()
            response = await is_valid_user(self.telegram_bot, telegram_chat_id, telegram_user_id)
            if response:
                otp = "".join([str(random.randint(0, 9)) for _ in range(6)])
                authdict[telegram_user_id] = {'id': interaction.user.id, 'code': otp, 'since': int(time.time())}
                await self.telegram_bot.send_message(telegram_chat_id, f"This is your Telecord authentication code:\n `{otp}`", parse_mode="markdownv2")
                await interaction.followup.send("<a:pending:1241031324119072789> Type the code sent by the bot in telegram to verify yourself in 2min")

                def check(m):
                    return m.author == interaction.user and m.channel == interaction.channel and re.match(r'^\d{6}$', m.content.strip())

                try:
                    # Wait for a message from the same user in the same channel for 120 seconds
                    reply = await self.wait_for('message', timeout=120, check=check)
                except asyncio.TimeoutError:
                    await interaction.followup.send("You didn't reply within 2 minutes.")
                    return

                authcode = int(reply.content.strip())
                if int(otp) == authcode:
                    insert_telecord = {"useriddc": interaction.user.id, "useridtg": telegram_user_id, "channelid": channel.id, "chatid": telegram_chat_id}
                    response = await func.insert_db(func.telecorddata, insert_telecord)
                    if response:
                        await interaction.followup.send("<a:chk:1241031331756904498> Your setup completed successfully!")
                    else:
                        await interaction.followup.send("<a:crs:1241031335250755746> Setup failed! Try again or contact support.")
                else:
                    await interaction.followup.send("<a:crs:1241031335250755746> Setup failed! Invalid code.")
            else:
                await interaction.followup.send("<a:crs:1241031335250755746> Setup failed! Invalid chatID or userID.")
        except:
            traceback.print_exc()


class TelegramBot(AsyncTeleBot):
    def __init__(self, token, discord_bot=None):
        super().__init__(token)
        self.discord_bot = discord_bot

        @self.message_handler(commands=['start'])
        async def send_welcome(message):
            await self.reply_to(message, f"Hello! This is your userid: `{message.from_user.id}`\nThis is your userid: `{message.chat.id}`", parse_mode="markdownv2")

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

    

class Telecord:
    def __init__(self):
        self.dctoken = func.tokens.dctoken
        self.tgtoken = func.tokens.tgtoken
        self.discord_bot = DiscordBot()
        self.telegram_bot = TelegramBot(token=self.tgtoken, discord_bot=self.discord_bot)
        self.discord_bot.telegram_bot = self.telegram_bot

    async def dcstart(self):
        try:
        	await self.discord_bot.start(self.dctoken)
        except:
            traceback.print_exc()

    async def tgstart(self):
        print("Telecord has connected to Telegram!")
        await self.telegram_bot.infinity_polling()