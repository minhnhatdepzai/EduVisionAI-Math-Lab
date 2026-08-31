# Math Vision Lab implementation plan

## Architectural decisions

1. Master Backend is the trust boundary for Math Lab contracts and planning.
2. `math_scene` will be an additional Lesson object type, not a second editor.
3. Saved state is renderer-neutral JSON. React, SVG and Three.js are consumers.
4. Rule-based selection is authoritative; future AI may suggest only registered
   visualization IDs.
5. All arithmetic and unit conversion is deterministic and testable.
6. The current JavaScript frontend uses JSDoc contracts plus runtime validators;
   adding a partial TypeScript toolchain would increase risk without improving
   the existing editor boundary.

## Phase 0 - audit and documentation

- Document current frontend, Master, Data Storage, Worker, AI, lesson editor,
  persistence, presentation and Three.js architecture.
- Record reuse points, risks and validation commands.
- Deliver all documents under `docs/math-lab/`.

## Phase 1 - foundation (this change)

### Backend

- Add Pydantic contracts for semantic entities, quantities, relations,
  unknowns, provenance/confidence, MathScene objects, visualization descriptors,
  world variables, constraints, actions and reveal steps.
- Add a grade-aware unit converter for length, mass, time, area, volume and
  speed.
- Add a visualization registry for the original 12 MVP engines; production now
  has a thirteenth dedicated `power_model` engine.
- Add a deterministic visual decision engine and Pedagogy Planner.
- Add a foundation service and authenticated teacher endpoint that converts a
  semantic model into a validated plan and renderer-neutral initial scene.
- Add golden and unit tests.

### Frontend

- Add matching JSDoc contracts and strict runtime normalization.
- Add a serializable MathWorldState reducer with set/reset/step operations.
- Add a whitelisted visualization registry contract.
- Add a service client for the Phase 1 planning endpoint.
- Do not add a visible panel or editor object renderer until Phase 2/3.

### Expected files

```text
master_be/app/schemas/math_lab.py
master_be/app/services/math_lab/
master_be/app/api/math_lab.py
master_be/test/test_math_lab_*.py
frontend/src/features/math-lab/
frontend/src/services/api.js
docs/math-lab/*.md
```

## Phase 2 - core 2D visualizers (playground implemented)

Implement Number Line, Fraction, Clock, Timeline, Motion Path and Geometry 2D
as small renderers reading the same MathWorldState. Include empty/invalid scene
fallbacks and accessible DOM equivalents. The teacher-only `#/math-lab`
playground now exposes these renderers plus Object Group, ten deterministic
fixtures, shared playback, teacher visibility overrides and a state inspector.
Lesson-canvas persistence remains Phase 3.

## Phase 3 - Lesson canvas integration

Add the `math_scene` Lesson object, toolbar insertion, Inspector controls,
SlideView rendering and presentation playback. Reuse existing object move,
resize, duplicate, delete, history, autosave and version serialization.

## Phase 4 - Math Vision pipeline

Add provider-neutral OCR/VLM adapters in Master, image/text upload endpoints,
structured output validation, teacher correction UI and explicit/inferred/
uncertain provenance handling. No provider output reaches the renderer without
validation.

## Phase 5 - interaction

Add play, pause, reset, previous/next reveal step and bounded What If controls.
Animation derives from centralized world state and is cancelled on unmount.

## Phase 6 - advanced visualizations (implemented for registered MVP types)

Add Object Group, Array/Grouping, Bar Model, Balance, Coordinate Graph and
Geometry 3D using the same registry and state contracts.

## Phase 7 - sketch beautification

Capture strokes and implement simplification, primitive classification,
snapping and deterministic constraints for point, line, arrow, circle,
rectangle and triangle.

## Phase 1 validation gates

- Pydantic rejects unknown fields, invalid grades, duplicate IDs, invalid
  references, incompatible units and unregistered visualization IDs.
- Unit conversions are dimension-safe.
- Golden cases select the expected primary/supporting visualizations.
- MathWorldState has one source of truth and deterministic reset/step behavior.
- Frontend tests and production build pass for Phase 1 modules.
- Master tests for Phase 1 pass; existing-suite status is reported separately.
- No AI SDK, new UI framework or second 3D engine is added.
