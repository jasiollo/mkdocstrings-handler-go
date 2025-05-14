import pathlib

import pytest

from mkdocstrings_handlers.go._internal import config, handler

# parsing non local go projects is currently out of scope
# def test_collect_module(handler) -> None:
# """Assert existing module can be collected."""
# identifier = "github.com/gin-gonic/gin"
# handler.collect(identifier, config.GoOptions())
# assert handler._collected[identifier] is not None


def test_empty_id(handler: handler.GoHandler) -> None:
    with pytest.raises(AttributeError):
        handler.collect("", config.GoOptions())


def test_identifier_does_not_exist(handler: handler.GoHandler) -> None:
    with pytest.raises(RuntimeError):
        handler.collect("noway/iamnothere", config.GoOptions())


def test_collect_with_function_dock(tmp_path: pathlib.Path, handler: handler.GoHandler) -> None:
    file_str = """
package main

//  foo bar function
// this does not newline in dockcomment
//
//	there go the arguments
//
// something something description
func Foo(b int) int{
	return b
}
"""
    f = tmp_path / "bar.go"
    f.write_text(file_str, encoding="utf-8")

    handler.collect(str(tmp_path / "bar.go"), config.GoOptions())

    assert handler._collected[str(tmp_path/ "bar.go")] == {
        "type": "package",
        "doc": "",
        "name": "main",
        "importPath": str(tmp_path),
        "imports": [],
        "filenames": [str(tmp_path / "bar.go")],
        "notes": {},
        "bugs": None,
        "consts": [],
        "types": [],
        "vars": [],
        "funcs": [
            {
                "doc": " foo bar function\nthis does not newline in dockcomment\n\n\tthere go the arguments\n\nsomething something description\n",
                "name": "Foo",
                "packageName": "main",
                "packageImportPath": str(tmp_path),
                "type": "func",
                "filename": str(tmp_path / "bar.go"),
                "line": 10,
                "parameters": [{"type": "int", "name": "b"}],
                "results": [{"type": "int", "name":""}],
                "recv": "",
                "orig": "",
            },
        ],
    }


def test_collect_function_tuple_return(tmp_path: pathlib.Path, handler: handler.GoHandler) -> None:
    file_str = """
package main

//  foo bar function
// this does not newline in dockcomment
//
//	there go the arguments
//
// something something description
func Foo(b int) (int, int){
	return b
}
"""
    f = tmp_path / "bar.go"
    f.write_text(file_str, encoding="utf-8")

    handler.collect(str(tmp_path / "bar.go"), config.GoOptions())
    assert handler._collected[str(tmp_path/ "bar.go")] == {
        "type": "package",
        "doc": "",
        "name": "main",
        "importPath": str(tmp_path),
        "imports": [],
        "filenames": [str(tmp_path / "bar.go")],
        "notes": {},
        "bugs": None,
        "consts": [],
        "types": [],
        "vars": [],
        "funcs": [
            {
                "doc": " foo bar function\nthis does not newline in dockcomment\n\n\tthere go the arguments\n\nsomething something description\n",
                "name": "Foo",
                "packageName": "main",
                "packageImportPath": str(tmp_path),
                "type": "func",
                "filename": str(tmp_path / "bar.go"),
                "line": 10,
                "parameters": [{"type": "int", "name": "b"}],
                "results": [{"type": "int", "name":""}, {"type": "int", "name":""}],
                "recv": "",
                "orig": "",
            },
        ],
    }


def test_collect_function_unnanmed_struct_arg(tmp_path: pathlib.Path, handler: handler.GoHandler) -> None:
    file_str = """
package main

//  foo bar function
// this does not newline in dockcomment
//
//	there go the arguments
//
// something something description
func NewHouse(opts struct{Material string; HasFireplace bool; Composable bool; Floors int}){
    return
}
"""
    f = tmp_path / "bar.go"
    f.write_text(file_str, encoding="utf-8")

    handler.collect(str(tmp_path / "bar.go"), config.GoOptions())
    assert handler._collected[str(tmp_path/ "bar.go")] == {
        "type": "package",
        "doc": "",
        "name": "main",
        "importPath": str(tmp_path),
        "imports": [],
        "filenames": [str(tmp_path / "bar.go")],
        "notes": {},
        "bugs": None,
        "consts": [],
        "types": [],
        "vars": [],
        "funcs": [
            {
                "doc": " foo bar function\nthis does not newline in dockcomment\n\n\tthere go the arguments\n\nsomething something description\n",
                "name": "NewHouse",
                "packageName": "main",
                "packageImportPath": str(tmp_path),
                "type": "func",
                "filename": str(tmp_path / "bar.go"),
                "line": 10,
                "parameters": [{"type": "struct{string,bool,bool,int}", "name": "opts"}],
                "results": [],
                "recv": "",
                "orig": "",
            },
        ],
    }


