import pygments
from pygments.lexers import get_lexer_for_filename, guess_lexer
from pygments.formatters import HtmlFormatter  # pylint: disable=no-name-in-module
import re, os
from .helper import make_async
from sanic.exceptions import NotFound, InvalidUsage
from pronounceable import PronounceableWord

matchers = {
    # First try shebangs and other things at the beginning of the file
    ".sh": re.compile(r"^#!/bin/(ba)?sh\s"),
    ".scala": re.compile(r"^#!/.*scala\s"),
    ".py": re.compile(r"^#!/.*python"),
    ".html": re.compile(r"^\s*<!doctype html", re.IGNORECASE),
    ".svg": re.compile(r"^\s*<!doctype svg", re.IGNORECASE),
    ".xml": re.compile(r"^\s*<?xml "),
    ".js": re.compile(r"""^\s*["']use strict["']"""),
    ".css": re.compile(r"^@charset ", re.IGNORECASE),
    # Try matching content on any line of the file
    ".sql": re.compile(r"^SELECT .* FROM |^INSERT INTO ", re.MULTILINE),
    ".scala": re.compile(r"^object [A-Z]\w* {$", re.MULTILINE),
    ".py": re.compile(r"^ *(def|if|while|for) .*:$", re.MULTILINE),
    ".cs": re.compile(r"using \w+;.*\n(public )?class \w+", re.DOTALL),
    ".java": re.compile(r"^public class \w+", re.MULTILINE),
    ".cpp": re.compile(r"#include .*\w::\w|using namespace \w+;", re.DOTALL),
    ".c": re.compile(r"#include .*(malloc|printf)\(|int main\(void\)", re.DOTALL),
    ".js": re.compile(r"""^\s*console.log\(|^\s*(var|let|const) \w+ = require|\) => {$|^function( \w)?\(""", re.MULTILINE),
    ".css": re.compile(r"^\s*(color: *#[0-9a-fA-F]{3,6}|width: \d+(px|r?em|%));$", re.IGNORECASE | re.MULTILINE),
}

formatter = HtmlFormatter(lineanchors=True)

def prepare_highlight(staticdir):
    with open(os.path.join(staticdir, "highlight.css"), "w") as f:
        f.write(formatter.get_style_defs())

def prettyprint(paste, paste_id):
    try: lexer = get_lexer_for_filename(paste_id)
    except Exception: lexer = get_lexer_for_filename(paste_id + ".txt")
    return pygments.highlight(paste, lexer, formatter)

@make_async
def process_paste(paste, paste_id):
    if isinstance(paste, bytes):
        # Charset autodetection (much better than chardet module)
        # - UTF16-LE with BOM is commonly used in Windows; if no BOM, default to UTF-8
        # - Fallback to 8-bit: ISO-8895-1 unless the content looks more like DOS CP437
        # - ISO-8859-1 and CP437 can decode any byte, and thus will never fail (in contrast to, e.g. CP1252)
        try: paste = paste.decode("UTF-16LE" if paste[:2] == b"\xFF\xFE" else "UTF-8")
        except UnicodeDecodeError:
            if 0 in paste: raise InvalidUsage("Binary files are not supported!")
            paste = paste.decode("CP437" if any(0x80 <= ch < 0xA0 for ch in paste) and b"\r\n" in paste else "ISO-8859-1")
    if paste[0] == "\uFEFF": paste = paste[1:]  # Remove Unicode BOM
    paste = paste.replace("\r\n", "\n").strip()
    if not paste: raise InvalidUsage("Empty paste (no data found)")
    paste += "\n"  # Training newline for downloads
    if paste_id:
        paste_id = "".join([c for c in paste_id.replace(" ", "_") if re.match(r'[-_\w\.]', c)])
    if not paste_id or len(paste_id) < 3:
        ext = next((e for e, r in matchers.items() if r.search(paste)), ".txt")
        paste_id = PronounceableWord().length(6, 15) + ext
    return paste_id, dict(text=paste, html=prettyprint(paste, paste_id))
