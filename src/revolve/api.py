import time
import falcon
import logging
import json
import traceback
import sys
import os
from wsgiref.simple_server import make_server, WSGIServer
from socketserver import ThreadingMixIn
from src.revolve.main import run_workflow


LOGLEVEL = os.environ.get("LOGLEVEL", "INFO").upper()
logging.basicConfig(level=LOGLEVEL)
logger = logging.getLogger(__name__)

class WorkflowResource:
    def on_post(self, req, resp):
        try:
            data = req.media 
            task = data.get("task", "Default task")
        except Exception:
            resp.status = falcon.HTTP_400
            resp.media = {"error": "Invalid JSON"}
            return

        resp.status = falcon.HTTP_200
        resp.content_type = 'application/x-ndjson'

        def generate():
            for item in run_workflow(task=task):
                line = json.dumps(item) + "\n"
                yield line.encode("utf-8")

        resp.stream = generate()

app = falcon.App()
app.add_route("/run_workflow", WorkflowResource())


# Threading WSGI server to handle concurrent requests
class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True


if __name__ == "__main__":
    port = int(os.environ.get("API_PORT", "48001"))
    with make_server("", port, app, ThreadingWSGIServer) as httpd:
        logger.info(f"Serving on http://localhost:{port}/")
        httpd.serve_forever()