import time
import falcon
import logging
import json
import traceback
import sys
import os
from wsgiref.simple_server import make_server, WSGIServer
from socketserver import ThreadingMixIn
from revolve.workflow_generator import run_workflow_generator
from revolve.functions import test_db, get_file_list, read_python_code
from revolve.utils import start_process, stop_process
from wsgiref.simple_server import make_server, WSGIRequestHandler

process_state = {
    "pid": None,
    "port": None,
    "link": None
}

logging.basicConfig(level=logging.INFO, filename="api.log")
logger = logging.getLogger(__name__)


class LoggingWSGIRequestHandler(WSGIRequestHandler):
    #     daemon_threads = True
    def log_message(self, format, *args):
        logger.info("%s - - [%s] %s\n" % (
            self.client_address[0],
            self.log_date_time_string(),
            format % args
        ))

class WorkflowResource:
    def on_post(self, req, resp):
        try:
            data = req.media 
            task = data.get("message", None)
            db_config = data.get("dbConfig", {})
        except Exception:
            resp.status = falcon.HTTP_400
            resp.media = {"error": "Invalid JSON"}
            return

        resp.status = falcon.HTTP_200
        resp.content_type = 'application/x-ndjson'

        def generate():
            for item in run_workflow_generator(task=task, db_config=db_config):
                line = json.dumps(item) + "\n"
                yield line.encode("utf-8")

        resp.stream = generate()

class _MockWorkflowResource:
    def on_post(self, req, resp):
        try:

            data = req.media
            task = data.get("message", None)
        except Exception:
            resp.status = falcon.HTTP_400
            resp.media = {"error": "Invalid JSON"}
            return

        resp.status = falcon.HTTP_200
        resp.content_type = 'application/x-ndjson'

        def generate():
            # Simulate 3 intermediate messages and 1 final message
            for i in range(10):
                message = {
                    "status": "processing",
                    "name": "node",
                    "level":"log",
                    "text": f"Step {i+1} kljhslkdhj lksahlkdfhsal dfhklshalkf haslkhf lksahklfh aslkdfh laskhfs alkhfkl saklfhsal kflsahlkfhsa lkflkashlk flsakhf lksahflk hasklhf lskahflksa flkahsl kfhklashf lksahklfh alskfhak lsflkas alfhla ksfh lshfkla completed"
                }
                yield (json.dumps(message) + "\n").encode("utf-8")
                time.sleep(2)  # Delay of 1 second

            final_message = {
                "status": "done",
                "level":"workflow",
                "name": "workflow",
                "text": "Task completed successfully",
            }
            yield (json.dumps(final_message) + "\n").encode("utf-8")

        resp.stream = generate()


class FileResource:
    def on_get(self, req, resp):
        path = req.path

        if path.endswith('/get-file-list'):
            self.get_file_list(req, resp)
        elif path.endswith('/get-file'):
            self.get_file(req, resp)
        else:
            resp.status = falcon.HTTP_404
            resp.media = {"error": "Unknown file endpoint"}

    def get_file_list(self, req, resp):
        file_list = get_file_list()
        file_list = [f for f in file_list if f.endswith(('.py', '.json', '.md'))]
        file_list.sort()
        resp.status = falcon.HTTP_200
        resp.media = {"files": file_list}

    def get_file(self, req, resp):
        file_name = req.get_param("name")
        content = read_python_code(file_name)
        if file_name.endswith(".py"):
            content = f"```python\n{content}\n```"
        elif file_name.endswith(".json"):
            content = f"```json\n{content}\n```"
        resp.status = falcon.HTTP_200
        resp.media = {"content": content}

class TestDBResource:
    def on_post(self, req, resp):
        try:
            data = req.media
            db_name = data.get("DB_NAME", None)
            db_user = data.get("DB_USER", None)
            db_password = data.get("DB_PASSWORD", None)
            db_host = data.get("DB_HOST", None)
            db_port = data.get("DB_PORT", None)
            if not all([db_name, db_user, db_password, db_host, db_port]):
                resp.status = falcon.HTTP_400
                resp.media = {"error": "Missing database connection parameters."}
                return
            
            result = test_db(
                db_name=db_name,
                db_user=db_user,
                db_password=db_password,
                db_host=db_host,
                db_port=db_port
            )

            if result:
                resp.status = falcon.HTTP_200
                resp.media = {"message": "Connection to DB was successful!"}
            else:
                resp.status = falcon.HTTP_500
                resp.media = {"error": "Connection to DB failed. Please check your credentials."}
        except Exception:
            resp.status = falcon.HTTP_500
            resp.media = {"error": "Database connection failed."}

class ServerControlResource:
    def on_post(self, req, resp):
        path = req.path
        if path.endswith('/start'):
            result = start_process()
        elif path.endswith('/stop'):
            result = stop_process()
        else:
            resp.status = falcon.HTTP_404
            resp.media = {"error": "Unknown command"}
            return

        resp.status = falcon.HTTP_200
        resp.media = result

app = falcon.App()
app.add_route("/api/chat", WorkflowResource())
app.add_route("/api/test_db", TestDBResource())
app.add_route("/api/start", ServerControlResource())
app.add_route("/api/stop", ServerControlResource())
app.add_route("/api/get-file-list", FileResource())
app.add_route("/api/get-file", FileResource())

#get current directory
static_resource = f"{os.path.dirname(os.path.abspath(__file__))}/ui/dist"
# Route handling:
app.add_static_route("/{filepath:path}", static_resource)
app.add_static_route("/", static_resource, fallback_filename='index.html')


# # Threading WSGI server to handle concurrent requests
class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True


if __name__ == "__main__":
    port = int(os.environ.get("API_PORT", "48001"))
    with make_server("", port, app, server_class=ThreadingWSGIServer, handler_class=LoggingWSGIRequestHandler) as httpd:
        logger.info(f"Serving on http://localhost:{port}/")
        print(f"Serving on http://localhost:{port}/")
        httpd.serve_forever()