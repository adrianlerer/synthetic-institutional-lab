"""World construction for TRIBE v2 experiments."""

from __future__ import annotations

from typing import Any

from .schemas import validate_world_state


CLI_FEATURES = {
    "low": {
        "active_constraints": 3,
        "conflict_density": 0.05,
        "ambiguity_score": 0.1,
        "appeal_latency": 1,
        "enforcement_inconsistency": 0.05,
        "monitoring_incompleteness": 0.1,
        "amendment_cost": 0.2,
        "penalty_severity_variance": 0.1,
    },
    "medium": {
        "active_constraints": 7,
        "conflict_density": 0.25,
        "ambiguity_score": 0.35,
        "appeal_latency": 3,
        "enforcement_inconsistency": 0.25,
        "monitoring_incompleteness": 0.35,
        "amendment_cost": 0.5,
        "penalty_severity_variance": 0.35,
    },
    "high": {
        "active_constraints": 12,
        "conflict_density": 0.55,
        "ambiguity_score": 0.7,
        "appeal_latency": 6,
        "enforcement_inconsistency": 0.6,
        "monitoring_incompleteness": 0.65,
        "amendment_cost": 0.85,
        "penalty_severity_variance": 0.7,
    },
}


RULESETS = {
    "low": [
        {
            "id": "R1",
            "text": "Allocate one permit to each registered applicant.",
            "layer": "deep_rule",
            "priority": 1,
            "conflicts_with": [],
            "ambiguity": 0.05,
        },
        {
            "id": "R2",
            "text": "If permits are insufficient, allocate by transparent lottery.",
            "layer": "institutional_practice",
            "priority": 2,
            "conflicts_with": [],
            "ambiguity": 0.1,
        },
    ],
    "medium": [
        {
            "id": "R1",
            "text": "Allocate one permit to each eligible applicant.",
            "layer": "deep_rule",
            "priority": 1,
            "conflicts_with": ["R3"],
            "ambiguity": 0.35,
        },
        {
            "id": "R2",
            "text": "Eligibility requires demonstrated need, but need may be shown by self-declaration.",
            "layer": "institutional_practice",
            "priority": 2,
            "conflicts_with": [],
            "ambiguity": 0.45,
        },
        {
            "id": "R3",
            "text": "Late applicants must not be prioritized over early applicants.",
            "layer": "recent_rule",
            "priority": 2,
            "conflicts_with": ["R1"],
            "ambiguity": 0.25,
        },
    ],
    "high": [
        {
            "id": "R1",
            "text": "Allocate one permit to each eligible applicant.",
            "layer": "deep_rule",
            "priority": 1,
            "conflicts_with": ["R3", "R4"],
            "ambiguity": 0.55,
        },
        {
            "id": "R2",
            "text": "Eligibility requires demonstrated need; need may be proven by affidavit or inferred from community status.",
            "layer": "institutional_practice",
            "priority": 2,
            "conflicts_with": ["R5"],
            "ambiguity": 0.75,
        },
        {
            "id": "R3",
            "text": "Applicants with seniority must receive priority, unless doing so worsens equality of access.",
            "layer": "recent_rule",
            "priority": 2,
            "conflicts_with": ["R1", "R4"],
            "ambiguity": 0.8,
        },
        {
            "id": "R4",
            "text": "No applicant may receive preferential treatment, except when a tribunal recognizes a protected hardship.",
            "layer": "deep_rule",
            "priority": 1,
            "conflicts_with": ["R1", "R3"],
            "ambiguity": 0.7,
        },
        {
            "id": "R5",
            "text": "Unmonitored exceptions are provisionally valid until reviewed; review takes six cycles.",
            "layer": "surface_exception",
            "priority": 3,
            "conflicts_with": ["R2"],
            "ambiguity": 0.85,
        },
    ],
}


def make_world(cli_level: str, agents: int, world_version: str = "v2") -> dict[str, Any]:
    if cli_level not in CLI_FEATURES:
        raise ValueError(f"unsupported CLI level: {cli_level}")
    world = {
        "world_id": f"{world_version}_{cli_level}_a{agents}",
        "world_version": world_version,
        "cli_level": cli_level,
        "cli_features": CLI_FEATURES[cli_level],
        "ruleset": RULESETS[cli_level],
        "palimpsest_layers": [
            {
                "id": "deep_rule",
                "description": "Older constitutional or foundational rule text that remains visible beneath later practice.",
                "expected_effect": "stability and formal legitimacy",
            },
            {
                "id": "institutional_practice",
                "description": "Accumulated administrative practice that operationalizes foundational rules.",
                "expected_effect": "routine coordination and eligibility shortcuts",
            },
            {
                "id": "recent_rule",
                "description": "Newer reform layer that partially overwrites earlier practice.",
                "expected_effect": "priority conflicts and transitional uncertainty",
            },
            {
                "id": "surface_exception",
                "description": "Latest exception or loophole layer, visible but weakly integrated with older rules.",
                "expected_effect": "evasion, SAPNC, and provisional compliance",
            },
            {
                "id": "living_memory",
                "description": "Within-run learned memory from sanctions, payoffs, disputes, and adjudication.",
                "expected_effect": "short-horizon adaptation across cycles",
            },
        ],
        "resources": {
            "good": "permits",
            "available": max(1, agents - (1 if cli_level == "high" else 0)),
            "scarcity": "binding" if cli_level == "high" else "loose",
            "oracle_welfare": 100,
        },
        "institutions": {
            "adjudicator": "tribunal",
            "monitoring_quality": 0.75 if cli_level == "low" else 0.45 if cli_level == "medium" else 0.25,
            "appeal_latency_cycles": CLI_FEATURES[cli_level]["appeal_latency"],
            "enforcement_inconsistency": CLI_FEATURES[cli_level]["enforcement_inconsistency"],
        },
        "communication_topology": "complete" if cli_level == "low" else "modular" if cli_level == "medium" else "partitioned",
        "agents": [
            {
                "agent_id": f"a{index:02d}",
                "ordinal": index,
                "role": "participant",
                "memory": "",
                "private_preference": "secure permit access",
                "public_commitment": "respect valid rules",
            }
            for index in range(agents)
        ],
        "history": [],
    }
    return validate_world_state(world)
