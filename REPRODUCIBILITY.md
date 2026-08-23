# Reproducibility and Provenance

## Computational reproduction

The archived structured `events.jsonl` file is sufficient to reproduce every numerical result reported in `analysis.json`. It contains validated action fields and error records, but not successful raw response strings or complete provider envelopes. The analyzer resamples whole worlds within each treatment cell, preserving the protocol-specified unit of inference and avoiding event-level pseudoreplication. It also runs stratified randomization inference and direct cross-model bootstrap contrasts.

## Independent replication

An independent live replication requires access to the named model endpoints. Exact numerical identity is not expected because the endpoints are stochastic, remotely hosted, and mutable. A replication should report:

1. execution date and model identifiers;
2. provider and routing metadata returned by the endpoint;
3. treatment cells, replica count, cycle count, and concurrency;
4. prompt and completion token limits;
5. parser, schema, timeout, and provider errors by model, cell, role, and cycle;
6. raw response text, validated structured events, provider envelopes where permitted, and the analysis artifact;
7. any difference from the frozen analysis protocol.

## Design safeguards

- The prompt never exposes a predicted policy, analytic policy score, cell purpose, or hypothesis label.
- State and worker roles receive the same world state but have role-specific admissible outputs.
- Only protocol-specified treatment fields and mechanically derived state variables differ across paired cells.
- Policy measurement uses structured outputs validated before analysis.
- Missing responses remain missing and are not manually reconstructed.
- The GPT-5.4 mini lane is reported as the primary index system; model-specific results remain separate and direct cross-system contrasts are reported.

## Public chronology limitation

The protocol and confirmatory structured events were first published in the same Git commit, `fe2290b2`. The package should therefore be described as protocol-governed, not as independently publicly preregistered.

## Known limitations

- The study measures model-system behavior, not human behavior.
- Remote endpoints can change without versioned weights or stable sampling semantics.
- Eight replicas per cell provide limited precision for sparse outcomes.
- Redistribution cost and repression cost are perfectly confounded in two bundled regimes; the separate effect of either cost is not identified.
- The persistence comparison after repression is descriptive because repressive transitions are sparse and not separately randomized.
- Provider routing is part of the tested configuration and a possible source of variation. Its separate causal effect was not identified because route was not independently randomized.
- Successful raw response text and complete provider envelopes were not archived in this run, limiting forensic replay even though deterministic statistical reproduction is possible.
