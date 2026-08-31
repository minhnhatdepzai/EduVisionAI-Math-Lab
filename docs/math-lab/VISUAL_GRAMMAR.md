# Visual grammar

The grammar is intentionally smaller than the family catalog. New problem
families should be composed from these primitives before a new renderer is
created.

| Primitive | Mathematical meaning | Typical renderers |
|---|---|---|
| `object_array` | concrete count, equal groups, rows and columns | object group, grouping, place value |
| `number_line` | ordered magnitude and signed unit movement | number line, number compare |
| `bar_model` | part-whole, ratio, proportional and conserved-work structure | bar model, part-whole |
| `fraction_strip` | equal partition, overlap and percent of a whole | fraction, percent grid |
| `ratio_table` | covarying multiplicative quantities | planned reusable primitive |
| `coordinate_plane` | points, graphs and functional relationships | coordinate graph |
| `geometry_construction` | points, segments, rays, angles and constraints | Geometry 2D, shape pattern |
| `chart` | a shared frequency table and visual scale | data chart |
| `probability_simulation` | trials, outcomes and relative frequency | probability simulator |
| `unit_ladder` | equivalent measures on a conversion scale | unit scale |
| `clock_timeline` | time state and elapsed change | clock, timeline, motion path |
| `balance_scale` | equality preserved by symmetric transformations | balance |
| `algebra_tiles` | signed coefficients grouped by degree | algebra tiles |
| `area_volume_model` | area partition, layers and 3D extent | power model, Geometry 3D |
| `text_overlay` | labels and safe blocked explanations | column algorithm, unsupported |

Each VisualPlan stage must bind to semantic IDs, describe a state delta, keep
the unknown unset until it is derived, and preserve the family invariant. A
fallback is accepted only when it preserves the same relationship graph; visual
similarity alone is not enough.
