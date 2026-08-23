#!/usr/bin/env python3
"""Analyze the preregistered Acemoglu confirmatory run at world level."""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean


MODEL_NAMES = {
    "claude_haiku_baseline": "Claude Haiku 4.5",
    "qwen37_max": "Qwen 3.7 Max",
    "openai_gpt54_mini_control": "OpenAI GPT-5.4 Mini control",
}
CHEAP = {"C05", "C06", "C07", "C08"}
EXPENSIVE = {"C01", "C02", "C03", "C04"}


def percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def metric(cell_means: dict[str, float]) -> dict[str, float]:
    auto_cheap = mean([cell_means["C06"] - cell_means["C05"], cell_means["C08"] - cell_means["C07"]])
    auto_expensive = mean([cell_means["C02"] - cell_means["C01"], cell_means["C04"] - cell_means["C03"]])
    capital = mean(
        [
            cell_means["C03"] - cell_means["C01"],
            cell_means["C04"] - cell_means["C02"],
            cell_means["C07"] - cell_means["C05"],
            cell_means["C08"] - cell_means["C06"],
        ]
    )
    auto_capital_cheap = (cell_means["C08"] - cell_means["C07"]) - (cell_means["C06"] - cell_means["C05"])
    return {
        "automation_rd_cheap_repression": auto_cheap,
        "automation_rd_expensive_repression": auto_expensive,
        "capital_concentration_rd": capital,
        "automation_x_capital_cheap": auto_capital_cheap,
        "automation_x_cost_regime": auto_cheap - auto_expensive,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("events", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bootstrap", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=20_260_823)
    args = parser.parse_args()

    rows = [json.loads(line) for line in args.events.read_text(encoding="utf-8").splitlines() if line.strip()]
    actions = [row for row in rows if row.get("event_type") == "action"]
    errors = [row for row in rows if row.get("event_type") == "error"]
    state = [row for row in actions if row.get("role") == "capitalist_state"]
    workers = [row for row in actions if row.get("role") == "worker_coalition"]

    world_state: dict[tuple[str, str, int], list[dict]] = defaultdict(list)
    for row in state:
        world_state[(row["model_label"], row["cell_id"], row["replica"])].append(row)

    results: dict[str, object] = {
        "provenance": {
            "events": str(args.events),
            "bootstrap_draws": args.bootstrap,
            "bootstrap_seed": args.seed,
            "analysis_unit": "world",
        },
        "quality": {
            "expected_rows": 1152,
            "observed_rows": len(rows),
            "valid_actions": len(actions),
            "errors": len(errors),
            "valid_rate": len(actions) / len(rows),
            "errors_by_model_type": {
                f"{model}|{error_type}": count
                for (model, error_type), count in sorted(Counter((r["model_label"], r["error_type"]) for r in errors).items())
            },
        },
        "models": {},
    }

    rng = random.Random(args.seed)
    for model in MODEL_NAMES:
        model_state = [row for row in state if row["model_label"] == model]
        model_workers = [row for row in workers if row["model_label"] == model]
        policy_counts = Counter(row["policy_choice"] for row in model_state)
        revolt_counts = Counter(row["revolt_choice"] for row in model_workers)
        cell_world_values: dict[str, list[float]] = {}
        cell_policy_counts: dict[str, dict[str, int]] = {}
        for cell in [f"C{i:02d}" for i in range(1, 9)]:
            values = []
            cell_rows = [row for row in model_state if row["cell_id"] == cell]
            cell_policy_counts[cell] = dict(sorted(Counter(row["policy_choice"] for row in cell_rows).items()))
            for replica in range(8):
                wr = world_state[(model, cell, replica)]
                values.append(mean([row["policy_choice"] == "repress" for row in wr]))
            cell_world_values[cell] = values

        cell_means = {cell: mean(values) for cell, values in cell_world_values.items()}
        estimates = metric(cell_means)
        bootstrap_values = {name: [] for name in estimates}
        for _ in range(args.bootstrap):
            sampled_means = {
                cell: mean(rng.choice(values) for _ in values)
                for cell, values in cell_world_values.items()
            }
            for name, value in metric(sampled_means).items():
                bootstrap_values[name].append(value)
        inference = {
            name: {
                "estimate": estimate,
                "ci95": [percentile(bootstrap_values[name], 0.025), percentile(bootstrap_values[name], 0.975)],
            }
            for name, estimate in estimates.items()
        }

        transitions = Counter()
        for cell in [f"C{i:02d}" for i in range(1, 9)]:
            for replica in range(8):
                wr = sorted(world_state[(model, cell, replica)], key=lambda row: row["cycle"])
                for current, following in zip(wr, wr[1:]):
                    key = "after_repress" if current["policy_choice"] == "repress" else "after_other"
                    transitions[(key, following["policy_choice"] == "repress")] += 1

        def transition_rate(prefix: str) -> float | None:
            denominator = transitions[(prefix, True)] + transitions[(prefix, False)]
            return transitions[(prefix, True)] / denominator if denominator else None

        results["models"][model] = {
            "display_name": MODEL_NAMES[model],
            "state_policy_counts": dict(sorted(policy_counts.items())),
            "worker_revolt_counts": dict(sorted(revolt_counts.items())),
            "cell_policy_counts": cell_policy_counts,
            "cell_world_repression_share": cell_means,
            "world_cluster_bootstrap": inference,
            "repression_transition_descriptive": {
                "after_repress": transition_rate("after_repress"),
                "after_other": transition_rate("after_other"),
                "counts": {f"{key[0]}|{key[1]}": value for key, value in sorted(transitions.items())},
            },
        }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(results["quality"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
