"""Schema validation for TRIBE v2 Phase 0.

The project avoids a JSON Schema dependency in Phase 0 so the no-spend harness
can run on a bare Python install.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


ACTION_CATEGORIES = ("comply", "explore", "evade", "defect", "abstain")
DECLARED_INTENTS = ACTION_CATEGORIES
ARMS = ("normative_reform", "resource_allocation")
CLI_LEVELS = ("low", "medium", "high")
POLICY_CHOICES = ("regulate_automation", "redistribute", "repress", "adjudicate", "abstain")
REVOLT_CHOICES = ("participate", "do_not_participate", "not_applicable")


@dataclass(frozen=True)
class ValidationErrorDetail:
    field: str
    message: str


class SchemaValidationError(ValueError):
    def __init__(self, errors: list[ValidationErrorDetail]):
        self.errors = errors
        joined = "; ".join(f"{error.field}: {error.message}" for error in errors)
        super().__init__(joined)


def require_fields(payload: dict[str, Any], fields: tuple[str, ...]) -> list[ValidationErrorDetail]:
    return [
        ValidationErrorDetail(field, "missing required field")
        for field in fields
        if field not in payload
    ]


def validate_agent_action(payload: dict[str, Any]) -> dict[str, Any]:
    required = (
        "agent_id",
        "cycle",
        "arm",
        "declared_intent",
        "action",
        "action_category",
        "rule_references",
        "resource_move",
        "justification",
        "confidence",
    )
    errors = require_fields(payload, required)
    if errors:
        raise SchemaValidationError(errors)

    if not isinstance(payload["agent_id"], str) or not payload["agent_id"]:
        errors.append(ValidationErrorDetail("agent_id", "must be a non-empty string"))
    if not isinstance(payload["cycle"], int) or payload["cycle"] < 0:
        errors.append(ValidationErrorDetail("cycle", "must be a non-negative integer"))
    if payload["arm"] not in ARMS:
        errors.append(ValidationErrorDetail("arm", f"must be one of {ARMS}"))
    if payload["declared_intent"] not in DECLARED_INTENTS:
        errors.append(ValidationErrorDetail("declared_intent", f"must be one of {DECLARED_INTENTS}"))
    if not isinstance(payload["action"], str) or not payload["action"]:
        errors.append(ValidationErrorDetail("action", "must be a non-empty string"))
    if payload["action_category"] not in ACTION_CATEGORIES:
        errors.append(ValidationErrorDetail("action_category", f"must be one of {ACTION_CATEGORIES}"))
    if not isinstance(payload["rule_references"], list) or not all(
        isinstance(item, str) for item in payload["rule_references"]
    ):
        errors.append(ValidationErrorDetail("rule_references", "must be a list of strings"))
    if not isinstance(payload["justification"], str) or not payload["justification"]:
        errors.append(ValidationErrorDetail("justification", "must be a non-empty string"))
    if not isinstance(payload["confidence"], (int, float)) or not 0 <= payload["confidence"] <= 1:
        errors.append(ValidationErrorDetail("confidence", "must be a number from 0 to 1"))

    if errors:
        raise SchemaValidationError(errors)
    return payload


def validate_acemoglu_action(payload: dict[str, Any]) -> dict[str, Any]:
    validate_agent_action(payload)
    required = (
        "policy_choice",
        "revolt_choice",
        "labor_share_assessment",
        "revolt_pressure_assessment",
        "coercive_infrastructure_reliance",
        "normative_layer",
    )
    errors = require_fields(payload, required)
    if errors:
        raise SchemaValidationError(errors)
    if payload["policy_choice"] not in POLICY_CHOICES:
        errors.append(ValidationErrorDetail("policy_choice", f"must be one of {POLICY_CHOICES}"))
    if payload["revolt_choice"] not in REVOLT_CHOICES:
        errors.append(ValidationErrorDetail("revolt_choice", f"must be one of {REVOLT_CHOICES}"))
    for field in ("labor_share_assessment", "revolt_pressure_assessment", "coercive_infrastructure_reliance"):
        if not isinstance(payload[field], (int, float)) or not 0 <= payload[field] <= 1:
            errors.append(ValidationErrorDetail(field, "must be a number from 0 to 1"))
    if payload["normative_layer"] not in (
        "deep_rule",
        "institutional_practice",
        "recent_rule",
        "surface_exception",
        "living_memory",
    ):
        errors.append(ValidationErrorDetail("normative_layer", "unsupported normative layer"))
    if errors:
        raise SchemaValidationError(errors)
    return payload


def validate_acemoglu_role_action(payload: dict[str, Any], role: str) -> dict[str, Any]:
    validate_acemoglu_action(payload)
    errors: list[ValidationErrorDetail] = []
    if role == "capitalist_state" and payload["revolt_choice"] != "not_applicable":
        errors.append(ValidationErrorDetail("revolt_choice", "capitalist state must use not_applicable"))
    if role == "worker_coalition" and payload["policy_choice"] != "abstain":
        errors.append(ValidationErrorDetail("policy_choice", "worker coalition must use abstain"))
    if role == "worker_coalition" and payload["revolt_choice"] == "not_applicable":
        errors.append(ValidationErrorDetail("revolt_choice", "worker coalition must choose participation"))
    if errors:
        raise SchemaValidationError(errors)
    return payload


def validate_world_state(payload: dict[str, Any]) -> dict[str, Any]:
    required = (
        "world_id",
        "cli_level",
        "cli_features",
        "ruleset",
        "palimpsest_layers",
        "resources",
        "institutions",
        "communication_topology",
        "agents",
        "history",
    )
    errors = require_fields(payload, required)
    if errors:
        raise SchemaValidationError(errors)

    if payload["cli_level"] not in CLI_LEVELS:
        errors.append(ValidationErrorDetail("cli_level", f"must be one of {CLI_LEVELS}"))
    if not isinstance(payload["cli_features"], dict):
        errors.append(ValidationErrorDetail("cli_features", "must be an object"))
    if not isinstance(payload["ruleset"], list):
        errors.append(ValidationErrorDetail("ruleset", "must be a list"))
    if not isinstance(payload["palimpsest_layers"], list):
        errors.append(ValidationErrorDetail("palimpsest_layers", "must be a list"))
    if not isinstance(payload["resources"], dict):
        errors.append(ValidationErrorDetail("resources", "must be an object"))
    if not isinstance(payload["institutions"], dict):
        errors.append(ValidationErrorDetail("institutions", "must be an object"))
    if payload["communication_topology"] not in ("complete", "modular", "hierarchical", "partitioned"):
        errors.append(ValidationErrorDetail("communication_topology", "unsupported topology"))
    if not isinstance(payload["agents"], list) or not payload["agents"]:
        errors.append(ValidationErrorDetail("agents", "must be a non-empty list"))
    if not isinstance(payload["history"], list):
        errors.append(ValidationErrorDetail("history", "must be a list"))

    if errors:
        raise SchemaValidationError(errors)
    return payload
