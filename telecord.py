import discord, aiohttp
from discord.ext import tasks
from discord.ext.commands import AutoShardedBot
import re, time
import traceback
import telebot
from telebot.async_telebot import AsyncTeleBot
from telebot.util import escape
from telebot.types import ReplyParameters
from helper import *
import function as func

class DiscordBot(AutoShardedBot):
    def __init__(self, telegram_bot=None)
        commandPrefix = func.settings.bot_prefix
        self.embed_color = func.settings.embed_color
        self.bot_access_user = func.settings.bot_access_user
        self.embed_color = func.settings.embed_color
        self.telegram_bot = telegram_bot
        super().__init__(command_prefix=commandPrefix, intents=discord.Intents.all())
        self.my_loop1.start()
        self.my_loop2.start()
        

    async def setup_hook(self) -> None:
        # Connecting to MongoDB
        await self.connect_db()
    
    @my_loop1.before_loop
    @my_loop2.before_loop
    async def before_my_loop(self):
        await self.wait_until_ready()

    @tasks.loop(seconds=240)
    async def my_loop1(self):
        for key, value in self.activeChannel_dict.items():
            if int(time.time()) - value['since'] > 600:
                result = await func.get_db(func.telecorddata, {"chatid": Int64(key)})
                primarychannel = result['channelid']
                if value['id']!=primarychannel:
                    data = {'id':primarychannel, 'since': int(time.time())}
                    await save_to_json("activechannels.json", key, data)
    
    @tasks.loop(seconds=300)
    async def my_loop2(self):
        self.reply_dict = await load_user_data("replydict.json")
        self.message_dict = await load_user_data("users.json")
        self.activeChannel_dict = await load_user_data("activechannels.json")

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
        self.message_dict = await load_user_data("users.json")
        self.reply_dict = await load_user_data("replydict.json")
        self.reply_dict = await load_user_data("activechannels.json")
        self.session = aiohttp.ClientSession()

    async def on_message(self, message):
        if (message.guild and isinstance(message.channel, discord.TextChannel) and not message.author.bot):
            await save_to_json("users.json", message.author.id, message.author.name)
            if message.reference:
                await self.telegram_bot.forward_to_telegram(message, self.reply_dict, message.reference.message_id)
            await self.telegram_bot.forward_to_telegram(message)
        await self.process_commands(message)

    async def on_tgmessage(self, message, replied_message):
        try:
            result_telecord = await func.get_db(func.telecorddata, {"useridtg": Int64(message.from_user.id)})
            dcchannel_id = result_telecord['channelid']
            useriddc = result_telecord['useriddc']
            chatid = result_telecord['chatid']
            author = self.message_dict[str(useriddc)]

            # Check if message is a reply
            replied_msgID = None
            if replied_message:
                if replied_message.text:
                    #replied_msgID = int(re.search(r"\b\d+\b(?![\s\S]*\b\d+\b)", replied_message.text).group())
                    last_line = message.text.strip().split("\n")[-1]
                    ids = [int(id.strip()) for id in last_line.split("|")]
                    replied_msgID, channelid = ids
                elif replied_message.caption:
                    #replied_msgID = int(re.search(r"\b\d+\b(?![\s\S]*\b\d+\b)", replied_message.caption).group()) 
                    last_line = message.caption.strip().split("\n")[-1]
                    ids = [int(id.strip()) for id in last_line.split("|")]
                    replied_msgID, channelid = ids          
            
            # Check if message has GIF file
            if message.animation:
                filename, gifname = await getAnimation(self.telegram_bot, message)
                if filename:
                    if replied_msgID:
                        activechannel_data = {'id':channelid,'since':int(time.time())}
                        await save_to_json("activechannels.json", chatid, activechannel_data)
                        data = [message.message_id, channelid, author, gifname]
                    else:
                        activechannel_data = {'id':dcchannel_id,'since':int(time.time())}
                        await save_to_json("activechannels.json", chatid, activechannel_data)
                        data = [message.message_id, dcchannel_id, author, gifname]
                    
                    msg_id = await send_gif(self.session, data, replied_msgID)
                    await delete_file(filename)
                    await delete_file(gifname)
                    if msg_id:
                        await save_to_json("replydict.json", msg_id, message.message_id)
                        return msg_id
                return

            embed = discord.Embed(description=message.text)
            embed.set_author(name=message.from_user.full_name[:25])
            if replied_msgID:
                activeChannel_data = {'id':channelid,'since':int(time.time())}
                await save_to_json("activechannels.json", chatid, activechannel_data)
                msg_id = await send_reply(self.session, channelid, message, author, replied_msgID)
            else:
                activeChannel_data = {'id':dcchannel_id,'since':int(time.time())}
                await save_to_json("activechannels.json", chatid, activechannel_data)
                msg_id = await send_reply(self.session, dcchannel_id, message, author, replied_msgID)
            if msg_id:
                await save_to_json("replydict.json", msg_id, message.message_id)
        except:
            traceback.print_exc()


