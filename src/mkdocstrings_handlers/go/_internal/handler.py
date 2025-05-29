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
from mkdocstrings_handlers.go._internal.helpers import (
    _extract_go_block,
    _find_dicts_with_value,
    _find_string_in_go_files,
    _get_rel_path,
    _inject_code_info,
)

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

    MAX_OBJECT_PARTS = 2  # Maximum parts after the package: Type.Method

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
        """Collect the documentation for the given identifier.

        Parameters:
            identifier: The identifier of the object to collect.
            options: The options to use for the collection.

        Returns:
            The collected item.
        """
        if not identifier:
            raise ValueError("Identifier cannot be empty!")

        _ = options or self.get_options({})

        pkg_path, obj, method, base_dir = self._parse_identifier(identifier)
        self._pkg_path = pkg_path

        valid_path = self._resolve_valid_path(pkg_path, base_dir)
        raw_data = self._run_godocjson(valid_path)

        filtered = [raw_data] if not obj else self._filter_data(raw_data, obj, method)

        if not filtered:
            raise ValueError(f"No data found for identifier: '{identifier}'")

        item = filtered[0]
        self._collected[identifier] = item

        code, path = self._get_code_snippet_and_path(item, method or obj)
        item["code"] = code
        item["relative_path"] = path

        return item

    def render(self, data: CollectorItem, options: GoOptions) -> str:
        """Render the documentation using a Jinja template.

        Parameters:
            data: The collected documentation data.
            options: The rendering options including heading levels and configuration.

        Returns:
            The rendered documentation as a string.
        """
        template = rendering.do_get_template(self.env, data)

        # All the following variables will be available in the Jinja templates.
        return template.render(
            config=options,
            data=data,  # You might want to rename `data` into something more specific.
            heading_level=options.heading_level,
            root=True,
        )

    def get_aliases(self, identifier: str) -> tuple[str, ...]:
        """Get aliases for the given identifier.

        Parameters:
            identifier: The identifier to retrieve aliases for.

        Returns:
            A tuple containing the identifier's name or an empty tuple if not found.
        """
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
        self.env.filters["format_struct_signature"] = rendering.do_format_struct_signature
        self.env.filters["format_const_signature"] = rendering.do_format_const_signature
        self.env.filters["format_code"] = rendering.do_format_code

    def _parse_identifier(
        self,
        identifier: str,
    ) -> tuple[str, str | None, str | None, str | None]:
        """Parse the identifier into components.

        Parameters:
            identifier: The full identifier string (e.g., 'pkg.Type.Method').

        Returns:
            A tuple of (pkg_path, object name, method name, base_dir).
        """
        pkg_path, *objects = identifier.split(".")
        obj = method = None
        base_dir = None  # Not used anymore in path logic

        if len(objects) > self.MAX_OBJECT_PARTS:
            raise ValueError(
                f"Invalid FQN: '{identifier}'. Max format: 'package.Type.Method'",
            )

        if len(objects) == self.MAX_OBJECT_PARTS:
            obj, method = objects
        elif len(objects) == 1:
            obj = objects[0]

        return pkg_path, obj, method, base_dir

    def _resolve_valid_path(self, pkg_path: str, _: str | None = None) -> Path:
        """Resolve the valid Go package path based on configured search paths.

        Parameters:
            pkg_path: The Go package path to search for.
            _: Optional base directory (currently unused).

        Returns:
            The resolved package path as a Path object.

        Raises:
            FileNotFoundError: If the path could not be resolved.
        """
        for base in self._paths:
            candidate = Path(base) / pkg_path
            if candidate.is_dir():
                return candidate

        raise FileNotFoundError(
            f"No valid package path found for '{pkg_path}'\nPaths tried: {self._paths}",
        )

    def _run_godocjson(self, valid_path: Path) -> dict:
        """Run the godocjson command and return parsed JSON output.

        Parameters:
            valid_path: The valid package path to pass to godocjson.

        Returns:
            The parsed JSON documentation data.

        Raises:
            RuntimeError: If the subprocess call fails.
            ValueError: If the resulting output is empty.
        """
        try:
            result = subprocess.run(  # noqa: S603
                [expanduser(self.godocjson_path), valid_path],
                check=True,
                capture_output=True,
                text=True,
            )
            if not result.stdout:
                raise ValueError("Provided package contains empty file")

            return json.loads(result.stdout)

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"godocjson failed:\n{e.stderr.strip()}") from e

    def _filter_data(self, data: dict, obj: str, method: str | None) -> list:
        """Filter the documentation data for a specific object or method.

        Parameters:
            data: The raw godocjson documentation data.
            obj: The object name to filter for (e.g., a type or constant).
            method: Optional method name to further narrow the result.

        Returns:
            A list of matching documentation dictionaries.
        """
        if method:
            # First find the type (receiver), then the method
            type_matches = _find_dicts_with_value(data, "name", obj)
            return _find_dicts_with_value(type_matches, "name", method)

        # Try to match constants/vars by 'names'; fall back to 'name' for types, interfaces
        by_names = _find_dicts_with_value(data, "names", obj)
        return by_names or _find_dicts_with_value(data, "name", obj)

    def _get_code_snippet_and_path(
        self,
        item: dict,
        obj: str | None = None,
    ) -> tuple[str | None, str | None]:
        """Extract the Go code block and source path for a given item.

        Parameters:
            item: The documentation item dictionary.
            obj: Optional name of the object to locate in the source.

        Returns:
            A tuple of (code block as a string, relative path to source file).
        """
        type_name = item["type"]

        if type_name == "package":
            # Package-level injection (possibly modifies the item in-place)
            _inject_code_info(item, self._get_code_snippet_and_path)
            return None, None

        # Determine source path and line number
        path, line_nr = self._resolve_code_location(item, obj, type_name)
        item["line"] = line_nr

        # Extract and return code snippet
        try:
            with open(path) as f:
                lines = f.readlines()
        except FileNotFoundError as err:
            raise FileNotFoundError(f"Source file not found at: {path}") from err

        block = _extract_go_block(lines, start_line=line_nr, block_type=type_name)
        code = "".join(block)
        rel_path = _get_rel_path(self._pkg_path, path) if path else None

        return code, rel_path

    def _resolve_code_location(
        self,
        item: dict,
        obj: str | None,
        type_name: str,
    ) -> tuple[str, int]:
        """Find the file path and line number for the given Go object.

        Parameters:
            item: The documentation item dictionary.
            obj: The name of the object (used for types).
            type_name: The kind of object (e.g., 'type', 'func').

        Returns:
            A tuple containing the source file path and the line number.

        Raises:
            ValueError: If the required fields are missing in the item.
        """
        if type_name == "type":
            if obj is None:
                raise ValueError("Object name is required for resolving type location")
            result = _find_string_in_go_files(item["packageImportPath"], obj)
            if result is None:
                raise FileNotFoundError(
                    f"Could not find '{obj}' in {item['packageImportPath']}",
                )
            return result

        path = item.get("filename")
        if not path:
            raise ValueError("Field 'filename' not found in item")
        line_nr = item.get("line")
        if line_nr is None:
            raise ValueError("Field 'line' not found in item")

        return path, line_nr


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
