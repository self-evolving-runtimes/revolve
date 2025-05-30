
import falcon
from datetime import datetime, date
from bson import ObjectId
from db_utils import get_db_connection

def mongo_serial(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, ObjectId):
        return str(obj)
    return obj

class HelloMongoResource:
    def on_get(self, req, resp):
        _test_mode = req.get_header('X-Test-Request') == 'true'
        try:
            client = get_db_connection()
            db = client.get_default_database()
            collection = db['helloDB']

            results = list(collection.find({}))

            # Serialize results
            serialized_results = [
                {k: mongo_serial(v) for k, v in row.items()}
                for row in results
            ]

            resp.media = {
                "message": "Hello, MongoDB!",
                "status": "success",
                "data": serialized_results,
            }
            resp.status = falcon.HTTP_200

        except Exception as e:
            resp.media = {"message": f"Server error: {str(e)}", "status": "error"}
            resp.status = falcon.HTTP_500
        finally:
            client.close()

class HelloMongoSchemaResource:
    def on_get(self, req, resp):
        resp.media = [
            {"field": "_id", "headerName": "ID", "type": "string", "width": 100},
            {"field": "name", "headerName": "Name", "type": "string", "width": 150},
            {"field": "age", "headerName": "Age", "type": "number", "width": 100},
            {"field": "email", "headerName": "Email", "type": "string", "width": 200},
            {"field": "gender", "headerName": "Gender", "type": "enum", "enumValues":["Male","Female"], "width": 200},
            {"field": "companyId", "headerName": "Company Id", "type": "foreignKey", "relatedTable":"company", "relatedColumn":"_id", "width": 200},
        ]
        resp.status = falcon.HTTP_200
