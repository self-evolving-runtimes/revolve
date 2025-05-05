import logging
import os
import sys
from socketserver import ThreadingMixIn
from wsgiref.simple_server import make_server, WSGIServer
import traceback
import json
import falcon

###IMPORTS###
#from hellodb import HelloDBResource (just an example, not implemented)

def debug_error_serializer(req, resp, exception):
    resp.content_type = falcon.MEDIA_JSON
    resp.text = json.dumps({
        'title': str(exception),
        'description': getattr(exception, 'description', None),
        'traceback': traceback.format_exc()
    })

LOGLEVEL = os.environ.get("LOGLEVEL", "INFO").upper()
logging.basicConfig(level=LOGLEVEL)
logger = logging.getLogger(__name__)
app = falcon.App()

app.set_error_serializer(debug_error_serializer)

###ENDPOINTS###
#app.add_route("/hello_db", HelloDBResource()) (just an example, not implemented)

class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    pass

if __name__ == "__main__":
    port = os.environ.get("PORT", "48000")
    with make_server("", int(port), app, ThreadingWSGIServer) as httpd:
        logger.info(f"Serving on port {port}...")

        httpd.serve_forever()
