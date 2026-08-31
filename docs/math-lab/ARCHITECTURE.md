# Math Vision Lab architecture

## Phase 1 data flow

```text
Validated MathSemanticModel
        | deterministic rules
        v
VisualDecisionEngine --> VisualizationRegistry
        |
        v
PedagogyPlanner
        |
        v
MathLabFoundationService
        |
        v
MathScene + one MathWorldState
```

Master Backend is authoritative. The frontend mirrors the schema to reject bad
cached/local data before a renderer mounts. Future AI providers may populate a
semantic model but cannot emit renderer code or bypass validation.

## Boundary decisions

- `MathScene` is renderer-neutral and serializable inside a Lesson object.
- `MathWorldState.values` is the only mathematical state. A visualization owns
  view state such as focus or camera angle, never its own distance/time/value.
- Registry IDs are a whitelist and not component names supplied by a model.
- Units normalize in Master; renderers receive display and canonical values.
- Phase 1 adds no database table, AI SDK, UI framework or 3D dependency.
- Because the existing frontend is JavaScript, JSDoc plus runtime validation is
  used. A one-feature TypeScript build would split the editor type system.

## Future editor object

```json
{
  "id": "obj-...",
  "type": "math_scene",
  "x": 180,
  "y": 120,
  "w": 1200,
  "h": 720,
  "scene": { "schema_version": "1.0" }
}
```

Existing Lesson reducer and SlideView will provide move, resize, duplicate,
delete, undo, redo, save, load and presentation behavior.
