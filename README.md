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

3. Set up your configuration:
   - Create a `settings.json` file based on the provided `settings.example.json`.
   - Fill in the required tokens and other configuration details.

4. Run the bot:

   ```bash
   python main.py
   ```

## Environment Variables

- Create a `.env` file in the root directory of the Telecord project.
   - Add the following variables to the `.env` file:
     ```
     DCTOKEN="Discord Bot Token"
     TGTOKEN="Telegram Bot Token"
     MONGODB_URL="YOUR MONGODB URL"
     MONGODB_NAME="YOUR DATABASE NAME"
     ```
     Replace `"YOUR MONGODB URL"` with the connection string you copied earlier and `"YOUR DATABASE NAME"` with the name of your MongoDB database.

- How to create MongoDB database for free: [Watch](https://youtu.be/jZ5MbbXbs7A)
   
## Dependencies

- [discord.py](https://pypi.org/project/discord.py/): Discord API wrapper for Python.
- [pyTelegramBotAPI](https://pypi.org/project/pyTelegramBotAPI/): Telegram Bot API wrapper for Python.
- [aiofiles](https://pypi.org/project/aiofiles/): Python library for handling local disk files in asyncio applications.
- [aiohttp](https://pypi.org/project/aiohttp/): Asynchronous HTTP Client/Server for asyncio and Python.
- [moviepy](https://pypi.org/project/moviepy/): Python library for video editing.
- [motor](https://pypi.org/project/motor/): Asynchronous driver for MongoDB.
- [python-dotenv](https://pypi.org/project/python-dotenv/): Read environment variables from `.env` file.

## Usage

Once Telecord is up and running, you can interact with it using various commands:

- `/start`: Setup your Discord-Telegram connection.
- `/end`: Disconnect your Discord-Telegram chat.
- `/mute`: Mute incoming messages from a specific channel.
- `/unmute`: Unmute incoming messages from a specific channel.
- `/help`: Get a guide on how to get started.

Additionally, you can use the following Discord-specific commands:

- `/ping`: Check the bot's latency with Discord API.

## Features

- Bidirectional communication between Discord and Telegram.
- Ability to mute/unmute specific channels.
- Command-based setup for ease of use.

## Contributors

- [Killua Zoldyck](https://github.com/killuazoldyckreal)

## License

This project is licensed under the [Apache License 2.0.](LICENSE).
