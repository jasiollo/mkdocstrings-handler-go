import pathlib
import sys
from pathlib import Path

import pytest

from mkdocstrings_handlers.go._internal.config import GoConfig, GoOptions
from mkdocstrings_handlers.go._internal.handler import GoHandler

# parsing non local go projects is currently out of scope
# def test_collect_module(handler) -> None:
# """Assert existing module can be collected."""
# identifier = "github.com/gin-gonic/gin"
# handler.collect(identifier, GoConfig())
# assert handler._collected[identifier] is not None


def test_empty_id(handler: GoHandler) -> None:
    with pytest.raises(AttributeError):
        handler.collect("", GoConfig())


def test_identifier_does_not_exist(handler: GoHandler) -> None:
    with pytest.raises(ValueError):
        handler.collect("noway/iamnothere", GoConfig())


def test_collect_with_function_dock(tmp_path: pathlib.Path, handler: GoHandler) -> None:
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

    handler.collect(str(tmp_path / "bar.go"), GoConfig())

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


def test_collect_with_package_dock(tmp_path: pathlib.Path, handler: GoHandler) -> None:
    file_str = """
//package does stuff
package main

func Foo() {
	return
}
"""
    f = tmp_path / "bar.go"
    f.write_text(file_str, encoding="utf-8")

    handler.collect(str(tmp_path / "bar.go"), GoConfig())

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


def test_collect_empty_file(tmp_path: pathlib.Path, handler: GoHandler) -> None:
    file_str = "package main"
    f = tmp_path / "bar.go"
    f.write_text(file_str, encoding="utf-8")

    handler.collect(str(tmp_path / "bar.go"), GoConfig())

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


def test_give_precedence_to_user_paths() -> None:
    """Assert user paths take precedence over default paths."""
    last_sys_path = sys.path[-1]
    handler = GoHandler(
        base_dir=Path("."),
        config=GoConfig.from_data(paths=[last_sys_path]),
        mdx=[],
        mdx_config={},
    )
    assert handler._paths[0] == last_sys_path


# @pytest.fixture
# def go_file(tmp_path):
#     code = """
# // package does stuff
# package main

# func Foo() {
#     return
# }
# """
#     f = tmp_path / "bar.go"
#     f.write_text(code, encoding="utf-8")
#     return f


@pytest.fixture
def go_project(tmp_path: str) -> str:
    # Simulate: mymod/pkg/utils/helper.go
    mod_path = tmp_path / "mymod"
    pkg_path = mod_path / "pkg" / "utils"
    pkg_path.mkdir(parents=True)

    (mod_path / "go.mod").write_text("module mymod\n", encoding="utf-8")

    (pkg_path / "helper.go").write_text(
        """
package utils

type MyType struct{}
// Function that returns greetings to user
func Hello() string {
    return "hello"
}

func (m MyType) Method() string {
	return "hello"
}
""",
        encoding="utf-8",
    )

    return mod_path


def test_collect_function_from_fqn(go_project: Path) -> None:
    identifier = "pkg/utils.Hello"
    search_path = str(go_project)
    handler = GoHandler(
        base_dir=Path("."),
        config=GoConfig.from_data(paths=[search_path]),
        mdx=[],
        mdx_config={},
    )
    handler.collect(identifier, GoOptions())
    assert handler._collected[identifier] == {
        "doc": "Function that returns greetings to user\n",
        "name": "Hello",
        "packageName": "utils",
        "packageImportPath": str(go_project / "pkg" / "utils"),
        "type": "func",
        "filename": str(go_project / "pkg" / "utils" / "helper.go"),
        "line": 6,
        "parameters": [],
        "results": [{"type": "string", "name": ""}],
        "recv": "",
        "orig": "",
    }


def test_collect_method_from_fqn(go_project: Path) -> None:
    identifier = "pkg/utils.MyType.Method"
    search_path = str(go_project)
    handler = GoHandler(
        base_dir=Path("."),
        config=GoConfig.from_data(paths=[search_path]),
        mdx=[],
        mdx_config={},
    )
    handler.collect(identifier, GoOptions())
    assert handler._collected[identifier] == {
        "doc": "",
        "name": "Method",
        "packageName": "utils",
        "packageImportPath": str(go_project / "pkg" / "utils"),
        "type": "func",
        "filename": str(go_project / "pkg" / "utils" / "helper.go"),
        "line": 10,
        "parameters": [],
        "results": [{"type": "string", "name": ""}],
        "recv": "MyType",
        "orig": "MyType",
    }


@pytest.fixture
def go_project_extended(tmp_path: str) -> str:
    # Simulate: mymod/pkg/utils/helper.go
    mod_path = tmp_path / "mymod"
    pkg_path = mod_path / "pkg" / "utils"
    pkg_path.mkdir(parents=True)

    (mod_path / "go.mod").write_text("module mymod\n", encoding="utf-8")

    (pkg_path / "helper.go").write_text(
        """
    package utils

    import "fmt"

    // Constant declaration
    const Version = "1.0.0"

    // Variable declaration
    var DefaultName = "GoUser"

    // Interface declaration
    type Greeter interface {
        Greet(name string) string
    }

    // Struct type with a field
    type MyType struct {
        ID int
    }

    // Method on MyType
    func (m MyType) Method() string {
        return fmt.Sprintf("ID is %d", m.ID)
    }

    // Function returning a string
    func Hello() string {
        return "hello"
    }

    // Function that implements Greeter interface
    func (m MyType) Greet(name string) string {
        return "Hello, " + name
    }
    """
    )
    return mod_path


def test_collect_interface_from_fqn(go_project: Path) -> None:
    identifier = "pkg/utils.Version"
    search_path = str(go_project)
    handler = GoHandler(
        base_dir=Path("."),
        config=GoConfig.from_data(paths=[search_path]),
        mdx=[],
        mdx_config={},
    )
    handler.collect(identifier, GoOptions())
    assert handler._collected[identifier] == {
        "doc": "",
        "name": "Greeter",
        "packageName": "utils",
        "packageImportPath": str(go_project / "pkg" / "utils"),
        "type": "interface",
        "filename": str(go_project / "pkg" / "utils" / "helper.go"),
        "line": 10,
        "parameters": [],
        "results": [{"type": "string", "name": ""}],
        "recv": "MyType",
        "orig": "MyType",
    }
