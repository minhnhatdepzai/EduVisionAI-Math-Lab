# EduVisionAI architecture audit for Math Vision Lab

## Scope and branch

This audit targets `FE-update-and-remove-` after merging `origin/main` at
`ac16a9b`. Math Vision Lab must extend the existing lesson system; it must not
become a separate demo application.

## Runtime topology

| Area | Current implementation | Math Lab consequence |
|---|---|---|
| Frontend | React 19, Vite 6, JavaScript/JSX, CSS Modules, custom hash router | Keep JavaScript and use JSDoc plus runtime validation instead of introducing TypeScript only for one feature. |
| Master API | FastAPI and Pydantic; owns auth, RBAC and orchestration | Own validated Math Lab contracts, deterministic planning and future vision-provider selection. |
| Data Storage | FastAPI, SQLAlchemy, PostgreSQL, Redis, MinIO and Qdrant | Phase 1 needs no new table. A MathScene is serialized inside existing Lesson JSON and versioned in MinIO. |
| Worker | Python room runtime with image, voice and intent pipelines | Existing camera processing can become an input source later, but Math Vision is not implemented and slow-path tasks are currently skipped. |
| Document Renderer | Office import and Lesson-to-PDF conversion | A future static MathScene PDF fallback belongs here, not in Phase 1. |
| Realtime | NATS JetStream plus Master gateways | Future collaborative/presentation state may reuse this; per-frame mathematical animation remains local and deterministic. |

## Lesson editor and persistence

- `frontend/src/modes/edit/useLessonEditor.js` owns Lesson state with a reducer,
  a 40-checkpoint undo/redo history, clipboard, slide duplication and autosave.
- Each slide has an `objects` array. Existing object types include text, shape,
  arrow, image, video and illustration. Objects share `id`, `x`, `y`, `w`, `h`
  and optional rotation/style fields.
- `EditorCanvas` and `SlideView` already implement selection, move, resize,
  multi-selection and keyboard-accessible presentation targets.
- `PresentationMode` renders the same saved slide objects through `SlideView`.
  A `math_scene` renderer added there will therefore work in edit and
  presentation without a second canvas.
- Master stores immutable Lesson version JSON in MinIO. PostgreSQL keeps Lesson
  and LessonVersion metadata. Draft autosave and optimistic version checks
  already exist.
- Current content validation only checks for an object with a `slides` array
  and optional `canvas` object. MathScene needs its own strict validator before
  it is accepted from AI or a future Math Lab panel.

## State management

The frontend has no global state library. Domain state is kept in React hooks
and reducers. A MathScene must therefore have one serializable
`MathWorldState`, plus local playback state derived from it. Renderers read the
same state and never keep independent mathematical values.

## AI and computer vision

- The browser does not call an AI vendor directly.
- Worker image pipelines handle classroom perception and interaction, not OCR
  or mathematical interpretation.
- The Worker intent router identifies fast versus slow tasks, but the slow AI
  agent path is intentionally not implemented.
- Master now owns the configured Ollama Math Vision adapter for text/image
  analysis. Structured provider output is validated by strict Pydantic DTOs,
  normalized into the semantic model and shown for teacher review before a
  scene is planned.
- Planning and rendering remain provider-neutral and deterministic: AI never
  supplies HTML, JavaScript or renderer code.

## Three.js reuse

- Three.js `0.163` and `@google/model-viewer` are already installed.
- `LazyScene` lazy-loads Three.js, selects a capability tier, pauses when hidden
  and disposes WebGL resources.
- `SlideView` already supports GLB illustration objects.
- The bounded cuboid/volume renderer uses an SVG x-y-z projection, so it works
  without WebGL and remains printable. Future free rotation, cross-sections or
  imported solids should reuse `LazyScene` and retain this SVG fallback.

## API and authorization boundary

- Public routes use `/api/v1` and dependency-injected authenticated principals.
- Teacher-only Lesson editing is enforced by Master. Frontend role controls are
  only a user-experience guard.
- The teacher-guarded planning and text/image analysis endpoints accept
  validated input and return deterministic semantic/scene contracts.

## Reusable components

- Lesson object geometry, selection and resize fields.
- Lesson reducer checkpoints for undo/redo and object duplication.
- Lesson version save/load/autosave and Presentation `SlideView`.
- FastAPI/Pydantic schema conventions and dependency-injected services.
- Existing Three.js lazy/capability/disposal layer.
- Existing UI controls, CSS tokens and accessibility conventions.

## Required additions

1. Strict `MathSemanticModel`, `MathScene`, `MathWorldState` and `MathStep`
   contracts in Master and matching browser runtime contracts.
2. Central unit normalization for grade 1-9 quantities.
3. A visualization registry with whitelisted IDs and parameter validators.
4. A rule-first visual decision engine with confidence and traceable reasons.
5. A grade-aware Pedagogy Planner that returns representations, interaction
   strategy and reveal steps.
6. A deterministic foundation endpoint and tests; no vendor AI and no fake
   mathematical answer.

## Technical risks

- The merged feature branch contains two generations of RBAC/classroom files;
  some legacy-only test modules currently conflict with the newer `main`
  architecture. Math Lab changes must be isolated and the final validation
  report must distinguish merge-baseline failures from Math Lab failures.
- Lesson objects are intentionally flexible JSON. Without explicit MathScene
  validation, invalid provider output could be persisted.
- JavaScript cannot provide TypeScript compile-time guarantees. Runtime schema
  validation and JSDoc types are required until the frontend is migrated as a
  whole.
- 3D and AI dependencies are large. Phase 1 adds neither a new 3D engine nor an
  AI SDK.
- Mathematical animation state must not be persisted every frame or broadcast
  through React at frame rate.
