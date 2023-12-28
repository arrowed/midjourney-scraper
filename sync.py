
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
from resolution_parser import ResolutionParser

load_dotenv()

WALLPAPER_OUTPUT_DIR = os.getenv('WALLPAPER_OUTPUT_DIR')
download_dir_name = "download"

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
os.makedirs("log", exist_ok=True)
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

def create_app_folders():
    os.makedirs(WALLPAPER_OUTPUT_DIR, exist_ok=True)

    for channel in os.getenv("DISCORD_CHANNELS").split(','):
        _, channel_name = channel.split('|')

        os.makedirs(os.path.join(WALLPAPER_OUTPUT_DIR, channel_name, download_dir_name), exist_ok=True)

        for d in ResolutionParser().get_all_targets():
            os.makedirs(os.path.join(WALLPAPER_OUTPUT_DIR, channel_name, d), exist_ok=True)

create_app_folders()


api=DiscordApi(os.getenv("DISCORD_USER_TOKEN"))
parser = ResolutionParser()

while True:
    for channel in os.getenv("DISCORD_CHANNELS").split(','):
        channel_id, channel_name = channel.split('|')

        r=api.get_messages(channel_id)
        with open("log/data.json", 'w', encoding="utf-8") as f:
            f.write(json.dumps(r, sort_keys=True, indent=2))

        for row in r:
            if 'attachments' in row.keys():
                for attachment in row['attachments']:
                    url = attachment['url']
                    filename = sanitise(url)
                    target = os.path.join(WALLPAPER_OUTPUT_DIR, channel_name, download_dir_name, filename)

                    if url not in downloaded_urls[channel_id]:
                        downloaded_urls[channel_id] += [url]

                        dl = requests.get(url)
                         
                        with open(target, 'wb') as f:
                            f.write(dl.content)

                        downloaded_bytes=HumanBytes.format(int(dl.headers.get('Content-Length')))
                        print(f'{sanitise(url)}\t')

                        resolution_target_dir, x, y, r = parser.get_folder_for_file(target)
                        print(f"{filename} ({downloaded_bytes}) -> {resolution_target_dir} ({x}, {y}, {r})")

                        os.rename(target, os.path.join(WALLPAPER_OUTPUT_DIR, channel_name, resolution_target_dir, filename))

    write_state(downloaded_urls)

    print("sleeping")
    import time
    time.sleep(60)

def bulk_process_download():
    for channel in os.getenv("DISCORD_CHANNELS").split(','):
        channel_id, channel_name = channel.split('|')
        parser = ResolutionParser()

        base = os.path.join(WALLPAPER_OUTPUT_DIR, channel_name)
        for d, n, fi in os.walk(os.path.join(base, download_dir_name)):
            print(d, n, fi)

            for f in fi:
                file_path = os.path.join(base, download_dir_name, f)
                target, x, y, r = parser.get_folder_for_file(file_path)
                print(f"{f} -> {target} ({x}, {y}, {r})")

                os.rename(file_path, os.path.join(base, target, f))

