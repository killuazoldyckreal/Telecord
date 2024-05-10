import os, aiofiles, re, aiohttp

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
