# Acemoglu Causal Synthetic Laboratory: Confirmatory Results

Date: 2026-08-23  
Status: confirmatory run complete; interpretation bounded to model-system behavior  
Protocol: `acemoglu-causal-preregistration-2026-08-23.md`

## 1. Run integrity

- Design: 8 preregistered cells, 3 model lanes, 8 world replicas, 3 cycles, and 2 role-arm assignments. Automation and capital concentration vary independently within two bundled cost regimes; redistribution cost and repression cost are perfectly confounded.
- Planned and observed rows: 1,152/1,152.
- Valid structured actions: 1,145 (99.39%).
- Errors: 7 (0.61%).
- Complete worlds: 192/192.
- Confirmatory spend: USD 5.425249100 under the separately authorized USD 10 hard cap.
- Inference unit: world, with 10,000 world-cluster bootstrap draws and seed 20260823.

Claude produced no errors. Qwen produced one malformed-JSON error in a worker-coalition response. OpenAI produced four worker-role schema violations and two worker-role timeouts. No capitalist-state policy observation was missing, so primary repression estimands are complete. Errors remain in the dataset and are not manually imputed.

## 2. Primary policy distributions

| Model | Redistribute | Adjudicate | Regulate | Repress | Abstain |
|---|---:|---:|---:|---:|---:|
| Claude Haiku 4.5 | 177 | 14 | 1 | 0 | 0 |
| Qwen 3.7 Max | 189 | 0 | 0 | 3 | 0 |
| OpenAI GPT-5.4 Mini control | 133 | 27 | 7 | 20 | 5 |

The model systems do not implement the same policy response function. Claude is nearly degenerate around redistribution. Qwen is also redistribution-dominant, with three repressive actions confined to C06. OpenAI uses the full policy vocabulary and places 11 of its 20 repressive actions in C08, the high-automation, high-capital cell in the regime combining costly redistribution with cheap repression.

## 3. Preregistered repression estimands

Risk differences are changes in within-world repression share. Intervals are percentile 95% world-cluster bootstrap intervals.

| Model | Automation RD, repression-favoring regime | Automation RD, redistribution-favoring regime | Automation x bundled regime | Capital RD | Automation x capital, repression-favoring regime |
|---|---:|---:|---:|---:|---:|
| Claude Haiku 4.5 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| Qwen 3.7 Max | 0.063 [0.000, 0.188] | 0.000 [0.000, 0.000] | 0.063 [0.000, 0.188] | -0.031 [-0.094, 0.000] | -0.125 [-0.375, 0.000] |
| OpenAI GPT-5.4 Mini control | 0.229 [0.063, 0.396] | 0.021 [0.000, 0.063] | 0.208 [0.042, 0.375] | 0.104 [0.021, 0.188] | 0.208 [-0.125, 0.542] |

### H1: automation in the repression-favoring bundled regime

**Partially supported and model-dependent.** OpenAI shows a positive automation risk difference whose bootstrap interval excludes zero. Qwen shows a weaker nonnegative signal with an interval touching zero. Claude shows no variation. Because costly redistribution and cheap repression are bundled, the design cannot attribute this contrast to either cost separately.

### H2: capital strengthens the automation-repression effect

**Not supported as a cross-model result.** OpenAI's automation-by-capital interaction is positive but imprecise and crosses zero. Qwen's estimate is negative; Claude's is zero.

### H3: repression creates later repressive persistence

**Exploratory signal only; confirmatory inference blocked by sparse support.** In OpenAI, next-cycle repression occurred after 30.8% of repressive decisions and after 9.6% of other decisions. Qwen had only two eligible post-repression transitions, both followed by repression. Claude supplied no repressive transitions. These descriptive contrasts are too sparse and treatment-confounded to identify the preregistered persistence effect.

### H4: redistribution becomes less attractive in the high-cost, high-automation/high-capital setting

**Supported only in the OpenAI control as a behavioral pattern.** OpenAI redistribution falls to 9/24 actions in C08, compared with 15/24 in C05, while repression rises to 11/24. Qwen and Claude remain dominated by redistribution, so the pattern does not generalize across model systems.

### H5: model family moderates effect size

**Strong descriptive support.** The policy distributions and treatment responses differ substantially by model. This is evidence about the tested model systems and routing configuration only. It is not national, cultural, worker, voter, or population evidence.

## 4. Worker-coalition outcome

| Model | Participate | Do not participate | Missing/error |
|---|---:|---:|---:|
| Claude Haiku 4.5 | 0 | 192 | 0 |
| Qwen 3.7 Max | 102 | 89 | 1 |
| OpenAI GPT-5.4 Mini control | 168 | 18 | 6 |

These large differences further demonstrate model-system sensitivity. They cannot be interpreted as calibrated human revolt probabilities.

## 5. Claim gate

The following claim passes:

> In a preregistered synthetic institutional laboratory, identical formal treatment cells generated sharply different policy response functions across three model systems. The OpenAI control exhibited a positive automation-repression response in the bundled regime combining costly redistribution with cheap repression, while Qwen showed a weak localized response and Claude showed none.

The following claims remain blocked:

- that the experiment replicates Acemoglu et al.'s formal theorem;
- that LLM agents are digital twins of workers, states, Argentina, or any population;
- that model-family differences are national or cultural differences;
- that repression causally produces later lock-in based on the sparse observed transitions;
- that the results predict an external institutional trajectory.

The correct current label remains **causal synthetic institutional laboratory**. Promotion to an institutional digital twin still requires external calibration, provenance-bearing state variables, preregistered out-of-sample prediction, reported prediction error, and a defined validity horizon.

## 6. Reproducibility artifacts

- Structured events and errors: `data/confirmatory/events.jsonl` (successful raw response strings and complete provider envelopes were not archived)
- Run manifest: `data/confirmatory/events.run.json`
- Completion summary: `data/confirmatory/events.summary.json`
- Derived analysis: `data/confirmatory/analysis.json`
- Analyzer: `experiments/tribe_v2_phase1/analyze_acemoglu_confirmatory.py`
