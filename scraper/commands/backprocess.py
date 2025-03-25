
from argparse import ArgumentParser
import os
from dotenv import load_dotenv

from scraper.resolution_parser import ResolutionParser

from scraper.commands.scrape import ScrapeCommand

load_dotenv()


class BackProcessCommand():

    WALLPAPER_OUTPUT_DIR = os.getenv('WALLPAPER_OUTPUT_DIR')
    download_dir_name = "download"

    def __init__(self):
        self.name = 'backprocess'
        self.help = 'Generate notifications for files already downloaded'

    def add_arguments(self, parser: ArgumentParser):
        pass

    def run(self):

        for channel in os.getenv("DISCORD_CHANNELS").split(','):
            channel_id, channel_name = channel.split('|')

            base = os.path.join(self.WALLPAPER_OUTPUT_DIR, channel_name)
            self.walk(channel_id, channel_name, base)

    def walk(self, channel_id, channel_name, path):
        for dirname, otherdirs, files in os.walk(os.path.join(path)):

            for f in files:
                self.process(channel_id, channel_name, dirname, f)

            for di in otherdirs:
                self.walk(channel_id, channel_name, os.path.join(path, di))

    def process(self, channel_id, channel_name, dirname, file):
        parser = ResolutionParser()
        file_path = os.path.join(dirname, file)
        target, x, y, r = parser.get_folder_for_file(file_path)
        print(f"{file} -> {target} ({x}, {y}, {r})")

        ScrapeCommand().publish(file_path, channel_id, channel_name,
                                target, file_path, x, y, os.path.getsize(file_path))


if __name__ == '__main__':
    BackProcessCommand().run()
