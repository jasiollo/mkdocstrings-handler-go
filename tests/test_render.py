import re

from mkdocstrings_handlers.go._internal import config, handler


def normalize_html(html: str) -> str:
    lines = [line.strip() for line in html.strip().splitlines()]
    lines = [line for line in lines if line]
    return "".join(lines)


def test_render_function(handler: handler.GoHandler) -> None:
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
            "results": [{"type": "int", "name": ""}],
            "recv": "",
            "orig": "",
            "code": "",
            "relative_path": "",
        },
        config.GoOptions(show_symbol_type_heading=True, show_root_heading=True, show_root_full_path=False),
    )
    html = """<div class="doc doc-object doc-function">
                <h2 id="./bar.go" class="doc doc-heading">
                    <code class="doc-symbol doc-symbol-heading doc-symbol-function"></code>
                    <span class="doc doc-object-name doc-object-function-name">Foo</span>
                </h2>
                <div class="doc-signature highlight">
                    <pre>
                    <span></span>
                    <code>
                        <span class="kd">func</span>
                        <span class="w"></span>
                        <span class="nx">Foo</span>
                        <span class="p">(</span>
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
                        <span class="p">(</span>
                        <span class="kt">int</span>
                        <span class="p">)</span>
                        </code>
                    </pre>
                </div>
                <div class="doc doc-contents first">
                    foo bar function
                    this does not newline in dockcomment
                    there go the arguments

                    something something description
                </div>
            </div>"""
    expected = re.sub(r"\n\s*", "", html)
    res = re.sub(r">\s+<", r"><", re.sub(r"\n\s*", "", res))
    assert res == expected


def test_render_package(handler: handler.GoHandler) -> None:
    package_json = {
        "type": "package",
        "doc": "package doc",
        "name": "main",
        "importPath": "/some/path",
        "imports": [],
        "filenames": ["/some/path/bar.go"],
        "notes": {},
        "bugs": None,
        "consts": [],
        "types": [],
        "vars": [],
        "funcs": [
            {
                "doc": " foo bar function\nthis does not newline in dockcomment\n\nthere go the arguments\n\nsomething something description\n",
                "name": "Foo",
                "packageName": "main",
                "packageImportPath": "/some/path",
                "type": "func",
                "filename": "/some/path/bar.go",
                "line": 10,
                "parameters": [{"type": "int", "name": "b"}, {"type": "int", "name": "c"}],
                "results": [{"type": "int", "name": ""}],
                "recv": "",
                "orig": "",
                "code": "",
                "relative_path": "",
            },
        ],
    }

    res = handler.render(package_json, config.GoOptions(show_symbol_type_heading=True, show_root_heading=True))

    html = """
    <div class="doc doc-object doc-module">
        <h2 id="/some/path" class="doc doc-heading">
            <code>/some/path/main</code>
        </h2>
        <div class="doc doc-contents first">
            package doc
            <div class="doc doc-object doc-function">
                <h3 id="/some/path/bar.go" class="doc doc-heading">
                    <code class="doc-symbol doc-symbol-heading doc-symbol-function"></code>
                    <span class="doc doc-object-name doc-object-function-name">Foo</span>
                </h3>
                <div class="doc-signature highlight">
                    <pre>
                    <span></span>
                        <code>
                        <span class="kd">func</span>
                        <span class="w"></span>
                        <span class="nx">Foo</span>
                        <span class="p">(</span>
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
                        <span class="p">(</span>
                        <span class="kt">int</span>
                        <span class="p">)</span>
                        </code>
                    </pre>
                </div>
                <div class="doc doc-contents ">
                    foo bar function
                    this does not newline in dockcomment
                    there go the arguments

                    something something description
                </div>
            </div>
        </div>
    </div>"""

    expected = re.sub(r"\n\s*", "", html)
    res = re.sub(r">\s+<", r"><", re.sub(r"\n\s*", "", res))
    assert res == expected


def test_render_struct(handler: handler.GoHandler) -> None:
    data_json = {
        "type": "package",
        "doc": "package says hello\n",
        "name": "utils",
        "importPath": ".",
        "imports": [],
        "filenames": [
            "handler.go",
        ],
        "notes": {},
        "bugs": "null",
        "consts": [],
        "types": [
            {
                "packageName": "utils",
                "packageImportPath": ".",
                "doc": "Struct type with a field\n",
                "name": "MyType",
                "type": "type",
                "filename": "",
                "line": 0,
                "consts": [],
                "vars": [],
                "funcs": [],
                "methods": [],
                "code": "",
                "relative_path": "",
            },
        ],
        "vars": [],
        "funcs": [],
    }

    html = handler.render(data_json, config.GoOptions(show_symbol_type_heading=True, show_root_heading=True))

    res = """<div class="doc doc-object doc-module">
   <h2 id="." class="doc doc-heading">
      <code>./utils</code>
   </h2>
   <div class="doc doc-contents first">
      package says hello
      <div class="doc doc-object doc-struct">
         <h3 id="-MyType" class="doc doc-heading">            <code class="doc-symbol doc-symbol-heading doc-symbol-struct"></code>
            <span class="doc doc-object-name doc-object-struct-name">MyType</span>
         </h3>
         <div class="doc-signature highlight">
            <pre><span></span><code><span class="kd">type</span><span class="w"> </span><span class="nx">MyType</span><span class="w"> </span><span class="kd">struct</span><span class="w">    </span><span class="p">{}</span>
</code></pre>
         </div>
         <div class="doc doc-contents ">
            Struct type with a field
         </div>
      </div>
   </div>
</div>"""

    assert normalize_html(html) == normalize_html(res)


def test_render_const(handler: handler.GoHandler) -> None:
    data_json = {
        "type": "package",
        "doc": "package says hello\n",
        "name": "utils",
        "importPath": "test_folder",
        "imports": [],
        "filenames": [
            "test_folder/hander.go",
        ],
        "notes": {},
        "bugs": "null",
        "consts": [
            {
                "packageName": "utils",
                "packageImportPath": "test_folder",
                "doc": "Another constant\n",
                "names": [
                    "Number",
                ],
                "type": "const",
                "filename": "test_folder/hander.go",
                "line": 5,
            },
        ],
        "types": [],
        "vars": [],
        "funcs": [],
    }

    html = handler.render(data_json, config.GoOptions(show_symbol_type_heading=True, show_root_heading=True))

    res = """
<div class="doc doc-object doc-module">
   <h2 id="test_folder" class="doc doc-heading">
      <code>test_folder/utils</code>
   </h2>
   <div class="doc doc-contents first">
      package says hello
      <div class="doc doc-object doc-const">
         <h3 id="test_folder/hander.go" class="doc doc-heading">            <code class="doc-symbol doc-symbol-heading doc-symbol-const"></code>
            <span class="doc doc-object-name doc-object-const-name">Number</span>
         </h3>
         <div class="doc-signature highlight">
            <pre><span></span><code><span class="kd">const</span><span class="w"> </span><span class="nx">Number</span>
</code></pre>
         </div>
         <div class="doc doc-contents ">
            Another constant
         </div>
      </div>
   </div>
</div>"""
    assert normalize_html(res) == normalize_html(html)
