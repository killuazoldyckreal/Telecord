# Copyright 2024 Killua Zoldyck
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import aiohttp
import discord
from discord.ext import commands
from discord import app_commands, Intents, TextChannel, Message
import os, re, time, asyncio
import traceback
from telebot.asyncio_helper import ApiTelegramException
from telebot.async_telebot import AsyncTeleBot
from telebot.types import ReplyParameters, LinkPreviewOptions
from telebot import asyncio_filters
from database import Database
from setting import Config as config
from helper import *
from dotenv import load_dotenv

load_dotenv()
DCTOKEN = os.getenv("DCTOKEN")
TGTOKEN = os.getenv("TGTOKEN")

channels = {}

class DiscordBot(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(command_prefix = config.prefix, intents = Intents.all(), help_command= None)
        self.telegram_bot = None
        clist = ["help", "info", "link", "unlink", "mute", "unmute", "ping", "privacy"]
        self.command_list = [f"{config.prefix}{i}" for i in clist]

    async def setup_hook(self) -> None:
        self.db = Database("telecord.db")
        await self.db.create_table()

    async def on_ready(self):
        print("Telecord has connected to Discord!")
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} command(s)")
            print(f"Server count {len(self.guilds)}")
            self.session = aiohttp.ClientSession()
        except:
            traceback.print_exc()

    async def on_message(self, message):
        if (message.guild and isinstance(message.channel, TextChannel) and not message.author.bot):
            try:
                if any(message.content.split(" ",1)[0] == command for command in self.command_list):
                    await self.process_commands(message)
                else:
                    if message.reference:
                        await self.forward_to_telegram(message, message.reference.message_id)
                    else:
                        await self.forward_to_telegram(message)
            except:
                traceback.print_exc()

    async def on_tgmessage(self, message, replied_message=None):
        try:
            reply_data = None
            channel_id = None
            embed_description = ""
            author = message.from_user
            content = ""
            if author.is_bot and author.username.lower()!="telecord_userbot":
                return
            author_name = author.username
            if replied_message and replied_message.from_user.is_bot:
                if replied_message.text:
                    reply_content = remove_reply_quote(replied_message.html_text)
                    reply_url = getreplyurl(reply_content)
                    reply_data = mdata(reply_url)
                    channel_id = reply_data.channel_id
                elif replied_message.caption:
                    reply_url = getreplyurl(replied_message.caption)
                    reply_data = mdata(reply_url)
                    channel_id = reply_data.channel_id
            elif replied_message:
                if replied_message.text:
                    content = f"╭──**@{replied_message.from_user.first_name[:250]}** *{replied_message.text[:50]}...*\n"
                elif replied_message.caption:
                    content = f"╭──**@{replied_message.from_user.first_name[:250]}** *{replied_message.caption[:50]}...*\n"
            if not channel_id:
                data = await bot.db.getActivech(chatid=message.chat.id)
                if not data:
                    return
                channel_id, guild_id = data
            embed = discord.Embed(title = message.from_user.first_name[:250], color=config.color)
            if message.text:
                embed_description+= (html_to_markdown(message.html_text)+"\n")
            elif message.caption:
                embed_description+= (html_to_markdown(message.html_caption)+"\n")
            if message.animation:
                embed_description+= "Some GIF\n"
            if message.audio:
                embed_description+= "🔉Some Audio\n"
            if message.document:
                embed_description+= "📄Some Document\n"
            if message.photo:
                embed_description+= "🖼Some Photo\n"
            if message.sticker:
                embed_description+= "🐾Some Sticker\n"
            if message.story:
                embed_description+= "📲Some Story\n"
            if message.video:
                embed_description+= "🎬Some Video\n"
            if message.voice:
                embed_description+= "🎤Some VoiceNote\n"
            if embed_description=="":
                return
            embed.description = embed_description
            await send_message(self.session, DCTOKEN, channel_id, content=content, embed=embed, reply=reply_data)
        except:
            traceback.print_exc()
            
    @limit_calls_per_second(max_calls=4)
    async def forward_to_telegram(self, message: Message, replied_messageid: int = None):
        try:
            channel = message.channel
            channel_name = channel.name
            author = message.author
            author_name = author.display_name
            reply = None
            content = None
            reply_params = None
            muted_user = await self.db.getUser(message.guild.id, author.id)
            if muted_user:
                return
            privacy  = await self.db.checkPrivacy(author.id)
            if privacy:
                return
            guild_data = await self.db.getGuild(message.guild)
            if not guild_data or not guild_data.groupid or channel.id in guild_data.mutedchannelids:
                return
                
            if replied_messageid:
                try:
                    rmsg = await message.channel.fetch_message(replied_messageid)
                    if rmsg.author.id==self.user.id:
                        if len(rmsg.embeds)>0 and rmsg.embeds[0].description and rmsg.embeds[0].description!="":
                            if rmsg.embeds[0].title and rmsg.embeds[0].title!="":
                                reply = f'<blockquote><strong><a href="{rmsg.jump_url}">Reply To: </a></strong>@{rmsg.embeds[0].title}\n'+ f"{rmsg.embeds[0].description[:50]}</blockquote>\n"
                    else:
                        if rmsg.content:
                            reply_content = cleanMessage(rmsg)
                            reply_author = rmsg.author.display_name
                            reply = f'<blockquote><strong><a href="{rmsg.jump_url}">Reply To: </a></strong>@{reply_author}\n'
                            if reply_content and reply_content!="":
                                reply = reply + f"{reply_content[:50]}</blockquote>\n"
                            else:
                                reply = reply + "</blockquote>\n"
                except:
                    reply = None
            if reply:
                content = reply + f'<u><strong><a href="{message.jump_url}">{author_name}</a></strong></u>|<u>#{channel_name}</u>\n'
            else:
                content = f'<u><strong><a href="{message.jump_url}">{author_name}</a></strong></u>|<u>#{channel_name}</u>\n'
            if message.content and message.content!="":
                message_content = cleanMessage(message)
                message_content = markdown_to_html(message_content)
                content = content + f"{message_content}\n"
            if message.attachments:
                for i, attachment in enumerate(message.attachments):
                    content = content + f'<a href="{attachment.url}">{i+1}. Attachment {i+1}</a>\n'
            try:
                await self.telegram_bot.send_message(guild_data.groupid, content, parse_mode="html", reply_parameters = reply_params, link_preview_options=LinkPreviewOptions(is_disabled=True))
            except ApiTelegramException as e:
                if e.description=="Bad Request: chat not found":
                    await self.db.deleteGuild(message.guild.id)
            except SlowDownError as e:
                time_to_wait = 1 - (time.time() - (deque(maxlen=4)[0] if len(deque(maxlen=4)) > 0 else time.time()))
                await asyncio.sleep(max(time_to_wait, 0))
                await self.telegram_bot.send_message(guild_data.groupid, reply, parse_mode="html", reply_parameters = reply_params)
        except:
            traceback.print_exc()

