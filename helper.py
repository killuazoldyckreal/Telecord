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


import re
import traceback, time
from collections import deque
from functools import wraps
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from markdown import markdown

nonusable_md = ['.', '-','=','#','>']
firstpos_md = ['>']

class SlowDownError(Exception):
    pass

def limit_calls_per_second(max_calls=4):
    def decorator(func):
        call_times = deque(maxlen=max_calls)  

        @wraps(func)
        def wrapper(*args, **kwargs):
            current_time = time.time()
            if len(call_times) == max_calls and current_time - call_times[0] < 1:
                raise SlowDownError("Rate limit exceeded!")
            
            call_times.append(current_time)
            return func(*args, **kwargs)

        return wrapper
    return decorator

class DiscordMessage:
    def __init__(self, guild_id, channel_id, message_id):
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.message_id = message_id

def generate_keyboard(channels, guildid, page):
    markup = InlineKeyboardMarkup()
    start_index = page * 4
    end_index = start_index + 4
    prev_button = None
    next_button = None

    for channel in channels[guildid][start_index:end_index]:
        button = InlineKeyboardButton(f"#{channel.name}", callback_data=f"{channel.id} {guildid} {int(time.time())}")
        markup.add(button)
        
    nav_buttons = []
    if page > 0:
        prev_button = InlineKeyboardButton("Prev", callback_data=f"prev_{page} {guildid} {int(time.time())}")
    
    if end_index < len(channels[guildid]):
        next_button = InlineKeyboardButton("Next", callback_data=f"next_{page} {guildid} {int(time.time())}")
    
    if prev_button and next_button:
        markup.add(prev_button, next_button)
    elif prev_button:
        markup.add(prev_button)
    elif next_button:
        markup.add(next_button)
    return markup

def mdata(url):
    pattern = r"https://discord\.com/channels/(\d+)/(\d+)/(\d+)"
    match = re.match(pattern, url)
    if match:
        guild_id, channel_id, message_id = match.groups()
        return DiscordMessage(guild_id, channel_id, message_id)
    return None

def remove_reply_quote(text):
    pattern = r'^<b><a href="[^"]+"><blockquote>[^<]+<\/blockquote><\/a><\/b>'
    cleaned_text = re.sub(pattern, '', text)
    return cleaned_text.strip()

def getreplyurl(text):
    pattern = r'href="([^"]+)"'
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    return None

def html_to_markdown(html_text):
    escape_chars = r'\*_\~\|\`\\'
    html_text = re.sub(f'([{escape_chars}])', r'\\\1', html_text)
    html_text = re.sub(r'<b>(.*?)<\/b>', r'**\1**', html_text)
    html_text = re.sub(r'<strong>(.*?)<\/strong>', r'**\1**', html_text)
    html_text = re.sub(r'<i>(.*?)<\/i>', r'*\1*', html_text)
    html_text = re.sub(r'<em>(.*?)<\/em>', r'*\1*', html_text)
    html_text = re.sub(r'<u>(.*?)<\/u>', r'__\1__', html_text)
    html_text = re.sub(r'<s>(.*?)<\/s>', r'~~\1~~', html_text)
    html_text = re.sub(r'<strike>(.*?)<\/strike>', r'~~\1~~', html_text)
    html_text = re.sub(r'<span class="tg-spoiler">(.*?)<\/span>', r'||\1||', html_text)
    html_text = re.sub(r'<a href="(.*?)">(.*?)<\/a>', r'[\2](\1)', html_text)
    html_text = re.sub(r'<code>(.*?)<\/code>', r'`\1`', html_text)
    html_text = re.sub(r'<pre>(.*?)<\/pre>', r'```\1```', html_text, flags=re.DOTALL)
    def blockquote_replacement(match):
        blockquote_content = match.group(1).strip()
        return '\n'.join([f'> {line.strip()}' for line in blockquote_content.splitlines() if line.strip()]) + '\n\n'

    html_text = re.sub(r'<blockquote.*?>(.*?)<\/blockquote>', blockquote_replacement, html_text, flags=re.DOTALL)
    html_text = re.sub(r'<.*?>', '', html_text)

    return html_text

def replace_blockquote(html):
    pattern = r'<blockquote>(.*?)</blockquote>'
    
    def replacer(match):
        content = match.group(1)
        line_count = len(content.splitlines())        
        if line_count > 5:
            return f'<blockquote expandable>{content}</blockquote>'
        else:
            return f'<blockquote>{content}</blockquote>'
    return re.sub(pattern, replacer, html, flags=re.DOTALL)

