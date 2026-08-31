# Controlled autolearning

Math Lab does not update production weights from an unreviewed teacher click.
Feedback is stored as `pending_review`; this is intentional safety, not a
missing reinforcement-learning loop.

## Implemented foundation

- feedback with semantic model and scene is versioned in PostgreSQL;
- recent exercises are isolated in Redis;
- source policies and immutable dataset versioning are enforced;
- semantic fingerprints ignore wording, names and numbers;
- unknown structures remain `UNKNOWN_CLUSTER`;
- candidate families require a configurable frequency gate;
- saturation requires three consecutive batches of at least 500 questions per
  grade with a new-family rate below 0.5%.

Commands:

```bash
python training/math_lab/discovery/discover_sources.py
python training/math_lab/discovery/normalize_questions.py INPUT OUTPUT
python training/math_lab/discovery/cluster_questions.py INPUT
python training/math_lab/discovery/classify_families.py INPUT OUTPUT
python training/math_lab/discovery/discover_new_families.py INPUT --minimum-frequency 5
python training/math_lab/discovery/audit_family_saturation.py INPUT
python -m training.math_lab.autolearn run
python training/math_lab/benchmarks/run_model_league.py
```

## Promotion gate (not yet automated end to end)

`feedback -> anonymize -> human review -> immutable dataset -> base/adapter
league -> holdout -> schema and visual oracle -> canary -> rollback`.

SFT is eligible for semantic extraction and relationship planning. DPO is
eligible only after reviewed preference pairs exist. RL is blocked until a
deterministic reward suite covers semantic correctness, invariant preservation,
visual faithfulness and pedagogy; no production RL job currently runs.
