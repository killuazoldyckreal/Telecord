# Telecord

Telecord is a Python script that facilitates communication between Discord and Telegram by forwarding messages between the two platforms. It allows users to interact seamlessly across Discord channels and Telegram group chats.

## Setup

1. **Discord Bot Token**: Replace `"Discord Bot Token"` with your Discord bot token.
2. **Telegram Bot Token**: Replace `"Telegram Bot Token"` with your Telegram bot token.
3. **Discord Channel ID**: Enter your Discord channel ID in `DISCORD_CHANNEL_ID`.
4. **Telegram Chat ID**: Enter your Telegram group chat ID in `TELEGRAM_CHAT_ID`.

## Usage

1. Run the script.
2. Send messages in Discord or Telegram.
3. Telecord will forward messages between the platforms automatically.
4. Discord messages will be forwarded to Telegram group chat, and vice versa.

## Dependencies

- [discord.py](https://pypi.org/project/discord.py/): Discord API wrapper for Python.
- [pyTelegramBotAPI](https://pypi.org/project/pyTelegramBotAPI/): Telegram Bot API wrapper for Python.
- [aiofiles](https://pypi.org/project/aiofiles/): Python library for handling local disk files in asyncio applications.
- [aiohttp](https://pypi.org/project/aiohttp/): Asynchronous HTTP Client/Server for asyncio and Python.
- [moviepy](https://pypi.org/project/moviepy/): Python library for video editing.

## Configuration

- **Command Prefix**: Change the command prefix for Discord bot in `command_prefix`.
- **Discord Channel**: Modify the Discord channel settings in `DISCORD_CHANNEL_ID`.
- **Telegram Chat**: Adjust the Telegram group chat settings in `TELEGRAM_CHAT_ID`.

## Notes

- The script utilizes asyncio to handle concurrent events from both platforms.
- Markdown formatting is supported for message content.
- Messages are forwarded bidirectionally between Discord and Telegram.
- Ensure proper token and ID configurations for seamless functionality.

## Contributors

- [Killua Zoldyck](https://github.com/killuazoldyckreal)

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
