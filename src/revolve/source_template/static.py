import falcon
import os
import mimetypes

class StaticResource:
    def __init__(self, static_dir):
        """
        Initialize the StaticResource with a specific static directory.
        """
        self.static_dir = os.path.abspath(static_dir)

    def on_get(self, req, resp, filepath=""):
        """
        Handles requests for both root files and nested assets.
        """
        # Ensure filepath is safely joined to prevent path traversal
        file_path = os.path.normpath(os.path.join(self.static_dir, filepath))

        # Prevent path traversal by ensuring the file_path starts with static_dir
        if not file_path.startswith(self.static_dir):
            resp.status = falcon.HTTP_404
            resp.text = "404 - Not Found"
            return

        # Handle fallback for missing assets
        if not os.path.isfile(file_path):
            if filepath == "favicon.ico":
                resp.status = falcon.HTTP_404
                resp.text = "404 - Favicon not found"
                return
            file_path = os.path.join(self.static_dir, "index.html")

        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(file_path)
        resp.content_type = mime_type or "application/octet-stream"

        # Serve the file
        try:
            with open(file_path, "rb") as f:
                resp.data = f.read()
        except Exception as e:
            resp.status = falcon.HTTP_500
            resp.text = f"Error serving file: {str(e)}"