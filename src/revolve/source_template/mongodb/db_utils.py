import os

from pymongo import MongoClient

def get_db_connection(test_mode):
    try:
        username = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        hostname = os.getenv("DB_HOST")
        port = os.getenv("DB_PORT", 27017)

        client = MongoClient(
            host=hostname,
            port=int(port),
            username=username,
            password=password
        )

        return client
    except Exception as e:
        raise Exception(f"Database connection error: {e}")

def get_db(client, test_mode):
    """
    Get a MongoDB database connection.
    client: MongoClient instance
    test_mode: boolean indicating if the connection is for testing
    """
    try:
        _db_name = os.getenv("DB_NAME") if not test_mode else os.getenv("DB_NAME_TEST")
        return client.get_database(_db_name)
    except Exception as e:
        raise Exception(f"Error getting database: {e}")