import logging
import os
from socketserver import ThreadingMixIn
from wsgiref.simple_server import make_server, WSGIServer
import traceback
import json
import falcon

from cors import set_cors
from static import StaticResource

###IMPORTS###
#from hellodb import HelloDBResource (just an example, not implemented)
#from hellodb import HelloDBSchemaResource (just an example, not implemented)

cors = set_cors()

def debug_error_serializer(req, resp, exception):
    resp.content_type = falcon.MEDIA_JSON
    # Format traceback directly from the exception if possible
    tb = getattr(exception, '__traceback__', None)
    if tb:
        tb_str = ''.join(traceback.format_exception(type(exception), exception, tb))
    else:
        tb_str = 'Traceback unavailable'

    resp.text = json.dumps({
        'title': str(exception),
        'description': getattr(exception, 'description', None),
        'traceback': tb_str
    })

LOGLEVEL = os.environ.get("LOGLEVEL", "DEBUG").upper()
logging.basicConfig(level=LOGLEVEL)
logger = logging.getLogger(__name__)
app = falcon.App(middleware=[cors.middleware])

app.set_error_serializer(debug_error_serializer)

# Instantiate StaticResource with the static directory
if os.environ.get("STATIC_DIR") != "-":
    static_resource = StaticResource(os.environ.get("STATIC_DIR")   )
    # Route handling:
    app.add_route("/{filepath:path}", static_resource)
    app.add_route("/", static_resource)

###ENDPOINTS###
#app.add_route("/hello_db", HelloDBResource()) (just an example, not implemented)
#app.add_route/"hello_db/schema", HelloDBSchemaResource()) (just an example, not implemented)

class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    pass

if __name__ == "__main__":
    port = os.environ.get("PORT", "48000")
    with make_server("", int(port), app, ThreadingWSGIServer) as httpd:
        logger.info(f"Serving on port {port}...")

        httpd.serve_forever()
