import discord
from discord.ext.commands import AutoShardedBot
from collections import OrderedDict
import asyncio, re, time
import traceback
import telebot
from telebot.async_telebot import AsyncTeleBot
from telebot.util import escape
from telebot.types import ReplyParameters
from helper import *
import function as func

activeChannel_dict = OrderedDict()
reply_dict = OrderedDict()

class DiscordBot(AutoShardedBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.telegram_bot = None

    async def setup_hook(self) -> None:
        # Connecting to MongoDB
        await self.connect_db()

    async def watch_for_changes(interval=240):
        while True:
            await asyncio.sleep(interval)
            for key, value in activeChannel_dict.items():
                if int(time.time()) - value['since'] > 600:
                    result = await func.get_db(func.telecorddata, {"chatid": Int64(key)})
                    primarychannel = result['channelid']
                    if value['id']!=primarychannel:
                        activeChannel_dict[key] = {'id':primarychannel, 'since': int(time.time())}

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
        await self.watch_for_changes()
        self.message_dict = await load_user_data()
        self.session = aiohttp.ClientSession()

    async def on_message(self, message):
        if (message.guild and isinstance(message.channel, discord.TextChannel) and not message.author.bot):
            await save_user_data(message.author.id, message.author.name)
            if message.reference:
                await self.forward_to_telegram(message, message.reference.message_id)
            await self.forward_to_telegram(message)
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
                    last_line = message.strip().split("\n")[-1]
                    
                    #IDs from the last line
                    ids = [int(id.strip()) for id in last_line.split("|")]
                    replied_msgID, channelid = ids
                elif replied_message.caption:
                    #replied_msgID = int(re.search(r"\b\d+\b(?![\s\S]*\b\d+\b)", replied_message.caption).group()) 
                    last_line = message.strip().split("\n")[-1]
                    
                    #IDs from the last line
                    ids = [int(id.strip()) for id in last_line.split("|")]
                    replied_msgID, channelid = ids          
            
            # Check if message has GIF file
            if message.animation:
                if replied_msgID:
                    activeChannel_dict[chatid] = {'id':channelid,'since':int(time.time())}
                    data = [message, channelid, reply_dict]
                else:
                    activeChannel_dict[chatid] = {'id':dcchannel_id,'since':int(time.time())}
                    data = [message, dcchannel_id, reply_dict]
                await sendAnimation2DC(self.telegram_bot, data, author, replied_msgID)
                return

            embed = discord.Embed(description=message.text)
            embed.set_author(name=message.from_user.full_name[:25])
            if replied_msgID:
                activeChannel_dict[chatid] = {'id':channelid,'since':int(time.time())}
                msg = await send_reply(channelid, message.text, author, replied_msgID)
            else:
                activeChannel_dict[chatid] = {'id':dcchannel_id,'since':int(time.time())}
                msg = await send_reply(dcchannel_id, message.text, author, replied_msgID)
            reply_dict[msg.id] = message.message_id
        except:
            traceback.print_exc()

    async def forward_to_telegram(self, message: discord.Message, replied_messageid: int = None):
        try:
            TELEGRAM_CHAT_ID = result_telecord['chatid']
            activeChannel_dict[TELEGRAM_CHAT_ID] = {'id':message.channel.id,'since':int(time.time())} 
            header = ""
            reply_params = None
            if replied_messageid:
                try:
                    tg_msgid = reply_dict[replied_messageid]
                    reply_params = ReplyParameters(message_id=tg_msgid)
                except:
                    pass
            if message.attachments:
                adata = [TELEGRAM_CHAT_ID, replied_messageid]
                response = await sendAttachments(message, self.telegram_bot, adata, reply_dict, reply_params)
                if response:
                    return 
            header = header + f"__*{message.author.display_name}* | _#{message.channel.name}_ __\n"
            # Check if message has any emoji, mentions for channels, roles or members
            msgcontent = getRtext(message)
            items = [msgcontent, header, TELEGRAM_CHAT_ID] 
            # Check if message has any emoji
            if isinstance(msgcontent, list):
                await sendEmoji(self.telegram_bot, message, items, reply_dict, reply_params)
                return 
            # Check if message has any discord GIF
            if "gif" in msgcontent and is_valid_url(msgcontent.strip()):
                await sendAnimation(self.telegram_bot, message, items, reply_dict, reply_params)
                return 
            # Frame the message without any attachments
            text = f"{escape(msgcontent)}\n\n`{message.id}` | `{message.channel.id}`"
            content = header + text
            content = escapeMD(content)
            msg = await self.telegram_bot.send_message(TELEGRAM_CHAT_ID, content, parse_mode="markdownv2", reply_parameters = reply_params)
            reply_dict[message.id] = msg.message_id
        except:
            traceback.print_exc()

class TelegramBot(AsyncTeleBot):
    def __init__(self, token):
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

    
