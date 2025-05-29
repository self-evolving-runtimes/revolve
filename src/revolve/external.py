import os

def get_source_folder():
    return os.environ.get("SOURCE_FOLDER")

def get_db_type():
    return os.environ.get("DB_TYPE")