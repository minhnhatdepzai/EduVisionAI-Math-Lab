# Claude Code master prompt — Math Vision Lab grade 1–9

Copy the block below into Claude Code from the repository root.

```text
Use the project skill `/math-lab-grade-1-9` now. Before any action, read
`.claude/skills/math-lab-grade-1-9/SKILL.md` and all three files under its
`references/` directory completely. Then read the current Math Lab source and
the required docs named by the skill. Do not rely on README claims when code or
runtime evidence differs.

MISSION

Act as Principal Full-stack Engineer, ML/Vision Engineer, Vietnamese grade 1–9
math curriculum specialist, EdTech pedagogy designer and visualization QA lead.
Continue working autonomously until the versioned Math Lab acceptance catalog
passes end to end. Do not stop after an audit, plan, list of recommendations or
one repaired example. Inspect, reproduce, implement, test, deploy the isolated
demo, operate the real web page, fix regressions and document verified results.

HARD SCOPE

Modify only Math Lab paths permitted by the skill. Preserve all unrelated dirty
worktree changes. Do not alter login, classroom, lesson editor, camera, voice or
general user-state behavior. Do not delete Docker volumes, teacher history,
feedback, credentials, raw data or checkpoints. Never expose tokens or
`kaggle.json`. You may prioritize the isolated Math Lab demo on port 8443 and
stop only exact conflicting EduVision containers after resolving their names;
never kill unrelated user processes or erase their data.

CURRENT P0 REGRESSION

Reproduce this exact input on `https://localhost:8443/#/math-lab`:

    3x+y=z

It is not a one-variable equation and is not unsupported. Implement a general
linear-expression canonicalizer that collects variable coefficients on both
sides:

    3x + y = z  ->  3x + y - z = 0

Classify it as a three-variable linear equation and visualize the plane through
the origin on Oxyz with normal vector (3,1,-1). Because all three axis
intercepts coincide at O, do not fabricate three distinct intercepts. Show a
translucent plane, Oxyz axes with equal scale, the origin, normal direction and
several sample points verified against `3x+y-z=0`. Explain that there are
infinitely many solutions; do not invent unique x, y or z values.

Add permanent regressions for at least:

- `2x+1` -> algebra tiles;
- `2x+3=9` -> balance with identical operations on both sides;
- `2x+y=1`, `y=2x+1` -> line on Oxy;
- `3x+y=z`, `x+y=z`, `3x+y+z=6`, `-2x+4y-z=8` -> planes on Oxyz;
- systems of two equations -> lines and intersection/no-intersection/coincident
  states as mathematically appropriate.

Do not special-case only these strings. Support spaces, implicit coefficients,
signs, decimals/fractions, variables on either side, Vietnamese prefixes, image
OCR and old-history migration. Reject nonlinear expressions from the linear
family without crashing.

GRADE 1–9 COVERAGE MISSION

Regenerate and audit the executable family catalog. Exercise every observed
family from grade 1 through 9, including every currently partial/missing family,
and add newly discovered exam families instead of hiding them behind a generic
fallback. For each family create accented, unaccented/reordered, unseen-number,
clean-image, degraded-image, boundary and adversarial near-family cases. Split
holdout by template/stem so paraphrases do not leak between train and test.

The release catalog must have:

- zero `unsupported` for valid in-catalog questions;
- zero required `quantities=[]`, unsupported units or unresolved references;
- zero HTTP 5xx, timeout, connection-close/refused or blank renderer;
- zero misleading generic fallback;
- 100% schema validity and zero requested-answer leakage;
- 100% curated browser matrix pass, with per-grade and per-family totals.

Do not make the logically impossible claim that unseen mathematics can never
fail. Instead make the acceptance catalog broad, versioned and measurable, run
a saturation/discovery audit, and make out-of-catalog/ambiguous inputs degrade
to a calm Vietnamese clarification rather than a technical error.

