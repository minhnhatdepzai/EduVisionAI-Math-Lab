# Visual architecture

Math Lab uses a typed intermediate plan so a model never writes UI code:

```text
image/text
  -> ProviderDocument
  -> MathSemanticModel (entities, quantities, unknowns, relationships, constraints)
  -> VisualDecision
  -> VisualConcept + VisualPlan
  -> PedagogyPlan
  -> MathScene / MathWorldState
  -> deterministic React renderer
```

`MathSemanticModel` is the mathematical source of truth. `VisualPlan` records
the primary concept, reusable primitive, stage bindings, state deltas and the
oracle checks each stage must pass. `MathScene` remains the runtime contract.
The same world value is reused by every view; a bar, counter group and number
line cannot hold separate copies of the same operand.

## Current implementation status

| Component | Status | Evidence |
|---|---|---|
| Strict semantic/world/scene schemas | Implemented | Pydantic and frontend validation tests |
| Relationship graph | Partial | Runtime supports typed references; short arithmetic now creates `part_whole` or `equal_groups`; the VLM contract does not yet emit every relationship family |
| VisualConcept/VisualPlan compiler | Implemented | Backend response and scene metadata contain concepts, stages, primitive bindings and required checks |
| Deterministic renderers | Implemented for catalog rows marked exact | 23 visual renderer IDs plus safe `unsupported` |
| Numeric/symbolic oracle execution | Partial | Renderer-derived arithmetic and invariant tests exist; the new VisualPlan check list is recorded but no general oracle service executes every check yet |
| Browser visual regression | Partial | Real Chrome smoke cases exist; a full family-by-difficulty screenshot matrix is not yet automated |

`unsupported` is a blocked VisualPlan, not a successful visualization. A green
product badge is valid only when the plan is ready and the renderer contract
has all operands.
