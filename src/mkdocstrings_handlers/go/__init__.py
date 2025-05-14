"""Go handler for mkdocstrings."""

from mkdocstrings_handlers.go._internal.config import (
    GoConfig,
    GoInputConfig,
    GoInputOptions,
    GoOptions,
)

from mkdocstrings_handlers.go._internal.rendering import do_format_types

from mkdocstrings_handlers.go._internal.handler import GoHandler, get_handler

__all__ = [
    "GoConfig",
    "GoHandler",
    "GoInputConfig",
    "GoInputOptions",
    "GoOptions",
    "get_handler",
    "do_format_types",
]
