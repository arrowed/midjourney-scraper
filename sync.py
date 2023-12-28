
import os
from dotenv import load_dotenv
import requests
import json
import logging
import logging.handlers
import re
import uuid
from human_scaling import HumanBytes
from discord import DiscordApi

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

def sanitise(url):
    resource_name = url.split('/')[-1].split('?')[0]
    extension = '.' + resource_name.split('.')[-1]
    file_base = "".join(resource_name.split('.')[0:-1])

    uniq = '_' + uuid.uuid4().hex

    return ("".join([c for c in file_base if re.match(r'\w', c)]) + uniq + extension)[0:200]


def read_state():
    fetched = {}
    for channel in os.getenv("DISCORD_CHANNELS").split(','):
        channel_id, channel_name = channel.split('|')

        state_file = f"state-{channel_name}.txt"
        fetched[channel_id] = []

        if os.path.exists(os.path.join(WALLPAPER_OUTPUT_DIR, state_file)):
            with open(os.path.join(WALLPAPER_OUTPUT_DIR, state_file), 'r') as checkpoint:
                for line in checkpoint.readlines():
                    fetched[channel_id] += [line.strip()]

    return fetched

def write_state(state): 
    for channel in os.getenv("DISCORD_CHANNELS").split(','):
        channel_id, channel_name = channel.split('|')

        state_file = f"state-{channel_name}.txt"

        with open(os.path.join(WALLPAPER_OUTPUT_DIR, state_file), 'w') as checkpoint:
            checkpoint.writelines([str(i)+'\n' for i in state[channel_id]])

downloaded_urls = read_state()

api=DiscordApi(os.getenv("DISCORD_USER_TOKEN"))
while True:
    for channel in os.getenv("DISCORD_CHANNELS").split(','):
        channel_id, channel_name = channel.split('|')
        os.makedirs(os.path.join(WALLPAPER_OUTPUT_DIR, channel_name), exist_ok=True)

        r=api.get_messages(channel_id)
        with open("log/data.json", 'w', encoding="utf-8") as f:
            f.write(json.dumps(r, sort_keys=True, indent=2))

        for row in r:
            if 'attachments' in row.keys():
                for attachment in row['attachments']:
                    url = attachment['url']
                    
                    target = os.path.join(WALLPAPER_OUTPUT_DIR, channel_name, sanitise(url))

                    if url not in downloaded_urls[channel_id]:
                        downloaded_urls[channel_id] += [url]

                        dl = requests.get(url)
                         
                        with open(target, 'wb') as f:
                            f.write(dl.content)
                        downloaded_bytes=HumanBytes.format(int(dl.headers.get('Content-Length')))
                        print(f'{sanitise(url)}\t{downloaded_bytes}')

    write_state(downloaded_urls)

    print("sleeping")
    import time
    time.sleep(60)
