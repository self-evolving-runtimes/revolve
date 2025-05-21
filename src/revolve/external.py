import os

def get_source_folder():
    return os.environ.get("SOURCE_FOLDER", "revolve/source_generated")
