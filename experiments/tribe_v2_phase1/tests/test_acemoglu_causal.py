from __future__ import annotations

import json
import unittest

from experiments.tribe_v2_phase1.acemoglu_worlds import (
    CELLS,
    CELLS_BY_ID,
    analytic_baseline,
    differing_paths,
    make_acemoglu_world,
)
from experiments.tribe_v2_phase1.acemoglu_runner import run_fixture
from experiments.tribe_v2_phase1.prompts import build_messages
from experiments.tribe_v2_phase1.schemas import SchemaValidationError, validate_acemoglu_role_action


class AcemogluWorldTests(unittest.TestCase):
    def test_eight_preregistered_cells_are_unique(self) -> None:
        self.assertEqual(len(CELLS), 8)
        treatments = {
            (cell.automation, cell.capital_concentration, cell.redistribution_cost, cell.repression_cost)
            for cell in CELLS
        }
        self.assertEqual(len(treatments), 8)

    def test_world_contains_no_hypothesis_leakage(self) -> None:
        world = make_acemoglu_world("C08", replica=3)
        serialized = json.dumps(world, sort_keys=True).lower()
        for forbidden in ("repression-favoring", "predicted", "strongest", "hypothesis"):
            self.assertNotIn(forbidden, serialized)

    def test_prompt_exposes_treatments_and_causal_state(self) -> None:
        world = make_acemoglu_world("C01")
        messages = build_messages(world, world["agents"][0], 0, "normative_reform")
        payload = json.loads(messages[1]["content"])
        self.assertEqual(payload["world"]["experiment"], "automation_repression_causal")
        self.assertEqual(payload["world"]["treatments"]["automation"], "low")
        self.assertIn("labor_share", payload["world"]["political_economy"])
        self.assertNotIn("baseline_policy", payload["world"]["political_economy"])
        self.assertNotIn("repression_score", payload["world"]["political_economy"])
        self.assertNotIn("fixture_kind", payload["world"]["political_economy"])

    def test_automation_directional_calibration(self) -> None:
        low = analytic_baseline(CELLS_BY_ID["C01"])
        high = analytic_baseline(CELLS_BY_ID["C02"])
        self.assertLess(high["labor_share"], low["labor_share"])
        self.assertGreaterEqual(high["revolt_pressure"], low["revolt_pressure"])

    def test_capital_directional_calibration(self) -> None:
        low = analytic_baseline(CELLS_BY_ID["C01"])
        high = analytic_baseline(CELLS_BY_ID["C03"])
        self.assertLess(high["labor_share"], low["labor_share"])
        self.assertGreaterEqual(high["revolt_pressure"], low["revolt_pressure"])

    def test_lower_repression_cost_does_not_reduce_repression_score(self) -> None:
        costly = analytic_baseline(CELLS_BY_ID["C01"])
        cheap = analytic_baseline(CELLS_BY_ID["C05"])
        self.assertGreater(cheap["repression_score"], costly["repression_score"])

    def test_coercive_infrastructure_increases_lock_in(self) -> None:
        cell = CELLS_BY_ID["C08"]
        none = analytic_baseline(cell, coercive_infrastructure=0.0)
        accumulated = analytic_baseline(cell, coercive_infrastructure=0.8)
        self.assertGreater(accumulated["institutional_lock_in"], none["institutional_lock_in"])

    def test_treatment_pair_changes_only_declared_and_derived_fields(self) -> None:
        low = make_acemoglu_world("C01", replica=0)
        high = make_acemoglu_world("C02", replica=0)
        paths = differing_paths(low, high)
        allowed_prefixes = (
            "world_id",
            "treatments.automation",
            "political_economy.",
        )
        unexpected = sorted(path for path in paths if not path.startswith(allowed_prefixes))
        self.assertEqual(unexpected, [])

    def test_no_spend_runner_covers_all_cells_and_accumulates_lock_in(self) -> None:
        rows = run_fixture(replicas=1, cycles=3)
        self.assertEqual(len(rows), 8 * 1 * 3 * 2)
        self.assertEqual({row["cell_id"] for row in rows}, set(CELLS_BY_ID))
        self.assertTrue(all(row["cost_usd"] == 0.0 for row in rows))
        repressive = [
            row for row in rows
            if row["role"] == "capitalist_state" and row["policy_choice"] == "repress"
        ]
        self.assertTrue(repressive)
        self.assertTrue(any(row["coercive_infrastructure_reliance"] > 0 for row in repressive))

    def test_role_validator_blocks_worker_policy_and_missing_revolt_choice(self) -> None:
        rows = run_fixture(replicas=1, cycles=1)
        worker = next(row for row in rows if row["role"] == "worker_coalition")
        invalid = dict(worker, policy_choice="redistribute", revolt_choice="not_applicable")
        with self.assertRaises(SchemaValidationError):
            validate_acemoglu_role_action(invalid, "worker_coalition")


if __name__ == "__main__":
    unittest.main()
