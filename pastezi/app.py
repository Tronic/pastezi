import mimetypes
from pathlib import Path

from sanic import Sanic
from sanic.response import empty, html, redirect, text

from . import content, db
from .layout import Layout


app = Sanic("pastezi", strict_slashes=True)

app.config.REQUEST_MAX_SIZE = 1_000_000

staticdir = Path(__file__).resolve().parent.parent / "static"
if not staticdir.is_dir():
    raise RuntimeError(f"Static files not found in {staticdir}")
app.static("/", staticdir)

@app.before_server_start
async def init(app):
    global backend
    backend = db.Backend()
    await backend.start()

@app.get("/", name="index")
@app.get(f"/p/<paste_id>/edit")
async def edit_paste(req, paste_id=None):
    paste = paste_id and await backend[paste_id]
    layout = Layout(req)
    return html(layout.edit_paste(paste, paste_id))

# Forced raw download - end with filename for wget support
@app.get(f"/dl/<paste_id>")
async def download_paste(req, paste_id):
    paste = await backend[paste_id]
    if not paste: return text(None, status=404)
    headers = {"content-type": mimetypes.guess_type(paste_id), "content-disposition": "attachment"}
    return text(paste["text"], headers=headers)

# View for browser and API depending on accept header
@app.get(f"/p/<paste_id>/view", name="old_view_paste")
@app.get(f"/p/<paste_id>")
async def view_paste(req, paste_id):
    paste = await backend[paste_id]
    layout = Layout(req)
    h = "text/html" in req.headers.get("accept", "")  # Note: "text/html" in req.accept allows */* too!
    if not paste:
        return html(layout.view_paste(None, paste_id), status=404) if h else empty(404)
    return html(layout.view_paste(paste, paste_id)) if h else text(paste["text"])

# HTML form API
@app.post("/")
async def post_paste(req):
    await req.receive_body()
    paste, paste_id = req.form.get("paste"), req.form.get("paste_id")
    if not paste and "paste" in req.files:
        mime, paste, paste_id = req.files["paste"][0]
    paste_id, paste_object = await content.process_paste(paste, paste_id, fallback_charset=req.args.get("charset"))
    created = await backend.store(paste_id, paste_object)
    url = get_url(req, paste_id)
    if "text/html" in req.headers.getone("accept", "*/*"):
        return redirect(url)
    else:
        status = 201 if created else 200
        return text(f"{url}\n", status=status)

# CRUD API

@app.put("/", name="put_paste_noid")
@app.put("/p/", name="put_paste_noid2")
@app.put("/p/<paste_id>")
async def put_paste(req, paste_id=None):
    await req.receive_body()
    paste_id, paste_object = await content.process_paste(req.body, paste_id, fallback_charset=req.args.get("charset"))
    created = await backend.store(paste_id, paste_object)
    status = 201 if created else 200
    url = req.url_for("view_paste", paste_id=paste_id)
    return text(f"{url}\n", status=status)

@app.delete("/p/<paste_id>")
async def delete_paste(req, paste_id):
    deleted = await backend.delete(paste_id)
    return empty(204 if deleted else 404)
