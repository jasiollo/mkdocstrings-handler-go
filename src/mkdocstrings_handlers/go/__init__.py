"""Go handler for mkdocstrings."""

from mkdocstrings_handlers.go._internal.config import (
    GoConfig,
    GoInputConfig,
    GoInputOptions,
    GoOptions,
)
from mkdocstrings_handlers.go._internal.handler import (
    GoHandler,
    _find_dicts_with_value,
    get_handler,
)
from mkdocstrings_handlers.go._internal.rendering import (
    do_format_code,
    do_format_const_signature,
    do_format_signature,
    do_format_struct_signature,
    do_format_types,
    do_get_template,
)

__all__ = [
    "GoConfig",
    "GoHandler",
    "GoInputConfig",
    "GoInputOptions",
    "GoOptions",
    "_find_dicts_with_value",
    "do_format_code",
    "do_format_const_signature",
    "do_format_signature",
    "do_format_struct_signature",
    "do_format_types",
    "do_get_template",
    "get_handler",
]
