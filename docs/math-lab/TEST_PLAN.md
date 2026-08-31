# Math Vision Lab test plan

## Phase 1 automated coverage

- Pydantic validation, unique IDs and reference integrity.
- Confidence/provenance rules for facts and locked constraints.
- Dimension-safe unit normalization and conversion.
- Seven golden grade 1-9 visualization decisions.
- Teacher override compatibility and registry whitelist.
- Motion scene data binding and absence of a hard-coded arrival answer.
- Browser schema rejection of unknown visualizations/references.
- Deterministic world next/previous/reset and bounded What If updates.

## Commands

```bash
cd master_be && PYTHONPATH=. pytest -q test/test_math_lab_foundation.py
cd frontend && npx vitest run src/features/math-lab/mathLabFoundation.test.js
cd frontend && npm test && npm run build
cd master_be && PYTHONPATH=. pytest -q
cd data_storage && PYTHONPATH=. pytest -q
```

Phase 2/3 must add renderer empty/invalid/change-state tests plus real editor
save/load/presentation checks. Phase 4 must add provider-invalid-schema,
timeout and teacher-correction integration tests.

## Playground coverage now implemented

- Registry resolution and unsupported-renderer fallback.
- Motion, clock and timeline synchronization through one progress value.
- Fraction equivalence, subtraction direction, number-line bounds and object
  removal semantics.
- Playback play/pause/reset/replay/scrub behavior.
- Constraint evidence propagation from semantic model to renderer scene.
- Browser acceptance for Motion, Fraction, Number Line and Geometry 2D through
  the real `/api/v1/math-lab/plan` router.
