import json

with open("config.json", 'rb') as file:
    settings = json.load(file)

class Config:
    def __init__(self):
        prefix = settings['discordbot_prefix']
        color = int(settings['main_color'], 16)
        success_color = int(settings['success_color'], 16)
        error_color = int(settings['error_color'], 16)
