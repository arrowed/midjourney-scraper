
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
import time

from requests.exceptions import ConnectionError

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

def publish(target, channel_id, channel_name, resolution_target_dir, filename):
    if os.getenv("NOTIFY_SERVER_URL", "") == "":
        return

    url = f"{os.getenv('NOTIFY_SERVER_URL')}/image"
    headers = {"authorization": os.getenv("NOTIFY_SERVER_TOKEN"), "content-type": "application/json"}

    try:    
        payload = {
            "channel": {
                "id": channel_id,
                "name": channel_name
            },
            "image": {
                "classification": resolution_target_dir,
                "filename": filename,
                "data_path": target
            }
        }
        r = requests.post(url, headers=headers, data=json.dumps(payload))
        if r.status_code in [200]:
            return r.json()
        else:
            return []
    except ConnectionError:
        pass
    except Exception as e:
        print(f"{e}")
    finally:
        pass

def download_loop():
    print(f"All channels {os.getenv('DISCORD_CHANNELS')}")
    
    for channel in os.getenv("DISCORD_CHANNELS").split(','):
        channel_id, channel_name = channel.split('|')
        print(f"Starting {channel_name} ({channel_id})")

        api_response=api.get_messages(channel_id)
        with open(f"log/data-{channel_name}.json", 'w', encoding="utf-8") as f:
            f.write(json.dumps(api_response, sort_keys=True, indent=2))

        for row in api_response:
            if 'attachments' in row.keys():
                for attachment in row['attachments']:
                    url = attachment['url']
                    filename = sanitise(url)
                    download_file = os.path.join(WALLPAPER_OUTPUT_DIR, channel_name, download_dir_name, filename)

                    if url not in downloaded_urls[channel_id]:
                        downloaded_urls[channel_id] += [url]

                        dl = requests.get(url)
                         
                        with open(download_file, 'wb') as f:
                            f.write(dl.content)

                        size = dl.headers.get('Content-Length')
                        if size is None:
                            size = 0
                        else:
                            size = int(size)
                            
                        downloaded_bytes=HumanBytes.format(size)

                        resolution_target_dir, x, y, api_response = parser.get_folder_for_file(download_file)
                        print(f"{channel_name}/{filename} ({downloaded_bytes}) -> {resolution_target_dir} ({x}, {y}, {api_response})")

                        target_file =  os.path.join(WALLPAPER_OUTPUT_DIR, channel_name, resolution_target_dir, filename)
                        os.rename(download_file, target_file)

                        publish(target_file, channel_id, channel_name, resolution_target_dir, filename)

    write_state(downloaded_urls)


api=DiscordApi(os.getenv("DISCORD_USER_TOKEN"))
parser = ResolutionParser()

while True:
    try:
        # asyncio.run(publish_loop())
        download_loop()
    finally:
        print("sleeping")
        time.sleep(30)