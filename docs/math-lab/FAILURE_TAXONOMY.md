# Failure taxonomy

Every failure must become a reproducible record with input hash, source policy,
model version, semantic fingerprint, family, difficulty band, expected
relationship graph, selected renderer and screenshot/log evidence.

| Code | Failure | Gate |
|---|---|---|
| `OCR_MISS` | symbol, choice, unit or diagram text lost | OCR/vision holdout |
| `SEMANTIC_ROLE` | value exists but has wrong role or unit | Pydantic + role oracle |
| `UNKNOWN_LEAKAGE` | requested answer appears as known data | hard reject |
| `RELATIONSHIP_MISS` | values are right but relation/sequence is wrong | relationship graph oracle |
| `FAMILY_FORCED` | unknown problem is silently mapped to a known family | fingerprint/cluster gate |
| `RENDERER_CONTRACT` | renderer selected without required operands | decision-engine readiness gate |
| `VISUAL_FALSEHOOD` | scene is attractive but mathematically misleading | numeric/symbolic + visual oracle |
| `PEDAGOGY_GAP` | answer is correct but intermediate structure is hidden | stage rubric |
| `RUNTIME_5XX` | ingress, provider or service unavailable | health/E2E gate |
| `STATE_LOSS` | account, history or feedback volume disappears | external-volume and backup gate |

Resolved regression `ML-2026-08-27-ADD-EMPTY`: `4+3=?` was classified as
`addition_basic` with empty quantities, while the number-line derivation
defaulted both missing operands to zero. The analyzer now recovers only the two
printed operands, creates a `part_whole` relationship, the decision engine
requires both bindings, and the renderer abstains instead of inventing zeros.

## Regressions resolved on 28/08/2026

Each entry names the code path that failed, the rule that replaced it and the
permanent test that keeps it closed. Every one of them was found by running the
pipeline, not by reading it.

### `ML-2026-08-28-LINEAR-TEMPLATE` — `FAMILY_FORCED`

`3x+y=z` matched none of the three hand-written linear templates
(`ax+b=c`, `ax+by=c`, `ax+by+cz=d`), fell through to the vision model and
reached teachers as an abstention card. The templates were replaced by a
general canonicalizer that parses both sides and subtracts them, so
`3x + y = z` becomes `3x + y − z = 0`: a plane through the origin with normal
`(3, 1, −1)`. `y = 2x + 1`, `5x = 2x + 9`, bracketed equations and systems of
two equations now reach the same path.
Tests: `master_be/test/test_math_lab_linear.py`.

### `ML-2026-08-28-PLANE-INTERCEPTS` — `VISUAL_FALSEHOOD`

The Oxyz scene always drew three axis intercepts. When `d = 0` all three
collapse onto the origin, so the picture asserted three distinct points that do
not exist. The scene now branches on `d = 0`, names the origin as a solution,
draws the normal vector and lists sample points that are re-checked against the
equation before being displayed.
Tests: `mathLabRenderers.test.jsx` — plane through origin, sample points.

### `ML-2026-08-28-UNSUPPORTED-VOCABULARY` — `PEDAGOGY_GAP`

The abstention card printed the internal family slug and an English engine
reason (“No exact deterministic renderer is registered…”). A teacher cannot act
on either. It now states, in Vietnamese, what is missing and what to try, and
the acceptance matrix asserts that no engine vocabulary leaks into it.

### `ML-2026-08-28-FRACTION-SUBTRAHEND` — `SEMANTIC_ROLE`

`ngày 2 bán 3/4 phần còn lại` matched the whole-number subtraction grammar on
the digit `3`, relabelled a two-stage fraction problem as `subtraction_basic`
and drew a confident subtraction scene. The primary word-arithmetic grammar now
abstains whenever the stem prints a fraction.

### `ML-2026-08-28-RATIO-AS-DIVISION` — `FAMILY_FORCED`

The short-expression repair searched the whole stem, so `theo tỉ số 4 : 6`
inside a ratio word problem became a division scene. The repair is now limited
to genuinely short expressions and only fires when the question is actually
missing its operands.

### `ML-2026-08-28-RATIO-PARTS-DROPPED` — `SEMANTIC_ROLE`

Fraction roles were stripped unless the stem printed `a/b`, which deleted the
two ratio parts from `tỉ lệ với 2 và 3` and left a bar model with nothing to
partition. Printed ratio notation now counts as evidence.

### `ML-2026-08-28-BLANK-AS-EQUATION` — `VISUAL_FALSEHOOD`

`Điền số thích hợp: ? + 6 = 12` lost its blank during normalization and parsed
as `6 = 12`, so a grade-2 fill-in-the-blank exercise was reported as a
contradiction. A blank placeholder anywhere in the stem now makes the linear
parser abstain.

### `ML-2026-08-28-UNIT-AS-VARIABLE` — `FAMILY_FORCED`

While stripping a Vietnamese lead-in, a character-level scan restarted parsing
mid-word: `bán kính 12 m` became the expression `12·m`, `2/x = 4` became
`x = 4`, and `x^2 + 1 = 0` became `+1 = 0`. The scan now drops whole words, only
while the dropped word carries no mathematics of its own, and a lifted fragment
must be an equation or have more than one term.

### `ML-2026-08-28-EMPTY-UNKNOWNS` — `RENDERER_CONTRACT`

The two-variable and three-variable recoveries assigned an empty unknown list.
The resulting document could not be re-validated against its own schema, so any
`y = mx + b` stem reaching that path raised a 502. A construction now keeps the
thing it is asked to build — the line, the plane, the tile model — as its
unknown.

### `ML-2026-08-28-SOLVE-RIGHT-TRIANGLE` — `SEMANTIC_ROLE` + `FAMILY_FORCED`

Reported from the live page: `Hãy giải tam giác ABC vuông tại A. Biết AB = 5 cm,
BC = 13 cm. (Góc làm tròn đến phút).` reached a teacher as “not enough data”
with an empty **DỮ KIỆN ĐÃ BIẾT** panel, even though both sides are printed.

The grammar only understood one shape — two legs, find the hypotenuse — and
required an explicit `Tính <đoạn>`. “Giải tam giác” names no single target and
gives a leg plus the **hypotenuse**, so nothing matched, no operand was
recovered, and readiness correctly refused to draw a scene it had no numbers
for. The abstention card was working; the extraction was not.

The grammar now reads every printed side and acute angle of a right triangle,
and the relation records which segment is the hypotenuse — the fact that
decides whether the third side comes from a sum or a difference of squares.
Two legs with only the hypotenuse asked stays `right_triangle_hypotenuse`;
everything else is `right_triangle_solution`, which derives the missing side by
Pythagoras and both acute angles by trigonometry, rounded to minutes when the
question asks for it, and checks that the two acute angles sum to 90°.
A leg longer than the stated hypotenuse draws nothing instead of an imaginary
length.

Tests: `test_math_lab_linear.py::test_solving_a_right_triangle_*`,
`mathLabRenderers.test.jsx` — "solves a right triangle from a leg and the
hypotenuse", matrix cases `g9-right-triangle-solution*`.