class TelegramBot(AsyncTeleBot):
    def __init__(self, token, discord_bot=None):
        super().__init__(token)
        self.discord_bot = discord_bot
        self.add_custom_filter(asyncio_filters.IsAdminFilter(self))

        @self.message_handler(commands=['start'])
        async def send_welcome(message):
            content = (
                f"Hello {message.from_user.first_name}!\n"
                "This bot will help you connect you Discord & Telegram group\n"
                "For Integration setup go to Discord and use /help in the server where Telecord is present.\n\n"
                "Note: Only Discord server Admins or Mods can start integration setup."
            )
            await self.reply_to(message, content)

        @self.message_handler(commands=['help'])
        async def send_help(message):
            content = (
                "These are available useful commands!\n\n"
                "/link <code>: Connect your Telegram group with Discord Server\n"
                "/unlink: Disconnect your Telegram group from Discord Server\n"
                "/mute [channel_id]: Stop incoming messages from this channel\n"
                "/forcemute [channel_id]: Force mute disables unmute command\n"
                "/unmute [channel_id]: Unmute incoming messages from this channel\n"
                "/muteuser [user_id]: Stop incoming messages from this user\n"
                "/unmuteuser [user_id]: Unmute incoming messages from this user\n"
                "/privacy: Enable/Disable forwading your messages to Discord\n\n"
                "Note: You can also mute Discord channel or user by replying to the Telecord message.\n"
                "Note: Mute/Unmute command doesn't work on Telegram Group members.\n"
                "Note: Commands only work in Telegram Groups."
            )
            await self.reply_to(message, content)

        @self.message_handler(commands=['changechannel'])
        async def change_channel(message):
            query = "SELECT guildid FROM auth WHERE groupid = ?;"
            async with self.discord_bot.db.execute(query, (message.chat.id,)) as cursor:
                row = await cursor.fetchone()
            if not row:
                await self.send_message(message.chat.id, "Your Telegram Group is not connected to any Discord Server!")
                return
            guildid = row[0]
            guild = self.discord_bot.get_guild(guildid)
            if not guild:
                guild = await self.discord_bot.fetch_guild(guildid)
            if not guild:
                await self.discord_bot.db.deleteGuild(guildid)
                await self.send_message(message.chat.id, "Discord Server not found!")
                return
            channels[guild.id] = []
            for channel in guild.text_channels:
                permissions = channel.permissions_for(guild.me)
                if permissions.view_channel and permissions.send_messages and permissions.read_message_history:
                    channels[guild.id].append(channel)
                    
            if not channels:
                await self.send_message(message.chat.id, "Insufficient Permissions!\nNo channel found where bot can send message!")
                return
            markup = generate_keyboard(channels, guild.id, 0)
            await self.send_message(message.chat.id, "Choose a channel:", reply_markup=markup)

        @self.message_handler(commands=['link'], chat_types=['group', 'supergroup'], is_chat_admin=True)
        async def send_link(message):
            user_message = message.text
            content = user_message.split()[1:]
            if content:
                try:
                    code = int(content[0].strip())
                except:
                    await self.send_message(message.chat.id, "Please provide valid authentication code!")
                    return
            else:
                await self.send_message(message.chat.id, "You didn't provide the authentication code!")
                return
            query = "SELECT code, guildid FROM auth;"
            async with self.discord_bot.db.execute(query) as cursor:
                rows = await cursor.fetchall()
            if rows:
                for row in rows:
                    if code==row[0]:
                        code, guildid = row
                        guild = self.discord_bot.get_guild(guildid)
                        if not guild:
                            guild = await self.discord_bot.fetch_guild(guildid)
                        if not guild:
                            await self.discord_bot.db.deleteGuild(guildid)
                            await self.send_message(message.chat.id, "Discord Server not found!")
                            return
                        for channel in guild.text_channels:
                            permissions = channel.permissions_for(guild.me)
                            if permissions.view_channel and permissions.send_messages and permissions.read_message_history:
                                await self.discord_bot.db.updateGuild(guildid, groupid=message.chat.id, invite= message.chat.invite_link, code_used=True)
                                await self.discord_bot.db.insertActivech(guildid, message.chat.id, channel.id)
                                await self.send_message(message.chat.id, f"Successfully connected to {guild.name}!\nTo change current chatting channel use /changechannel command.")
                                msg = await self.send_message(message.chat.id, f"You are currently chatting in #{channel.name}!")
                                await self.pin_chat_message(message.chat.id, msg.message_id, disable_notification=True)
                                embed = discord.Embed(title="Telegram Group successfully connected!", description=f"{guild.name} has successfully connected with `{message.chat.first_name}` Telegram Group.", color=config.success_color)
                                embed.set_footer(text="Admins can disconnect Telegram anytime using /unlink command.")
                                await channel.send(embed=embed)
                                return
            await self.send_message(message.chat.id, "Please provide valid authentication code!")

        @self.message_handler(commands=['unlink'], chat_types=['group', 'supergroup'], is_chat_admin=True)
        async def send_unlink(message):
            query = "SELECT guildid FROM auth WHERE groupid = ?;"
            async with self.discord_bot.db.execute(query, (message.chat.id,)) as cursor:
                row = await cursor.fetchone()
            if row:
                await self.discord_bot.db.deleteGuild(guildid)
                await self.send_message(message.chat.id, "Unlinked Discord Server successfully!")
                return
            await self.send_message(message.chat.id, "Telegram Group is not connected to any Discord Server!")

        @self.message_handler(commands=['mute'], chat_types=['group', 'supergroup'], is_chat_admin=True)
        async def send_mute(message):
            user_message = message.text
            content = user_message.split()[1:]
            channelid = None
            if content:
                try:
                    channelid = int(content[0].strip())                     
                except:
                    await self.send_message(message.chat.id, "Please provide valid channel id!")
                    return
            elif message.reply_to_message and message.reply_to_message.from_user.username.lower()=="telecord_userbot":
                reply_message = message.reply_to_message
                reply_url = getreplyurl(replied_message.text)
                reply_data = None
                if reply_url:
                    reply_data = mdata(reply_url)
                if not reply_url or not reply_data:
                    await self.send_message(message.chat.id, "This message doesn't contain channel info!")
                    return
                channelid = reply_data.channel_id
            if not channelid:
                await self.send_message(message.chat.id, "Please provide channel id!")
                return
            query = "SELECT guildid FROM auth WHERE groupid = ?;"
            async with self.discord_bot.db.execute(query, (message.chat.id,)) as cursor:
                row = await cursor.fetchone()
            if not row:
                await self.send_message(message.chat.id, "Your Telegram Group is not connected to any Discord Server!")
                return
            guildid = row[0]
            guild_data = await self.discord_bot.db.getGuild(guildid)
            if channelid in guild_data.mutedchannelids:
                await self.send_message(message.chat.id, "Channel is already muted!")
                return
            channel = self.discord_bot.get_channel(channelid)
            if not channel:
                channel = await self.discord_bot.fetch_channel(channelid)
            if not channel or channel.guild!=guildid:
                await self.send_message(message.chat.id, "Channel not found!")
                return
            guild_data.mutedchannelids.append(channelid)
            await self.discord_bot.db.updateGuild(guildid, mutedchannelids=guild_data.mutedchannelids)
            await self.send_message(message.chat.id, "Channel muted successfully!")  

        @self.message_handler(commands=['forcemute'], chat_types=['group', 'supergroup'], is_chat_admin=True)
        async def send_forcemute(message):
            query = "SELECT guildid FROM auth WHERE groupid = ?;"
            async with self.discord_bot.db.execute(query, (message.chat.id,)) as cursor:
                row = await cursor.fetchone()
            if not row:
                await self.send_message(message.chat.id, "Your Telegram Group is not connected to any Discord Server!")
                return
            guildid = row[0]
            guild_data = await self.discord_bot.db.getGuild(guildid)
            if guild_data.force_mute:
                await self.discord_bot.db.updateGuild(guildid, force_mute=False)
                await self.send_message(message.chat.id, "Force mute setting turned off!")
            else:
                await self.discord_bot.db.updateGuild(guildid, force_mute=True)
                await self.send_message(message.chat.id, "Force mute setting turned on!")

        @self.message_handler(commands=['unmute'], chat_types=['group', 'supergroup'], is_chat_admin=True)
        async def send_unmute(message):
            user_message = message.text
            content = user_message.split()[1:]
            channelid = None
            if content:
                try:
                    channelid = int(content[0].strip())                     
                except:
                    await self.send_message(message.chat.id, "Please provide valid channel id!")
                    return
            elif message.reply_to_message and message.reply_to_message.from_user.username.lower()=="telecord_userbot":
                reply_message = message.reply_to_message
                reply_url = getreplyurl(replied_message.text)
                reply_data = None
                if reply_url:
                    reply_data = mdata(reply_url)
                if not reply_url or not reply_data:
                    await self.send_message(message.chat.id, "This message doesn't contain channel info!")
                    return
                channelid = reply_data.channel_id
            if not channelid:
                await self.send_message(message.chat.id, "Please provide channel id!")
                return
            query = "SELECT guildid FROM auth WHERE groupid = ?;"
            async with self.discord_bot.db.execute(query, (message.chat.id,)) as cursor:
                row = await cursor.fetchone()
            if not row:
                await self.send_message(message.chat.id, "Your Telegram Group is not connected to any Discord Server!")
                return
            guildid = row[0]
            guild_data = await self.discord_bot.db.getGuild(guildid)
            if guild_data.force_mute:
                await self.send_message(message.chat.id, "Force Mute setting is on!\n\nTurn off force mute to unmute channels!")
                return
            if channelid not in guild_data.mutedchannelids:
                await self.send_message(message.chat.id, "Channel is already unmuted!")
                return
            channel = self.discord_bot.get_channel(channelid)
            if not channel:
                channel = await self.discord_bot.fetch_channel(channelid)
            if not channel or channel.guild!=guildid:
                await self.send_message(message.chat.id, "Channel not found!")
                return
            guild_data.mutedchannelids.remove(channelid)
            await self.discord_bot.db.updateGuild(guildid, mutedchannelids=guild_data.mutedchannelids)
            await self.send_message(message.chat.id, "Channel unmuted successfully!")
        
        @self.message_handler(commands=['muteuser'], chat_types=['group', 'supergroup'], is_chat_admin=True)
        async def send_muteuser(message):
            user_message = message.text
            content = user_message.split()[1:]
            userid = None
            guild = None
            if content:
                try:
                    userid = int(content[0].strip())                     
                except:
                    await self.send_message(message.chat.id, "Please provide valid User id!")
                    return
            elif message.reply_to_message and message.reply_to_message.from_user.username.lower()=="telecord_userbot":
                reply_message = message.reply_to_message
                reply_url = getreplyurl(replied_message.text)
                reply_data = None
                if reply_url:
                    reply_data = mdata(reply_url)
                if not reply_url or not reply_data:
                    await self.send_message(message.chat.id, "This message doesn't contain User info!")
                    return
                channel_id = reply_data.channel_id
                message_id = reply_data.message_id
                channel = await self.discord_bot.fetch_guild(channel_id)
                if not channel:
                    await self.send_message(message.chat.id, "That message doesn't exist anymore!")
                    return
                guild = channel.guild
                replymessage = await channel.fetch_message(message_id)
                if not replymessage:
                    await self.send_message(message.chat.id, "That message doesn't exist anymore!")
                    return
                userid = replymessage.author.id
            if not userid:
                await self.send_message(message.chat.id, "Please provide User id!")
                return
            if not guild:
                query = "SELECT guildid FROM auth WHERE groupid = ?;"
                async with self.discord_bot.db.execute(query, (message.chat.id,)) as cursor:
                    row = await cursor.fetchone()
                if not row:
                    await self.send_message(message.chat.id, "Your Telegram Group is not connected to any Discord Server!")
                    return
                guildid = row[0]
                guild = self.discord_bot.get_guild(guildid)
                if not guild:
                    guild = await self.discord_bot.fetch_guild(guildid)
            user = guild.get_member(userid)
            if not user:
                user = await guild.fetch_member(userid)
            if not user:
                await self.send_message(message.chat.id, "User not found!")
                returnreturn
            status = await self.discord_bot.db.getUser(guild.id, user.id)
            if status:
                await self.send_message(message.chat.id, "User is already muted!")
                return
            await self.discord_bot.db.updateUser(guild.id, user.id, muted=True)
            await self.send_message(message.chat.id, "User muted successfully!")
            
        @self.message_handler(commands=['unmuteuser'], chat_types=['group', 'supergroup'], is_chat_admin=True)
        async def send_unmuteuser(message):
            user_message = message.text
            content = user_message.split()[1:]
            userid = None
            guild = None
            if content:
                try:
                    userid = int(content[0].strip())                     
                except:
                    await self.send_message(message.chat.id, "Please provide valid User id!")
                    return
            elif message.reply_to_message and message.reply_to_message.from_user.username.lower()=="telecord_userbot":
                reply_message = message.reply_to_message
                reply_url = getreplyurl(replied_message.text)
                reply_data = None
                if reply_url:
                    reply_data = mdata(reply_url)
                if not reply_url or not reply_data:
                    await self.send_message(message.chat.id, "This message doesn't contain User info!")
                    return
                channel_id = reply_data.channel_id
                message_id = reply_data.message_id
                channel = await self.discord_bot.fetch_guild(channel_id)
                if not channel:
                    await self.send_message(message.chat.id, "That message doesn't exist anymore!")
                    return
                guild = channel.guild
                replymessage = await channel.fetch_message(message_id)
                if not replymessage:
                    await self.send_message(message.chat.id, "That message doesn't exist anymore!")
                    return
                userid = replymessage.author.id
            if not userid:
                await self.send_message(message.chat.id, "Please provide User id!")
                return
            if not guild:
                query = "SELECT guildid FROM auth WHERE groupid = ?;"
                async with self.discord_bot.db.execute(query, (message.chat.id,)) as cursor:
                    row = await cursor.fetchone()
                if not row:
                    await self.send_message(message.chat.id, "Your Telegram Group is not connected to any Discord Server!")
                    return
                guildid = row[0]
                guild = self.discord_bot.get_guild(guildid)
                if not guild:
                    guild = await self.discord_bot.fetch_guild(guildid)
            user = guild.get_member(userid)
            if not user:
                user = await guild.fetch_member(userid)
            if not user:
                await self.send_message(message.chat.id, "User not found!")
                return
            status = await self.discord_bot.db.getUser(guild.id, user.id)
            if not status:
                await self.send_message(message.chat.id, "User is already unmuted!")
                return
            await self.discord_bot.db.updateUser(guild.id, user.id, muted=False)
            await self.send_message(message.chat.id, "User unmuted successfully!")
            
        @self.message_handler(commands=['privacy'], chat_types=['group', 'supergroup'])
        async def send_privacy(message):
            privacy = await self.discord_bot.db.checkPrivacy(message.from_user.id)
            new_privacy = not privacy
            p = "on" if new_privacy else "off"
            w = "won't" if new_privacy else "will"
            await self.discord_bot.db.updatePrivacy(message.from_user.id, privacy=new_privacy)
            await self.send_message(message.chat.id, f"Privacy mode turned {p}! Your messages {w} be forwaded to discord.")

        @self.message_handler(func=lambda message: True, content_types=['photo', 'text', 'sticker', 'animation', 'audio', 'voice', 'video', 'document'], chat_types=['group', 'supergroup'])
        async def echo_all(message):
            replied_message = None
            if message.reply_to_message:
                replied_message = message.reply_to_message
            
            await self.forward_to_discord(message, replied_message)
            
        @self.callback_query_handler(func=lambda call: True)
        async def handle_query(call):
            data = call.data
            inline_message = call.message
            await self.edit_message_reply_markup(inline_message.chat.id, message_id=inline_message.message_id , reply_markup=None)
            chat = await self.get_chat(inline_message.chat.id)
            last_pinned_message = chat.pinned_message
            if last_pinned_message and last_pinned_message.from_user.username.lower()=="telecord_userbot":
                await self.unpin_chat_message(inline_message.chat.id, message_id=last_pinned_message.message_id)
            query, guildid, timestamp = data.split()
            guildid = int(guildid)
            timestamp = int(timestamp)
            if (int(time.time())-timestamp)>60:
                if guildid in channels:
                    del channels[guildid]
                return
            if guildid not in channels:
                await self.answer_callback_query(call.id, f"Channel data flushed out! Please try /changechannel command again.")
                return

            if query.isdigit():
                channel_id = int(query)
                selected_channel = next((channel for channel in channels[guildid] if channel.id == channel_id), None)
                if selected_channel:
                    await self.discord_bot.db.updateActivech(selected_channel.id, guildid=guildid)
                    await self.answer_callback_query(call.id, f"You selected: {selected_channel.name}")
                    msg = await self.send_message(call.message.chat.id, f"You are currently chatting in #{selected_channel.name}!")
                    await self.pin_chat_message(call.message.chat.id, msg.message_id, disable_notification=True)
            else:
                if query.startswith("prev_"):
                    current_page = int(query.split("_")[1])
                    new_page = current_page - 1
                elif query.startswith("next_"):
                    current_page = int(query.split("_")[1])
                    new_page = current_page + 1
                
                markup = generate_keyboard(channels, guildid, new_page)
                await self.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    async def forward_to_discord(self, message, replied_message):
        privacy = await self.discord_bot.db.checkPrivacy(message.from_user.id)
        if privacy:
            return
        self.discord_bot.dispatch("tgmessage", message, replied_message)

    
