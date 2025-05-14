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
