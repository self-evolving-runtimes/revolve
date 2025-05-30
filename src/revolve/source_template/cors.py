import falcon_cors

def set_cors():
    """
    Set up CORS for the Falcon application.
    This allows all origins, headers, and methods.
    """
    cors = falcon_cors.CORS(
        allow_all_origins=False,
        allow_all_headers=True,
        allow_all_methods=True
    )
    return cors