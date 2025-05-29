import os
from typing import Any, Callable, Optional, Union


# --- JSON Utilities ---
def _find_dicts_with_value(obj: Any, target_key: str, target_value: str) -> list[dict]:
    """Recursively find all dicts containing a specific key-value pair.

    Parameters:
        obj: The dictionary or list to search within.
        target_key: The key to look for.
        target_value: The value to match against.

    Returns:
        A list of dictionaries where the key-value pair is found.
    """
    results = []

    if isinstance(obj, dict):
        if target_key in obj:
            value = obj[target_key]
            if value == target_value or (isinstance(value, list) and target_value in value):
                results.append(obj)

        for val in obj.values():
            results.extend(_find_dicts_with_value(val, target_key, target_value))

    elif isinstance(obj, list):
        for item in obj:
            results.extend(_find_dicts_with_value(item, target_key, target_value))

    return results


# --- Filesystem Utilities ---
def _find_string_in_go_files(
    search_dir: str,
    search_string: str,
) -> Optional[tuple[str, int]]:
    """Search for a string in Go files within a directory.

    Parameters:
        search_dir: The root directory to search.
        search_string: The string to search for in the files.

    Returns:
        A tuple of the file path and line number of the first match, or None if not found.
    """
    for root, _, files in os.walk(search_dir):
        for file in files:
            if file.endswith(".go"):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, encoding="utf-8", errors="ignore") as f:
                        for i, line in enumerate(f, start=1):
                            stripped = line.strip()
                            if search_string in stripped and not stripped.startswith(
                                "//",
                            ):
                                return filepath, i
                except FileNotFoundError:
                    continue
    return None


def _get_rel_path(pkg_path: str, path: str) -> str:
    """Get the relative path from the package path within a full file path.

    Parameters:
        pkg_path: The Go package path.
        path: The full file path.

    Returns:
        The relative path starting from the package directory, or the full path if not found.
    """
    index = path.find(pkg_path)
    return path[index:] if index != -1 else path


# --- Go Code Utilities ---
def _extract_go_block(lines: list[str], start_line: int, block_type: str) -> list[str]:
    """Extract a Go code block from source lines based on block type.

    Parameters:
        lines: The list of lines from the Go source file.
        start_line: The 1-based line number to start extraction.
        block_type: The type of Go block ('func', 'type', 'const', 'var').

    Returns:
        A list of lines representing the extracted block.
    """
    start_line -= 1  # Convert to 0-based
    block = []

    if block_type in {"func", "type"}:
        opener, closer = "{", "}"
    elif block_type in {"const", "var"}:
        line = lines[start_line].strip()
        if line.startswith(("const (", "var (")):
            opener, closer = "(", ")"
        else:
            return [lines[start_line]]
    else:
        return []

    depth = 0
    found_start = False

    for line in lines[start_line:]:
        block.append(line)
        if opener in line:
            depth += line.count(opener)
            found_start = True
        if closer in line:
            depth -= line.count(closer)
        if found_start and depth <= 0:
            break

    return block


def _inject_code_info(obj: Union[dict, list], find_code_fn: Callable) -> None:
    """Inject code snippets and relative paths into documentation data.

    Parameters:
        obj: The documentation object or list of objects to modify.
        find_code_fn: The function used to locate and extract code snippets.

    Returns:
        None
    """
    if isinstance(obj, dict):
        obj_type = obj.get("type")
        name = obj.get("name")

        if obj_type in {"func", "const", "var"}:
            code, rel_path = find_code_fn(obj)
            obj["code"] = code
            obj["relative_path"] = rel_path
        elif obj_type == "type" and name:
            code, rel_path = find_code_fn(obj, name)
            obj["code"] = code
            obj["relative_path"] = rel_path

        for val in obj.values():
            _inject_code_info(val, find_code_fn)

    elif isinstance(obj, list):
        for item in obj:
            _inject_code_info(item, find_code_fn)
