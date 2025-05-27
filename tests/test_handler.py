import sys
from pathlib import Path

import pytest

from mkdocstrings_handlers.go._internal.config import GoConfig, GoOptions
from mkdocstrings_handlers.go._internal.handler import (
    GoHandler,
)


@pytest.fixture
def go_empty_project(tmp_path: str) -> str:
    # Simulate: mymod/pkg/utils/helper.go
    mod_path = tmp_path / "mymod"  # type: ignore [operator]
    pkg_path = mod_path / "pkg" / "utils"
    pkg_path.mkdir(parents=True)

    (mod_path / "go.mod").write_text("module mymod\n", encoding="utf-8")
    pkg_path.touch("helper.go")
    return mod_path


@pytest.fixture
def go_project(tmp_path: str) -> str:
    # Simulate: mymod/pkg/utils/helper.go
    mod_path = tmp_path / "mymod"  # type: ignore [operator]
    pkg_path = mod_path / "pkg" / "utils"
    pkg_path.mkdir(parents=True)

    (mod_path / "go.mod").write_text("module mymod\n", encoding="utf-8")

    (pkg_path / "helper.go").write_text(
        """
// package says hello
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


@pytest.fixture
def go_project_many_files(tmp_path: str) -> str:
    mod_path = tmp_path / "mymod"
    pkg_path = mod_path / "pkg" / "utils"
    pkg_path.mkdir(parents=True)

    (mod_path / "go.mod").write_text("module mymod\n", encoding="utf-8")

    files = {
        "helper.go": """
package utils

type MyType struct{}
func (m MyType) Method() string { return "hello" }
""",
        "math.go": """
package utils

func Add(a int, b int) int { return a + b }
""",
        "string.go": """
package utils

func Greet(name string) string { return "Hello, " + name }
""",
    }

    for name, content in files.items():
        (pkg_path / name).write_text(content, encoding="utf-8")

    return mod_path


@pytest.fixture
def go_project_name_mismatch(tmp_path: str) -> str:
    # Simulate: mymod/pkg/utils/helper.go
    mod_path = tmp_path / "mymod"  # type: ignore [operator]
    pkg_path = mod_path / "pkg" / "utils"
    pkg_path.mkdir(parents=True)

    (mod_path / "go.mod").write_text("module mymod\n", encoding="utf-8")

    (pkg_path / "helper.go").write_text(
        """
// package says hello
package hello

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


@pytest.fixture
def go_project_extended(tmp_path: str) -> str:
    # Simulate: mymod/pkg/helper.go
    mod_path = tmp_path / "mymodule"  # type: ignore [operator]
    pkg_path = mod_path / "pkg"
    pkg_path.mkdir(parents=True)

    (mod_path / "go.mod").write_text("module mymod\n", encoding="utf-8")

    (pkg_path / "helper.go").write_text(
        """
    // package says hello
    package pkg

    import "fmt"

    // Constant declaration
    const Version = "1.0.0"

    // Another constant
    const Number = 777

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

    // Embedded struct - Person
    type Person struct {
    Name string
    Address struct {
        Street string
        City   string
    }
    }

    // Block of variables
    var (
    A int
    B = "text"
    C float64 = 3.14
    )
    """,
    )

    return mod_path


def test_empty_id(handler: GoHandler) -> None:
    with pytest.raises(AttributeError):
        handler.collect("", GoOptions())


def test_identifier_does_not_exist(handler: GoHandler) -> None:
    with pytest.raises(FileNotFoundError):
        handler.collect("noway/iamnothere", GoOptions())


def test_collect_with_package_dock(go_project: Path) -> None:
    identifier = "pkg/utils"
    search_path = str(go_project)
    handler = GoHandler(
        base_dir=Path("."),
        config=GoConfig.from_data(paths=[search_path]),
        mdx=[],
        mdx_config={},
    )
    handler.collect(identifier, GoOptions())
    assert handler._collected[identifier] == {
        "type": "package",
        "doc": "package says hello\n",
        "name": "utils",
        "importPath": str(go_project / "pkg" / "utils"),
        "imports": [],
        "filenames": [
            str(go_project / "pkg" / "utils" / "helper.go"),
        ],
        "notes": {},
        "bugs": None,
        "consts": [],
        "types": [
            {
                "packageName": "utils",
                "packageImportPath": str(go_project / "pkg" / "utils"),
                "doc": "",
                "name": "MyType",
                "type": "type",
                "relative_path": "pkg/utils/helper.go",
                "filename": "",
                "line": 5,
                "consts": [],
                "code": "type MyType struct{}\n",
                "vars": [],
                "funcs": [],
                "methods": [
                    {
                        "doc": "",
                        "name": "Method",
                        "packageName": "utils",
                        "packageImportPath": str(go_project / "pkg" / "utils"),
                        "type": "func",
                        "filename": str(go_project / "pkg" / "utils" / "helper.go"),
                        "line": 11,
                        "parameters": [],
                        "results": [{"type": "string", "name": ""}],
                        "recv": "MyType",
                        "orig": "MyType",
                        "code": 'func (m MyType) Method() string {\n\treturn "hello"\n}\n',
                        "relative_path": "pkg/utils/helper.go",
                    },
                ],
            },
        ],
        "vars": [],
        "funcs": [
            {
                "doc": "Function that returns greetings to user\n",
                "name": "Hello",
                "packageName": "utils",
                "packageImportPath": str(go_project / "pkg" / "utils"),
                "type": "func",
                "filename": str(go_project / "pkg" / "utils" / "helper.go"),
                "line": 7,
                "parameters": [],
                "results": [{"type": "string", "name": ""}],
                "recv": "",
                "orig": "",
                "code": 'func Hello() string {\n    return "hello"\n}\n',
                "relative_path": "pkg/utils/helper.go",
            },
        ],
        "code": None,
        "relative_path": None,
    }


def test_collect_empty_file(go_empty_project: Path) -> None:
    identifier = "pkg/utils"
    search_path = str(go_empty_project)
    handler = GoHandler(
        base_dir=Path("."),
        config=GoConfig.from_data(paths=[search_path]),
        mdx=[],
        mdx_config={},
    )
    with pytest.raises(ValueError, match="Provided package contains empty file"):
        handler.collect(identifier, GoOptions())


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
        "line": 7,
        "parameters": [],
        "results": [{"type": "string", "name": ""}],
        "recv": "",
        "orig": "",
        "code": 'func Hello() string {\n    return "hello"\n}\n',
        "relative_path": "pkg/utils/helper.go",
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
        "line": 11,
        "parameters": [],
        "results": [{"type": "string", "name": ""}],
        "recv": "MyType",
        "orig": "MyType",
        "code": 'func (m MyType) Method() string {\n\treturn "hello"\n}\n',
        "relative_path": "pkg/utils/helper.go",
    }


