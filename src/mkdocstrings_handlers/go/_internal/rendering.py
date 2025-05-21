
from jinja2 import Environment, Template, TemplateNotFound, pass_context, pass_environment
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



@pass_context
def do_format_types(ctx: Context, _ : str) -> str:
    data = ctx.get("data")
    if not data:
        _logger.warning("No 'data' found in context for do_format_types.")
        return ""

    try:
        template = ctx.environment.get_template("types.html.jinja")
    except TemplateNotFound:
        _logger.warning("Template 'types.html.jinja' not found.")
        return ""

    return template.render(data=data)



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

_TEMPLATE_MAP = {
    "func": "function.html.jinja",
    "type": "struct.html.jinja",
    "package": "package.html.jinja"
}

@pass_environment
def do_get_template(env: Environment, obj: dict) -> Template:
    """Get the template name used to render an object.

    Parameters:
        env: The Jinja environment, passed automatically.
        obj: A dict representing collected object.

    Returns:
        A template name.
    """
    name = _TEMPLATE_MAP.get(obj["type"])
    if name is None:
        raise AttributeError(f"Object type {obj['type']} does not appear to have a TEMPLATE_MAP entry")
    return env.get_template(name)
