#!/usr/bin/env python3
"""Run the deterministic no-spend automation-and-repression fixture."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[2]))

from experiments.tribe_v2_phase1.acemoglu_worlds import CELLS, advance_acemoglu_state, make_acemoglu_world
from experiments.tribe_v2_phase1.schemas import validate_acemoglu_action


DEFAULT_OUTPUT = Path("output/tribe_v2_phase1/acemoglu_phase0/events.jsonl")


def fixture_action(world: dict[str, Any], agent: dict[str, Any], cycle: int) -> dict[str, Any]:
    state = world["political_economy"]
    role = agent["role"]
    policy = state["baseline_policy"] if role == "capitalist_state" else "abstain"
    revolt = (
        "participate" if state["revolt_pressure"] >= 0.55 else "do_not_participate"
    ) if role == "worker_coalition" else "not_applicable"
    action_category = "comply" if policy in ("redistribute", "abstain") else "explore"
    action = {
        "agent_id": agent["agent_id"],
        "cycle": cycle,
        "arm": "normative_reform",
        "declared_intent": action_category,
        "action": f"select_{policy}" if role == "capitalist_state" else f"worker_{revolt}",
        "action_category": action_category,
        "rule_references": ["AR3" if policy == "redistribute" else "AR4" if policy == "repress" else "AR1"],
        "resource_move": None,
        "justification": "deterministic Phase 0 fixture",
        "confidence": 1.0,
        "policy_choice": policy,
        "revolt_choice": revolt,
        "labor_share_assessment": state["labor_share"],
        "revolt_pressure_assessment": state["revolt_pressure"],
        "coercive_infrastructure_reliance": state["coercive_infrastructure"],
        "normative_layer": "surface_exception" if policy == "repress" else "recent_rule",
    }
    return validate_acemoglu_action(action)


def run_fixture(replicas: int = 2, cycles: int = 3) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for cell in CELLS:
        for replica in range(replicas):
            world = make_acemoglu_world(cell.cell_id, replica=replica)
            for cycle in range(cycles):
                cycle_actions = []
                for agent in world["agents"]:
                    action = fixture_action(world, agent, cycle)
                    action.update(
                        {
                            "event_type": "action",
                            "experiment": world["experiment"],
                            "cell_id": cell.cell_id,
                            "replica": replica,
                            "world_id": world["world_id"],
                            "role": agent["role"],
                            "treatments": dict(world["treatments"]),
                            "provider": "deterministic_fixture",
                            "cost_usd": 0.0,
                        }
                    )
                    rows.append(action)
                    cycle_actions.append(action)
                advance_acemoglu_state(world, cycle_actions)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replicas", type=int, default=2)
    parser.add_argument("--cycles", type=int, default=3)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    rows = run_fixture(args.replicas, args.cycles)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    print(json.dumps({"status": "PASS", "rows": len(rows), "cost_usd": 0.0, "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