bot = DiscordBot()
telegram_bot = TelegramBot(token = TGTOKEN, discord_bot = bot)
bot.telegram_bot = telegram_bot

@bot.hybrid_command(name="unmute", description="Starts forwading messages of the channel", with_app_command = True)
@app_commands.checks.has_permissions(manage_guild=True)
@commands.has_permissions(manage_guild=True)
@app_commands.describe(channel="Select channel that you want to unmute")
async def unmute_command(ctx: commands.Context, channel: TextChannel = None):
    try:
        channel = channel if channel else ctx.channel
        guild_data = await bot.db.getGuild(ctx.guild)
        if not guild_data or not guild_data.groupid:
            guild_data = await bot.db.insertGuild(ctx.guild.id)
            embed = discord.Embed(title="Telegram Group Not Found!", description="<a:pending:1241031324119072789> No Telegram Group is connected with Server currently.", color=config.error_color)
        else:
            if guild_data.force_mute:
                embed = discord.Embed(title="Force Mute Activated!", description="<a:pending:1241031324119072789> Can't Unmute! Channel has been force muted by Telegram Admin.", color=config.error_color)
            else:
                mutedchannelids = guild_data.mutedchannelids
                if channel.id not in mutedchannelids:
                    embed = discord.Embed(description="<a:chk:1241031331756904498> Channel Already Unmuted!", color=config.success_color)
                else:
                    mutedchannelids.remove(channel.id)
                    await bot.db.updateGuild(ctx.guild.id, mutedchannelids=mutedchannelids)
                    embed = discord.Embed(title="Channel Unmuted Successfully! <a:chk:1241031331756904498>", description = "Messages will now be forwarded to the connected Telegram Group", color=config.success_color)
        await ctx.send(embed=embed)
    except:
        traceback.print_exc()

