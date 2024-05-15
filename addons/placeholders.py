from discord.ext import commands
from re import findall

class Placeholders:
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.variables = {
            "guilds": self.guilds_count,
            "users": self.users_count
        }
    
    def guilds_count(self) -> int:
        return len(self.bot.guilds)
    
    def users_count(self) -> int:
        return len(self.bot.users)
    
    def replace(self, msg: str) -> str:
        keys = findall(r'@@(.*?)@@', msg)

        for key in keys:
            value = self.variables.get(key.lower(), None)
            if value:
                msg = msg.replace(f"@@{key}@@", str(value()))

        return msg