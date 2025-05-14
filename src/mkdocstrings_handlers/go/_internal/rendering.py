from jinja2 import TemplateNotFound, pass_context
from jinja2.runtime import Context
from markupsafe import Markup
from mkdocstrings import get_logger

_logger = get_logger(__name__)


# def _format_signature(name: Markup, signature: str, line_length:int) -> str:
#     name = str(name).strip()
#     signature = signature.strip()
#     if len(name+signature) < line_length:
#         return name + signature

#     # TODO: add _get_formatter()
#     # and call it in similar way as in python handler
#     # https://go.dev/blog/gofmt

#     # very temporary solution
#     return name + "\n" + signature

# @pass_context
# def do_format_signature(
#     context: Context,
#     callable_path: Markup,
#     function: dict,
#     line_length: int,
# ) -> str:
#     """Format a signature.

#     Parameters:
#         context: Jinja context, passed automatically.
#         callable_path: The path of the callable we render the signature of.
#         function: The function we render the signature of.
#         line_length: The line length.

#     Returns:
#         The same code, formatted.
#     """
#     env = context.environment
#     template = env.get_template("signature.html.jinja")

#     new_context = context.parent

#     signature = template.render(new_context, function=function, signature=True)
#     signature = _format_signature(callable_path, signature, line_length)

#     signature = str(
#         env.filters["highlight"](
#             Markup.escape(signature),
#             language="go",
#             inline=False,
#             classes=["doc-signature"],
#             linenums=False,
#         ),
#     )
#     return signature




def _format_types(name: Markup, signature: str, line_length: int) -> str:
    name = str(name).strip()
    signature = signature.strip()
    if len(name + signature) < line_length:
        return signature  # name is already inside the signature block

    # temporary solution: split long structs
    return "\n" + signature


@pass_context
def do_format_types(ctx: Context, block_content: str,data, line_length) -> str:
    config = ctx.get("config", {})

    if not data:
        _logger.warning("No 'data' found in context for struct signature.")
        return ""

    try:
        template = ctx.environment.get_template("types.html.jinja")
    except TemplateNotFound:
        _logger.warning("Template 'types.html.jinja' not found.")
        return ""

    signature = template.render(data=data)
    formatted = _format_types(data["name"], signature, line_length)

    return Markup(
        ctx.environment.filters["highlight"](
            Markup.escape(formatted),
            language="go",
            inline=False,
            classes=["doc-signature"],
            linenums=False,
        ),
    )
