import falcon
import psycopg2
import psycopg2.extras
from datetime import datetime, date
import json
from utils import get_db_connection, json_serial, sanitize_uuid, sanitize_str, sanitize_json

WATCH_HISTORY_COLUMNS = [
    "id",
    "customer_id",
    "movie_id",
    "device",
    "progress_percent",
    "metadata",
    "created_at",
    "updated_at",
    "watched_at",
]

class WatchHistoryResource:
    def on_post(self, req, resp):
        _test_mode = req.get_header('X-Test-Request') == 'true'
        try:
            data = req.media
            # Validate required fields
            required_fields = ["id", "customer_id", "movie_id", "created_at", "updated_at", "watched_at"]
            for field in required_fields:
                if field not in data or data[field] is None:
                    resp.status = falcon.HTTP_400
                    resp.media = {"status": "error", "message": f"Missing required field: {field}"}
                    return
            # Prepare values
            values = [
                sanitize_uuid(data["id"]),
                sanitize_uuid(data["customer_id"]),
                sanitize_uuid(data["movie_id"]),
                data.get("device"),
                data.get("progress_percent"),
                json.dumps(data.get("metadata")) if data.get("metadata") is not None else None,
                data["created_at"],
                data["updated_at"],
                data["watched_at"],
            ]
            with get_db_connection(test_mode=_test_mode) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO watch_history (id, customer_id, movie_id, device, progress_percent, metadata, created_at, updated_at, watched_at)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        """,
                        values,
                    )
                    conn.commit()
            resp.status = falcon.HTTP_201
            resp.media = {"status": "success", "id": data["id"]}
        except psycopg2.Error as e:
            resp.status = falcon.HTTP_500
            resp.media = {"status": "error", "message": str(e)}
        except Exception as e:
            resp.status = falcon.HTTP_500
            resp.media = {"status": "error", "message": str(e)}

    def on_get(self, req, resp):
        _test_mode = req.get_header('X-Test-Request') == 'true'
        # Filtering, pagination, sorting
        params = req.params
        where_clauses = []
        values = []
        for col in ["customer_id", "movie_id"]:
            if col in params:
                where_clauses.append(f"{col} = %s")
                values.append(sanitize_uuid(params[col]))
        # Date filtering
        for date_col in ["created_at", "updated_at", "watched_at"]:
            for op in ["gt", "lt", "gte", "lte"]:
                key = f"{date_col}_{op}"
                if key in params:
                    op_map = {"gt": ">", "lt": "<", "gte": ">=", "lte": "<="}
                    where_clauses.append(f"{date_col} {op_map[op]} %s")
                    values.append(params[key])
        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        # Pagination
        skip = int(params.get("skip", 0))
        limit = int(params.get("limit", 100))
        # Sorting
        sort_col = params.get("sort", "created_at")
        order = params.get("order", "asc").lower()
        if sort_col not in WATCH_HISTORY_COLUMNS:
            sort_col = "created_at"
        if order not in ["asc", "desc"]:
            order = "asc"
        try:
            with get_db_connection(test_mode=_test_mode) as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    # Get total
                    cur.execute(f"SELECT COUNT(*) FROM watch_history {where_sql}", values)
                    total = cur.fetchone()["count"]
                    # Get data
                    cur.execute(
                        f"SELECT * FROM watch_history {where_sql} ORDER BY {sort_col} {order} OFFSET %s LIMIT %s",
                        values + [skip, limit],
                    )
                    results = cur.fetchall()
            # Deserialize metadata json
            for row in results:
                if row.get("metadata") is not None and isinstance(row["metadata"], str):
                    try:
                        row["metadata"] = json.loads(row["metadata"])
                    except Exception:
                        row["metadata"] = None
                # Serialize datetimes
                for k in ["created_at", "updated_at", "watched_at"]:
                    if row.get(k) is not None and isinstance(row[k], (datetime, date)):
                        row[k] = json_serial(row[k])
            resp.status = falcon.HTTP_200
            resp.media = {
                "status": "success",
                "data": results,
                "skip": skip,
                "limit": limit,
                "total": total,
            }
        except psycopg2.Error as e:
            resp.status = falcon.HTTP_500
            resp.media = {"status": "error", "message": str(e)}
        except Exception as e:
            resp.status = falcon.HTTP_500
            resp.media = {"status": "error", "message": str(e)}

class WatchHistoryItemResource:
    def on_get(self, req, resp, id):
        _test_mode = req.get_header('X-Test-Request') == 'true'
        try:
            with get_db_connection(test_mode=_test_mode) as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("SELECT * FROM watch_history WHERE id = %s", (sanitize_uuid(id),))
                    row = cur.fetchone()
            if not row:
                resp.status = falcon.HTTP_404
                resp.media = {"status": "error", "message": "Not found"}
                return
            # Deserialize metadata json
            if row.get("metadata") is not None and isinstance(row["metadata"], str):
                try:
                    row["metadata"] = json.loads(row["metadata"])
                except Exception:
                    row["metadata"] = None
            # Serialize datetimes
            for k in ["created_at", "updated_at", "watched_at"]:
                if row.get(k) is not None and isinstance(row[k], (datetime, date)):
                    row[k] = json_serial(row[k])
            resp.status = falcon.HTTP_200
            resp.media = {"status": "success", "data": row}
        except psycopg2.Error as e:
            resp.status = falcon.HTTP_500
            resp.media = {"status": "error", "message": str(e)}
        except Exception as e:
            resp.status = falcon.HTTP_500
            resp.media = {"status": "error", "message": str(e)}

    def on_patch(self, req, resp, id):
        _test_mode = req.get_header('X-Test-Request') == 'true'
        data = req.media
        allowed_fields = ["device", "progress_percent", "metadata", "updated_at", "watched_at"]
        fields = []
        values = []
        for field in allowed_fields:
            if field in data:
                if field == "metadata":
                    fields.append(f"{field} = %s")
                    values.append(json.dumps(data[field]))
                else:
                    fields.append(f"{field} = %s")
                    values.append(data[field])
        if not fields:
            resp.status = falcon.HTTP_400
            resp.media = {"status": "error", "message": "No fields to update"}
            return
        try:
            with get_db_connection(test_mode=_test_mode) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"UPDATE watch_history SET {', '.join(fields)} WHERE id = %s",
                        values + [sanitize_uuid(id)],
                    )
                    if cur.rowcount == 0:
                        resp.status = falcon.HTTP_404
                        resp.media = {"status": "error", "message": "Not found"}
                        return
                    conn.commit()
            resp.status = falcon.HTTP_200
            resp.media = {"status": "success"}
        except psycopg2.Error as e:
            resp.status = falcon.HTTP_500
            resp.media = {"status": "error", "message": str(e)}
        except Exception as e:
            resp.status = falcon.HTTP_500
            resp.media = {"status": "error", "message": str(e)}

    def on_delete(self, req, resp, id):
        _test_mode = req.get_header('X-Test-Request') == 'true'
        try:
            with get_db_connection(test_mode=_test_mode) as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM watch_history WHERE id = %s", (sanitize_uuid(id),))
                    if cur.rowcount == 0:
                        resp.status = falcon.HTTP_404
                        resp.media = {"status": "error", "message": "Not found"}
                        return
                    conn.commit()
            resp.status = falcon.HTTP_200
            resp.media = {"status": "success"}
        except psycopg2.Error as e:
            resp.status = falcon.HTTP_500
            resp.media = {"status": "error", "message": str(e)}
        except Exception as e:
            resp.status = falcon.HTTP_500
            resp.media = {"status": "error", "message": str(e)}

class WatchHistorySchemaResource:
    def on_get(self, req, resp):
        schema = [
            {"field": "id", "headerName": "ID", "type": "uuid", "width": 70},
            {"field": "customer_id", "headerName": "Customer ID", "type": "uuid", "width": 150},
            {"field": "movie_id", "headerName": "Movie ID", "type": "uuid", "width": 150},
            {"field": "device", "headerName": "Device", "type": "string", "width": 100},
            {"field": "progress_percent", "headerName": "Progress %", "type": "number", "width": 100},
            {"field": "metadata", "headerName": "Metadata", "type": "json", "width": 200},
            {"field": "created_at", "headerName": "Created At", "type": "datetime", "width": 200},
            {"field": "updated_at", "headerName": "Updated At", "type": "datetime", "width": 200},
            {"field": "watched_at", "headerName": "Watched At", "type": "datetime", "width": 200},
        ]
        resp.status = falcon.HTTP_200
        resp.media = schema
