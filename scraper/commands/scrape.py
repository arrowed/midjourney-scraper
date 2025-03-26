
from argparse import ArgumentParser, Namespace
import json
import logging
import logging.config
import logging.handlers
import os
import re
import time
import uuid

import requests
import requests_cache
from scraper.human_scaling import HumanBytes
from scraper.discord import DiscordApi
from scraper.resolution_parser import ResolutionParser

logger = logging.getLogger(__name__)


class ScrapeCommand():

    def __init__(self):
        self.name = 'scrape'
        self.help = 'Stream images from Discord to disk and notify sink'

        self.base_dir = os.path.dirname(os.getenv('BASE_DATA_DIR', 'data'))
        self.download_dir_name = "download"
        self.WALLPAPER_OUTPUT_DIR: str
        self.args = Namespace()

        self.parser = ResolutionParser()
        self.api: DiscordApi

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument('--limit-resolutions', '-r', choices=[name for _, _, _, name in ResolutionParser.rules],
                            default=[], action='append',
                            help='Limit to specific resolutions')

    def sanitise(self, url) -> str:
        resource_name = url.split('/')[-1].split('?')[0]
        extension = '.' + resource_name.split('.')[-1]
        file_base = "".join(resource_name.split('.')[0:-1])

        uniq = '_' + uuid.uuid4().hex

        return ("".join([c for c in file_base if re.match(r'\w', c)]) + uniq + extension)[0:200]

    def create_app_folders(self):
        os.makedirs(self.WALLPAPER_OUTPUT_DIR, exist_ok=True)

    def bulk_process_download(self):
        for channel in os.getenv("DISCORD_CHANNELS").split(','):
            _, channel_name = channel.split('|')
            parser = ResolutionParser()

            base = os.path.join(
                self.base_dir, self.WALLPAPER_OUTPUT_DIR, channel_name)
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
        headers = {"authorization": os.getenv(
            "NOTIFY_SERVER_TOKEN"), "content-type": "application/json"}

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
            r = requests.post(url, headers=headers,
                              data=json.dumps(payload), timeout=10)
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
        self.base_dir = os.getenv('BASE_DATA_DIR', 'data')
        self.WALLPAPER_OUTPUT_DIR = os.path.join(
            self.base_dir, os.getenv('WALLPAPER_OUTPUT_DIR'))

        self.create_app_folders()

        self.api = DiscordApi(os.getenv("DISCORD_USER_TOKEN"))

        print(f"All channels {os.getenv('DISCORD_CHANNELS')}")
        print(f"Saving to {self.WALLPAPER_OUTPUT_DIR}")

        while True:
            try:
                for channel in os.getenv("DISCORD_CHANNELS").split(','):
                    channel_id, channel_name = channel.split('|')
                    print(f"Starting {channel_name} ({channel_id})")

                    api_response = self.api.get_messages(channel_id)
                    with open(f"log/data-{channel_name}.json", 'w', encoding="utf-8") as f:
                        f.write(json.dumps(api_response,
                                sort_keys=True, indent=2))

                    for row in api_response:
                        if 'attachments' in row.keys():
                            for attachment in row['attachments']:
                                width, height, size = self._get_metadata(
                                    attachment)

                                downloaded_bytes = HumanBytes.format(size)
                                resolution_target_dir, x, y, api_response = self.parser.get_folder_for_dimensions(
                                    width, height)
                                filename = self.sanitise(attachment['url'])
                                print(
                                    f"{channel_name}/{filename} ({downloaded_bytes}) -> {resolution_target_dir} ({x}, {y}, {api_response})", end=' ')

                                if args.limit_resolutions and resolution_target_dir not in args.limit_resolutions:
                                    print('skipped')
                                    continue  # skip and move on

                                print('keeping')

                                target_dir = os.path.join(
                                    self.WALLPAPER_OUTPUT_DIR, resolution_target_dir, channel_name)

                                # download it
                                target_file = self.download_attachment(
                                    attachment, target_dir)
                                size = os.path.getsize(target_file)

                                self.publish(
                                    target_file, channel_id, channel_name, resolution_target_dir, filename, x, y, size)

            finally:
                print("sleeping")
                time.sleep(30)

    # x, y, size
    def _get_metadata(self, discord_response: dict) -> tuple[int, int, int]:
        width = discord_response['width']
        height = discord_response['height']
        size = discord_response['size']
        return width, height, size

    def download_attachment(self, attach_data: dict, to_directory: str) -> str:
        session = requests_cache.CachedSession(
            os.path.join(self.base_dir, 'image_download_cache'),
            expire_after=3600,
            backend='sqlite'
        )

        url = attach_data['url']
        filename = self.sanitise(url)
        download_file = os.path.join(to_directory, filename)
        os.makedirs(to_directory, exist_ok=True)

        dl = session.get(url, timeout=10)

        with open(download_file, 'wb') as f:
            f.write(dl.content)

        return download_file


if __name__ == '__main__':
    ScrapeCommand().run(Namespace())
