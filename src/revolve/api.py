import random
import time
import falcon
import logging
import json
import sys
import os
from wsgiref.simple_server import make_server, WSGIServer
from socketserver import ThreadingMixIn

from revolve.db import get_adapter
from revolve.workflow_generator import run_workflow_generator
from revolve.utils import start_process, stop_process
from revolve.utils import read_python_code
from revolve.functions import get_file_list
from wsgiref.simple_server import WSGIRequestHandler


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
            messages = data.get("messages", None)
            db_config = data.get("dbConfig", {})
            settings = data.get("settings", {})

            if not all([settings.get("openaiKey"), settings.get("sourceFolder")]):
                resp.status = falcon.HTTP_400
                resp.media = {"error": "Missing settings parameters."}
                return
            
            source_folder = settings.get("sourceFolder")
            if not os.path.exists(source_folder):
                try:
                    os.makedirs(source_folder)
                except Exception:
                    resp.status = falcon.HTTP_400
                    resp.media = {"error": f"Source folder {source_folder} does not exist."}
                    return
            
            #set env vars 
            os.environ["SOURCE_FOLDER"] = source_folder
            os.environ["OPENAI_API_KEY"] = settings.get("openaiKey")

            logger.info("Received task: %s", messages[-1]["content"] if messages else "No messages provided")
        except Exception:
            resp.status = falcon.HTTP_400
            resp.media = {"error": "Invalid JSON"}
            return

        resp.status = falcon.HTTP_200
        resp.content_type = 'application/x-ndjson'

        def generate():
            for item in run_workflow_generator(task=messages, db_config=db_config):
                line = json.dumps(item) + "\n"
                yield line.encode("utf-8")

        resp.stream = generate()

class _MockWorkflowResource:
    def on_post(self, req, resp):
        try:

            data = req.media
            task = data.get("message", None)
            logger.info("Received task: %s", task)
        except Exception:
            resp.status = falcon.HTTP_400
            resp.media = {"error": "Invalid JSON"}
            return

        resp.status = falcon.HTTP_200
        resp.content_type = 'application/x-ndjson'

        def generate():
            levels = ["system", "workflow", "notification"]
            for i in range(10):
                random_level = random.choice(levels)
                message = {
                    "status": "processing",
                    "name": "node",
                    "level":random_level,
                    "text": f"Step {i+1} test completed puya..."
                }
                yield (json.dumps(message) + "\n").encode("utf-8")
                time.sleep(1)  # Delay of 1 second

            final_message = {
                "status": "done",
                "level":"workflow",
                "name": "workflow",
                "text": "Task completed successfully",
            }
            yield (json.dumps(final_message) + "\n").encode("utf-8")

        resp.stream = generate()

class EnvResource:
    def on_get(self, req, resp):
        if req.path.endswith('/settings'):
            env_vars = {
            "SOURCE_FOLDER": os.environ.get("SOURCE_FOLDER", ""),
            "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", ""),
        }
        elif req.path.endswith('/db'):
            env_vars = {
                "DB_NAME": os.environ.get("DB_NAME", ""),
                "DB_USER": os.environ.get("DB_USER", ""),
                "DB_PASSWORD": os.environ.get("DB_PASSWORD", ""),
                "DB_HOST": os.environ.get("DB_HOST", ""),
                "DB_PORT": os.environ.get("DB_PORT", ""),
                "DB_TYPE": os.environ.get("DB_TYPE", ""),
            }
        resp.status = falcon.HTTP_200
        resp.media = env_vars


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
        
        try:
            file_list = get_file_list()
            file_list = [f for f in file_list if f.endswith(('.py', '.json', '.md'))]
            file_list.sort()
            resp.status = falcon.HTTP_200
            resp.media = {"files": file_list}
        except Exception as e:
            resp.status = falcon.HTTP_500
            resp.media = {"error": str(e)}

    def get_file(self, req, resp):
        file_name = req.get_param("name")
        content = read_python_code(file_name)
        if file_name.endswith(".py"):
            content = f"```python\n{content}\n```"
        elif file_name.endswith(".json"):
            content = f"```json\n{content}\n```"
        resp.status = falcon.HTTP_200
        resp.media = {"content": content}

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
            db_type = data.get("DB_TYPE")

            os.environ["DB_NAME"] = db_name
            os.environ["DB_USER"] = db_user
            os.environ["DB_PASSWORD"] = db_password
            os.environ["DB_HOST"] = db_host
            os.environ["DB_PORT"] = db_port
            os.environ["DB_TYPE"] = db_type

            if not all([db_name, db_user, db_password, db_host, db_port]):
                resp.status = falcon.HTTP_400
                resp.media = {"error": "Missing database connection parameters."}
                return

            adapter = get_adapter(db_type)

            result = adapter.check_db(
                db_name=db_name,
                db_user=db_user,
                db_password=db_password,
                db_host=db_host,
                db_port=db_port
            )

            permissions = adapter.check_permissions()
            if permissions["status"]=="error":
                resp.status = falcon.HTTP_403
                resp.media = permissions
                return

            schemas = adapter.get_schemas_from_db()
            table_names = list(schemas.keys())
            random.shuffle(table_names)
            
            if result:
                resp.status = falcon.HTTP_200
                resp.media = {"message": "Connection to DB was successful!", "tables": table_names}
            else:
                resp.status = falcon.HTTP_500
                resp.media = {"error": "Connection to DB failed. Please check your credentials."}
        except Exception as e:
            print(e)
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
app.add_route("/api/env/settings", EnvResource())
app.add_route("/api/env/db", EnvResource())

#get current directory
static_resource = f"{os.path.dirname(os.path.abspath(__file__))}/ui/dist"
# Route handling:
app.add_static_route("/{filepath:path}", static_resource)
app.add_static_route("/", static_resource, fallback_filename='index.html')


# # Threading WSGI server to handle concurrent requests
class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True

#function to check if env vars are set
def check_env_vars():
    required_vars = ["SOURCE_FOLDER", "OPENAI_API_KEY"]
    missing = []
    for var in required_vars:
        if var not in os.environ:
            missing.append(var)
    if len(missing) > 0:
        #print with emoji and red with f""
        print("\033[91m" + "❌" + "\033[0m", end=" ")
        print(f"Missing environment variables: {', '.join(missing)}")
        #raise exception and exit
        sys.exit(1)

def main():
    port = int(os.environ.get("API_PORT", "48001"))
    with make_server("", port, app, server_class=ThreadingWSGIServer, handler_class=LoggingWSGIRequestHandler) as httpd:
        logger.info(f"Serving on http://localhost:{port}/")
        #print port with emoji and green
        print("\033[92m" + "✅" + "\033[0m", end=" ")
        print(f"Serving on http://localhost:{port}/")
        httpd.serve_forever()

if __name__ == "__main__":
    main()
