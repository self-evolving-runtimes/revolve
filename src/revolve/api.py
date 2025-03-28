import logging
import os
import sys
from socketserver import ThreadingMixIn
from wsgiref.simple_server import make_server, WSGIServer
from routes import Routes

import falcon

LOGLEVEL = os.environ.get("LOGLEVEL", "INFO").upper()
logging.basicConfig(level=LOGLEVEL)
logger = logging.getLogger(__name__)
app = falcon.App()


routes = Routes()
routes.configure(app)

class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    pass


if __name__ == "__main__":
    port = os.environ.get("PORT", "48000")
    with make_server("", int(port), app, ThreadingWSGIServer) as httpd:
        logger.info(f"Serving on port {port}...")

        httpd.serve_forever()
