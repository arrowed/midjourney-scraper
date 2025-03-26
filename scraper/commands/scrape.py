
from argparse import ArgumentParser, Namespace
import json
import logging
import logging.config
import logging.handlers
import os
import time

import requests

from scraper.discord import DiscordApi
from scraper.resolution_parser import ResolutionParser
from scraper.scrape import Scraper


logger = logging.getLogger(__name__)


class ScrapeCommand():

    def __init__(self):
        self.name = 'scrape'
        self.help = 'Stream images from Discord to disk and notify sink'

        self.args = Namespace()

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument('--limit-resolutions', '-r', choices=[name for _, _, _, name in ResolutionParser.rules],
                            default=[], action='append',
                            help='Limit to specific resolutions')

    # def bulk_process_download(self):
    #     for channel in os.getenv("DISCORD_CHANNELS").split(','):
    #         _, channel_name = channel.split('|')
    #         parser = ResolutionParser()

    #         base = os.path.join(
    #             self.base_dir, self.WALLPAPER_OUTPUT_DIR, channel_name)
    #         for d, n, fi in os.walk(os.path.join(base, self.download_dir_name)):
    #             print(d, n, fi)

    #             for f in fi:
    #                 file_path = os.path.join(base, self.download_dir_name, f)
    #                 target, x, y, r = parser.get_folder_for_file(file_path)
    #                 print(f"{f} -> {target} ({x}, {y}, {r})")

    #                 os.rename(file_path, os.path.join(base, target, f))

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

    def run(self, args: Namespace):
        api = DiscordApi(os.getenv("DISCORD_USER_TOKEN"))

        scrapers = [
            Scraper(channel_id, channel_name, api, args)
            for channel in os.getenv("DISCORD_CHANNELS").split(',')
            if (channel_id := channel.split('|')[0]) and (channel_name := channel.split('|')[1])
        ]

        print(f"All channels {os.getenv('DISCORD_CHANNELS')}")

        while True:
            try:
                for scraper in scrapers:
                    print(f"Starting {channel_name} ({channel_id})")

                    scraper.poll(self.publish)

            finally:
                print("sleeping")
                time.sleep(30)


if __name__ == '__main__':
    ScrapeCommand().run(Namespace())
