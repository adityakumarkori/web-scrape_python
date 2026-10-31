from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import config

_client = None

def connect_db():
    global _client
    if _client is not None:
        return _client
    
    uri = config.MONGODB_URI
    timeout_ms = config.REQUEST_TIMEOUT * 1000
    
    try:
        _client = MongoClient(uri, serverSelectionTimeoutMS=timeout_ms)
        _client.admin.command("ping")
        return _client
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        _client = None
        raise ConnectionError(f"Failed to connect to MongoDB: {e}")

def close_db():
    global _client
    if _client is not None:
        _client.close()
        _client = None

def get_database():
    client = connect_db()
    return client[config.MONGODB_DATABASE]

def check_connection():
    try:
        client = connect_db()
        client.admin.command("ping")
        return True, "Connected"
    except ConnectionError as e:
        return False, str(e)