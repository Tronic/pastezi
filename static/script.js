"use strict";

const copy = text => {
    const textarea = document.createElement("textarea")
    document.body.appendChild(textarea)
    textarea.value = text
    textarea.select()
    document.execCommand("Copy")
    textarea.remove()
}

const copy_all_without_formatting = () => {
    copy(document.querySelector("pre").textContent)
    notify("Full text copied to clipboard!")
    shake("#copy")
}

var notify_timeout

const notify = msg => {
    const elem = document.querySelector("#notify")
    elem.value = ""
    elem.classList.remove("visible")
    clearTimeout(notify_timeout)
    if (!msg) return
    console.log("Notify: ", msg)
    elem.value = msg
    elem.classList.add("visible")
    notify_timeout = setTimeout(() => elem.classList.remove("visible"), 3000)
}

const shake = button_selector => {
    const button = document.querySelector(button_selector)
    button.className = "shake"
    setTimeout(() => button.className = "", 200)
}

let editor, textarea, idinput, fileinput

window.addEventListener("load", () => {
    const flash = sessionStorage.getItem("flash")
    if (flash) { sessionStorage.removeItem("flash"); notify(flash) }
    idinput = document.querySelector("input#paste_id")
    if (!idinput) return  /* Viewing paste, not editing */
    document.querySelector("form").addEventListener("submit", send_paste)
    textarea = document.querySelector("#paste")
    let use_editor = new URLSearchParams(window.location.search).get("editor")
    if (use_editor === null) use_editor = /(android)/i.test(navigator.userAgent) ? "0" : "1"
    if (use_editor === "1") {
        CodeMirror.modeURL = "/codemirror/mode/%N/%N.js";
        editor = CodeMirror.fromTextArea(textarea, { lineNumbers: true, indentUnit: 4, tabSize: 4, dragDrop: false, viewportMargin: Infinity, lineWrapping: true })
    }
    fileinput = document.querySelector("input[type=file]")
    fileinput.addEventListener("change", fileOpen)
    idinput.addEventListener("change", updateMode)
    updateMode()
    /* Automatic paste in Chrome */
    if (navigator.clipboard.readText && get().length === 0) {
        notify("Shall I auto-paste into the editor?")
        navigator.clipboard.readText().then(text => {
            if (text.startsWith(location.origin) || text.trim().length === 0) return notify()
            set(text)
            notify(" ⃪ click to upload auto-pasted text")
        }).catch(e => notify())
    }
})

document.addEventListener('dragover', ev => ev.preventDefault())
const get = () => (editor ? editor.getValue() : textarea.value)
const set = text => editor ? editor.setValue(text) : textarea.value = text

const send_paste = ev => {
    ev.preventDefault()
    send_paste_async()
}

const send_paste_async = async () => {
    shake("#upload")
    const text = get();
    const has_text = text.trim().length > 0
    const paste_id = idinput.value.trim() || idinput.placeholder
    if (!has_text && paste_id.length === 0) return notify("Write some text in the box first!")
    const res = await fetch("/p/" + encodeURIComponent(paste_id), {
        method: has_text ? "PUT" : "DELETE",
        body: has_text ? text : undefined,
    })
    if (res.type === "text/html") return document.write(await res.text())
    if (!has_text) return notify(res.status === 204 ? "Deleted from server" : "Nothing to do!")
    if (res.status === 413) return notify("Too much text. Try shorter.")
    if (res.status >= 400) return notify(await res.text())
    const url = (await res.text()).trim()
    if (res.status === 201) { copy(url); sessionStorage.setItem("flash", "Link copied:\n" + url) }
    else if (res.status === 200) sessionStorage.setItem("flash", "Changes saved!")
    window.location = url
}

const download = ev => {
    shake("#dl")
    window.location = document.querySelector("#dl").href  // File is saved, user stays on current page
    ev.preventDefault()
}

document.onkeydown = function(e) {
    const ctrl = e.ctrlKey || e.metaKey && navigator.platform === "MacIntel"
    if ((ctrl && e.key === "s") || ((ctrl || e.shiftKey) && e.key === "Enter")) {
        if (textarea) send_paste(e)
        else download(e)
    }
    if (!textarea && ctrl && e.key === "c" && window.getSelection().isCollapsed) {
        copy_all_without_formatting()
        e.preventDefault()
    }
    if (fileinput && ctrl && e.key == "o") {
        shake("#open")
        fileinput.click()
        e.preventDefault()
    }
}

const decode = text => {
    // Unicode strings with BOMs
    const header = new TextDecoder("ISO-8859-1").decode(text.slice(0, 4));  /* Kludge to allow compare on arraybuffer */
    const boms = {"\xEF\xBB\xBF": "UTF-8", "\xFF\xFE": "UTF-16LE", "\xFE\xFF": "UTF-16BE", "\xFF\xFE\0\0": "UTF-32LE", "\0\0\xFE\xFF": "UTF-32BE"}
    for (const bom in boms) {
        if (header.startsWith(bom)) return new TextDecoder(boms[bom]).decode(text.slice(bom.length))
    }
    // Try UTF-8 without BOM
    try {
        return new TextDecoder("UTF-8", {fatal: true}).decode(text)
    } catch(err) {}
    // 8-bit guesswork (NUL usually means binary file; use ?charset= parameter or otherwise assume Latin-1)
    const utext = new Uint8Array(text)
    if (utext.includes(0)) return notify("Binary files are not supported!")
    return new TextDecoder(new URLSearchParams(window.location.search).get("charset") || "ISO-8859-1").decode(text)
}

// Dropping or opening files cause them being loaded into textbox/editor

document.addEventListener('drop', ev => {
    loadFile(ev.dataTransfer.files[0])
    ev.preventDefault()
})

const fileOpen = async () => await loadFile(fileinput.files[0])

const loadFile = async file => {
    if (!file) return
    const text = decode(await new Response(file).arrayBuffer())
    if (!text) return
    idinput.value = file.name
    fileinput.value = ""
    set(text)
    setTimeout(updateMode, 0)
}

const updateMode = () => {
    if (!editor) return
    const name = (idinput.value || idinput.placeholder).toLowerCase()
    const {mode} = CodeMirror.findModeByFileName(name) || {mode: "null"}
    editor.setOption("mode", mode)
    CodeMirror.autoLoadMode(editor, mode)
    let tabs = editor.getValue().indexOf("\t") > -1
    editor.setOption("extraKeys", {
        Tab: cm => {
            if (cm.somethingSelected()) cm.indentSelection("add")
            else cm.execCommand(tabs ? "insertTab" : "insertSoftTab")
        },
        "Ctrl-I": cm => { tabs = true; cm.execCommand("insertTab") },
        "Enter": cm => {
            cm.execCommand("newlineAndIndent")
            const cursor = cm.listSelections()[0].head
            const lineno = cursor.line
            const [prev_indent] = cm.getLine(lineno - 1).match(/^[ \t]*/)
            cm.replaceRange(prev_indent,
                {...cursor, ch: 0},
                {...cursor, ch: CodeMirror.countColumn(prev_indent, null, cm.options.tabSize)}
            )
        }
    })
}

if (navigator.serviceWorker) navigator.serviceWorker.register("/serviceworker.js", {scope: "/"})
