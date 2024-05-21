import os, aiofiles, re, aiohttp, string
import discord,random, json, traceback
from telebot.util import escape
from telebot import types
from moviepy.editor import VideoFileClip
import function as func 
BOT_TOKEN = func.tokens.dctoken


def generate_random_filename(length=20, extension=None):
    """Generate a random filename with the specified length and extension."""
    # Define characters to choose from (only alphabetic characters)
    characters = string.ascii_letters

    # Generate random filename
    random_filename = ''.join(random.choice(characters) for _ in range(length))

    # Add extension if provided
    if extension:
        random_filename += f'.{extension}'

    return random_filename

async def sendAttachments(message, tgbot, TELEGRAM_CHAT_ID, reply_params=None):
    media_group = []  # List to store media attachments
    try:
        for attachment in message.attachments:
            # Determine the type of attachment based on its URL extension
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
                # Default to InputMediaDocument if the attachment type is unknown
                media_group.append(types.InputMediaDocument(attachment.url))
        
        # Construct the message header with author and channel information
        header = f"{message.author.name} | #{message.channel.name}\n\n`{message.id}` | `{message.channel.id}`"
        # Escape markdown characters in the header
        content = escapeMD(header)
        # Send the header as a Markdown-formatted message
        await tgbot.send_message(TELEGRAM_CHAT_ID, content, parse_mode='markdownv2')
        # Send the media group to the specified Telegram chat
        msg = await tgbot.send_media_group(TELEGRAM_CHAT_ID, media_group, reply_parameters=reply_params)
        # Save the message ID mapping to a JSON file
        await save_to_json("jsonfiles/replydict.json", message.id, msg.message_id)
        return msg  # Return the sent message object

    except:
        traceback.print_exc()
        return None  # Return None if an exception occurs

async def sendEmoji(tgbot, message, items, reply_params=None):
    try:
        msgcontent, header, TELEGRAM_CHAT_ID = items
        # Check if message has single emoji
        if len(msgcontent) == 1:
            header = header + f"\n`{message.id}` | `{message.channel.id}`"
            caption = escapeMD(header)
            # Determine if the emoji is a PNG or GIF and send the emoji accordingly
            if ".png" in msgcontent[0]:
                msg = await tgbot.send_photo(TELEGRAM_CHAT_ID, msgcontent[0], caption=caption, parse_mode = "markdownv2", reply_parameters = reply_params)
            elif ".gif" in msgcontent[0]:
                msg = await tgbot.send_animation(TELEGRAM_CHAT_ID, msgcontent[0], caption=caption, parse_mode = "markdownv2", reply_parameters = reply_params)
            # Save the message ID mapping to a JSON file
            await save_to_json("jsonfiles/replydict.json", message.id, msg.message_id)
            return msg

        # Send multiple emojis as an album
        media_group = []
        for url in msgcontent:
            if ".png" in url:
                media_group.append(types.InputMediaPhoto(url))
            elif ".gif" in url:
                media_group.append(types.InputMediaAnimation(url))
        header = header + f"\n`{message.id}` | `{message.channel.id}`"
        content = escapeMD(header)
        msg = await self.tgbot.send_message(TELEGRAM_CHAT_ID, content, parse_mode="markdownv2", reply_parameters = reply_params)
        await save_to_json("jsonfiles/replydict.json", message.id, msg.message_id)
        await self.tgbot.send_media_group(TELEGRAM_CHAT_ID, media_group)
        return msg
    except:
        tracback.print_exc
        return None

async def sendAnimation(session, tgbot, message, items, reply_params = None):
    try:
        msgcontent, header, TELEGRAM_CHAT_ID = items
        # If the animation is from Tenor, get the direct URL
        if "tenor" in msgcontent:
            msgcontent = await get_direct_gif_url(session, msgcontent.strip())
        header = header + f"\n`{message.id}` | `{message.channel.id}`"
        caption = escapeMD(header)
        
        # Send the animation with the provided caption
        msg = await tgbot.send_animation(TELEGRAM_CHAT_ID, msgcontent, caption=caption, parse_mode="markdownv2", reply_parameters = reply_params)
        await save_to_json("jsonfiles/replydict.json", message.id, msg.message_id)
        return msg
    except:
        traceback.print_exc()
        return None

def getExtension(content_type):
    # Map content types to file extensions
    extensions = {
        'image/jpeg': 'jpg',
        'image/png': 'png',
        'image/svg+xml': 'svg',
        'image/gif': 'gif'
    }
    return extensions.get(content_type, '')