def test_collect_interface_from_fqname(go_project_extended: Path) -> None:
    identifier = "pkg.Greeter"
    search_path = str(go_project_extended)
    handler = GoHandler(
        base_dir=Path("."),
        config=GoConfig.from_data(paths=[search_path]),
        mdx=[],
        mdx_config={},
    )
    handler.collect(identifier, GoOptions())
    assert handler._collected[identifier] == {
        "packageName": "pkg",
        "packageImportPath": str(go_project_extended / "pkg"),
        "doc": "Interface declaration\n",
        "name": "Greeter",
        "type": "type",
        "filename": "",
        "line": 17,
        "consts": [],
        "vars": [],
        "funcs": [],
        "methods": [],
        "code": "    type Greeter interface {\n        Greet(name string) string\n    }\n",
        "relative_path": "pkg/helper.go",
    }


def test_collect_const_from_fqname(go_project_extended: Path) -> None:
    identifier = "pkg.Number"
    search_path = str(go_project_extended)
    handler = GoHandler(
        base_dir=Path("."),
        config=GoConfig.from_data(paths=[search_path]),
        mdx=[],
        mdx_config={},
    )
    handler.collect(identifier, GoOptions())
    assert handler._collected[identifier] == {
        "packageName": "pkg",
        "packageImportPath": str(go_project_extended / "pkg"),
        "doc": "Another constant\n",
        "names": ["Number"],
        "type": "const",
        "filename": str(go_project_extended / "pkg" / "helper.go"),
        "line": 11,
        "code": "    type Greeter interface {\n        Greet(name string) string\n    }\n",
        "relative_path": "pkg/helper.go",
        "code": "    const Number = 777\n",
    }
    identifier = "pkg.Version"
    handler.collect(identifier, GoOptions())
    assert handler._collected[identifier] == {
        "packageName": "pkg",
        "packageImportPath": str(go_project_extended / "pkg"),
        "doc": "Constant declaration\n",
        "names": ["Version"],
        "type": "const",
        "filename": str(go_project_extended / "pkg" / "helper.go"),
        "line": 8,
        "relative_path": "pkg/helper.go",
        "code": '    const Version = "1.0.0"\n',
    }


