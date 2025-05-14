from pathlib import Path

from mkdocstrings_handlers.go._internal.config import GoConfig, GoOptions
from mkdocstrings_handlers.go._internal.handler import GoHandler

dummy_config = GoConfig(options={})
dummy_base_dir = Path(".")

handler = GoHandler(config=dummy_config, base_dir=dummy_base_dir)
options = GoOptions()


result = handler.collect("your/package/path", options)
print(result)
