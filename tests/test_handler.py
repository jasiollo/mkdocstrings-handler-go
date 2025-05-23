import sys
from pathlib import Path

import pytest

from mkdocstrings_handlers.go._internal.config import GoConfig, GoOptions
from mkdocstrings_handlers.go._internal.handler import GoHandler


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
def go_project_extended(tmp_path: str) -> str:
    # Simulate: mymod/pkg/helper.go
    mod_path = tmp_path / "mymodule"  # type: ignore [operator]
    pkg_path = mod_path / "pkg"
    pkg_path.mkdir(parents=True)

    (mod_path / "go.mod").write_text("module mymod\n", encoding="utf-8")

    (pkg_path / "helper.go").write_text(
        """
    // package says hello
    package utils

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
    assert handler._collected[identifier].get("doc") == "package says hello\n"


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
        "packageName": "utils",
        "packageImportPath": str(go_project_extended / "pkg"),
        "doc": "Interface declaration\n",
        "name": "Greeter",
        "type": "type",
        "filename": "",
        "line": 0,  # might be confusing but that's how godocsjson works
        "consts": [],
        "vars": [],
        "funcs": [],
        "methods": [],
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
        "packageName": "utils",
        "packageImportPath": str(go_project_extended / "pkg"),
        "doc": "Another constant\n",
        "names": ["Number"],
        "type": "const",
        "filename": str(go_project_extended / "pkg" / "helper.go"),
        "line": 11,
    }
    identifier = "pkg.Version"
    handler.collect(identifier, GoOptions())
    assert handler._collected[identifier] == {
        "packageName": "utils",
        "packageImportPath": str(go_project_extended / "pkg"),
        "doc": "Constant declaration\n",
        "names": ["Version"],
        "type": "const",
        "filename": str(go_project_extended / "pkg" / "helper.go"),
        "line": 8,
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
