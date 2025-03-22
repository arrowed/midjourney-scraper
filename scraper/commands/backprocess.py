
import os
from dotenv import load_dotenv
import requests
import json
import logging
import logging.handlers
import re
import uuid
from scraper.human_scaling import HumanBytes
from scraper.discord import DiscordApi
from scraper.resolution_parser import ResolutionParser
import time

from requests.exceptions import ConnectionError

load_dotenv()

WALLPAPER_OUTPUT_DIR = os.getenv('WALLPAPER_OUTPUT_DIR')
download_dir_name = "download"


from scraper.commands.sync import publish

def backprocess():
    for channel in os.getenv("DISCORD_CHANNELS").split(','):
        channel_id, channel_name = channel.split('|')
        
        base = os.path.join(WALLPAPER_OUTPUT_DIR, channel_name)
        walk(channel_id, channel_name, base)

def walk(channel_id, channel_name, path):
    for dirname, otherdirs, files in os.walk(os.path.join(path)):
       
        for f in files: 
            process(channel_id, channel_name, dirname, f)
        
        for di in otherdirs:
            walk(channel_id, channel_name, os.path.join(path, di))

def process(channel_id, channel_name, dirname, file):
    parser = ResolutionParser()
    file_path = os.path.join(dirname, file)
    target, x, y, r = parser.get_folder_for_file(file_path)
    print(f"{file} -> {target} ({x}, {y}, {r})")

    publish(file_path, channel_id, channel_name, target, file_path, x, y, os.path.getsize(file_path))

if __name__ == '__main__':
    backprocess()