# This module implements a handler for Go.

from __future__ import annotations

import glob
import json
import os
import subprocess
import sys
from os.path import expanduser
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

from mkdocs.exceptions import PluginError
from mkdocstrings import BaseHandler, CollectorItem, get_logger

from mkdocstrings_handlers.go._internal import rendering
from mkdocstrings_handlers.go._internal.config import GoConfig, GoOptions

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping, MutableMapping

    from mkdocs.config.defaults import MkDocsConfig
    from mkdocstrings import HandlerOptions

# YORE: EOL 3.10: Replace block with line 2.
if sys.version_info >= (3, 11):
    from contextlib import chdir
else:
    from contextlib import contextmanager

    @contextmanager
    def chdir(path: str) -> Iterator[None]:
        old_wd = os.getcwd()
        os.chdir(path)
        try:
            yield
        finally:
            os.chdir(old_wd)


_logger = get_logger(__name__)


class GoHandler(BaseHandler):
    """The Go handler class."""

    name: ClassVar[str] = "go"
    """The handler's name."""

    domain: ClassVar[str] = "go"
    """The cross-documentation domain/language for this handler."""
    # Typically: the file extension, like `py`, `go` or `rs`.
    # For non-language handlers, use the technology/tool name, like `openapi` or `click`.

    enable_inventory: ClassVar[bool] = False
    """Whether this handler is interested in enabling the creation of the `objects.inv` Sphinx inventory file."""

    fallback_theme: ClassVar[str] = "material"
    """The theme to fallback to."""

    def __init__(
        self,
        config: GoConfig,
        base_dir: Path,
        *,
        godocjson_path: str = "~/go/bin/godocjson",
        **kwargs: Any,
    ) -> None:
        """Initialize the handler.

        Parameters:
            config: The handler configuration.
            base_dir: The base directory of the project.
            **kwargs: Arguments passed to the parent constructor.
        """
        super().__init__(**kwargs)

        self.config = config
        """The handler configuration."""
        self.base_dir = base_dir
        """The base directory of the project."""
        self.global_options = config.options
        """The global configuration options."""
        self.godocjson_path = godocjson_path
        """The path to go parser"""

        paths = config.paths or []

        # Expand paths with glob patterns.
        with chdir(str(base_dir)):
            resolved_globs = [glob.glob(path) for path in paths]
        paths = [path for glob_list in resolved_globs for path in glob_list]

        # By default, add the base directory to the search paths.
        if not paths:
            paths.append(str(base_dir))

        # Initialize search paths from `sys.path`, eliminating empty paths.
        search_paths = [path for path in sys.path if path]

        for path in reversed(paths):
            # If it's not absolute, make path relative to the config file path, then make it absolute.
            if not os.path.isabs(path):
                path = os.path.abspath(base_dir / path)  # noqa: PLW2901
            # Remove pre-listed paths.
            if path in search_paths:
                search_paths.remove(path)
            # Give precedence to user-provided paths.
            search_paths.insert(0, path)

        self._paths = search_paths
        self._collected: dict[str, CollectorItem] = {}

    def get_options(self, local_options: Mapping[str, Any]) -> HandlerOptions:
        """Get combined default, global and local options.

        Arguments:
            local_options: The local options.

        Returns:
            The combined options.
        """
        extra = {
            **self.global_options.get("extra", {}),
            **local_options.get("extra", {}),
        }
        options = {**self.global_options, **local_options, "extra": extra}
        try:
            return GoOptions.from_data(**options)
        except Exception as error:
            raise PluginError(f"Invalid options: {error}") from error

    def collect(self, identifier: str, options: GoOptions) -> CollectorItem:
        """Collect documentation data for a given Go identifier (package, type, or method)."""
        if not identifier:
            raise AttributeError("Identifier cannot be empty!")

        # check for options
        if options == {}:
            options = self.get_options({})

        # Example identifier: mymod/pkg/utils.Type.Method
        pkg_path, *objects = identifier.split(
            ".",
        )  # Split into package path and optional object parts
        obj, method = (None, None)

        self._pkg_path = pkg_path

        max_fqn_parts = 2  # Maximum parts after the package: Type.Method
        # TODO - only package
        if len(objects) > max_fqn_parts:
            raise ValueError(
                f"Invalid FQN: '{identifier}'. Max format: 'package.Type.Method'",
            )
        if len(objects) == max_fqn_parts:
            obj, method = objects  # Method with receiver
        elif not objects:
            base_dir, _, obj = identifier.partition(
                "/",
            )  # Only a package name is provided
        else:
            obj = objects[0]  # Single object like a type, constant, or interface

        valid_path = next(
            (Path(base) / pkg_path for base in self._paths if (Path(base) / pkg_path).is_dir()),
            None,
        )
        if not valid_path:
            valid_path = next(
                (Path(base) / base_dir for base in self._paths if (Path(base) / base_dir).is_dir()),
                None,
            )
            if not valid_path:
                raise FileNotFoundError(
                    f"No valid package path found for '{pkg_path} or {base_dir}'\n with paths {self._paths}\n ",
                )

        try:
            result = subprocess.run(  # noqa: S603
                [expanduser(self.godocjson_path), valid_path],
                check=True,
                capture_output=True,
                text=True,
            )
            if not result.stdout:
                raise ValueError("Provided package contains empty file")

            data = json.loads(result.stdout)
            if not obj:
                filtered = [data]
            else:
                filtered = self._filter_data(data, obj, method)

            if not filtered:
                raise ValueError(f"No data found for identifier: '{identifier}'")

            self._collected[identifier] = filtered[0]
            item = self._collected[identifier]

            (code, path) = (
                self._get_code_snippet_and_path(item, method) if method else self._get_code_snippet_and_path(item, obj)
            )

            self._collected[identifier]["code"] = code
            self._collected[identifier]["relative_path"] = path

            return filtered[0]

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"godocjson failed:\n{e.stderr.strip()}") from e

    def _filter_data(self, data: dict, obj: str, method: str | None) -> list:
        if method:
            # Search by receiver type, then method name
            data = find_dicts_with_value(data, "name", obj)  # type: ignore [assignment]
            return find_dicts_with_value(data, "name", method)
        # Try looking by 'names' (constants, vars), fallback to 'name' (types, interfaces)
        result = find_dicts_with_value(data, "names", obj)
        return result or find_dicts_with_value(data, "name", obj)

    def _get_code_snippet_and_path(self, item: str, obj=None) -> None:
        type_name = item.get("type")

        if type_name == "package":
            inject_code_info(item, self._get_code_snippet_and_path)
            return None, None

        if type_name == "type":
            path, line_nr = find_string_in_go_files(
                item["packageImportPath"],
                obj,
                type_name,
            )
            item["line"] = line_nr

        else:
            path = item["filename"]
            line_nr = item["line"]

        with open(path) as f:
            lines = f.readlines()

        block = extract_go_block(lines, start_line=line_nr, block_type=type_name)

        code = "".join(block)
        rel_path = get_rel_path(self._pkg_path, path) if path is not None else None
        return code, rel_path

    def render(self, data: CollectorItem, options: GoOptions) -> str:
        """Render a template using provided data and configuration options."""
        # The `data` argument is the data to render, that was collected above in `collect()`.
        # The `options` argument is the configuration options for loading/rendering the data.
        # It contains both the global and local options, combined together.

        # You might want to get the template based on the data type.

        # template = self.env.get_template(data)

        template = rendering.do_get_template(self.env, data)

        # All the following variables will be available in the Jinja templates.
        return template.render(
            config=options,
            data=data,  # You might want to rename `data` into something more specific.
            heading_level=options.heading_level,
            root=True,
        )

    def get_aliases(self, identifier: str) -> tuple[str, ...]:
        """Get aliases for a given identifier."""
        try:
            data = self._collected[identifier]
        except KeyError:
            return ()
        # Update the following code to return the canonical identifier and any aliases.
        return data["name"]

    def update_env(self, config: dict) -> None:  # noqa: ARG002
        """Update the Jinja environment with any custom settings/filters/options for this handler.

        Parameters:
            config: MkDocs configuration, read from `mkdocs.yml`.
        """
        self.env.trim_blocks = True
        self.env.lstrip_blocks = True
        self.env.keep_trailing_newline = False

        self.env.filters["format_types"] = rendering.do_format_types

        self.env.filters["format_signature"] = rendering.do_format_signature
        self.env.filters["get_template"] = rendering.do_get_template

    # You can also implement the `get_inventory_urls` and `load_inventory` methods
    # if you want to support loading object inventories.
    # You can also implement the `render_backlinks` method if you want to support backlinks.


