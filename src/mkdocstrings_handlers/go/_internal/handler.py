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
    from collections.abc import Mapping, MutableMapping

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
        """Collect data given an identifier and selection configuration."""
        if not identifier:
            raise AttributeError("Identifier cannot be empty!\n")

        fqn_depth = 2
        parts = identifier.split(".")
        pkg_path, *objects = parts

        if len(objects) > fqn_depth:
            raise ValueError(
                f"Invalid FQN: '{identifier}'. Go identifiers must be at most 'package.Type.Method'",
            )

        obj = method_with_recv = None
        if len(objects) == fqn_depth:
            obj, method_with_recv = objects
        elif len(objects) == 0:
            obj = identifier.split("/")[-1]
        else:
            obj = objects[0]

        valid_path = next(
            (Path(base) / pkg_path for base in self._paths if (Path(base) / pkg_path).is_dir()),
            None,
        )

        if valid_path is None:
            raise FileNotFoundError(f"No valid package path found for '{pkg_path}'")

        try:
            result = subprocess.run(  # noqa: S603 i fount no way to fix S603 other than to not run anything
                [expanduser(self.godocjson_path), valid_path],
                check=True,
                capture_output=True,
                text=True,
            )
            if not result.stdout:
                raise ValueError("Provided package contains empty file")
            data = json.loads(result.stdout)

            if method_with_recv:
                filtered_data = find_dicts_with_value(data, "name", obj)
                filtered_data = find_dicts_with_value(
                    filtered_data,
                    "name",
                    method_with_recv,
                )
            else:
                filtered_data = find_dicts_with_value(data, "names", obj)

            if len(filtered_data) == 0:
                filtered_data = find_dicts_with_value(data, "name", obj)
            result = filtered_data[0]
            self._collected[identifier] = result
            return result
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"godocjson failed:\n{e.stderr.strip()}") from e

    def render(self, data: CollectorItem, options: GoOptions) -> str:
        """Render a template using provided data and configuration options."""
        # The `data` argument is the data to render, that was collected above in `collect()`.
        # The `options` argument is the configuration options for loading/rendering the data.
        # It contains both the global and local options, combined together.

        # You might want to get the template based on the data type.

        template = self.env.get_template(template_name)

        template = rendering.do_get_template(self.env, data)

        # All the following variables will be available in the Jinja templates.
        return template.render(
            config=options,
            data=data,  # You might want to rename `data` into something more specific.
            heading_level=options.heading_level,
            root=False,
        )

    def get_aliases(self, identifier: str) -> tuple[str, ...]:
        """Get aliases for a given identifier."""
        try:
            data = self._collected[identifier]
        except KeyError:
            return ()
        # Update the following code to return the canonical identifier and any aliases.
        return (data.path,)

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
