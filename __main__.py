from .app import app
import os

debug = os.getenv("DEBUG", "") == "1"
app.config.SERVER_NAME = "http://localhost:8008" if debug else "https://paste.zi.fi"
app.config.REQUEST_MAX_SIZE = 100_000
app.run(host="::1", port=8008, debug=debug, auto_reload=True)