VISUAL DIFFERENTIATION

The product must be visibly different from an ordinary text solution. Every
valid question must automatically select a meaningful model and play it without
asking teachers to inspect semantic data. Use bordered and labelled scenes;
contextual objects; equal groups/arrays; number lines; fraction bars/area grids;
ratio bars; place-value blocks; column algorithms; algebra tiles; balance
scales; tables/charts; clocks; timelines; routes; Oxy graphs; Oxyz planes;
geometric marks and 3D layers as appropriate.

Each result needs 3–6 clear stages:

1. highlight givens and what is sought;
2. build the mathematical picture with labels attached to the right objects;
3. animate/reveal the valid operation or invariant;
4. show intermediate reasoning, not only the answer;
5. conclude and visually check by substitution/conservation/recomposition.

Every step must change visible mathematical state or reveal a necessary
annotation. Keep one world state across playback, step previous/next, scrub,
speed and reset. Prevent overlapping labels, unreadable hundreds of ticks,
decorative-only illustrations and answer cards pretending to be simulations.

ARCHITECTURE RULE

The VLM extracts an evidence-backed `ProviderDocument`; strict Pydantic code
normalizes semantics; a deterministic decision engine and readiness gate select
registered renderers; a pedagogy planner builds steps; React/SVG/Canvas/Three.js
renders from the same MathWorldState. The model must not generate UI code or
coordinates. A schema-valid payload missing required operands is still a
failure. Narrow deterministic recovery may copy only facts printed in the
source and must never copy the unknown answer into givens.

REAL FINE-TUNING, NOT LABELING

Audit and expand `training/math_lab` from real reviewed failures and licensed
deterministic data. Fine-tune only semantic extraction on the production target
Qwen3-VL 8B using the checked-in QLoRA protocol. Keep evaluation-only datasets
out of training and protect credentials/private images. Run the VRAM gate and
do not terminate other users' GPU processes.

You may say “fine-tuned” only after an actual non-smoke run produces a hashed
checkpoint, processor/config, training/eval metrics and beats or matches the
base model on untouched holdout while meeting: schema 100%, leakage 0%, semantic
roles >=99%, renderer selection >=98% overall and >=95% each family, with all
visual/API/browser gates passing. A 4B one-step checkpoint is only a smoke. Do
not deploy an adapter merely because train loss decreased. Use canary + rollback.

Teacher feedback remains pending review. Implement the safe offline loop:
redact -> review -> immutable dataset -> SFT/DPO -> holdout -> canary ->
promote/rollback. Never update live weights from one unreviewed click.

REQUIRED VERIFICATION

Run all commands and gates from the skill references, including backend tests,
the full frontend suite, production build, SFT audit, coverage audit and
relevant persistence tests. Build images while the existing web remains
available, then replace only Math Lab containers. Test analyze + plan through
real HTTPS 8443 and use a real Chromium session for representative text and
image cases from every grade plus every P0 regression. Assert visible objects,
labels, step changes and conclusions; HTTP 200 alone is not success. Inspect
logs for 5xx/tracebacks and keep port 8443 healthy at handoff.

DELIVERABLES

1. Working scoped code, not pseudocode.
2. Versioned grade 1–9 manifest and matrix runner.
3. Permanent analyzer/plan/renderer/browser regressions for every failure.
4. Exact visual renderers and pedagogy steps for all catalog families.
5. Honest training artifacts and base-vs-adapter report, or a precise statement
   that production fine-tuning remains pending and why.
6. Updated Math Lab README, coverage matrix, failure taxonomy and evidence.
7. Final report with changed files, commands, exact pass counts, per-grade and
   per-family results, deployed bundle/container health, screenshots and all
   remaining limitations. Do not report completion while any required gate is
   failing.
```

## Invocation

From the repository root, start Claude Code and either paste the block above or
run `/math-lab-grade-1-9`, then provide the mission beginning at `MISSION`.
