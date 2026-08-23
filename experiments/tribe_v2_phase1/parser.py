"""Deterministic parsing and repair helpers for model responses."""

from __future__ import annotations

import json
import re
from typing import Any

from .schemas import SchemaValidationError, validate_agent_action


class ParseError(ValueError):
    pass


FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    fenced = FENCE_RE.search(stripped)
    if fenced:
        stripped = fenced.group(1).strip()

    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start < 0 or end <= start:
            raise ParseError("response does not contain a JSON object")
        try:
            payload = json.loads(stripped[start : end + 1])
        except json.JSONDecodeError as exc:
            raise ParseError(f"invalid JSON object: {exc}") from exc

    if not isinstance(payload, dict):
        raise ParseError("response JSON must be an object")
    return payload


def parse_agent_action(text: str) -> dict[str, Any]:
    payload = extract_json_object(text)
    try:
        return validate_agent_action(payload)
    except SchemaValidationError as exc:
        raise ParseError(str(exc)) from exc


def repair_prompt(raw_response: str, error: Exception) -> str:
    """Return a deterministic repair prompt for a second model call.

    Phase 0 does not call a model; tests assert that this prompt is stable.
    """

    return (
        "Return only one valid JSON object matching the TRIBE action schema. "
        "Do not include Markdown fences or explanatory prose. "
        f"Previous parse error: {error}. "
        f"Previous response: {raw_response}"
    )

