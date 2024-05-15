import os
from dotenv import load_dotenv

class Settings:
    def __init__(self, settings: dict) -> None:
        self.invite_link: str = "https://discord.gg/GxjbupJpAp"
        self.bot_prefix: str = settings.get("prefix", "")
        self.activity: dict = settings.get("activity", [{"listen": "/help"}])
        self.embed_color: str = int(settings.get("embed_color", "0xb3b3b3"), 16)
        self.bot_access_user: list = settings.get("bot_access_user", [])
        self.sources_settings: dict = settings.get("sources_settings", {})
        self.cooldowns_settings: dict = settings.get("cooldowns", {})
        self.aliases_settings: dict = settings.get("aliases", {})
        self.version: str = settings.get("version", "")

class TOKENS:
    def __init__(self) -> None:
        load_dotenv()

        self.dctoken = os.getenv("DCTOKEN")
        self.tgtoken = os.getenv("TGTOKEN")
        self.bug_report_channel_id = int(os.getenv("BUG_REPORT_CHANNEL_ID"))
        self.mongodb_url = os.getenv("MONGODB_URL")
        self.mongodb_name = os.getenv("MONGODB_NAME")