@bot.hybrid_command(name="mute", description="Stop forwading messages of the channel", with_app_command = True)
@app_commands.checks.has_permissions(manage_guild=True)
@commands.has_permissions(manage_guild=True)
@app_commands.describe(channel="Select channel that you want to mute")
async def mute_command(ctx: commands.Context, channel: TextChannel = None):
    try:
        channel = channel if channel else ctx.channel
        guild_data = await bot.db.getGuild(ctx.guild)
        if not guild_data or not guild_data.groupid:
            guild_data = await bot.db.insertGuild(ctx.guild.id)
            embed = discord.Embed(title="Telegram Group Not Found!", description="<a:pending:1241031324119072789> No Telegram Group is connected with Server currently.", color=config.error_color)
        else:
            mutedchannelids = guild_data.mutedchannelids
            if channel.id in mutedchannelids:
                embed = discord.Embed(description="<a:chk:1241031331756904498> Channel Already Muted!", color=config.success_color)
            else:
                mutedchannelids.append(channel.id)
                await bot.db.updateGuild(ctx.guild.id, mutedchannelids=mutedchannelids)
                embed = discord.Embed(title="Channel Muted Successfully! <a:chk:1241031331756904498>", description = "Messages won't be forwarded to the connected Telegram Group.", color=config.success_color)
        await ctx.send(embed=embed)
    except:
        traceback.print_exc()
          
