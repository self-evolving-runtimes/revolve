import falcon
import os
import psycopg2
import psycopg2.extras
from datetime import datetime, date


def get_db_connection():
    try:
        return psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
        )
    except psycopg2.Error as e:
        raise Exception(f"Database connection error: {e}")


def json_serial(obj):
    """Helper function to convert datetime objects into strings."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


class HelloDBResource:
    def on_get(self, req, resp):
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("SELECT * FROM helloDB")
                    results = cur.fetchall()

            # Serialize datetime columns to strings
            serialized_results = [
                {
                    k: json_serial(v) if isinstance(v, (datetime, date)) else v
                    for k, v in row.items()
                }
                for row in results
            ]

            resp.media = {
                "message": "Hello, Database!",
                "status": "success",
                "data": serialized_results,
            }
            resp.status = falcon.HTTP_200

        except psycopg2.Error as e:
            resp.media = {"message": f"Database error: {str(e)}", "status": "error"}
            resp.status = falcon.HTTP_500

        except Exception as e:
            resp.media = {"message": f"Server error: {str(e)}", "status": "error"}
            resp.status = falcon.HTTP_500

class HelloDBSchemaResource:
    def on_get(self, req, resp):
        return [
        {"field": "id", "headerName": "ID", "type": "number", "width": 70},
        {"field": "name", "headerName": "Name", "type": "string", "width": 150},
        {"field": "age", "headerName": "Age", "type": "number", "width": 100},
        {"field": "email", "headerName": "Email", "type": "string", "width": 200},
    ]

