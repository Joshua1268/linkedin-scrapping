import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1")
    HEADLESS_MODE = not DEBUG

    DB_URI = os.getenv("DB_URI")
    KEYWORDS = os.getenv("MOTS_CLES_D", "Data Scientist").split(",")
    USERNAME = os.getenv("USERNAME")
    PASSWORD = os.getenv("PASSWORD")

    SAVE_INTERVAL = 30
    MAX_SEARCH_TIME = 300