@bot.hybrid_command(name="help", description="Show guide to how to get started.", with_app_command = True)
async def send_bot_help(ctx: commands.Context):
    embed = discord.Embed(title="Telecord Help Menu!", color=config.color)
    embed.description = f"A Bot designed to facilitate communication between Discord and Telegram. It forwards messages from Telegram to Discord and vice versa."
    embed.add_field(name=f"{config.prefix}help", value="Shows Telecord help menu", inline=False)
    embed.add_field(name=f"{config.prefix}info", value="Show info about connected Telegram Group", inline=False)
    embed.add_field(name=f"{config.prefix}link", value="Setup discord-telegram connection", inline=False)
    embed.add_field(name=f"{config.prefix}unlink", value="Revoke discord-telegram connection", inline=False)
    embed.add_field(name=f"{config.prefix}mute <channel>", value="Stop forwading messages of the channel", inline=False)
    embed.add_field(name=f"{config.prefix}unmute <channel>", value="Starts forwading messages of the channel", inline=False)
    embed.add_field(name=f"{config.prefix}ping", value="Checks bot latency with discord API", inline=False)
    embed.add_field(name=f"{config.prefix}privacy <on/off>", value="Stop forwading your message to telegram", inline=False)
    await ctx.send(embed=embed)

@bot.hybrid_command(name="info", description="Show info about connected Telegram Group", with_app_command = True)
async def info_command(ctx: commands.Context):
    try:
        guild_data = await bot.db.getGuild(ctx.guild)
        if not guild_data or not guild_data.groupid:
            guild_data = await bot.db.insertGuild(ctx.guild.id)
            embed = discord.Embed(title="Telegram Group Not Found!", description="<a:pending:1241031324119072789> No Telegram Group is connected with Server currently.", color=config.error_color)
        else:
            chat = await bot.telegram_bot.get_chat(guild_data.groupid)
            embed = discord.Embed(title="Telegram Group Info!", description="", color=config.color)
            embed.add_field(name="Group name", value=chat.title, inline=False)
            embed.add_field(name="Type", value=chat.type, inline=False)
            description = chat.description if chat.description else "None"
            embed.add_field(name="Description", value=description, inline=False)
            embed.add_field(name="Invite Link", value=chat.invite_link, inline=False)
        await ctx.send(embed=embed)
    except:
        traceback.print_exc()
        