async def saveFile(filepath, content):
    try:
        async with aiofiles.open(filepath, mode='wb') as file:
            await file.write(content)
        return True
    except:
        traceback.print_exc()
        return False

async def downloadFile(session, url):
    async with session.get(url) as response:
        if response.status == 200:
            content_type = response.headers['Content-Type']
            file_extension = getExtension(content_type)

            if file_extension:
                filename = generate_random_filename(extension=file_extension)
                save_path = os.path.join("telegramdownloads", filename)
                content = await response.read()
                await saveFile(save_path, content)
                return save_path
    return None

async def getSavepath(file_id, animation: bool = False):
    # Get the file information using the file ID
    file_info = await tgbot.get_file(file_id)
    filepath = file_info.file_path

    # Construct the URL to download the file
    file_url = f'https://api.telegram.org/file/bot{func.tokens.tgtoken}/{filepath}'
    save_path = await downloadFile(session, file_url)

    if save_path
        if animation:
            # Convert video to GIF
            videoClip = VideoFileClip(save_path)
            videoClip.write_gif(gifpath)
            return save_path, gifpath
        return save_path
    return None

async def getTGMedia(session, tgbot, message, animation: bool = False):
    try:
        # Ensure the directory exists or create it
        if not os.path.exists("telegramdownloads"):
            os.makedirs("telegramdownloads")

        if message.animation:
            videopath, filepath = await getSavepath(message.animation.file_id)
            await delete_file(videopath)
            return filepath

        elif message.video:
            filepath = await getSavepath(message.video.file_id)
            return filepath

        elif message.voice:
            filepath = await getSavepath(message.voice.file_id)
            return filepath
        
        elif message.photo:
            filepaths = []
            for photo in message.photo
                filepath = await getSavepath(photo.file_id)
                filepaths.append(filepath)
            return filepaths

        elif message.document:
            filepath = await getSavepath(message.document.file_id)
            return filepath
        
        else:
            return None


    except Exception as e:
        traceback.print_exc()
        return None, None
    
    

def escapeMD(text):
    markdown_symbols = ["-", "|", "#", "+", "."]
    escaped_text = ""

    for char in text:
        if char in markdown_symbols:
            escaped_text += "\\" + char
        else:
            escaped_text += char

    return escaped_text


def remake_url(original_url):
    pattern = r"https://media\d.tenor.com/(.*)/.*\.gif"
    match = re.search(pattern, original_url)
    if match:
        new_url = "https://c.tenor.com/" + match.group(1) + "/tenor.gif"
        gifurl = new_url.replace("/m/", "/")
        return gifurl
    return None


