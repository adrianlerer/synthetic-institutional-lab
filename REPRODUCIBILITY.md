# Reproducibility and Provenance

## Computational reproduction

The archived `events.jsonl` file is sufficient to reproduce every numerical result reported in `analysis.json`. The analyzer resamples whole worlds within each treatment cell, preserving the preregistered unit of inference and avoiding event-level pseudoreplication.

## Independent replication

An independent live replication requires access to the named model endpoints. Exact numerical identity is not expected because the endpoints are stochastic, remotely hosted, and mutable. A replication should report:

1. execution date and model identifiers;
2. provider and routing metadata returned by the endpoint;
3. treatment cells, replica count, cycle count, and concurrency;
4. prompt and completion token limits;
5. parser, schema, timeout, and provider errors by model, cell, role, and cycle;
6. raw outputs and the analysis artifact;
7. any difference from the preregistered protocol.

## Design safeguards

- The prompt never exposes a predicted policy, analytic policy score, cell purpose, or hypothesis label.
- State and worker roles receive the same world state but have role-specific admissible outputs.
- Only preregistered treatment fields and mechanically derived state variables differ across paired cells.
- Policy measurement uses structured outputs validated before analysis.
- Missing responses remain missing and are not manually reconstructed.
- The OpenAI lane is reported as a preregistered control and is not retroactively pooled to redefine hypotheses.

## Known limitations

- The study measures model-system behavior, not human behavior.
- Remote endpoints can change without versioned weights or stable sampling semantics.
- Eight replicas per cell provide limited precision for sparse outcomes.
- The persistence comparison after repression is descriptive because repressive transitions are sparse and not separately randomized.
- Provider routing is part of the tested system and a possible source of variation.

