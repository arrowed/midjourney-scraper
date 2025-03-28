
from argparse import Namespace
import hashlib
import json
import logging
import logging.config
import logging.handlers
import os
import re
from typing import Callable

import requests

from scraper.human_scaling import HumanBytes
from scraper.discord import DiscordApi
from scraper.resolution_parser import ResolutionParser

logger = logging.getLogger(__name__)


class Scraper():
    def __init__(self, channel_id, channel_name, api: DiscordApi, args: Namespace, debug=False):
        self.parser = ResolutionParser()

        self.download_dir_name = "download"

        self.base_dir = os.getenv('BASE_DATA_DIR', 'data')
        self.WALLPAPER_OUTPUT_DIR: str = os.path.join(
            self.base_dir, os.getenv('WALLPAPER_OUTPUT_DIR'))

        self.api = api
        self.channel_id = channel_id
        self.channel_name = channel_name
        self.args = args

        self.debug = ('debug' in args) or debug

    def get_safe_local_filename(self, ref: dict) -> str:
        file_component = '.'.join(ref['filename'].split('.')[:-1])
        extension = '.' + ref['filename'].split('.')[-1]

        # sometimes filename is 'image.png', so make it unique per url
        addition = hashlib.md5(ref['url'].encode('utf-8')).hexdigest()

        return ("".join([c for c in file_component if re.match(r'\w', c)]) + "_" + addition + extension)[0:200]

    def ensure_folders(self):
        os.makedirs(self.WALLPAPER_OUTPUT_DIR, exist_ok=True)

    def poll(self, publish_fn: Callable[[str, str, str, str, str, int, int, int], None]):

        api_response = self.api.get_messages(self.channel_id)
        if self.debug:
            with open(os.path.join(self.base_dir, f"data-{self.channel_name}.json"), 'w', encoding="utf-8") as f:
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
                    print(
                        f"{self.channel_name}/{attachment['filename']} ({downloaded_bytes}) -> {resolution_target_dir} ({x}, {y}, {api_response})", end=' ')

                    if self.args.limit_resolutions and resolution_target_dir not in self.args.limit_resolutions:
                        print('skipped')
                        continue  # skip and move on

                    print('keeping')

                    target_dir = os.path.join(
                        self.WALLPAPER_OUTPUT_DIR, resolution_target_dir, self.channel_name)

                    # download it
                    target_file = self.download_attachment(
                        attachment, target_dir)
                    size = os.path.getsize(target_file)

                    publish_fn(
                        target_file, self.channel_id, self.channel_name, resolution_target_dir, os.path.basename(target_file), x, y, size)

     # x, y, size
    def _get_metadata(self, discord_response: dict) -> tuple[int, int, int]:
        width = discord_response['width']
        height = discord_response['height']
        size = discord_response['size']
        return width, height, size

    def download_attachment(self, attach_data: dict, to_directory: str) -> str:
        url = attach_data['url']
        filename = self.get_safe_local_filename(attach_data)
        download_file = os.path.join(to_directory, filename)

        if os.path.exists(download_file):
            return download_file

        os.makedirs(to_directory, exist_ok=True)

        dl = requests.get(url, timeout=10)

        with open(download_file, 'wb') as f:
            f.write(dl.content)

        return download_file
