# Pastezi

An attempt to create a pastebin site that does not suck. https://paste.zi.fi/

* Automatic paste of text into editbox (if you give permission)
* Automatic copy of link after saving
* The usual keyboard shortcuts for save/open/copy
* Syntax hilight for editor and viewer (format detected by file extension or content)
* No line numbers etc. get copied (even if you manually paint them or Ctrl+A)

RESTful API returns the viewing URL:

    curl -XPUT https://paste.zi.fi/ -T your_file.txt

No access control. Anyone may edit or delete pastes, if they have the URL. If no filename is provided, a random name is created.

Pastes are preserved for a week since last edit or view.
