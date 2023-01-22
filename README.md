# Pastezi

An attempt to create a pastebin site that does not suck. https://paste.zi.fi/

* Auto-paste into textbox (if you give permission)
* Auto-copy of link after saving
* The usual keyboard shortcuts for save/open/copy/print
* Syntax hilight for editor and viewer
* Autodetection by file extension and content
* No extra cruft gets copied (even by Ctrl+A) or printed
* Implemented with [Sanic](https://sanic.readthedocs.io/) and [Redis](https://redis.io/) in async Python for insanely high performance

No access control. Anyone may edit or delete pastes, if they have the URL. If no filename is provided, a random name is created.

Pastes are deleted after one year without views, or when re-uploaded with empty content.

## Scriptable API

A PUT request to site root creates a randomly named paste, while a PUT request to full URL (with filename) creates or modifies that paste. HTTP 201 Created is given if the paste didn't exist before. The URL of the paste will be returned (for viewing in browser or raw curl/wget/fetch).

    curl https://paste.zi.fi/ -X PUT -d "text to paste"
    curl https://paste.zi.fi/p/ -T your_file.txt
    wget https://paste.zi.fi/p/your_file.txt

Notice that binary files are not supported and that trailing newlines and such may get altered.
