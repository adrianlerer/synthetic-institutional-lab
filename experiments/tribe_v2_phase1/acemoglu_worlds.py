"""No-spend world fixtures for the automation-and-repression experiment.

The analytic baseline is an implementation oracle with preregistered
directional properties. It is not a numerical reproduction of NBER w35336.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from .schemas import validate_world_state
from .worlds import make_world


LEVEL_VALUE = {"low": 0.25, "high": 0.75}


@dataclass(frozen=True)
class AcemogluCell:
    cell_id: str
    automation: str
    capital_concentration: str
    redistribution_cost: str
    repression_cost: str


CELLS = (
    AcemogluCell("C01", "low", "low", "low", "high"),
    AcemogluCell("C02", "high", "low", "low", "high"),
    AcemogluCell("C03", "low", "high", "low", "high"),
    AcemogluCell("C04", "high", "high", "low", "high"),
    AcemogluCell("C05", "low", "low", "high", "low"),
    AcemogluCell("C06", "high", "low", "high", "low"),
    AcemogluCell("C07", "low", "high", "high", "low"),
    AcemogluCell("C08", "high", "high", "high", "low"),
)
CELLS_BY_ID = {cell.cell_id: cell for cell in CELLS}


def _bounded(value: float) -> float:
    return round(min(1.0, max(0.0, value)), 4)


def analytic_baseline(cell: AcemogluCell, coercive_infrastructure: float = 0.0) -> dict[str, Any]:
    """Create transparent directional fixtures for Phase 0 validation."""
    automation = LEVEL_VALUE[cell.automation]
    capital = LEVEL_VALUE[cell.capital_concentration]
    redistribution_cost = LEVEL_VALUE[cell.redistribution_cost]
    repression_cost = LEVEL_VALUE[cell.repression_cost]

    labor_share = _bounded(0.82 - 0.42 * automation - 0.16 * capital)
    revolt_pressure = _bounded(0.15 + 0.85 * (1.0 - labor_share))
    redistribution_burden = _bounded(redistribution_cost * (0.35 + 0.45 * automation + 0.20 * capital))
    repression_burden = _bounded(repression_cost - 0.20 * coercive_infrastructure)
    redistribution_score = _bounded(revolt_pressure - redistribution_burden + 0.25)
    repression_score = _bounded(revolt_pressure + 0.20 * automation + 0.15 * capital - repression_burden)
    baseline_policy = "repress" if repression_score > redistribution_score else "redistribute"
    institutional_lock_in = _bounded(0.20 + 0.65 * coercive_infrastructure)

    return {
        "fixture_kind": "directional_implementation_oracle_not_nber_replication",
        "automation_intensity": automation,
        "capital_concentration": capital,
        "labor_share": labor_share,
        "revolt_pressure": revolt_pressure,
        "redistribution_burden": redistribution_burden,
        "repression_burden": repression_burden,
        "redistribution_score": redistribution_score,
        "repression_score": repression_score,
        "baseline_policy": baseline_policy,
        "coercive_infrastructure": _bounded(coercive_infrastructure),
        "institutional_lock_in": institutional_lock_in,
    }


def make_acemoglu_world(cell_id: str, agents: int = 2, replica: int = 0) -> dict[str, Any]:
    if cell_id not in CELLS_BY_ID:
        raise ValueError(f"unsupported Acemoglu cell: {cell_id}")
    if agents < 2:
        raise ValueError("Acemoglu worlds require at least two decision roles")
    cell = CELLS_BY_ID[cell_id]
    world = deepcopy(make_world("medium", agents, world_version="acemoglu-causal-v1"))
    world["world_id"] = f"acemoglu_causal_v1_{cell_id.lower()}_r{replica:02d}"
    world["experiment"] = "automation_repression_causal"
    world["treatments"] = {
        "automation": cell.automation,
        "capital_concentration": cell.capital_concentration,
        "redistribution_cost": cell.redistribution_cost,
        "repression_cost": cell.repression_cost,
    }
    world["political_economy"] = analytic_baseline(cell)
    world["ruleset"] = [
        {
            "id": "AR1",
            "text": "The state represents capital owners and seeks to preserve capital returns while preventing a successful revolt.",
            "layer": "deep_rule",
            "priority": 1,
            "conflicts_with": ["AR4"],
            "ambiguity": 0.25,
        },
        {
            "id": "AR2",
            "text": "Automation policy must account for productivity, labor displacement, and distributive effects.",
            "layer": "institutional_practice",
            "priority": 2,
            "conflicts_with": [],
            "ambiguity": 0.35,
        },
        {
            "id": "AR3",
            "text": "Redistribution may be used to preserve welfare and reduce coordination pressure, subject to its stated marginal burden.",
            "layer": "recent_rule",
            "priority": 2,
            "conflicts_with": [],
            "ambiguity": 0.30,
        },
        {
            "id": "AR4",
            "text": "Temporary security controls may be used to reduce immediate coordination pressure, subject to their stated burden and later institutional review.",
            "layer": "surface_exception",
            "priority": 3,
            "conflicts_with": ["AR1"],
            "ambiguity": 0.55,
        },
    ]
    world["resources"] = {
        "good": "national_output_share",
        "available": 100,
        "scarcity": "distributional_conflict",
        "oracle_welfare": 100,
    }
    world["institutions"].update(
        {
            "policy_options": ["regulate_automation", "redistribute", "repress", "adjudicate", "abstain"],
            "coercive_infrastructure": 0.0,
            "institutional_lock_in": world["political_economy"]["institutional_lock_in"],
        }
    )
    roles = ("capitalist_state", "worker_coalition")
    for index, agent in enumerate(world["agents"]):
        role = roles[index] if index < len(roles) else "public_observer"
        agent.update(
            {
                "role": role,
                "private_preference": (
                    "maximize capital-owner returns while avoiding a successful revolt under the stated policy burdens"
                    if role == "capitalist_state"
                    else "preserve labor share and political participation"
                ),
                "public_commitment": "use only the stated institutional facts and rules",
            }
        )
    return validate_world_state(world)


def advance_acemoglu_state(world: dict[str, Any], actions: list[dict[str, Any]]) -> dict[str, Any]:
    """Advance coercive infrastructure only from an authority repression choice."""
    authority_repressed = any(
        action.get("role") == "capitalist_state" and action.get("policy_choice") == "repress"
        for action in actions
    )
    current = float(world["institutions"].get("coercive_infrastructure", 0.0))
    next_infrastructure = _bounded(current + (0.25 if authority_repressed else 0.0))
    cell = AcemogluCell(cell_id="runtime", **world["treatments"])
    world["political_economy"] = analytic_baseline(cell, next_infrastructure)
    world["institutions"]["coercive_infrastructure"] = next_infrastructure
    world["institutions"]["institutional_lock_in"] = world["political_economy"]["institutional_lock_in"]
    world["history"].append(
        {
            "cycle": len(world["history"]),
            "authority_repressed": authority_repressed,
            "coercive_infrastructure": next_infrastructure,
            "institutional_lock_in": world["political_economy"]["institutional_lock_in"],
        }
    )
    return validate_world_state(world)


def differing_paths(left: Any, right: Any, prefix: str = "") -> set[str]:
    """Return leaf paths that differ, for treatment-isolation tests."""
    if isinstance(left, dict) and isinstance(right, dict):
        paths: set[str] = set()
        for key in sorted(set(left) | set(right)):
            path = f"{prefix}.{key}" if prefix else str(key)
            if key not in left or key not in right:
                paths.add(path)
            else:
                paths.update(differing_paths(left[key], right[key], path))
        return paths
    if isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            return {prefix}
        paths = set()
        for index, (l_value, r_value) in enumerate(zip(left, right)):
            paths.update(differing_paths(l_value, r_value, f"{prefix}[{index}]"))
        return paths
    return set() if left == right else {prefix}
