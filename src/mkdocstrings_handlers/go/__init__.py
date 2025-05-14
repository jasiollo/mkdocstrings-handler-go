"""Go handler for mkdocstrings."""

from mkdocstrings_handlers.go._internal.config import (
    GoConfig,
    GoInputConfig,
    GoInputOptions,
    GoOptions,
)
from mkdocstrings_handlers.go._internal.handler import GoHandler, get_handler
from mkdocstrings_handlers.go._internal.rendering import do_format_types

__all__ = [
    "GoConfig",
    "GoHandler",
    "GoInputConfig",
    "GoInputOptions",
    "GoOptions",
    "do_format_types",
    "get_handler",
]
