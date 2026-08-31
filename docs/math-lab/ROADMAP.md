# Math Vision Lab roadmap

1. **Current:** 28 registered visual renderers plus the safe `unsupported`
   state. Exact family support is tracked separately in
   `VISUAL_COVERAGE_MATRIX.md`; registry presence is not a coverage claim.
2. `math_scene` Lesson object and Math Lab teacher panel with save/load,
   resize/move, history and Presentation support.
3. Provider-neutral image/text analysis and correction workflow.
4. Playback, reveal, Why and What If controls.
5. **Implemented:** object grouping, bar model, balance, coordinate graph and
   dimensioned Geometry 3D.
6. Sketch simplification, primitive detection, snapping and constraints.
7. Addition carrying, subtraction borrowing and long division. Multiplication
   arrays plus fraction addition/subtraction/multiplication transformations are
   implemented.
8. Pythagorean area proof, cube unfold/fold, unit cubes and 3D cross sections.
   The `(a+b)^2` algebra area model is implemented.
9. **Implemented in the observed baseline:** probability simulations,
   statistics charts, ratio, percent, measurement, linear systems, solution
   sets, grade-9 trigonometric geometry and one-quadratic-variable Oxyz
   surfaces. Transformations and symmetry remain discovery/catalog work.
10. Evidence-backed AI Why, Hint and student experimentation analytics.

Every phase keeps one MathWorldState, uses only registered renderers and must
pass existing editor/presentation tests before it is complete.
