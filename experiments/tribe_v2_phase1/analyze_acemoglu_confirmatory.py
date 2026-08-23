#!/usr/bin/env python3
"""Analyze the protocol-governed Acemoglu confirmatory run at world level."""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean


MODEL_NAMES = {
    "claude_haiku_baseline": "Claude Haiku 4.5",
    "qwen37_max": "Qwen3.7-Max",
    "openai_gpt54_mini_control": "GPT-5.4 mini index system",
}
CELLS = [f"C{i:02d}" for i in range(1, 9)]
AUTOMATION_PAIRS = (("C01", "C02"), ("C03", "C04"), ("C05", "C06"), ("C07", "C08"))


def percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def metric(cell_means: dict[str, float]) -> dict[str, float]:
    auto_repression_favoring = mean(
        [cell_means["C06"] - cell_means["C05"], cell_means["C08"] - cell_means["C07"]]
    )
    auto_redistribution_favoring = mean(
        [cell_means["C02"] - cell_means["C01"], cell_means["C04"] - cell_means["C03"]]
    )
    capital = mean(
        [
            cell_means["C03"] - cell_means["C01"],
            cell_means["C04"] - cell_means["C02"],
            cell_means["C07"] - cell_means["C05"],
            cell_means["C08"] - cell_means["C06"],
        ]
    )
    auto_capital_repression_favoring = (
        (cell_means["C08"] - cell_means["C07"]) - (cell_means["C06"] - cell_means["C05"])
    )
    return {
        "automation_rd_repression_favoring": auto_repression_favoring,
        "automation_rd_redistribution_favoring": auto_redistribution_favoring,
        "capital_concentration_rd": capital,
        "automation_x_capital_repression_favoring": auto_capital_repression_favoring,
        "automation_x_cost_regime": auto_repression_favoring - auto_redistribution_favoring,
    }


def permutation_p_value(
    cell_world_values: dict[str, list[float]],
    statistic: str,
    *,
    draws: int,
    rng: random.Random,
) -> dict[str, float | int | str]:
    """Monte Carlo randomization inference under exchangeability within design strata."""
    observed = metric({cell: mean(values) for cell, values in cell_world_values.items()})[statistic]
    exceedances = 0
    for _ in range(draws):
        permuted: dict[str, float] = {}
        for low_cell, high_cell in AUTOMATION_PAIRS:
            pooled = [*cell_world_values[low_cell], *cell_world_values[high_cell]]
            rng.shuffle(pooled)
            permuted[low_cell] = mean(pooled[:8])
            permuted[high_cell] = mean(pooled[8:])
        candidate = metric(permuted)[statistic]
        exceedances += abs(candidate) >= abs(observed) - 1e-12
    return {
        "estimate": observed,
        "p_value_two_sided": (exceedances + 1) / (draws + 1),
        "draws": draws,
        "null": "automation labels exchangeable within capital-by-cost-regime strata",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("events", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bootstrap", type=int, default=10_000)
    parser.add_argument("--permutations", type=int, default=100_000)
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
            "permutation_draws": args.permutations,
            "permutation_seed": args.seed + 1,
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
        "cross_model_contrasts": {},
    }

    rng = random.Random(args.seed)
    model_world_values: dict[str, dict[str, list[float]]] = {}
    for model in MODEL_NAMES:
        model_state = [row for row in state if row["model_label"] == model]
        model_workers = [row for row in workers if row["model_label"] == model]
        policy_counts = Counter(row["policy_choice"] for row in model_state)
        revolt_counts = Counter(row["revolt_choice"] for row in model_workers)
        cell_world_values: dict[str, list[float]] = {}
        cell_policy_counts: dict[str, dict[str, int]] = {}
        for cell in CELLS:
            values = []
            cell_rows = [row for row in model_state if row["cell_id"] == cell]
            cell_policy_counts[cell] = dict(sorted(Counter(row["policy_choice"] for row in cell_rows).items()))
            for replica in range(8):
                wr = world_state[(model, cell, replica)]
                values.append(mean([row["policy_choice"] == "repress" for row in wr]))
            cell_world_values[cell] = values
        model_world_values[model] = cell_world_values

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
        for cell in CELLS:
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
            "automation_randomization_inference": {
                name: permutation_p_value(
                    cell_world_values,
                    name,
                    draws=args.permutations,
                    rng=random.Random(args.seed + 1 + index),
                )
                for index, name in enumerate(
                    ("automation_rd_repression_favoring", "automation_x_cost_regime")
                )
            },
            "provider_counts": dict(
                sorted(
                    Counter(
                        row.get("provider", "missing")
                        for row in actions
                        if row["model_label"] == model
                    ).items()
                )
            ),
            "zero_event_sensitivity": {
                "state_decisions": len(model_state),
                "repressive_state_decisions": policy_counts.get("repress", 0),
                "rule_of_three_upper95_if_zero": (
                    3 / len(model_state) if model_state and policy_counts.get("repress", 0) == 0 else None
                ),
                "per_cell_world_any_repression_upper95_if_zero": 3 / 8,
            },
            "repression_transition_descriptive": {
                "after_repress": transition_rate("after_repress"),
                "after_other": transition_rate("after_other"),
                "counts": {f"{key[0]}|{key[1]}": value for key, value in sorted(transitions.items())},
            },
        }

    contrast_rng = random.Random(args.seed + 10_000)
    index_model = "openai_gpt54_mini_control"
    for comparator in ("claude_haiku_baseline", "qwen37_max"):
        observed_index = metric(
            {cell: mean(values) for cell, values in model_world_values[index_model].items()}
        )
        observed_comparator = metric(
            {cell: mean(values) for cell, values in model_world_values[comparator].items()}
        )
        draws = {
            "automation_rd_repression_favoring": [],
            "automation_x_cost_regime": [],
        }
        for _ in range(args.bootstrap):
            sampled = {}
            for model in (index_model, comparator):
                sampled[model] = metric(
                    {
                        cell: mean(contrast_rng.choice(values) for _ in values)
                        for cell, values in model_world_values[model].items()
                    }
                )
            for name in draws:
                draws[name].append(sampled[index_model][name] - sampled[comparator][name])
        results["cross_model_contrasts"][f"{index_model}_minus_{comparator}"] = {
            "index_system": MODEL_NAMES[index_model],
            "comparator": MODEL_NAMES[comparator],
            **{
                name: {
                    "estimate": observed_index[name] - observed_comparator[name],
                    "ci95": [percentile(values, 0.025), percentile(values, 0.975)],
                }
                for name, values in draws.items()
            },
        }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(results["quality"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
