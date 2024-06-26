import pygments
from pygments.lexers import get_lexer_for_filename, guess_lexer
from pygments.formatters import HtmlFormatter  # pylint: disable=no-name-in-module
import re, os
from .helper import make_async
from sanic.exceptions import NotFound, InvalidUsage
from pronounceable import PronounceableWord

matchers = (
    # First try shebangs and other things at the beginning of the file
    (".sh", re.compile(r"^#!/bin/(ba)?sh\s")),
    (".scala", re.compile(r"^#!/.*scala\s")),
    (".py", re.compile(r"^#!/.*python")),
    (".html", re.compile(r"^\s*<!doctype html", re.IGNORECASE)),
    (".svg", re.compile(r"^\s*<!doctype svg", re.IGNORECASE)),
    (".xml", re.compile(r"^\s*<?xml ")),
    (".php", re.compile(r"^\s*<\?php\s", re.IGNORECASE)),
    (".js", re.compile(r"""^\s*["']use strict["']""")),
    (".css", re.compile(r"^\s*@charset ", re.IGNORECASE)),
    # Try matching content on any line of the file
    (".sql", re.compile(r"^SELECT .* FROM |^INSERT INTO ", re.MULTILINE)),
    (".scala", re.compile(r"^object [A-Z]\w* {$", re.MULTILINE)),
    (".py", re.compile(r"^ *(def|if|while|for) .*:$", re.MULTILINE)),
    (".cs", re.compile(r"using \w+;.*\n(public )?class \w+", re.DOTALL)),
    (".java", re.compile(r"^public class \w+", re.MULTILINE)),
    (".cpp", re.compile(r"#include .*\w::\w|using namespace \w+;", re.DOTALL)),
    (".c", re.compile(r"#include .*(malloc|printf)\(|int main\(void\)", re.DOTALL)),
    (".js", re.compile(r"^\s*console.log\(|^\s*(var|let|const) \w+ = require|\) => {$|^\s*function( \w+)?\(", re.MULTILINE)),
    (".php", re.compile(r"<\?php.*\?>")),
    (".css", re.compile(r"^\s*(color: *#[0-9a-fA-F]{3,6}|width: \d+(px|r?em|%));$", re.IGNORECASE | re.MULTILINE)),
)

class Formatter(HtmlFormatter):
    # Link & anchor line numbers
    def _wrap_lineanchors(self, inner):
        i = self.linenostart - 1
        for t, line in inner:
            if t:
                i += 1
                yield 1, f'<a class=line href=#{i} id={i} tabindex=-1></a>' + line
            else:
                yield 0, line
    # A bit shorter wrapper, and link URLs
    def _wrap_pre(self, inner):
        yield 0, '<pre><code>'
        for i, t in inner:
            if i == 1:
                t = re.sub(r'(http[s]?://\S+)', r'<a href="\1">\1</a>', t)
            yield i, t
        yield 0, '</code></pre>'

def prettyprint(paste, paste_id):
    n = 1 + re.search("^\s*", paste)[0].count("\n")  # Pygments removes initial empty lines, account for that
    formatter = Formatter(lineanchors=True, linenostart=n)
    try: lexer = get_lexer_for_filename(paste_id)
    except Exception: lexer = get_lexer_for_filename(paste_id + ".txt")
    return pygments.highlight(paste, lexer, formatter)

def decode(text: bytes, fallback_charset: str = None) -> str:
    """Decode with charset autodetection. Removes Unicode BOMs automatically."""
    # Unicode strings with BOMs
    boms = (b"\xEF\xBB\xBF", "UTF-8"), (b"\xFF\xFE", "UTF-16LE"), (b"\xFE\xFF", "UTF-16BE"), (b"\xFF\xFE\0\0", "UTF-32LE"), (b"\0\0\xFE\xFF", "UTF-32BE")
    for bom, charset in boms:
        if text.startswith(bom): return text[len(bom):].decode(charset, errors="replace")
    # Try UTF-8 without BOM
    try: return text.decode()
    except UnicodeDecodeError: pass
    # If fallback is provided, just use that
    if fallback_charset: return text.decode(fallback_charset, errors="replace")
    # 8-bit guesswork
    # - NUL usually means binary data (could be actual NUL or UTF-16/32 w/o BOM, but all those are rare)
    if 0 in text: raise InvalidUsage("Looks like binary data")
    # - With CR/LF line terminators, CP437 umlauts are more likely than ISO-8859-1 extended control chars
    if any(0x80 <= ch < 0xA0 for ch in text) and b"\r\n" in text: return text.decode("CP437")
    # - The most common 8-bit encoding is a reasonable final fallback
    return text.decode("ISO-8859-1")

@make_async
def process_paste(paste, paste_id, fallback_charset = None):
    if isinstance(paste, bytes): paste = decode(paste, fallback_charset)
    elif paste is None: raise InvalidUsage("Malformed request (no paste found)")
    elif paste[0] == "\uFEFF": paste = paste[1:]  # Remove Unicode BOM
    paste = paste.replace("\r\n", "\n")
    if not paste.strip(): raise InvalidUsage("Empty paste (no data found)")
    if not paste.endswith("\n"): paste += "\n"
    if paste_id:
        paste_id = "".join([c for c in paste_id.replace(" ", "_") if re.match(r'[-_\w\.]', c)])
    if not paste_id or len(paste_id) < 3:
        ext = next((e for e, r in matchers if r.search(paste)), ".txt")
        paste_id = PronounceableWord().length(6, 15) + ext
    return paste_id, dict(text=paste, html=prettyprint(paste, paste_id))
