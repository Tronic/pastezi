from sanic import Sanic
from sanic.response import json, redirect, html, text, raw
import mimetypes
from pathlib import PurePosixPath
from glob import glob
from .helper import make_async
from . import content, layout, db
import os

app = Sanic(strict_slashes=True)

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
    if paste: return html(layout.view_paste(paste, paste_id))
    return html(layout.view_paste(None, paste_id), status=404)

@app.post("/")
async def post_paste(req):
    paste, paste_id = req.form.get("paste"), req.form.get("paste_id")
    if not paste and "paste" in req.files:
        mime, paste, paste_id = req.files["paste"][0]
    paste_id, paste_object = await content.process_paste(paste, paste_id, fallback_charset=req.args.get("charset"))
    created = await backend.store(paste_id, paste_object)
    return redirect(app.url_for("view_paste", paste_id=paste_id), status=200+created)

@app.put("/")
@app.put("/p/")
@app.put("/p/<paste_id>", name="put_paste")
async def put_paste(req, paste_id=None):
    paste_id, paste_object = await content.process_paste(req.body, paste_id, fallback_charset=req.args.get("charset"))
    created = await backend.store(paste_id, paste_object)
    return text(app.url_for("view_paste", paste_id=paste_id, _external=True) + "\n", status=200+created)

@app.delete(f"/p/<paste_id>", name="delete")
async def delete_paste(req, paste_id):
    return text(None, status=204 if await backend.delete(paste_id) else 404)

staticdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "static")
app.static("/", staticdir)
layout = layout.Layout(app)
backend = db.Backend()
