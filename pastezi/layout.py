from html import escape

class Layout:
    def __init__(self, req):
        self.url = req.url_for
        self.header1 = """<!DOCTYPE html><meta charset=UTF-8><title>"""
        self.header2 = (
            """</title>"""
            """<meta name=viewport content="width=device-width, initial-scale=1">"""
            f"""<link rel=stylesheet href="{self.static("fonts.css")}">"""
            f"""<link rel=stylesheet href="{self.static("codemirror/lib/codemirror.css")}">"""
            f"""<link rel=stylesheet href="{self.static("highlight.css")}">"""
            f"""<link rel=stylesheet href="{self.static("style.css")}">"""
            f"""<link rel=manifest href="{self.static("manifest.json")}"">"""
            f"""<link rel="apple-touch-icon" sizes="180x180" href="{self.static("icons/apple-touch-icon.png")}">"""
            f"""<link rel="icon" type="image/svg" sizes="32x32" href="{self.static("icons/favicon-32x32.png")}">"""
            f"""<link rel="icon" type="image/png" sizes="32x32" href="{self.static("icons/favicon-32x32.png")}">"""
            f"""<link rel="icon" type="image/png" sizes="16x16" href="{self.static("icons/favicon-16x16.png")}">"""
            f"""<link rel="mask-icon" href="{self.static("icons/safari-pinned-tab.svg")}" color="#ffcc33">"""
            f"""<link rel="shortcut icon" href="{self.static("icons/favicon.ico")}">"""
            f"""<meta name="msapplication-TileColor" content="#ffcc33">"""
            f"""<meta name="msapplication-config" content="{self.static("icons/browserconfig.xml")}">"""
            f"""<meta name="theme-color" content="#ffcc33">"""
        )
        self.nav_start = f"""<header><a id=new title="New paste" href=/></a>"""
        scripts = "script.js", "codemirror/lib/codemirror.js", "codemirror/mode/meta.js", "codemirror/addon/mode/loadmode.js"
        for s in scripts: self.header2 += f"""<script src="{self.static(s)}"></script>"""
    def static(self, filename): return self.url("static", filename=filename)

    def __call__(self, body, head = "", title = ""):
        return self.header1 + title + self.header2 + head + self.nav_start + body

    def edit_paste(self, paste, paste_id):
        text = escape(paste["text"]) if paste else ""
        head = f"""<form action="{self.url("post_paste")}" method=POST enctype=multipart/form-data>"""
        body = (
            """<label id=open title="Open file"><input type=file name=paste></label>"""
            f"""<label>Save as:<input id=paste_id name=paste_id value="{escape(paste_id or '')}" placeholder="filename.txt (optional)" """
            r"""pattern="[^/]{3,}" autocomplete=off autofocus></label>"""
            f"""<label id=upload title=Upload><input type=submit></label>"""
            """<data id=notify value=""></data></header><main>"""
            f"""<textarea id=paste name=paste>\n{text}</textarea>"""
            """</main></form>"""
            """<footer><a href="https://github.com/Tronic/pastezi">Pastezi</a> - a pastebin that doesn't suck!</footer>"""
        )
        return self(body, head, title=paste_id or "New Paste")

    def view_paste(self, paste, paste_id):
        body = f"""<data id=paste_id value="{paste_id}"></data>"""
        if paste: body += (
            f"""<a id=copy title="Copy all" href="javascript:copy_all_without_formatting()"></a>"""
            f"""<a id=dl title=Download href="{self.url("download_paste", paste_id=paste_id)}"></a>"""
        )
        body += f"""<a id=edit title=Edit href="{self.url("edit_paste", paste_id=paste_id)}"></a>"""
        body += """<data id=notify value=""></data></header><main>"""
        body += paste["html"] if paste else f"<p>{paste_id} not found. This paste may have been deleted or you got the address wrong."
        body += "</main>"
        return self(body, title=paste_id or "Pastezi")
