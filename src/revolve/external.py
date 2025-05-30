import os

def get_source_folder():
    return os.environ.get("SOURCE_FOLDER")

def get_db_type():
    db_type = os.getenv("DB_TYPE")
    if db_type is None:
        port = int(os.environ["DB_PORT"])
        if port == 5432:
            db_type =  "postgres"
        elif port == 27017:
            db_type =  "mongodb"

    return db_type