def test_collect_wrong_fqname(go_project_extended: Path) -> None:
    identifier = "pkg.Nothing"
    search_path = str(go_project_extended)
    handler = GoHandler(
        base_dir=Path("."),
        config=GoConfig.from_data(paths=[search_path]),
        mdx=[],
        mdx_config={},
    )
    with pytest.raises(
        ValueError,
        match=f"No data found for identifier: '{identifier}'",
    ):
        handler.collect(identifier, GoOptions())


def test_interface(go_project_extended: Path):
    identifier = "pkg.Greeter"
    search_path = str(go_project_extended)
    handler = GoHandler(
        base_dir=Path("."),
        config=GoConfig.from_data(paths=[search_path]),
        mdx=[],
        mdx_config={},
    )
    handler.collect(identifier, GoOptions())
    assert (
        handler._collected[identifier]["code"]
        == "    type Greeter interface {\n        Greet(name string) string\n    }\n"
    )
    assert handler._collected[identifier]["relative_path"] == "pkg/helper.go"


def test_nested_struct(go_project_extended: Path):
    identifier = "pkg.Person"
    search_path = str(go_project_extended)
    handler = GoHandler(
        base_dir=Path("."),
        config=GoConfig.from_data(paths=[search_path]),
        mdx=[],
        mdx_config={},
    )
    handler.collect(identifier, GoOptions())
    assert (
        handler._collected[identifier]["code"]
        == "    type Person struct {\n    Name string\n    Address struct {\n        Street string\n        City   string\n    }\n    }\n"
    )
    assert handler._collected[identifier]["relative_path"] == "pkg/helper.go"


def test_multiple_var(go_project_extended: Path):
    identifier = "pkg.C"
    search_path = str(go_project_extended)
    handler = GoHandler(
        base_dir=Path("."),
        config=GoConfig.from_data(paths=[search_path]),
        mdx=[],
        mdx_config={},
    )
    handler.collect(identifier, GoOptions())
    assert (
        handler._collected[identifier]["code"] == '    var (\n    A int\n    B = "text"\n    C float64 = 3.14\n    )\n'
    )
    assert handler._collected[identifier]["relative_path"] == "pkg/helper.go"


def test_receiver(go_project_extended: Path):
    identifier = "pkg.MyType.Method"
    search_path = str(go_project_extended)
    handler = GoHandler(
        base_dir=Path("."),
        config=GoConfig.from_data(paths=[search_path]),
        mdx=[],
        mdx_config={},
    )
    handler.collect(identifier, GoOptions())
    assert (
        handler._collected[identifier]["code"]
        == '    func (m MyType) Method() string {\n        return fmt.Sprintf("ID is %d", m.ID)\n    }\n'
    )
    assert handler._collected[identifier]["relative_path"] == "pkg/helper.go"


def test_collect_method_from_fqn_mismatch(go_project_name_mismatch: Path) -> None:
    identifier = "pkg/utils.MyType.Method"
    search_path = str(go_project_name_mismatch)
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
        "packageName": "hello",
        "packageImportPath": str(go_project_name_mismatch / "pkg" / "utils"),
        "type": "func",
        "filename": str(go_project_name_mismatch / "pkg" / "utils" / "helper.go"),
        "line": 11,
        "parameters": [],
        "results": [{"type": "string", "name": ""}],
        "recv": "MyType",
        "orig": "MyType",
        "code": 'func (m MyType) Method() string {\n\treturn "hello"\n}\n',
        "relative_path": "pkg/utils/helper.go",
    }