@bot.hybrid_command(name="link", description="Starts Discord-Telegram Integration Process", with_app_command = True)
@app_commands.checks.has_permissions(manage_guild=True)
@commands.has_permissions(manage_guild=True)
async def link_command(ctx: commands.Context):
    try:
        guild_data = await bot.db.getGuild(ctx.guild)
        if not guild_data:
            guild_data = await bot.db.insertGuild(ctx.guild.id)
        if guild_data.groupid:
            embed = discord.Embed(title="Telegram Group already connected!", description="There's already a Telegram Group attached to your Server! Unlink it first to add another.", color=config.error_color)
            
        else:
            code = int(int(time.time())+ctx.guild.id)
            await bot.db.updateGuild(ctx.guild.id, code=code)
            embed = discord.Embed(title="Telegram Group integration Setup", description = "Follow these steps to link your Discord server with a Telegram group:", color=config.color)
            embed.add_field(
                name="1. Create a Telegram Group",
                value="Go to Telegram and create a new **Group** where you'll add the bot.",
                inline=False
            )
    
            embed.add_field(
                name="2. Add Telecord Bot",
                value="Add the **Telecord** bot to your Telegram group and make sure it has **Admin** permissions to function properly.",
                inline=False
            )
    
            embed.add_field(
                name="3. Link the Group with Discord",
                value=f"Use the following command in your Telegram group to connect the group with server: `/link {code}`",
                inline=False
            )
            embed.set_footer(text="Tip: Don't share the code as it can only be used once.")
        await ctx.send(embed=embed)
    except:
        traceback.print_exc()

