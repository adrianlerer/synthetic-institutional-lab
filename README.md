# Causal Synthetic Institutional Laboratory

This repository contains the complete replication package for the protocol-governed experiment reported in **When Synthetic Institutions Repress: A Protocol-Governed Causal Laboratory of Automation, Capital Concentration, and Model-Specific Governance**.

The experiment tests how three language-model systems choose among regulation, redistribution, adjudication, abstention, and repression under controlled changes in automation and capital concentration within two bundled cost regimes. Redistribution cost and repression cost move together in opposite directions, so their separate effects are not identified. It studies **model-system behavior under interventions**. It does not model real people, estimate population preferences, or claim to be a digital twin of any society.

## Confirmatory Run

- 8 protocol-specified treatment cells
- 3 model systems
- 8 independent world replicas per cell and model
- 3 sequential cycles
- 2 role-specific decisions per cycle
- 1,152 recorded rows across 192 worlds
- 1,145 valid structured actions (99.39%)
- 10,000 world-cluster bootstrap draws, seed `20260823`

The exact model identifiers used on 23 August 2026 were:

- `anthropic/claude-haiku-4.5`
- `qwen/qwen3.7-max`
- `openai/gpt-5.4-mini`

Model endpoints are mutable external services. Re-running the code later may test a later provider snapshot even when the identifier is unchanged. The archived event file is therefore the canonical record of the reported run.

## Repository Map

- `docs/acemoglu-causal-preregistration-2026-08-23.md`: frozen design, hypotheses, estimands, and claim gates.
- `docs/acemoglu-confirmatory-results-2026-08-23.md`: bounded results report.
- `data/confirmatory/events.jsonl`: validated structured actions and error records. Successful raw response strings and complete provider envelopes were not archived.
- `data/confirmatory/events.run.json`: run manifest and treatment cells.
- `data/confirmatory/events.summary.json`: completion and cost summary.
- `data/confirmatory/analysis.json`: derived world-level estimates and bootstrap intervals.
- `experiments/tribe_v2_phase1/prompts.py`: exact prompt builder.
- `experiments/tribe_v2_phase1/paid_acemoglu.py`: guarded live runner.
- `experiments/tribe_v2_phase1/analyze_acemoglu_confirmatory.py`: deterministic analysis.
- `experiments/tribe_v2_phase1/make_figures.py`: publication figures generated from the analysis artifact.
- `experiments/tribe_v2_phase1/tests/test_acemoglu_causal.py`: treatment-isolation and calibration checks.

## Reproduce the Published Analysis

Python 3.11 or later is recommended. The analysis uses only the Python standard library.

```bash
python3 experiments/tribe_v2_phase1/analyze_acemoglu_confirmatory.py \
  data/confirmatory/events.jsonl \
  --output /tmp/analysis.json

cmp data/confirmatory/analysis.json /tmp/analysis.json
```

No API key and no paid model call are required to reproduce the reported statistics.

Publication figures can be regenerated with Matplotlib:

```bash
python3 experiments/tribe_v2_phase1/make_figures.py \
  data/confirmatory/analysis.json \
  --output-dir figures
```

## Run the Tests

```bash
python3 -m unittest discover -s experiments/tribe_v2_phase1/tests -v
```

## Execute a New Paid Run

This is optional and incurs third-party API charges. Obtain your own OpenRouter key and set a hard budget before running:

```bash
export OPENROUTER_API_KEY='your-own-key'
export TRIBE_MAX_COST_USD='10'

python3 experiments/tribe_v2_phase1/paid_acemoglu.py \
  --model-labels claude_haiku_baseline,qwen37_max,openai_gpt54_mini_control \
  --replicas 8 \
  --cycles 3 \
  --concurrency 4 \
  --retries 1 \
  --purpose independent_replication \
  --output output/replication/events.jsonl \
  --confirm-paid-run
```

Never commit an API key. Provider availability, pricing, routing, and model behavior may differ from the archived 2026 run.

## Interpretation Boundary

The package supports the following bounded computational claim: controlled institutional treatments generated materially different observed policy-response functions across the tested configurations. The GPT-5.4 mini index system displayed a positive automation-repression response in the bundled regime combining costly redistribution with cheap repression; that response exceeded Claude's but did not conclusively exceed Qwen's.

## Protocol chronology

The analysis protocol was frozen locally before the paid run, but the protocol and structured event file first received a public Git timestamp together in commit `fe2290b2` after execution. The repository supplies an auditable protocol and reproducible analysis, not independent proof of public preregistration.

It does not support claims that:

- the agents represent workers, voters, countries, or cultures;
- the experiment validates the external behavior of a real institution;
- model differences are national or cultural differences;
- the laboratory is an institutional or societal digital twin;
- the run independently proves or replicates the formal theorem that motivated the treatment design.

## Licenses

Code is released under the MIT License. Documentation and the archived dataset are released under CC BY 4.0. Model outputs may remain subject to the applicable provider terms.

## Citation

Please cite the associated paper and this repository. A machine-readable citation is provided in `CITATION.cff`.
