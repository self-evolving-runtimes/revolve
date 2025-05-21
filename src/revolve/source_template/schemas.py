import falcon
class SchemasResource:
    def on_get(self, req, resp):
        resp.media = [
            ## Routes
    ]
        resp.status = falcon.HTTP_200

