"""Go handler for mkdocstrings."""

from mkdocstrings_handlers.go._internal.config import (
    GoConfig,
    GoInputConfig,
    GoInputOptions,
    GoOptions,
)
from mkdocstrings_handlers.go._internal.handler import (
    GoHandler,
    find_dicts_with_value,
    get_handler,
)
from mkdocstrings_handlers.go._internal.rendering import (
    do_format_const_signature,
    do_format_signature,
    do_format_struct_signature,
    do_format_types,
    do_get_template,
    do_format_code,
)

__all__ = [
    "GoConfig",
    "GoHandler",
    "GoInputConfig",
    "GoInputOptions",
    "GoOptions",
    "do_format_const_signature",
    "do_format_signature",
    "do_format_struct_signature",
    "do_format_types",
    "do_get_template",
    "find_dicts_with_value",
    "get_handler",
    "do_format_code",
]
