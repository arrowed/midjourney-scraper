import os
from dotenv import load_dotenv

load_dotenv()

WALLPAPER_OUTPUT_DIR = os.getenv('WALLPAPER_OUTPUT_DIR')
os.makedirs(WALLPAPER_OUTPUT_DIR, exist_ok=True)
os.makedirs("log", exist_ok=True)
