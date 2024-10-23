# Telecord

Telecord is a Discord bot designed to facilitate communication between Discord and Telegram. It allows users to send messages from Telegram to Discord and vice versa, with additional features like muting channels and setting up connections.

## Installation

To use Telecord, follow these steps:

1. Clone the repository:

   ```bash
   git clone https://github.com/killuazoldyckreal/Telecord
   ```

2. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the bot:
   ```bash
   python main.py
   ```

## Environment Variables

- Create a `.env` file in the root directory of the Telecord project.
   - Add the following variables to the `.env` file:
     ```
     DCTOKEN="Discord Bot Token"
     TGTOKEN="Telegram Bot Token"
     ```
   
## Dependencies

- [discord.py](https://pypi.org/project/discord.py/): Discord API wrapper for Python.
- [pyTelegramBotAPI](https://pypi.org/project/pyTelegramBotAPI/): Telegram Bot API wrapper for Python.
- [aiofiles](https://pypi.org/project/aiofiles/): Python library for handling local disk files in asyncio applications.
- [aiohttp](https://pypi.org/project/aiohttp/): Asynchronous HTTP Client/Server for asyncio and Python.
- [python-dotenv](https://pypi.org/project/python-dotenv/): Read environment variables from `.env` file.
- [Markdown](https://pypi.org/project/Markdown/): This is a Python implementation of John Gruber's Markdown.
- [aiosqlite](https://pypi.org/project/aiosqlite/): Replicates the standard sqlite3 module, but with async versions.

## Usage

Once Telecord is up and running, you can interact with it using various commands:

### Telegram-side commands
- `/start`: Starts the Telecord bot
- `/changechannel`: Change Discord chatting channel
- `/link`: Command to link Discord server
- `/unlink`: Command to unlink Discord server
- `/mute`: Mute a Discord channel
- `/muteuser`: Mute a Discord user
- `/forcemute`: Force mute a Discord channel
- `/unmute`: Unmute a Discord channel
- `/unmuteuser`: Unmute a Discord user
- `/privacy`: Toggle send/stop your messages to discord
- `/help`: Get list of Telecord bot commands

### Discord-side commands
- `/help`: Shows Telecord help menu
- `/info`: Show info about connected Telegram Group
- `/link`: Setup discord-telegram connection
- `/unlink`: Revoke discord-telegram connection
- `/mute <channel>`: Stop forwading messages of the channel
- `/unmute <channel>`: Starts forwading messages of the channel
- `/ping`: Checks bot latency with discord API
- `/privacy <on/off>`: Stop forwading your message to telegram

## Features

- Bidirectional communication between Discord and Telegram.
- Ability to mute/unmute specific channels.
- Command-based setup for ease of use.

## Contributors

- [Killua Zoldyck](https://github.com/killuazoldyckreal)

## License

This project is licensed under the [Apache License 2.0.](LICENSE).
