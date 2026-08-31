# Visual coverage matrix

Generated from catalog version `math-family-catalog-v3`
by `training/math_lab/scripts/build_coverage_docs.py`.
The frontend registry contains 27 IDs including `unsupported`;
registry presence alone is not counted as family readiness.

| Renderer | Observed families | Exact SFT | Renderer-only | Partial | Missing | Families |
|---|---:|---:|---:|---:|---:|---|
| `algebra_tiles` | 3 | 3 | 0 | 0 | 0 | `polynomial_evaluate_reorder`, `polynomial_add_subtract`, `algebraic_expression_modeling` |
| `balance` | 4 | 3 | 1 | 0 | 0 | `linear_equation`, `compound_linear_equation`, `word_equation_rectangle`, `fractional_linear_equation` |
| `bar_model` | 7 | 7 | 0 | 0 | 0 | `multi_step_arithmetic_word`, `ratio_total_parts`, `arithmetic_mean`, `proportional_system_two_variables`, `sequential_fraction_remainder_ratio`, `sequential_fraction_remainder_quantity`, `work_rate_with_variable_people` |
| `calendar` | 1 | 1 | 0 | 0 | 0 | `time_calendar_duration` |
| `circle_model` | 2 | 2 | 0 | 0 | 0 | `circle_area`, `circle_tangent_cyclic_proof` |
| `column_algorithm` | 2 | 2 | 0 | 0 | 0 | `column_arithmetic_regrouping`, `decimal_arithmetic` |
| `coordinate_graph` | 3 | 3 | 0 | 0 | 0 | `linear_function`, `quadratic_function_graph`, `quadratic_equation_vieta` |
| `data_chart` | 2 | 2 | 0 | 0 | 0 | `picture_bar_chart_reading`, `statistics_probability_from_chart` |
| `expression_tree` | 1 | 1 | 0 | 0 | 0 | `mixed_rational_arithmetic_percent` |
| `factor_lattice` | 1 | 1 | 0 | 0 | 0 | `divisibility_common_multiple` |
| `fraction` | 5 | 5 | 0 | 0 | 0 | `fraction_equivalence`, `fraction_addition`, `fraction_subtraction`, `fraction_multiplication`, `fraction_division` |
| `geometry_2d` | 11 | 11 | 0 | 0 | 0 | `rectangle_perimeter`, `circle_radius_diameter`, `rhombus_parallelogram_area_properties`, `triangle_area`, `ray_segment_midpoint`, `triangle_congruence_centroid_proof`, `triangle_similarity_metric_relation`, `angle_bisector`, `angle_of_depression_distance`, `oblique_triangle_altitude_solution`, `parallelogram_perpendicular_diagonal_area` |
| `geometry_3d` | 3 | 3 | 0 | 0 | 0 | `cuboid_volume`, `cylinder_cone_sphere_volume`, `quadratic_surface_three_variables` |
| `grouping` | 2 | 2 | 0 | 0 | 0 | `multiplication_equal_groups`, `division_equal_groups` |
| `motion_path` | 2 | 2 | 0 | 0 | 0 | `single_leg_motion`, `multi_segment_equal_distance_motion` |
| `number_compare` | 2 | 2 | 0 | 0 | 0 | `number_ordering_rounding`, `signed_decimal_fraction_ordering` |
| `object_group` | 2 | 2 | 0 | 0 | 0 | `concrete_addition_word_problem`, `concrete_subtraction_word_problem` |
| `part_whole` | 1 | 1 | 0 | 0 | 0 | `missing_number_equation` |
| `percent_grid` | 3 | 3 | 0 | 0 | 0 | `percentage_part_whole`, `discount_tax_percentage`, `two_item_discount_system` |
| `place_value` | 2 | 2 | 0 | 0 | 0 | `place_value_read_write`, `decimal_read_write` |
| `power_model` | 1 | 1 | 0 | 0 | 0 | `fraction_power` |
| `probability_simulator` | 1 | 1 | 0 | 0 | 0 | `experimental_probability` |
| `shape_pattern` | 1 | 1 | 0 | 0 | 0 | `shape_recognition_counting_pattern` |
| `solution_set` | 7 | 3 | 4 | 0 | 0 | `linear_inequality_one_variable`, `product_equation_roots`, `rational_equation_domain`, `absolute_value_equation`, `biquadratic_equation`, `radical_equation`, `rational_equation` |
| `unit_scale` | 2 | 2 | 0 | 0 | 0 | `measurement_conversion_comparison`, `map_scale` |

`missing` groups families with no truthful current renderer. Quality gates are
per family and per difficulty band; a renderer passing one family does not
automatically validate all families routed to it.
