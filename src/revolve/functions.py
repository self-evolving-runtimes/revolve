

from datetime import datetime, time
import os
from pathlib import Path
import shutil
from pprint import pprint

import subprocess
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Any, Dict, List, Optional, Any
from langchain_openai import ChatOpenAI


import psycopg2
import json


def log(method_name, description):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{method_name:<20} - {timestamp:<20} - {description:<30}")


def run_query_on_db(query: str) -> str:
    """
    This function runs the given query on the database.
    Args:
        query (str): The query to be run.
    """
    # log("run_query_on_db", f"Running query: {query}")
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
        )
        cur = conn.cursor()
        cur.execute(query)
        # if cur.rowcount:
        result = cur.fetchall()
        # else:
        #     result = None
        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        log("run_query_on_db", f"Error running query: {e}")
        return f"Error running query: {e}"

    # log("run_query_on_db", f"Query executed successfully.")
    # log("run_query_on_db", f"Result: {result}")
    return json.dumps(result)


# if __name__ =="__main__":
#     result = run_query_on_db("""SELECT jsonb_object_agg(
#            table_name,
#            columns
#        ) AS schema_dict
# FROM (
#     SELECT
#         table_name,
#         jsonb_agg(
#             jsonb_build_object(
#                 'column_name', column_name,
#                 'data_type', data_type,
#                 'is_nullable', is_nullable
#             )
#         ) AS columns
#     FROM information_schema.columns
#     WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
#     GROUP BY table_name
# ) AS sub;""")