@bot.hybrid_command(name="unlink", description="Revoke Discord-Telegram connection.", with_app_command = True)
@app_commands.checks.has_permissions(manage_guild=True)
@commands.has_permissions(manage_guild=True)
async def unlink_command(ctx: commands.Context):
    try:
        guild_data = await bot.db.getGuild(ctx.guild)
        if guild_data:
            guild_data = await bot.db.deleteGuild(ctx.guild.id)
            embed = discord.Embed(title="Unlinked Successfully!", description="Your server has been unlinked from telegram group successfully.", color=config.success_color)
        else:
            embed = discord.Embed(title="No Links Found!", description = "Your server isn't connected to any telegram group", color=config.error_color)
        await ctx.send(embed=embed)
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

@bot.hybrid_command(name="privacy", description="Stop forwading your messages to Telegram", with_app_command = True)
async def privacy_command(ctx: commands.Context):
    try:
        privacy = await bot.db.checkPrivacy(ctx.author.id)
        new_privacy = not privacy
        p = "on" if new_privacy else "off"
        w = "won't" if new_privacy else "will"
        await bot.db.updatePrivacy(ctx.author.id, privacy=new_privacy)
        embed = discord.Embed(title=f"Privacy mode turned {p}!", description=f"<a:chk:1241031331756904498> Your messages {w} be forwaded to Telegram.", color=config.success_color)
        await ctx.send(embed=embed)
    except:
        traceback.print_exc()

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(title="Permission Denied", description="You lack the required permissions to use this command.", color=discord.Color.red())
        await ctx.send(embed=embed)
    elif isinstance(error, commands.BotMissingPermissions):
        embed = discord.Embed(title="Bot Missing Permissions", description="The bot doesn't have the necessary permissions to execute this command.", color=discord.Color.red())
        await ctx.send(embed=embed)
    elif isinstance(error, commands.CommandNotFound):
        pass
    elif isinstance(error, commands.BadArgument):
        embed = discord.Embed(title="Invalid Argument", description="The arguments provided are invalid. Check the usage and try again.", color=discord.Color.red())
        await ctx.send(embed=embed)
    elif isinstance(error, commands.CommandInvokeError):
        embed = discord.Embed(title="Command Error", description="An error occurred while executing the command. Please try again later.", color=discord.Color.red())
        await ctx.send(embed=embed)
        traceback.print_exc()
    else:
        embed = discord.Embed(title="Error", description="An unexpected error occurred.", color=discord.Color.red())
        await ctx.send(embed=embed)
        traceback.print_exc()

class Telecord:
    def __init__(self):
        self.discord_bot = bot
        self.telegram_bot = telegram_bot

    async def dcstart(self):
        try:
        	await self.discord_bot.start(DCTOKEN)
        except:
            traceback.print_exc()

    async def tgstart(self):
        print("Telecord has connected to Telegram!")
        await self.telegram_bot.infinity_polling()
