import subprocess
from os.path import expanduser, isfile

from jinja2 import Environment, Template, TemplateNotFound, pass_context, pass_environment
from jinja2.runtime import Context
from markupsafe import Markup
from mkdocstrings import get_logger

_logger = get_logger(__name__)


@pass_context
def do_format_types(ctx: Context, _: str) -> str:
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


def _format_signature(name: Markup, signature: str, line_length: int) -> str:
    name = str(name).strip()  # type: ignore[assignment]
    signature = signature.strip()
    if len(name + signature) < line_length:
        return name + signature

    # try to use golines formatter if installed
    full = name + signature
    if(isfile(expanduser("~/go/bin/golines"))):
        formatted = subprocess.run( # noqa: S603
            [expanduser("~/go/bin/golines"), f"--max-len={line_length}"],
            input = full,
            capture_output=True,
            text= True, check=False,
        )
        if formatted.stdout != "":
            return formatted.stdout

    # try to manualy format
    code = name + signature
    code = code.replace("(", "\n(\n")
    code = code.replace(")", "\n)\n")
    return code.replace(", ", ",\n")


def _format_type_signature(name: Markup, signature: str, line_length: int) -> str:
    return signature.strip()


def do_format_code(
    code: str,
    line_length: int,
    format_code: bool,
) -> str:
    """Format source code block.

    Parameters:
        code: go code to format
        line_length: line length specified in GoOptions
        format_code: flag wether to perform formatting specified in GoOptions


    Formats given code bloc using golines formatter.
    If golines is unavailable code is left unformatted.

    Returns:
        The same code, formatted.
    """
    if not format_code or not isfile(expanduser("~/go/bin/golines")):
        return code
    formatted = subprocess.run( # noqa: S603
            [expanduser("~/go/bin/golines"), f"--max-len={line_length}"],
            input = code,
            capture_output=True,
            text= True, check=False,
        )
    if formatted.stdout !="":
        return formatted.stdout
    # golines failed - no format
    return code

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

    Formats given signature using golines formatter.
    If golines is unavailable code is left unformatted.

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


@pass_context
def do_format_struct_signature(
    context: Context,
    struct_path: Markup,
    struct: dict,
    line_length: int,
) -> str:
    """Format a Go struct type signature.

    Args:
        context: Jinja context
        struct_path: Path to the struct (used as label)
        struct: Struct object with name, fields, etc.
        line_length: Max line length

    Returns:
        Highlighted formatted signature
    """
    env = context.environment
    template = env.get_template("struct_signature.html.jinja")

    new_context = context.parent
    signature = template.render(new_context, struct=struct, signature=True)
    signature = _format_type_signature(struct_path, signature, line_length)

    return str(
        env.filters["highlight"](
            Markup.escape(signature),
            language="go",
            inline=False,
            classes=["doc-signature"],
            linenums=False,
        ),
    )


@pass_context
def do_format_const_signature(
    context: Context,
    const_path: Markup,
    const: dict,
    line_length: int,
) -> str:
    """Format a Go const declaration.

    Args:
        context: Jinja context
        const_path: Path to the const
        const: Const object
        line_length: Max line length

    Returns:
        Highlighted const declaration
    """
    env = context.environment
    template = env.get_template("const_signature.html.jinja")

    new_context = context.parent
    signature = template.render(new_context, const=const, signature=True)
    signature = _format_type_signature(const_path, signature, line_length)

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
    "package": "package.html.jinja",
    "const": "const.html.jinja",
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
