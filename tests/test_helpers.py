import pytest

from mkdocstrings_handlers.go._internal.handler import (
    find_dicts_with_value,
)

data = {
    "type": "package",
    "doc": "",
    "name": "pkg",
    "consts": [
        {
            "packageName": "pkg",
            "doc": "Constant declaration\n",
            "names": ["Version", "Number"],
            "type": "const",
        },
    ],
    "types": [
        {
            "packageName": "pkg",
            "doc": "Interface declaration\n",
            "name": "Greeter",
            "type": "type",
        },
        {
            "packageName": "pkg",
            "doc": "Struct type with a field\n",
            "name": "MyType",
            "methods": [
                {
                    "doc": "Function that implements Greeter interface\n",
                    "name": "Greet",
                    "packageName": "pkg",
                    "type": "func",
                },
                {
                    "doc": "Method on MyType\n",
                    "name": "Method",
                    "packageName": "pkg",
                    "type": "func",
                    "recv": "MyType",
                    "orig": "MyType",
                },
            ],
        },
    ],
    "vars": [
        {
            "packageName": "pkg",
            "doc": "Variable declaration\n",
            "names": ["DefaultName"],
            "type": "var",
        },
    ],
    "funcs": [
        {
            "doc": "Function returning a string\n",
            "name": "Hello",
        },
    ],
}


@pytest.fixture
def example_data() -> dict:
    """Fixture to provide access to the pkg package data."""
    return data


def test_name_search(example_data: dict) -> None:
    assert find_dicts_with_value(example_data, "name", "Hello") == [
        {"doc": "Function returning a string\n", "name": "Hello"},
    ]

    assert find_dicts_with_value(example_data, "names", "Number") == [
        {
            "packageName": "pkg",
            "doc": "Constant declaration\n",
            "names": ["Version", "Number"],
            "type": "const",
        },
    ]
