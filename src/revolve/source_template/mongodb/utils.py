import os

from pymongo import MongoClient

def get_db_connection(test_mode):
    try:
        _db_name = os.getenv("DB_NAME") if not test_mode else os.getenv("DB_NAME_TEST")
        username = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        hostname = os.getenv("DB_HOST")
        port = os.getenv("DB_PORT", 27017)

        uri = f"mongodb://{username}:{password}@{hostname}:{port}/{_db_name}"#  ?authSource=admin - more settings to consider
        return MongoClient(uri)
    except Exception as e:
        raise Exception(f"Database connection error: {e}")