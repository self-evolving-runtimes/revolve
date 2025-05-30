import falcon
import psycopg2
import psycopg2.extras
from datetime import datetime, date
from db_utils import get_db_connection, json_serial

class HelloDBResource:
    def on_get(self, req, resp):
        _test_mode = req.get_header('X-Test-Request') == 'true'
        try:
            with get_db_connection(test_mode=_test_mode) as conn:
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
        {"field": "gender", "headerName": "Gender", "type": "enum", "enumValues":["Male","Female"], "width": 200},
        {"field": "companyId", "headerName": "Company Id", "type": "foreignKey", "relatedTable":"company", "relatedColumn":"id", "width": 200},
    ]