def process_spoilers(text):
    parts = re.split(r'(<[^>]+>)', text)
    for i, part in enumerate(parts):
        if not part.startswith('<'):
            parts[i] = re.sub(r'\|\|(.*?)\|\|', r'<span class="tg-spoiler">\1</span>', part, flags=re.DOTALL)
    return ''.join(parts)

def remove_unsupported_tags(html_text):
    supported_tags = ['strong', 'i', 'u', 's', 'span', 'a', 'code', 'pre', 'blockquote', 'blockquote expandable']
    pattern = re.compile(r'<(\/?)(\w+).*?>')
    def tag_replacer(match):
        tag = match.group(2)
        if tag not in supported_tags:
            return ""
        return match.group(0)
    html_text = re.sub(pattern, tag_replacer, html_text)
    return html_text

def format_code_blocks(text):
    text = re.sub(r'```(\w+)\n([\s\S]+?)```', r'<pre><code language="\1">\2</code></pre>', text)
    text = re.sub(r'```(.*?)```', r'<pre>\1</pre>', text, flags=re.DOTALL)
    return text

def markdown_to_html(text: str):
    lines = text.splitlines()
    new_lines = ["<!--newline-->" if line == "" else line for line in lines]
    markdown_text = "\n".join(new_lines)
    markdown_text = re.sub(r'(\n>[^>]*\n)(\n>[^>]*\n)', r'\1<!-- -->\2', markdown_text)
    markdown_text = re.sub(r'__(.*?)__', r'<u>\1</u>', markdown_text)
    markdown_text = re.sub(r'~~(.*?)~~', r'<s>\1</s>', markdown_text, flags=re.DOTALL)
    markdown_text = format_code_blocks(markdown_text)
    html_text = markdown(markdown_text)
    html_text = process_spoilers(html_text)
    html_text = re.sub(r'(<\/blockquote>)\s*<!--newline-->\s*(<blockquote>)', r'\1\2', html_text)
    html_text = re.sub(r'(<blockquote>)\s*\n+', r'\1', html_text)
    html_text = replace_blockquote(html_text)
    html_text = html_text.replace("<em>","<i>")
    html_text = html_text.replace("</em>","</i>")
    html_text = remove_unsupported_tags(html_text)
    lines = html_text.splitlines()
    new_lines = [line for line in lines if line != ""]
    html_text = "\n".join(new_lines)
    html_text = html_text.replace("<!--newline-->","")
    return html_text

def cleanMessage(message):
    try:
        emoji_pattern = r"<a?:\w+:\d+>"  
        user_pattern = r"<@!?(\d+)>"  
        role_pattern = r"<@&(\d+)>"  
        channel_pattern = r"<#(\d+)>" 

        message_text = re.sub(emoji_pattern, "", message.content)

        def replace_user(match):
            user_id = int(match.group(1))
            user = message.guild.get_member(user_id)
            return f"@{user.display_name}" if user else "@UnknownUser"

        def replace_role(match):
            role_id = int(match.group(1))
            role = message.guild.get_role(role_id)
            return f"@{role.name}" if role else "@UnknownRole"

        def replace_channel(match):
            channel_id = int(match.group(1))
            channel = message.guild.get_channel(channel_id)
            return f"#{channel.name}" if channel else "#UnknownChannel"

        message_text = re.sub(user_pattern, replace_user, message_text)
        message_text = re.sub(role_pattern, replace_role, message_text)
        message_text = re.sub(channel_pattern, replace_channel, message_text)

        return message_text.strip()

    except Exception as e:
        traceback.print_exc()
        return None

async def send_message(session, BOT_TOKEN, channel_id, embed, content=None, reply=None):
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    headers = {
        "Authorization": f"Bot {BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    embed_data = embed.to_dict() if hasattr(embed, 'to_dict') else {}
    data = {
        "embeds": [embed_data]
    }
    
    if content and content != "":
        data["content"] = content
        
    if reply and reply.message_id:
        data["message_reference"] = {
            "message_id": reply.message_id
        }
        data["allowed_mentions"] = {
            "replied_user": False
        }

    async with session.post(url, headers=headers, json=data) as response:
        if response.status == 200:
            return True
        response_data = await response.json()
        print(f'Status: {response.status}, Response: {response_data}')
        return False
