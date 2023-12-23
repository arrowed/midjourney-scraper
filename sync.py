import discord
import os
from dotenv import load_dotenv


import logging
import logging.handlers

load_dotenv()

WALLPAPER_OUTPUT_DIR = os.getenv('WALLPAPER_OUTPUT_DIR')
os.makedirs(WALLPAPER_OUTPUT_DIR, exist_ok=True)
os.makedirs("log", exist_ok=True)

def init_logging(): 
    discord_logger = logging.getLogger('discord')
    discord_logger.setLevel(logging.DEBUG)

    logging.getLogger('discord.http').setLevel(logging.DEBUG)

    handler = logging.handlers.RotatingFileHandler(
        filename='log/discord.log',
        encoding='utf-8',
        maxBytes=32 * 1024 * 1024,  # 32 MiB
        backupCount=5,  # Rotate through 5 files
    )
    dt_fmt = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
    handler.setFormatter(formatter)
    discord_logger.addHandler(handler)

    return discord_logger

handler = init_logging()

class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as', self.user)

    async def on_message(self, message):
        # don't respond to ourselves
        if message.author == self.user:
            return

        logging.info("Hi")

intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)
client.run(os.getenv('DISCORD_CLIENT_TOKEN'))
