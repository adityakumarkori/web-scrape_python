import os
from dotenv import load_dotenv

MONGODB_URI = None
MONGODB_DATABASE = "granit_blinkit_data"
REQUEST_TIMEOUT = 20
REQUEST_DELAY = 2.0
MAX_RECORDS = 100

_required = ["MONGODB_URI"]

def load_env():
    """Load environment variables from .env file"""
    load_dotenv()
    global MONGODB_URI, MONGODB_DATABASE, REQUEST_TIMEOUT, REQUEST_DELAY, MAX_RECORDS
    MONGODB_URI = os.getenv("MONGODB_URI")
    MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "granit_blinkit_data")
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "20"))
    REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "2"))
    MAX_RECORDS = int(os.getenv("MAX_RECORDS", "100"))

def validate():
    missing = [var for var in _required if not os.getenv(var)]
    if missing:
        raise ValueError(f"Missing required environment variable(s): {', '.join(missing)}")

def reload_config():
    load_env()
    validate()

# Initialize with current environment but don't validate yet
load_env()