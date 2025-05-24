import uuid
import os
import psycopg2
from datetime import datetime, date
import json
from uuid import UUID

def get_db_connection(test_mode):
    try:
        _db_name = os.getenv("DB_NAME") if not test_mode else os.getenv("DB_NAME_TEST")
        return psycopg2.connect(
            dbname=_db_name,
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
        )
    except psycopg2.Error as e:
        raise Exception(f"Database connection error: {e}")

def json_serial(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def is_valid_uuid(val):
    try:
        UUID(str(val))
        return True
    except Exception:
        return False

def sanitize_str(val):
    if val is None:
        return None
    return str(val)

def json_serial(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return str(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

def sanitize_str(val):
    if not isinstance(val, str):
        raise ValueError("Expected string value")
    return val

def sanitize_uuid(val):
    try:
        return str(UUID(val))
    except Exception:
        raise ValueError("Invalid UUID format")

def sanitize_bool(val):
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        if val.lower() in ['true', '1', 't', 'yes']:
            return True
        elif val.lower() in ['false', '0', 'f', 'no']:
            return False
    raise ValueError("Invalid boolean value")

def sanitize_json(val):
    if val is None:
        return None
    if isinstance(val, dict):
        return val
    try:
        return json.loads(val)
    except Exception:
        raise ValueError("Invalid JSON value")

def sanitize_array(val):
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        try:
            return json.loads(val)
        except Exception:
            raise ValueError("Invalid array value")
    raise ValueError("Invalid array value")

def get_unique_id():
    """Generate a unique UUID."""
    return str(uuid.uuid4())