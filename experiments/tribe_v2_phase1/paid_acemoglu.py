#!/usr/bin/env python3
"""Run the guarded paid automation-and-repression reliability pilot."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import threading
import time
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[2]))

from experiments.tribe_v2_phase1.acemoglu_worlds import CELLS, advance_acemoglu_state, make_acemoglu_world
from experiments.tribe_v2_phase1.cost_estimate import DEFAULT_CONFIG, fetch_models, load_config
from experiments.tribe_v2_phase1.openrouter_transport import BudgetGate, OpenRouterTransport
from experiments.tribe_v2_phase1.parser import ParseError, parse_agent_action, repair_prompt
from experiments.tribe_v2_phase1.schemas import validate_acemoglu_role_action


DEFAULT_OUTPUT = Path("output/tribe_v2_phase1/acemoglu_paid_pilot/events.jsonl")
ROLE_ARMS = {
    "capitalist_state": "normative_reform",
    "worker_coalition": "resource_allocation",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--model-labels",
        default="claude_haiku_baseline,qwen37_max,mistral_large_2512",
    )
    parser.add_argument("--replicas", type=int, default=2)
    parser.add_argument("--cycles", type=int, default=3)
    parser.add_argument("--cell-ids", default=None, help="Comma-separated subset for reliability smoke tests.")
    parser.add_argument("--max-prompt-tokens", type=int, default=1800)
    parser.add_argument("--max-completion-tokens", type=int, default=450)
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--purpose", default="excluded_reliability_pilot")
    parser.add_argument("--confirm-paid-run", action="store_true")
    return parser.parse_args()


def selected_models(config_path: Path, labels: str) -> list[dict[str, Any]]:
    wanted = {label.strip() for label in labels.split(",") if label.strip()}
    models = [entry for entry in load_config(config_path)["models"] if entry["label"] in wanted]
    missing = wanted - {entry["label"] for entry in models}
    if missing:
        raise ValueError(f"missing configured model labels: {sorted(missing)}")
    return models


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def run_world(
    *,
    model_entry: dict[str, Any],
    cell_id: str,
    replica: int,
    args: argparse.Namespace,
    api_key: str,
    live_models: dict[str, Any],
    budget_gate: BudgetGate,
    run_id: str,
    emit_row: Any,
) -> tuple[int, int]:
    model_id = model_entry["openrouter_id"]
    response_token_budget = int(
        model_entry.get("budget_completion_tokens", args.max_completion_tokens)
    )
    transport = OpenRouterTransport(
        api_key=api_key,
        model_id=model_id,
        model_metadata=live_models[model_id],
        budget_gate=budget_gate,
        max_prompt_tokens=args.max_prompt_tokens,
        # The pilot needs room for providers that count hidden reasoning against
        # max_tokens before emitting the required JSON object.
        max_completion_tokens=response_token_budget,
        budget_completion_tokens=response_token_budget,
        timeout_seconds=args.timeout_seconds,
        prompt_language="en",
    )
    world = make_acemoglu_world(cell_id, replica=replica)
    rows = 0
    errors = 0
    for cycle in range(args.cycles):
        cycle_actions: list[dict[str, Any]] = []
        for agent in world["agents"]:
            role = agent["role"]
            if role not in ROLE_ARMS:
                continue
            arm = ROLE_ARMS[role]
            result = None
            for attempt in range(args.retries + 1):
                try:
                    result = transport.complete_action(world, agent, cycle, arm)
                    action = validate_acemoglu_role_action(parse_agent_action(result.raw_text), role)
                except Exception as exc:
                    if attempt < args.retries and model_entry.get("retry_on_error", True):
                        time.sleep(2 ** attempt)
                        continue
                    row = {
                        "event_type": "error",
                        "experiment": world["experiment"],
                        "run_id": run_id,
                        "cell_id": cell_id,
                        "replica": replica,
                        "world_id": world["world_id"],
                        "model_label": model_entry["label"],
                        "model_family": model_entry.get("family"),
                        "model_id": model_id,
                        "agent_id": agent["agent_id"],
                        "role": role,
                        "cycle": cycle,
                        "arm": arm,
                        "treatments": dict(world["treatments"]),
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                        "attempt": attempt + 1,
                    }
                    if isinstance(exc, ParseError) and result is not None:
                        row["repair_prompt"] = repair_prompt(result.raw_text, exc)
                    emit_row(row)
                    rows += 1
                    errors += 1
                    break
                else:
                    action.update(
                        {
                            "event_type": "action",
                            "experiment": world["experiment"],
                            "run_id": run_id,
                            "cell_id": cell_id,
                            "replica": replica,
                            "world_id": world["world_id"],
                            "model_label": model_entry["label"],
                            "model_family": model_entry.get("family"),
                            "model_id": result.model_id,
                            "provider": result.provider,
                            "finish_reason": result.finish_reason,
                            "role": role,
                            "treatments": dict(world["treatments"]),
                            "attempt": attempt + 1,
                            "prompt_tokens": result.usage.get("prompt_tokens", 0),
                            "completion_tokens": result.usage.get("completion_tokens", 0),
                            "reasoning_tokens": (result.usage.get("completion_tokens_details") or {}).get(
                                "reasoning_tokens", 0
                            ),
                            "cost_usd": float(result.cost_usd),
                        }
                    )
                    emit_row(action)
                    cycle_actions.append(action)
                    rows += 1
                    break
        advance_acemoglu_state(world, cycle_actions)
    return rows, errors


def main() -> int:
    args = parse_args()
    if not args.confirm_paid_run:
        raise SystemExit("Refusing paid run without --confirm-paid-run")
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        raise SystemExit("OPENROUTER_API_KEY is required")
    model_entries = selected_models(args.config, args.model_labels)
    live_models = fetch_models()
    missing = [entry["openrouter_id"] for entry in model_entries if entry["openrouter_id"] not in live_models]
    if missing:
        raise SystemExit(f"Configured model IDs missing from OpenRouter: {missing}")
    budget_gate = BudgetGate.from_env()
    run_id = f"acemoglu_paid_pilot_{int(time.time())}"
    selected_cell_ids = (
        {value.strip() for value in args.cell_ids.split(",") if value.strip()}
        if args.cell_ids
        else {cell.cell_id for cell in CELLS}
    )
    unknown_cells = selected_cell_ids - {cell.cell_id for cell in CELLS}
    if unknown_cells:
        raise SystemExit(f"Unknown cell IDs: {sorted(unknown_cells)}")
    jobs = [
        (entry, cell.cell_id, replica)
        for entry in model_entries
        for cell in CELLS
        if cell.cell_id in selected_cell_ids
        for replica in range(args.replicas)
    ]
    expected_rows = len(jobs) * args.cycles * len(ROLE_ARMS)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    ledger_path = args.output.with_suffix(".ledger.json")
    run_path = args.output.with_suffix(".run.json")
    summary_path = args.output.with_suffix(".summary.json")
    lock = threading.Lock()
    counters = {"rows": 0, "errors": 0, "completed_worlds": 0}
    write_json(
        run_path,
        {
            "run_id": run_id,
            "purpose": args.purpose,
            "models": model_entries,
            "cells": [cell.__dict__ for cell in CELLS if cell.cell_id in selected_cell_ids],
            "replicas": args.replicas,
            "cycles": args.cycles,
            "role_arms": ROLE_ARMS,
            "worlds": len(jobs),
            "expected_rows": expected_rows,
            "budget_cap_usd": str(budget_gate.max_cost_usd),
        },
    )
    with args.output.open("w", encoding="utf-8") as handle:
        def emit_row(row: dict[str, Any]) -> None:
            with lock:
                handle.write(json.dumps(row, sort_keys=True) + "\n")
                handle.flush()
                counters["rows"] += 1
                counters["errors"] += int(row.get("event_type") == "error")
                write_json(ledger_path, budget_gate.ledger)

        with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as executor:
            futures = [
                executor.submit(
                    run_world,
                    model_entry=entry,
                    cell_id=cell_id,
                    replica=replica,
                    args=args,
                    api_key=api_key,
                    live_models=live_models,
                    budget_gate=budget_gate,
                    run_id=run_id,
                    emit_row=emit_row,
                )
                for entry, cell_id, replica in jobs
            ]
            for future in concurrent.futures.as_completed(futures):
                future.result()
                with lock:
                    counters["completed_worlds"] += 1
                    write_json(
                        summary_path,
                        {
                            **counters,
                            "worlds": len(jobs),
                            "expected_rows": expected_rows,
                            "spent_usd": str(budget_gate.spent_usd),
                            "remaining_usd": str(budget_gate.remaining_usd),
                        },
                    )
    print(json.dumps({**counters, "expected_rows": expected_rows, "spent_usd": str(budget_gate.spent_usd)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
