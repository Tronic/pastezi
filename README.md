# Pastezi

An attempt to create a pastebin site that does not suck. https://paste.zi.fi/

* Auto-paste into textbox (if you give permission)
* Auto-copy of link after saving
* The usual keyboard shortcuts for save/open/copy/print
* Syntax hilight for editor and viewer
* Autodetection by file extension and content
* No extra cruft gets copied (even by Ctrl+A) or printed
* Implemented with [Sanic](https://sanic.readthedocs.io/) and [Redis](https://redis.io/) in async Python for insanely high performance

Use PUT request to send files without browser:

    curl https://paste.zi.fi/ -T your_file.txt

An URL for viewing in browser is returned. For direct download, remove the `/view` part at the end of the URL (or add `?view=0` to PUT URL so that it returns this):

    wget https://paste.zi.fi/p/your_file.txt

No access control. Anyone may edit or delete pastes, if they have the URL. If no filename is provided, a random name is created.

Pastes are deleted after six weeks without views, or when edited to empty content.