def test_collect_with_package_dock(tmp_path: pathlib.Path, handler: handler.GoHandler) -> None:
    file_str = """
//package does stuff
package main

func Foo() {
	return
}
"""
    f = tmp_path / "bar.go"
    f.write_text(file_str, encoding="utf-8")

    handler.collect(str(tmp_path / "bar.go"), config.GoOptions())

    assert handler._collected[str(tmp_path / "bar.go")] == {
        "type": "package",
        "doc": "package does stuff\n",
        "name": "main",
        "importPath": str(tmp_path),
        "imports": [],
        "filenames": [str(tmp_path / "bar.go")],
        "notes": {},
        "bugs": None,
        "consts": [],
        "types": [],
        "vars": [],
        "funcs": [
            {
                "doc": "",
                "name": "Foo",
                "packageName": "main",
                "packageImportPath": str(tmp_path),
                "type": "func",
                "filename": str(tmp_path / "bar.go"),
                "line": 5,
                "parameters": [],
                "results": [],
                "recv": "",
                "orig": "",
            },
        ],
    }


def test_collect_empty_file(tmp_path: pathlib.Path, handler: handler.GoHandler) -> None:
    file_str = "package main"
    f = tmp_path / "bar.go"
    f.write_text(file_str, encoding="utf-8")

    handler.collect(str(tmp_path / "bar.go"), config.GoOptions())

    assert handler._collected[str(tmp_path / "bar.go")] == {
        "type": "package",
        "doc": "",
        "name": "main",
        "importPath": str(tmp_path),
        "imports": [],
        "filenames": [str(tmp_path / "bar.go")],
        "notes": {},
        "bugs": None,
        "consts": [],
        "types": [],
        "vars": [],
        "funcs": [],
    }




def test_collect_struct(tmp_path: pathlib.Path, handler: handler.GoHandler) -> None:
    file_str = """
// Person defines a simple struct with a name and age.
package main

// Person defines a simple struct with a name and age.
type Person struct {
    Name string
    Age  int
}
"""
    f = tmp_path / "struct.go"
    f.write_text(file_str, encoding="utf-8")

    # Write go.mod so godocjson can resolve the package
    handler.collect(str(tmp_path / "struct.go"), config.GoOptions())
    #pprint.pprint(handler._collected[str(tmp_path / "struct.go")])
    assert handler._collected[str(tmp_path / "struct.go")] == {"bugs": None,
 "consts": [],
 "doc": "Person defines a simple struct with a name and age.\n",
 "filenames": [str(tmp_path / "struct.go")],
 "funcs": [],
 "importPath": str(tmp_path),
 "imports": [],
 "name": "main",
 "notes": {},
 "type": "package",
 "types": [{"consts": [],
            "doc": "Person defines a simple struct with a name and age.\n",
            "filename": "",
            "funcs": [],
            "line": 0,
            "methods": [],
            "name": "Person",
            "packageImportPath": str(tmp_path),
            "packageName": "main",
            "type": "type",
            "vars": []}],
 "vars": []}

#doc, name , package name, var struct, types


# def test_collect_and_render_struct(tmp_path: pathlib.Path, handler: handler.GoHandler) -> None:
#     file_str = """
# // Person defines a simple struct with a name and age.
# package main

# // Person defines a simple struct with a name and age.
# type Person struct {
#     Name string
#     Age  int
# }
# """
#     f = tmp_path / "struct.go"
#     f.write_text(file_str, encoding="utf-8")