def get_handler(
    handler_config: MutableMapping[str, Any],
    tool_config: MkDocsConfig,
    **kwargs: Any,
) -> GoHandler:
    """Simply return an instance of `GoHandler`.

    Arguments:
        handler_config: The handler configuration.
        tool_config: The tool (SSG) configuration.

    Returns:
        An instance of `GoHandler`.
    """
    base_dir = Path(tool_config.config_file_path or "./mkdocs.yml").parent
    return GoHandler(
        config=GoConfig.from_data(**handler_config),
        base_dir=base_dir,
        **kwargs,
    )


def find_dicts_with_value(obj: dict, target_key: str, target_value: str) -> list:
    results = []
    if isinstance(obj, dict):
        # Check if the current dict has the key and value
        if target_key in obj:
            if obj[target_key] == target_value:
                results.append(obj)
            elif isinstance(obj[target_key], list):
                results.extend(obj for elem in obj[target_key] if elem == target_value)
        # Recursively search in each value
        for value in obj.values():
            results.extend(find_dicts_with_value(value, target_key, target_value))
    elif isinstance(obj, list):
        # If it's a list, search each item
        for item in obj:
            results.extend(find_dicts_with_value(item, target_key, target_value))
    return results


def find_string_in_go_files(search_dir, search_string, type):
    for root, _, files in os.walk(search_dir):
        for file in files:
            if file.endswith(".go"):
                filepath = os.path.join(root, file)
                with open(filepath, encoding="utf-8", errors="ignore") as f:
                    for i, line in enumerate(f, start=1):
                        stripped = line.strip()
                        if search_string in stripped and not stripped.startswith("//"):
                            return (filepath, i)
    return None


