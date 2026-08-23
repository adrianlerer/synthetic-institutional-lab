#!/usr/bin/env python3
"""Generate publication figures from the archived confirmatory analysis."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


MODELS = ["claude_haiku_baseline", "qwen37_max", "openai_gpt54_mini_control"]
NAMES = ["Claude Haiku 4.5", "Qwen3.7-Max", "GPT-5.4 mini"]
COLORS = {
    "redistribute": "#2A9D8F",
    "adjudicate": "#457B9D",
    "regulate_automation": "#E9C46A",
    "repress": "#C44536",
    "abstain": "#8D99AE",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("analysis", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.analysis.read_text(encoding="utf-8"))
    args.output_dir.mkdir(parents=True, exist_ok=True)

    cells = [f"C{i:02d}" for i in range(1, 9)]
    matrix = np.array(
        [[data["models"][model]["cell_world_repression_share"][cell] for cell in cells] for model in MODELS]
    )
    fig, ax = plt.subplots(figsize=(9.2, 3.6), constrained_layout=True)
    image = ax.imshow(matrix, cmap="YlOrRd", vmin=0, vmax=0.5, aspect="auto")
    ax.set_xticks(range(len(cells)), cells)
    ax.set_yticks(range(len(NAMES)), NAMES)
    ax.set_xlabel("Preregistered treatment cell")
    ax.set_title("World-level repression share by model system and treatment cell")
    for row in range(matrix.shape[0]):
        for col in range(matrix.shape[1]):
            value = matrix[row, col]
            ax.text(col, row, f"{value:.3f}", ha="center", va="center", color="white" if value > 0.28 else "black", fontsize=8)
    bar = fig.colorbar(image, ax=ax, pad=0.02)
    bar.set_label("Repression share")
    fig.savefig(args.output_dir / "figure1_repression_heatmap.png", dpi=300)
    plt.close(fig)

    policies = ["redistribute", "adjudicate", "regulate_automation", "repress", "abstain"]
    fig, ax = plt.subplots(figsize=(8.6, 4.7), constrained_layout=True)
    left = np.zeros(len(MODELS))
    for policy in policies:
        values = np.array([data["models"][model]["state_policy_counts"].get(policy, 0) / 192 for model in MODELS])
        ax.barh(NAMES, values, left=left, color=COLORS[policy], label=policy.replace("_", " "))
        left += values
    ax.set_xlim(0, 1)
    ax.set_xlabel("Share of capitalist-state decisions")
    ax.set_title("Different model systems implement different institutional policy functions")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.34), ncol=3, frameon=False)
    fig.savefig(args.output_dir / "figure2_policy_distribution.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.8, 4.7), constrained_layout=True)
    y = np.arange(len(MODELS))
    estimates = []
    low = []
    high = []
    for model in MODELS:
        result = data["models"][model]["world_cluster_bootstrap"]["automation_rd_repression_favoring"]
        estimates.append(result["estimate"])
        low.append(result["estimate"] - result["ci95"][0])
        high.append(result["ci95"][1] - result["estimate"])
    ax.errorbar(estimates, y, xerr=[low, high], fmt="o", color="#1D3557", ecolor="#457B9D", capsize=5)
    ax.axvline(0, color="#555555", linewidth=1)
    ax.set_yticks(y, NAMES)
    ax.set_xlabel("Automation risk difference in repression share")
    ax.set_title(
        "Automation effect in the repression-favoring bundled cost regime\n"
        "(world-cluster bootstrap 95% intervals)"
    )
    fig.savefig(args.output_dir / "figure3_automation_effect.png", dpi=300)
    plt.close(fig)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
