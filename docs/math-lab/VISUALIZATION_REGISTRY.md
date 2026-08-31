# Visualization registry

The production registry currently exposes thirteen renderer IDs:

```text
object_group · number_line · grouping · bar_model · fraction · power_model · clock
timeline · motion_path · balance · geometry_2d · coordinate_graph · geometry_3d
```

Each backend definition declares supported domains and grade range. The visual
decision engine returns ranked decisions with a score, reason and source. A
teacher override is accepted only when the requested ID is registered and
compatible with the semantic model.

The frontend registry has working React/SVG/CSS/Three.js renderers for all thirteen IDs.
Operation-specific visual semantics include equal groups, equal-part ratio
bars, common-denominator fraction addition/subtraction, fraction-product
intersection grids, equation balance, function slope/point tables and a
dimensioned cuboid on x-y-z axes. `power_model` shows repeated factors, sign,
separate numerator/denominator powers and a bounded magnitude model. Unknown IDs still fail closed; provider HTML,
JavaScript, shaders or component paths are never accepted.