async def download_file_size(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        content = await response.read()
        return len(content), content


def getRtext(message):
    try:
        emoji_pattern = r"<:(\w+):(\d+)>"
        animated_emoji_pattern = r"<a:(\w+):(\d+)>"
        user_pattern = r"<@!?(\d+)>"
        role_pattern = r"<@&(\d+)>"
        channel_pattern = r"<#(\d+)>"
        emoji_replacement = "https://cdn.discordapp.com/emojis/{0}.png"
        animated_emoji_replacement = "https://cdn.discordapp.com/emojis/{0}.gif"
        user_replacement = "@{0}"
        role_replacement = "@{0}"
        channel_replacement = "#{0}"
        emojis = re.findall(r"<a?:\w+:\d+>", message.content)
        non_emoji_text = re.sub(r"<a?:\w+:\d+>", "", message.content)
        only_emoji = len(non_emoji_text.strip()) == 0
        if only_emoji:
            replaced_message = re.sub(emoji_pattern, lambda match: emoji_replacement.format(match.group(2)) + ",", message.content)
            replaced_message = re.sub(animated_emoji_pattern, lambda match: animated_emoji_replacement.format(match.group(2)) + ",", replaced_message)
            replaced_message = replaced_message[:-1]
            r = [url.strip() for url in replaced_message.split(",") if url.strip() != ""]
            return r
        else:
            replaced_message = re.sub(user_pattern, lambda match: user_replacement.format(message.guild.get_member(int(match.group(1))).name), non_emoji_text)
            replaced_message = re.sub(role_pattern, lambda match: role_replacement.format(message.guild.get_role(int(match.group(1))).name), replaced_message)
            replaced_message = re.sub(channel_pattern, lambda match: channel_replacement.format(message.guild.get_channel(int(match.group(1))).name), replaced_message)
    except:
        traceback.print_exc()
        return None
    return replaced_message


async def delete_file(file_path):
    try:
        async with aiofiles.open(file_path, "rb") as f:
            os.remove(file_path)
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
    except Exception as e:
        print(f"Error deleting file '{file_path}': {e}")


async def get_direct_gif_url(session, tenor_url):
    async with session.get(tenor_url) as response:
        if response.status == 200:
            content = await response.text()
            start_index = content.find("https://media1.tenor.com/")
            end_index = content.find(".gif", start_index) + 4
            gif_url = content[start_index:end_index]
            gifurl = remake_url(gif_url)
            return gifurl
        else:
            return None


def is_valid_url(text):
    regex = re.compile(
        r"^(?:http|ftp)s?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )
    return re.match(regex, text) is not None

async def is_valid_private_chat(tgbot, chat_id):
    try:
        # Get chat information
        chat = await tgbot.get_chat(chat_id)
        
        # Check if the chat type is 'private'
        if chat.type == 'private':
            return True
        else:
            return False
    except telebot.apihelper.ApiException as e:
        # If an error occurs (e.g., chat not found), print the error and return False
        print(f"Error: {e}")
        return False

async def is_valid_user(tgbot, chat_id, user_id):
    try:
        chat_member = await tgbot.get_chat_member(chat_id, user_id)
        
        if chat_member.status =='member':
            return True  # The chat_id belongs to your bot and the chat belongs to the specified user_id
        else:
            return False  # The chat_id does not belong to your bot or the chat does not belong to the specified user_id
    except Exception as e:
        print("Error:", e)
        return False

async def send_reply(session, channel_id, message, author, reply_messageid=None):
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    headers = {
        "Authorization": f"Bot {BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "content": "",
        "embeds": [{
            "description": message.text,
            "color": func.settings.embed_color,
            "author": {
                "name": author
            }
        }]
    }
    if reply_messageid:
        data["message_reference"] = {
            "message_id": reply_messageid
        }
        data["allowed_mentions"] = {
            "replied_user": False
        }

    async with session.post(url, headers=headers, json=data) as response:
        if response.status == 200:
            response_json = await response.json()
            m_id = response_json.get('id')
            return m_id
        else:
            print(f"Failed to send message: {response.status}")
            return None

async def send_media(session, channel_id, author, file_path: Union[list, str], reply_messageid=None):
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    headers = {
        "Authorization": f"Bot {BOT_TOKEN}"
    }

    data = aiohttp.FormData()
    image_extensions = ['.png', '.jpg', '.jpeg', '.gif']

    # Create the payload JSON as a separate field
    payload_json = {"content": ""}

    if isinstance(file_path, str):
        file = open(file_path, 'rb')
        file_name = os.path.basename(file_path)
        file_extension = "."+file_path.split(".",-1)[1]
        if file_extension in image_extensions:
            payload_json["embeds"] = [{
                "image": {
                    "url": f"attachment://{file_name}"
                },
                "color": func.settings.embed_color,
                "author": {
                    "name": author
                }
            }]
        data.add_field('file', file, filename=file_name)

    else:
        for i, file_path in enumerate(file_path):
            with open(file_path, 'rb') as file:
                file_name = os.path.basename(file_path)
                file_extension = "."+file_name.split(".",-1)[1]
                data.add_field(f'file{i}', file, filename=file_name)
    
    if reply_messageid:
        payload_json["message_reference"] = {
            "message_id": reply_messageid
        }
    data.add_field('payload_json', json.dumps(payload_json))

    async with session.post(url, data=data, headers=headers) as response:
        file.close()
        if response.status == 200:
            response_json = await response.json()
            m_id = response_json.get('id')
            return m_id
        else:
            print(f"Failed to send message: {response.status}")
            return None

async def save_to_json(file_path, key, value):
    try:
        # Read the existing JSON file content
        async with aiofiles.open(file_path, mode='r') as file:
            content = await file.read()
            data = json.loads(content)
        
        # Append the new key-value pair
        data[str(key)] = value
        
        # Write the updated JSON back to the file
        async with aiofiles.open(file_path, mode='w') as file:
            await file.write(json.dumps(data, indent=4))
    
    except FileNotFoundError:
        # If the file does not exist, create it and add the key-value pair
        data = {str(key): value}
        async with aiofiles.open(file_path, mode='w') as file:
            await file.write(json.dumps(data, indent=4))
    except:
        traceback.print_exc()

async def load_user_data(file_path):
    try:
        async with aiofiles.open(file_path, 'r') as file:
            user_data = json.loads(await file.read())
    except FileNotFoundError:
        user_data = {}
    return user_data