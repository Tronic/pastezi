import mimetypes
import os
from glob import glob
from pathlib import PurePosixPath

from sanic import Sanic
from sanic.exceptions import NotFound
from sanic.log import logging
from sanic.response import empty, html, json, raw, redirect, text

from . import content, db
from .helper import make_async
from .layout import Layout

app = Sanic("pastezi", strict_slashes=True)

@app.listener('before_server_start')
async def init(app, loop):
    await backend.start(loop)

@app.listener('after_server_stop')
def finish(app, loop):
    loop.run_until_complete(backend.close())
    loop.close()

@app.get("/", name="index")
@app.get(f"/p/<paste_id>/edit")
async def edit_paste(req, paste_id=None):
    paste = paste_id and await backend[paste_id]
    layout = Layout(req)
    return html(layout.edit_paste(paste, paste_id))

@app.get(f"/p/<paste_id>")
async def get_paste(req, paste_id):
    paste = await backend[paste_id]
    if not paste: return text(None, status=404)
    headers = {"Content-Type": mimetypes.guess_type(paste_id), "Content-Disposition": "attachment"}
    return text(paste["text"], headers=headers)

@app.get(f"/p/<paste_id>/view")
async def view_paste(req, paste_id):
    paste = await backend[paste_id]
    layout = Layout(req)
    if paste: return html(layout.view_paste(paste, paste_id))
    return html(layout.view_paste(None, paste_id), status=404)

def get_url(req, paste_id):
    view = req.args.get("view", "1") == "1"
    return req.url_for("view_paste" if view else "get_paste", paste_id=paste_id)

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

@app.put("/")
@app.put("/p/")
@app.put("/p/<paste_id>", name="put_paste")
async def put_paste(req, paste_id=None):
    await req.receive_body()
    paste_id, paste_object = await content.process_paste(req.body, paste_id, fallback_charset=req.args.get("charset"))
    created = await backend.store(paste_id, paste_object)
    status = 201 if created else 200
    return text(f"{get_url(req, paste_id)}\n", status=status)

@app.delete("/p/<paste_id>", name="delete")
async def delete_paste(req, paste_id):
    deleted = await backend.delete(paste_id)
    return empty(204 if deleted else 404)

staticdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "static")
app.static("/", staticdir)
backend = db.Backend()
