import os, aiofiles, re, aiohttp


async def sendAttachments(message, header, tgbot, TELEGRAM_CHAT_ID):
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
        await tgbot.send_message(
            TELEGRAM_CHAT_ID, content, parse_mode="markdownv2"
        )
        await tgbot.send_media_group(TELEGRAM_CHAT_ID, media_group)
        return True
    except:
        traceback.print_exc()
        return False

async def sendEmoji(tgbot, message, items):
    msgcontent, header, TELEGRAM_CHAT_ID = items
    # Check if message has single emoji
    if len(msgcontent) == 1:
        header = header + f"\n`{message.id}`"
        caption = escapeMD(header)
        if ".png" in msgcontent[0]:
            await tgbot.send_photo(
                TELEGRAM_CHAT_ID,
                msgcontent[0],
                caption=caption,
                parse_mode="markdownv2",
            )
        elif ".gif" in msgcontent[0]:
            await tgbot.send_animation(
                TELEGRAM_CHAT_ID,
                msgcontent[0],
                caption=caption,
                parse_mode="markdownv2",
            )
        return True

    # Send multiple emojis as an album
    media_group = []
    for url in msgcontent:
        if ".png" in url:
            media_group.append(types.InputMediaPhoto(url))
        elif ".gif" in url:
            media_group.append(types.InputMediaAnimation(url))
    header = header + f"\n`{message.id}`"
    content = escapeMD(header)
    await self.tgbot.send_message(
        TELEGRAM_CHAT_ID, content, parse_mode="markdownv2"
    )
    await self.tgbot.send_media_group(TELEGRAM_CHAT_ID, media_group)
    return True

async def sendAnimation(tgbot, message, items):
    msgcontent, header, TELEGRAM_CHAT_ID = items
    if "tenor" in msgcontent:
        msgcontent = await get_direct_gif_url(msgcontent.strip())
    header = header + f"\n`{message.id}`"
    caption = escapeMD(header)
    await tgbot.send_animation(
        TELEGRAM_CHAT_ID, msgcontent, caption=caption, parse_mode="markdownv2"
    )
    return True

def getReplyMsg(message_dict, dcchannel, message=None):
    rmsg = None
    replied_msgID = None
    if message:
        if message.text:
            replied_msgID = int(
                re.search(
                    r"\b\d+\b(?![\s\S]*\b\d+\b)", message.text
                ).group()
            )
        elif message.caption:
            replied_msgID = int(
                re.search(
                    r"\b\d+\b(?![\s\S]*\b\d+\b)", message.caption
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
    return rmsg

async def sendAnimation2DC(tgbot, message, dcchannel, rmsg=None):
    try:
        file_info = await tgbot.get_file(message.animation.file_id)
        file_content = await tgbot.download_file(file_info.file_path)
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
            await rmsg.reply(embed=embed, file=file, allowed_mentions=discord.AllowedMentions.none())
            await delete_file("image.gif")
        else:
            await dcchannel.send(embed=embed, file=file)
            await delete_file("image.gif")
    except:
        traceback.print_exc()
        return False
    return True

def getHeader(message):
    header = ""
    if message.embeds:
        embed = message.embeds[0]
        rcontent = embed.description
        if len(rcontent) > 60:
            rcontent = escape(message.content[:50]) + "..."
        author = embed.author.name
    else:
        if len(message.content) > 60:
            rcontent = escape(message.content[:50]) + "..."
        else:
            rcontent = escape(message.content)
        author = message.author.name
    header = f">*{escape(author)}:* {rcontent}\n⤷ "
    return header

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
            replaced_message = re.sub(
                emoji_pattern,
                lambda match: emoji_replacement.format(match.group(2)) + ",",
                message.content,
            )
            replaced_message = re.sub(
                animated_emoji_pattern,
                lambda match: animated_emoji_replacement.format(match.group(2)) + ",",
                replaced_message,
            )
            replaced_message = replaced_message[:-1]
            r = [
                url.strip() for url in replaced_message.split(",") if url.strip() != ""
            ]
            return r
        else:
            replaced_message = re.sub(
                user_pattern,
                lambda match: user_replacement.format(
                    message.guild.get_member(int(match.group(1))).name
                ),
                non_emoji_text,
            )
            replaced_message = re.sub(
                role_pattern,
                lambda match: role_replacement.format(
                    message.guild.get_role(int(match.group(1))).name
                ),
                replaced_message,
            )
            replaced_message = re.sub(
                channel_pattern,
                lambda match: channel_replacement.format(
                    message.guild.get_channel(int(match.group(1))).name
                ),
                replaced_message,
            )
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


async def get_direct_gif_url(tenor_url):
    async with aiohttp.ClientSession() as session:
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
