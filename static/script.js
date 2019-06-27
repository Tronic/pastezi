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

const notify = msg => {
    console.log("Notify: ", msg)
    const elem = document.querySelector("#notify")
    elem.textContent = msg
    setTimeout(() => elem.textContent = "", 1000)
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
    idinput = document.querySelector("#paste_id")
    if (!idinput) return  /* Viewing paste, not editing */
    document.querySelector("form").addEventListener("submit", send_paste)
    textarea = document.querySelector("#paste")
    CodeMirror.modeURL = "/_/codemirror/mode/%N/%N.js";
    editor = CodeMirror.fromTextArea(textarea, { lineNumbers: true, indentUnit: 4, tabSize: 4, viewportMargin: Infinity, theme: "pastel-on-dark" })
    fileinput = document.querySelector("input[type=file]")
    fileinput.addEventListener("change", fileUpload)
    idinput.addEventListener("change", updateMode)
    updateMode()
    /* Automatic paste in Chrome */
    if (navigator.clipboard.readText && editor.getValue().trim().length === 0) {
        navigator.clipboard.readText().then(text => text.startsWith(location.href) ? "" : editor.setValue(text)).catch(console.log)
    }
})

const send_paste = ev => {
    ev.preventDefault()
    send_paste_async()
}

const send_paste_async = async () => {
    shake("#upload")
    const text = editor ? editor.getValue() : textarea.value;
    const has_text = text.trim().length > 0
    const form = document.querySelector("form")
    const res = await fetch("/" + encodeURIComponent(idinput.value || ""), {
        method: has_text ? "PUT" : "DELETE",
        body: has_text ? text : undefined,
    })
    if (res.type === "text/html") return document.write(await res.text())
    if (!has_text) return notify(res.status === 204 ? "Deleted from server" : "Nothing to do!")
    if (res.status >= 400) return notify(await res.text())
    const url = (await res.text()).trim()
    if (res.status === 201) { copy(url); sessionStorage.setItem("flash", "Link copied:\n" + url) }
    else if (res.status === 200) sessionStorage.setItem("flash", "Changes saved!")
    window.location = url
}

const download = ev => {
    shake("#dl")
    window.location = document.querySelector("#dl").href
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

function fileUpload(ev) {
    const file = this.files[0]
    if (!file) return
    if (idinput.value.length === 0) idinput.value = file.name
    const reader = new FileReader()
    reader.onload = () => {
        fileinput.value = ""
        if (editor) editor.setValue(reader.result)
        else textarea.value = reader.result
        setTimeout(updateMode, 0)
    }
    reader.onerror = () => console.log("Reading file failed")
    reader.readAsText(file)
}

const updateMode = () => {
    if (!editor) return
    const name = idinput.value.toLowerCase()
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
