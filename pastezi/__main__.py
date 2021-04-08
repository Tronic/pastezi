from .app import app
import os

debug = os.getenv("DEBUG", "") == "1"
app.config.SERVER_NAME = "http://localhost:8080" if debug else "https://paste.zi.fi"
app.config.REQUEST_MAX_SIZE = 100_000
app.run(host="127.0.0.1", port=8080, debug=debug, access_log=False)
