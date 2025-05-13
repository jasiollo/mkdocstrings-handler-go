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
func Foo() {
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
                "name": "Foo",
                "packageName": "main",
                "packageImportPath": str(tmp_path),
                "type": "func",
                "filename": str(tmp_path / "bar.go"),
                "line": 10,
                "parameters": [],
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
    import pprint
    pprint.pprint(handler._collected[str(tmp_path / "struct.go")])
    assert handler._collected[str(tmp_path / "struct.go")] == {'bugs': None,
 'consts': [],
 'doc': 'Person defines a simple struct with a name and age.\n',
 'filenames': [str(tmp_path / "struct.go")],
 'funcs': [],
 'importPath': str(tmp_path),
 'imports': [],
 'name': 'main',
 'notes': {},
 'type': 'package',
 'types': [{'consts': [],
            'doc': 'Person defines a simple struct with a name and age.\n',
            'filename': '',
            'funcs': [],
            'line': 0,
            'methods': [],
            'name': 'Person',
            'packageImportPath': str(tmp_path),
            'packageName': 'main',
            'type': 'type',
            'vars': []}],
 'vars': []}
