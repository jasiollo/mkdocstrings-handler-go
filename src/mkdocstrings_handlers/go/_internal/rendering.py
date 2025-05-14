from jinja2 import pass_context
from jinja2.runtime import Context
from markupsafe import Markup
from mkdocstrings import get_logger

_logger = get_logger(__name__)


def _format_signature(name: Markup, signature: str, line_length:int) -> str:
    name = str(name).strip()    # type: ignore[assignment]
    signature = signature.strip()
    if len(name+signature) < line_length:
        return name + signature

    # TODO: add _get_formatter()
    # and call it in similar way as in python handler
    # https://go.dev/blog/gofmt

    # very temporary solution
    return name + "\n" + signature

@pass_context
def do_format_signature(
    context: Context,
    callable_path: Markup,
    function: dict,
    line_length: int,
) -> str:
    """Format a signature.

    Parameters:
        context: Jinja context, passed automatically.
        callable_path: The path of the callable we render the signature of.
        function: The function we render the signature of.
        line_length: The line length.

    Returns:
        The same code, formatted.
    """
    env = context.environment
    template = env.get_template("signature.html.jinja")

    new_context = context.parent

    signature = template.render(new_context, function=function, signature=True)
    signature = _format_signature(callable_path, signature, line_length)

    return str(
        env.filters["highlight"](
            Markup.escape(signature),
            language="go",
            inline=False,
            classes=["doc-signature"],
            linenums=False,
        ),
    )
