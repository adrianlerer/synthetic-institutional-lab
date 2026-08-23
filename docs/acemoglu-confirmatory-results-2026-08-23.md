# Protocol-Governed Confirmatory Results

## Scope and provenance

- Execution date: 2026-08-23.
- Design: 8 protocol-specified cells, 3 model-provider configurations, 8 world replicas, 3 cycles, and 2 role assignments.
- Scale: 1,152 recorded rows in 192 worlds.
- Valid structured actions: 1,145/1,152 (99.39%).
- Spend: USD 5.43 under the authorized USD 10 hard cap.
- Public chronology: protocol and events first appeared together in commit `fe2290b2`; this is not independent proof of public preregistration.

All seven errors occurred in worker responses. No state-policy observation was missing. Successful raw response strings and complete provider envelopes were not archived.

## State-policy distributions

| Configuration | Redistribute | Adjudicate | Regulate | Repress | Abstain |
|---|---:|---:|---:|---:|---:|
| Claude Haiku 4.5 / Amazon Bedrock | 177 | 14 | 1 | 0 | 0 |
| Qwen3.7-Max / Alibaba | 189 | 0 | 0 | 3 | 0 |
| GPT-5.4 mini / OpenAI | 133 | 27 | 7 | 20 | 5 |

Model and upstream provider are perfectly confounded. Results characterize each tested configuration and do not isolate model-weight or provider effects.

## World-level treatment effects

| Configuration | Automation RD, repression-favoring regime | Automation RD, redistribution-favoring regime | Automation x bundled regime | Capital RD | Automation x capital |
|---|---:|---:|---:|---:|---:|
| Claude Haiku 4.5 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| Qwen3.7-Max | 0.063 [0.000, 0.188] | 0.000 [0.000, 0.000] | 0.063 [0.000, 0.188] | -0.031 [-0.094, 0.000] | -0.125 [-0.375, 0.000] |
| GPT-5.4 mini index system | 0.229 [0.063, 0.396] | 0.021 [0.000, 0.063] | 0.208 [0.042, 0.375] | 0.104 [0.021, 0.188] | 0.208 [-0.125, 0.542] |

Intervals use 10,000 world-cluster bootstrap draws. The primary GPT-5.4 mini automation contrast has a stratified randomization p value of .031. The automation-by-regime interaction has p = .062 and is treated as suggestive.

## Direct model-system contrasts

- GPT-5.4 mini minus Claude, primary automation RD: 0.229 [0.063, 0.396].
- GPT-5.4 mini minus Qwen, primary automation RD: 0.167 [-0.042, 0.354].
- GPT-5.4 mini minus Claude, regime interaction: 0.208 [0.042, 0.375].
- GPT-5.4 mini minus Qwen, regime interaction: 0.146 [-0.063, 0.354].

Model-system moderation is supported against Claude, not established against Qwen.

## Zero-event and persistence sensitivity

Claude's zero-width bootstrap intervals do not prove a future null. The decision-level rule-of-three upper bound is 3/192 = 1.56%; the per-cell any-event bound with eight zero-event worlds is 3/8 = 37.5%.

Persistence remains descriptive:

- GPT-5.4 mini: 4/13 next-cycle repression after repression versus 11/115 after other policies.
- Qwen: 2/2 versus 0/126.
- Claude: no post-repression denominator and 0/128 after other policies.

These transitions are sparse and endogenous, so no causal persistence effect is identified.

## Protocol deviations

Estimands 1-4 were estimated with bundled-cost labels clarified. Planned persistence estimand 5 was downgraded to description. Planned mediation estimand 6 was not estimated because the proposed mediators are deterministic functions of treatment and the required identification assumptions fail. Randomization inference and direct system contrasts were added as robustness checks.

## Claim boundary

The artifact is a causal synthetic institutional laboratory, not a digital twin or a proxy for human populations. It supports configuration-level stress testing. It does not identify separate redistribution-cost and repression-cost effects, provider effects, human preferences, or a stable latent preference of an entire model family.