def test_whole_package_extended(go_project_extended: Path) -> None:
    identifier = "pkg"
    search_path = str(go_project_extended)
    handler = GoHandler(
        base_dir=Path("."),
        config=GoConfig.from_data(paths=[search_path]),
        mdx=[],
        mdx_config={},
    )
    handler.collect(identifier, GoOptions())
    print(handler._collected[identifier])
    assert handler._collected[identifier] == {
        "type": "package",
        "doc": "package says hello\n",
        "name": "pkg",
        "importPath": str(go_project_extended / "pkg"),
        "imports": ["fmt"],
        "filenames": [str(go_project_extended / "pkg" / "helper.go")],
        "notes": {},
        "bugs": None,
        "code": None,
        "relative_path": None,
        "consts": [
            {
                "packageName": "pkg",
                "packageImportPath": str(go_project_extended / "pkg"),
                "doc": "Another constant\n",
                "names": ["Number"],
                "type": "const",
                "filename": str(go_project_extended / "pkg" / "helper.go"),
                "line": 11,
                "code": "    const Number = 777\n",
                "relative_path": "pkg/helper.go",
            },
            {
                "packageName": "pkg",
                "packageImportPath": str(go_project_extended / "pkg"),
                "doc": "Constant declaration\n",
                "names": ["Version"],
                "type": "const",
                "filename": str(go_project_extended / "pkg" / "helper.go"),
                "line": 8,
                "code": '    const Version = "1.0.0"\n',
                "relative_path": "pkg/helper.go",
            },
        ],
        "types": [
            {
                "packageName": "pkg",
                "packageImportPath": str(go_project_extended / "pkg"),
                "doc": "Interface declaration\n",
                "name": "Greeter",
                "type": "type",
                "filename": "",
                "line": 17,
                "consts": [],
                "vars": [],
                "funcs": [],
                "methods": [],
                "code": "    type Greeter interface {\n        Greet(name string) string\n    }\n",
                "relative_path": "pkg/helper.go",
            },
            {
                "packageName": "pkg",
                "packageImportPath": str(go_project_extended / "pkg"),
                "doc": "Struct type with a field\n",
                "name": "MyType",
                "type": "type",
                "filename": "",
                "line": 22,
                "consts": [],
                "code": "    type MyType struct {\n        ID int\n    }\n",
                "vars": [],
                "funcs": [],
                "relative_path": "pkg/helper.go",
                "methods": [
                    {
                        "doc": "Function that implements Greeter interface\n",
                        "name": "Greet",
                        "packageName": "pkg",
                        "packageImportPath": str(go_project_extended / "pkg"),
                        "type": "func",
                        "filename": str(go_project_extended / "pkg" / "helper.go"),
                        "line": 37,
                        "parameters": [{"type": "string", "name": "name"}],
                        "results": [{"type": "string", "name": ""}],
                        "recv": "MyType",
                        "orig": "MyType",
                        "code": '    func (m MyType) Greet(name string) string {\n        return "Hello, " + name\n    }\n',
                        "relative_path": "pkg/helper.go",
                    },
                    {
                        "doc": "Method on MyType\n",
                        "name": "Method",
                        "packageName": "pkg",
                        "packageImportPath": str(go_project_extended / "pkg"),
                        "type": "func",
                        "filename": str(go_project_extended / "pkg" / "helper.go"),
                        "line": 27,
                        "parameters": [],
                        "results": [{"type": "string", "name": ""}],
                        "recv": "MyType",
                        "orig": "MyType",
                        "code": '    func (m MyType) Method() string {\n        return fmt.Sprintf("ID is %d", m.ID)\n    }\n',
                        "relative_path": "pkg/helper.go",
                    },
                ],
            },
            {
                "packageName": "pkg",
                "packageImportPath": str(go_project_extended / "pkg"),
                "doc": "Embedded struct - Person\n",
                "name": "Person",
                "type": "type",
                "filename": "",
                "line": 42,
                "consts": [],
                "vars": [],
                "funcs": [],
                "methods": [],
                "code": "    type Person struct {\n    Name string\n    Address struct {\n        Street string\n        City   string\n    }\n    }\n",
                "relative_path": "pkg/helper.go",
            },
        ],
        "vars": [
            {
                "packageName": "pkg",
                "packageImportPath": str(go_project_extended / "pkg"),
                "doc": "Block of variables\n",
                "names": ["A", "B", "C"],
                "type": "var",
                "filename": str(go_project_extended / "pkg" / "helper.go"),
                "line": 51,
                "code": '    var (\n    A int\n    B = "text"\n    C float64 = 3.14\n    )\n',
                "relative_path": "pkg/helper.go",
            },
            {
                "packageName": "pkg",
                "packageImportPath": str(go_project_extended / "pkg"),
                "doc": "Variable declaration\n",
                "names": ["DefaultName"],
                "type": "var",
                "filename": str(go_project_extended / "pkg" / "helper.go"),
                "line": 14,
                "code": '    var DefaultName = "GoUser"\n',
                "relative_path": "pkg/helper.go",
            },
        ],
        "funcs": [
            {
                "doc": "Function returning a string\n",
                "name": "Hello",
                "packageName": "pkg",
                "packageImportPath": str(go_project_extended / "pkg"),
                "type": "func",
                "filename": str(go_project_extended / "pkg" / "helper.go"),
                "line": 32,
                "parameters": [],
                "results": [{"type": "string", "name": ""}],
                "recv": "",
                "orig": "",
                "code": '    func Hello() string {\n        return "hello"\n    }\n',
                "relative_path": "pkg/helper.go",
            },
        ],
    }