def extract_go_block(lines, start_line, block_type):
    start_line -= 1  # Convert to 0-based index
    block = []

    if block_type in ["func", "type"]:
        opener, closer = "{", "}"
    elif block_type in ["const", "var"]:
        if lines[start_line].strip().startswith("const (") or lines[start_line].strip().startswith("var ("):
            opener, closer = "(", ")"
        else:
            return [lines[start_line]]  # single-line const
    else:
        return []

    depth = 0
    found_start = False

    for line in lines[start_line:]:
        if not found_start:
            if opener in line:
                found_start = True
                depth += line.count(opener) - line.count(closer)
            block.append(line)
            if closer in line:
                break
        else:
            block.append(line)
            depth += line.count(opener) - line.count(closer)
            if depth == 0:
                break

    return block


def inject_code_info(obj, find_code_fn):
    if isinstance(obj, dict):
        if obj.get("type") in {"func", "const", "var"}:
            code, rel_path = find_code_fn(obj)
            obj["code"] = code
            obj["relative_path"] = rel_path
        elif obj.get("type") == "type":
            obj_to_find = obj.get("name")
            code, rel_path = find_code_fn(obj, obj_to_find)
            obj["code"] = code
            obj["relative_path"] = rel_path
        for value in obj.values():
            inject_code_info(value, find_code_fn)
    elif isinstance(obj, list):
        for item in obj:
            inject_code_info(item, find_code_fn)


def get_rel_path(pkg_path, path):
    index = path.find(pkg_path)
    return path[index:]
