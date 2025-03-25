
from argparse import Namespace
import json
import logging
import logging.config
import logging.handlers
import os
import re
import requests
import time
import uuid

from requests.exceptions import ConnectionError

from scraper.human_scaling import HumanBytes
from scraper.discord import DiscordApi
from scraper.resolution_parser import ResolutionParser

logger = logging.getLogger(__name__)

class SyncCommand():
    
    def __init__(self):
        self.name = 'sync'
        self.help = 'Stream images from Discord to disk and notify sink'

        self.download_dir_name = "download"
        self.WALLPAPER_OUTPUT_DIR :str
        self.args = Namespace()

    def add_arguments(self, parser):
        pass

    def sanitise(self, url):
        resource_name = url.split('/')[-1].split('?')[0]
        extension = '.' + resource_name.split('.')[-1]
        file_base = "".join(resource_name.split('.')[0:-1])

        uniq = '_' + uuid.uuid4().hex

        return ("".join([c for c in file_base if re.match(r'\w', c)]) + uniq + extension)[0:200]


    def read_state(self):
        fetched = {}
        for channel in os.getenv("DISCORD_CHANNELS").split(','):
            channel_id, channel_name = channel.split('|')

            state_file = f"state-{channel_name}.txt"
            fetched[channel_id] = []

            if os.path.exists(os.path.join(self.WALLPAPER_OUTPUT_DIR, state_file)):
                with open(os.path.join(self.WALLPAPER_OUTPUT_DIR, state_file), 'r', encoding='utf-8') as checkpoint:
                    for line in checkpoint.readlines():
                        fetched[channel_id] += [line.strip()]

        return fetched

    def write_state(self, state):
        for channel in os.getenv("DISCORD_CHANNELS").split(','):
            channel_id, channel_name = channel.split('|')

            state_file = f"state-{channel_name}.txt"

            with open(os.path.join(self.WALLPAPER_OUTPUT_DIR, state_file), 'w', encoding='utf-8') as checkpoint:
                checkpoint.writelines([str(i)+'\n' for i in state[channel_id]])

    def create_app_folders(self):
        os.makedirs(self.WALLPAPER_OUTPUT_DIR, exist_ok=True)

        for channel in os.getenv("DISCORD_CHANNELS").split(','):
            _, channel_name = channel.split('|')

            os.makedirs(os.path.join(self.WALLPAPER_OUTPUT_DIR, channel_name, self.download_dir_name), exist_ok=True)

            for d in ResolutionParser().get_all_targets():
                os.makedirs(os.path.join(self.WALLPAPER_OUTPUT_DIR, channel_name, d), exist_ok=True)

    def bulk_process_download(self):
        for channel in os.getenv("DISCORD_CHANNELS").split(','):
            channel_id, channel_name = channel.split('|')
            parser = ResolutionParser()

            base = os.path.join(self.WALLPAPER_OUTPUT_DIR, channel_name)
            for d, n, fi in os.walk(os.path.join(base, self.download_dir_name)):
                print(d, n, fi)

                for f in fi:
                    file_path = os.path.join(base, self.download_dir_name, f)
                    target, x, y, r = parser.get_folder_for_file(file_path)
                    print(f"{f} -> {target} ({x}, {y}, {r})")

                    os.rename(file_path, os.path.join(base, target, f))

    def publish(self, target, channel_id, channel_name, resolution_target_dir, filename, width, height, lengthBytes):
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
                    "data_path": target,
                    "width": width,
                    "height": height,
                    "size": lengthBytes
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

    def run(self, args):
        self.args = args
        
        self.WALLPAPER_OUTPUT_DIR = os.getenv('WALLPAPER_OUTPUT_DIR')

        downloaded_urls = self.read_state()

        self.api=DiscordApi(os.getenv("DISCORD_USER_TOKEN"))
        self.parser = ResolutionParser()
        os.makedirs("log", exist_ok=True)
        self.create_app_folders()

        print(f"All channels {os.getenv('DISCORD_CHANNELS')}")
        
        while True:
            try:
                for channel in os.getenv("DISCORD_CHANNELS").split(','):
                    channel_id, channel_name = channel.split('|')
                    print(f"Starting {channel_name} ({channel_id})")

                    api_response=self.api.get_messages(channel_id)
                    with open(f"log/data-{channel_name}.json", 'w', encoding="utf-8") as f:
                        f.write(json.dumps(api_response, sort_keys=True, indent=2))

                    for row in api_response:
                        if 'attachments' in row.keys():
                            for attachment in row['attachments']:
                                url = attachment['url']
                                filename = self.sanitise(url)
                                download_file = os.path.join(self.WALLPAPER_OUTPUT_DIR, channel_name, self.download_dir_name, filename)

                                if url not in self.downloaded_urls[channel_id]:
                                    self.downloaded_urls[channel_id] += [url]

                                    dl = requests.get(url)
                                    
                                    with open(download_file, 'wb') as f:
                                        f.write(dl.content)

                                    size = dl.headers.get('Content-Length')
                                    if size is None:
                                        size = 0
                                    else:
                                        size = int(size)
                                        
                                    downloaded_bytes=HumanBytes.format(size)

                                    resolution_target_dir, x, y, api_response = self.parser.get_folder_for_file(download_file)
                                    print(f"{channel_name}/{filename} ({downloaded_bytes}) -> {resolution_target_dir} ({x}, {y}, {api_response})")

                                    target_file =  os.path.join(self.WALLPAPER_OUTPUT_DIR, channel_name, resolution_target_dir, filename)
                                    os.rename(download_file, target_file)

                                    self.publish(target_file, channel_id, channel_name, resolution_target_dir, filename, x, y, size)

                self.write_state(downloaded_urls)
            finally:
                print("sleeping")
                time.sleep(30)


if __name__ == '__main__':
    SyncCommand().run()
