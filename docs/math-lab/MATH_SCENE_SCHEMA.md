# Math semantic and scene schemas

The executable Pydantic source is `master_be/app/schemas/math_lab.py`; the
browser mirror is `frontend/src/features/math-lab/schemas/mathLabSchema.js`.

## MathSemanticModel

- `grade`: integer 1-9.
- `domain` and `problem_type`: mathematical classification.
- `entities`, `quantities`, `unknowns`: stable IDs and source data.
- `relations`: named participant references, never free coordinates.
- `constraints`: deterministic relations such as perpendicular or fixed length.
- `Evidence`: confidence, source and `explicit|inferred|uncertain` status.
- `time`: validated 24-hour start/end strings.

All IDs are unique. Relations and constraints cannot refer to missing data.
Low-confidence evidence cannot be promoted to an explicit or locked fact.

## MathScene

- `world`: centralized values with display and canonical units.
- `objects`: renderer-independent semantic objects.
- `visualizations`: whitelisted descriptors and bindings.
- `constraints`: deterministic scene constraints.
- `steps`: `show|hide|set|transform|highlight|explain` reveal operations.
- `actions`: bounded play/pause/reset/navigation/why/what-if actions.
- `verification_status`: starts as `unverified`; only a verifier may promote it.

Unknown fields are rejected by Master. Schema version `1.0` is required.
