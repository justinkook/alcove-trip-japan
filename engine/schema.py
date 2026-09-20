"""A small JSON Schema subset: type, const, enum, required, properties, items, pattern, minLength, additionalProperties."""

from __future__ import annotations

from typing import Any


def _type_ok(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return False


def validate(value: Any, schema: dict[str, Any], pointer: str = "") -> list[tuple[str, str]]:
    errors: list[tuple[str, str]] = []
    expected = schema.get("type")
    if isinstance(expected, list):
        if not any(_type_ok(value, item) for item in expected):
            return [(pointer or "/", f"has the wrong type; expected {' or '.join(expected)}")]
    elif isinstance(expected, str) and not _type_ok(value, expected):
        return [(pointer or "/", f"has the wrong type; expected {expected}")]

    if "const" in schema and value != schema["const"]:
        errors.append((pointer or "/", f"must equal {schema['const']!r}"))
    if "enum" in schema and value not in schema["enum"]:
        errors.append((pointer or "/", f"must be one of {schema['enum']!r}"))
    if isinstance(value, str):
        pattern = schema.get("pattern")
        if pattern is not None:
            import re

            if re.fullmatch(pattern, value) is None:
                errors.append((pointer or "/", f"must match {pattern}"))
        min_length = schema.get("minLength")
        if isinstance(min_length, int) and len(value) < min_length:
            errors.append((pointer or "/", f"must be at least {min_length} characters"))

    if isinstance(value, dict):
        properties = schema.get("properties") or {}
        for key in schema.get("required") or []:
            if key not in value:
                errors.append((f"{pointer}/{key}", "is required"))
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in properties:
                    errors.append((f"{pointer}/{key}", "is not allowed"))
        for key, child in value.items():
            if key in properties:
                errors.extend(validate(child, properties[key], f"{pointer}/{key}"))

    if isinstance(value, list) and "items" in schema:
        for index, child in enumerate(value):
            errors.extend(validate(child, schema["items"], f"{pointer}/{index}"))
    return errors