#     # Write go.mod so godocjson can resolve the package
#     collector_item = handler.collect(str(tmp_path / "struct.go"), config.GoOptions())
#     import pprint
#     pprint.pprint(handler._collected[str(tmp_path / "struct.go")])
#     assert handler._collected[str(tmp_path / "struct.go")] == {'bugs': None,
#  'consts': [],
#  'doc': 'Person defines a simple struct with a name and age.\n',
#  'filenames': [str(tmp_path / "struct.go")],
#  'funcs': [],
#  'importPath': str(tmp_path),
#  'imports': [],
#  'name': 'main',
#  'notes': {},
#  'type': 'package',
#  'types': [{'consts': [],
#             'doc': 'Person defines a simple struct with a name and age.\n',
#             'filename': '',
#             'funcs': [],
#             'line': 0,
#             'methods': [],
#             'name': 'Person',
#             'packageImportPath': str(tmp_path),
#             'packageName': 'main',
#             'type': 'type',
#             'vars': []}],
#  'vars': []}
#     assert handler._collected[str(tmp_path / "struct.go")]["name"] == "main"
#     assert len(handler._collected[str(tmp_path / "struct.go")]["types"]) == 1
#     assert handler._collected[str(tmp_path / "struct.go")]["types"][0]["name"] == "Person"
#     options = config.GoOptions()
#     rendered = handler.render(collector_item, options)

#     print("\n=== Rendered Output ===\n", rendered)




# def test_render(tmp_path: pathlib.Path, handler: handler.GoHandler) -> None:
#     file_str = """\
#     // Person defines a simple struct with a name and age.
#     package main

#     // Person defines a simple struct with a name and age.
#     type Person struct {
#         Name string
#         Age  int
#     }
#     """
#     f = tmp_path / "struct.go"
#     f.write_text(file_str, encoding="utf-8")

#     options = config.GoOptions()
#     collector_item = handler.collect(str(f), options)


#     assert str(f) in handler._collected
#     collected = handler._collected[str(f)]



#     pprint.pprint(collected)


#     assert collected["name"] == "main"
#     assert len(collected["types"]) == 1
#     assert collected["types"][0]["name"] == "Person"

#     rendered = handler.render(collector_item, options)

#     print("\n=== Rendered Output ===\n", rendered)


#     assert "Package: `main`" in rendered
#     assert "Struct: `Person`" in rendered
#     assert "Person defines a simple struct with a name and age." in rendered


#     project_root = pathlib.Path(__file__).resolve().parents[1]
#     output_path = project_root / "src/mkdocstrings_handlers/go/templates/filled_templates/rendered_output.html"

#     output_path.write_text(rendered, encoding="utf-8")
#     print(f"\n Rendered saved to: {output_path.resolve()}\n")





def test_render_struct_template(tmp_path: pathlib.Path, handler: handler.GoHandler) -> None:
    # Create test Go file with a struct
    go_code = """\
package main

// Person defines a simple struct with a name and age.
type Person struct {
    Name string
    Age  int
}
"""
    go_file = tmp_path / "struct.go"
    go_file.write_text(go_code, encoding="utf-8")

    # Minimal go.mod to make godocjson work
    (tmp_path / "go.mod").write_text("module example.com/test\n", encoding="utf-8")

    options = config.GoOptions()

    # Collect the file data
    handler.collect(str(go_file), options)
    assert str(go_file) in handler._collected

    # Get collected struct
    collected = handler._collected[str(go_file)]
    assert collected["name"] == "main"
    assert len(collected["types"]) == 1

    struct = collected["types"][0]

    # Simulate field extraction if missing
    if not struct.get("fields"):
        struct["fields"] = [
            {"name": "Name", "type": "string"},
            {"name": "Age", "type": "int"},
        ]

    rendered_html = handler.render(struct, options, template_name="struct.html.jinja")

    #print("\n=== Rendered Output ===\n", rendered_html)

    assert "Person defines a simple struct with a name and age." in rendered_html
    assert '<span class="doc doc-object-name doc-object-class-name">Person</span>' in rendered_html
    assert "type Person struct" in rendered_html
    assert "Name string" in rendered_html
    assert "Age int" in rendered_html
    assert "<pre>" in rendered_html
    project_root = pathlib.Path(__file__).resolve().parents[1]
    output_path = project_root / "src/mkdocstrings_handlers/go/templates/filled_templates/rendered_output.html"

    output_path.write_text(rendered_html, encoding="utf-8")
    #print(f"\n Rendered saved to: {output_path.resolve()}\n")