class TelegramBot(AsyncTeleBot):
    def __init__(self, token, discord_bot=None):
        super().__init__(token)
        self.discord_bot = discord_bot

        @self.message_handler(commands=['start'])
        async def send_welcome(message):
            await self.reply_to(message, "Hello!")

        @self.message_handler(commands=['help'])
        async def send_help(message):
            await self.reply_to(message, "This is help!")

        @self.message_handler(commands=['chatid'])
        async def send_chatid(message):
            await self.reply_to(message, f"Chat ID: {message.chat.id}")

        @self.message_handler(func=lambda message: True)
        async def echo_all(message):
            replied_message = None
            if message.reply_to_message:
                replied_message = message.reply_to_message
            
            # Forward the message from Telegram to Discord
            await self.forward_to_discord(message, replied_message)
    
    async def forward_to_discord(self, message, replied_message):
        # Create the event for sending the message
        self.discord_bot.dispatch("tgmessage", message, replied_message)

    async def forward_to_telegram(self, message: discord.Message, reply_dict={}, replied_messageid: int = None):
        try:
            result_telecord = await func.get_db(func.telecorddata, {"useridtg": Int64(message.author.id)})
            TELEGRAM_CHAT_ID = result_telecord['chatid']
            activeChannel_data = {'id':message.channel.id,'since':int(time.time())}
            await save_to_json("activechannels.json", TELEGRAM_CHAT_ID, activechannel_data) 
            header = ""
            reply_params = None
            if replied_messageid:
                try:
                    tg_msgid = reply_dict[str(replied_messageid)]
                    reply_params = ReplyParameters(message_id=tg_msgid)
                except:
                    pass
            if message.attachments:
                adata = [TELEGRAM_CHAT_ID, replied_messageid]
                response = await sendAttachments(message, self, adata, reply_params)
                if response:
                    return 
            header = header + f"__*{message.author.display_name}* | _#{message.channel.name}_ __\n"
            # Check if message has any emoji, mentions for channels, roles or members
            msgcontent = getRtext(message)
            items = [msgcontent, header, TELEGRAM_CHAT_ID] 
            # Check if message has any emoji
            if isinstance(msgcontent, list):
                await sendEmoji(self, message, items, reply_params)
                return 
            # Check if message has any discord GIF
            if "gif" in msgcontent and is_valid_url(msgcontent.strip()):
                await sendAnimation(self, message, items, reply_params)
                return 
            # Frame the message without any attachments
            text = f"{escape(msgcontent)}\n\n`{message.id}` | `{message.channel.id}`"
            content = header + text
            content = escapeMD(content)
            msg = await self.telegram_bot.send_message(TELEGRAM_CHAT_ID, content, parse_mode="markdownv2", reply_parameters = reply_params)
            await save_to_json("replydict.json", message.id, msg.message_id)
        except:
            traceback.print_exc()

class Telecord:
    def __init__(self):
        self.dctoken = func.tokens.dctoken
        self.tgtoken = func.tokens.tgtoken
        self.discord_bot = DiscordBot()
        self.telegram_bot = TelegramBot(token=tgtoken, discord_bot=self.discord_bot)
        self.discord_bot.telegram_bot = self.telegram_bot

    async def dcstart(self):
        await self.discord_bot.start(self.dctoken)

    async def tgstart(self):
        print("Telecord has connected to Telegram!")
        await self.telegram_bot.infinity_polling()

    
