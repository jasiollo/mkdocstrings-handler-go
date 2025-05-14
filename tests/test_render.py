
import re

from mkdocstrings_handlers.go._internal import config, handler


def test_(handler: handler.GoHandler) -> None:

    res = handler.render(
            {
                "doc": " foo bar function\nthis does not newline in dockcomment\n\nthere go the arguments\n\nsomething something description\n",
                "name": "Foo",
                "packageName": "main",
                "packageImportPath": "./",
                "type": "func",
                "filename": "./bar.go",
                "line": 10,
                "parameters": [{"type": "int", "name": "b"}, {"type": "int", "name": "c"}],
                "results": [{"type": "int", "name":""}],
                "recv": "",
                "orig": "",
            },
        config.GoOptions(show_symbol_type_heading = True),
    )
    html = """
    <div class="doc doc-object doc-function">
        <h2 id="./bar.go" class="doc doc-heading">
            <code class="doc-symbol doc-symbol-heading doc-symbol-function"></code>
            <span class="doc doc-object-name doc-object-function-name">Foo</span>
        </h2>
        <div class="doc-signature highlight">
            <pre>
            <span></span>
                <code>
                <span class="nx">Foo</span>
                <span class="p">(</span>
                <span class="w"></span>
                <span class="nx">b</span>
                <span class="w"></span>
                <span class="kt">int</span>
                <span class="p">,</span>
                <span class="w"></span>
                <span class="nx">c</span>
                <span class="w"></span>
                <span class="kt">int</span>
                <span class="p">)</span>
                <span class="w"></span>
                <span class="kt">int</span>\n
                </code>
            </pre>
        </div>
        <div class="doc doc-contents ">
            foo bar function
            this does not newline in dockcomment
            there go the arguments

            something something description


        </div>
    </div>"""
    expected =  re.sub(r"\n\s*", "", html)
    res = re.sub( r">\s+<", r"><",re.sub(r"\n\s*", "", res))
    assert  res == expected
