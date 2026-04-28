"""Regex verifier for string-valued targets (e.g., field values)."""
import re


def check_regex(item: dict, *, value: str) -> tuple[bool, str]:
    spec = item["verifier"]
    pattern = spec["pattern"]
    max_length = spec.get("max_length")
    min_length = spec.get("min_length")

    if min_length is not None and len(value) < min_length:
        return False, f"value '{value}' shorter than min_length {min_length}"
    if max_length is not None and len(value) > max_length:
        return False, f"value '{value}' (len={len(value)}) exceeds max_length {max_length}"
    if not re.search(pattern, value):
        return False, f"value '{value}' did not match pattern {pattern!r}"
    return True, f"value '{value}' matched pattern {pattern!r}"
