#!/usr/bin/env python3
"""Estimate TRIBE v2 Phase 1 OpenRouter cost from live model metadata.

This script intentionally does not require an API key. It reads OpenRouter's
public model listing, validates configured model IDs, and computes a conservative
upper-bound estimate from experiment dimensions and token caps.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from decimal import Decimal
from pathlib import Path
from typing import Any


OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"
DEFAULT_CONFIG = Path(__file__).resolve().parent / "config" / "phase1_models.json"


def money(value: Decimal) -> str:
    return f"${value.quantize(Decimal('0.0001'))}"


def fetch_models(url: str = OPENROUTER_MODELS_URL) -> dict[str, dict[str, Any]]:
    with urllib.request.urlopen(url, timeout=30) as response:
        payload = json.load(response)
    return {model["id"]: model for model in payload.get("data", [])}


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def decimal_price(model: dict[str, Any], key: str) -> Decimal:
    raw = (model.get("pricing") or {}).get(key)
    if raw is None:
        raise ValueError(f"Missing pricing.{key} for {model.get('id')}")
    return Decimal(str(raw))


def estimate_for_model(
    model: dict[str, Any],
    calls: int,
    prompt_tokens: int,
    completion_tokens: int,
    retry_multiplier: Decimal,
) -> Decimal:
    prompt_price = decimal_price(model, "prompt")
    completion_price = decimal_price(model, "completion")
    per_call = (prompt_price * prompt_tokens) + (completion_price * completion_tokens)
    return per_call * calls * retry_multiplier


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--models", type=int, default=None, help="Override number of models.")
    parser.add_argument("--model-labels", default=None, help="Comma-separated model labels to include.")
    parser.add_argument("--cli-levels", type=int, default=3)
    parser.add_argument("--compositions", type=int, default=1)
    parser.add_argument("--replicas", type=int, default=5)
    parser.add_argument("--cycles", type=int, default=12)
    parser.add_argument("--agents", type=int, default=10)
    parser.add_argument("--arms", type=int, default=2)
    parser.add_argument("--prompt-tokens", type=int, default=1800)
    parser.add_argument("--completion-tokens", type=int, default=450)
    parser.add_argument(
        "--use-model-token-budgets",
        action="store_true",
        help="Use per-model budget_completion_tokens from config when present.",
    )
    parser.add_argument("--retry-rate", type=Decimal, default=Decimal("0.15"))
    parser.add_argument("--max-cost-usd", type=Decimal, default=None)
    parser.add_argument(
        "--include-fallbacks",
        action="store_true",
        help="Validate and price fallback candidates separately.",
    )
    args = parser.parse_args()
    if args.max_cost_usd is None and os.environ.get("TRIBE_MAX_COST_USD"):
        args.max_cost_usd = Decimal(os.environ["TRIBE_MAX_COST_USD"])
    return args


def main() -> int:
    args = parse_args()
    config = load_config(args.config)
    live_models = fetch_models()

    configured = config["models"]
    if args.model_labels:
        wanted = {label.strip() for label in args.model_labels.split(",") if label.strip()}
        configured = [entry for entry in configured if entry["label"] in wanted]
        missing_labels = wanted - {entry["label"] for entry in configured}
        if missing_labels:
            print("Missing configured model labels:", file=sys.stderr)
            for label in sorted(missing_labels):
                print(f"  - {label}", file=sys.stderr)
            return 2
    if args.models is not None:
        configured = configured[: args.models]

    missing = [entry["openrouter_id"] for entry in configured if entry["openrouter_id"] not in live_models]
    if missing:
        print("Missing configured model IDs:", file=sys.stderr)
        for model_id in missing:
            print(f"  - {model_id}", file=sys.stderr)
        return 2

    calls_per_model = args.cli_levels * args.compositions * args.replicas * args.cycles * args.agents * args.arms
    retry_multiplier = Decimal("1") + args.retry_rate

    print("TRIBE v2 Phase 1 live OpenRouter cost estimate")
    print(f"Config: {args.config}")
    print(f"Calls per model: {calls_per_model:,}")
    print(
        "Token cap per call: "
        f"{args.prompt_tokens:,} prompt + {args.completion_tokens:,} completion"
    )
    print(f"Retry multiplier: {retry_multiplier}")
    print()

    total = Decimal("0")
    for entry in configured:
        model = live_models[entry["openrouter_id"]]
        completion_tokens = (
            int(entry.get("budget_completion_tokens", args.completion_tokens))
            if args.use_model_token_budgets
            else args.completion_tokens
        )
        estimate = estimate_for_model(
            model,
            calls_per_model,
            args.prompt_tokens,
            completion_tokens,
            retry_multiplier,
        )
        total += estimate
        pricing = model.get("pricing") or {}
        print(
            f"{entry['label']}: {entry['openrouter_id']} | "
            f"prompt={pricing.get('prompt')} completion={pricing.get('completion')} | "
            f"context={model.get('context_length')} | completion_budget={completion_tokens} | "
            f"estimate={money(estimate)}"
        )

    print()
    print(f"Total estimate: {money(total)}")

    if args.max_cost_usd is not None:
        if total > args.max_cost_usd:
            print(
                f"FAIL: estimate {money(total)} exceeds cap {money(args.max_cost_usd)}",
                file=sys.stderr,
            )
            return 3
        print(f"PASS: estimate is within cap {money(args.max_cost_usd)}")

    if args.include_fallbacks:
        print()
        print("Fallback candidate validation")
        for entry in config.get("fallback_candidates", []):
            model_id = entry["openrouter_id"]
            status = "available" if model_id in live_models else "missing"
            print(f"{status}: {entry['label']} -> {model_id} ({entry['reason']})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
