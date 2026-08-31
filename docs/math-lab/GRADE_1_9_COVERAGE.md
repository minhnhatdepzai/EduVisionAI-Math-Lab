# Grade 1–9 coverage

Generated from `training/math_lab/catalogs/grade_1_9_exam_families.json` by
`training/math_lab/scripts/build_coverage_docs.py` on the catalog date
**2026-08-31**.

This is an observed-family baseline, not proof that every Vietnamese exam type
has been discovered. Exact coverage is 66/71
(93.0%); 0 families are partial
and 0 are missing. The separate saturation audit must pass before
any broad coverage claim is made.

| Grade | Observed families | Exact | Partial | Missing | Exact coverage | Renderer reach incl. partial | P0 gaps |
|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 8 | 8 | 0 | 0 | 100.0% | 100.0% | — |
| 2 | 10 | 10 | 0 | 0 | 100.0% | 100.0% | — |
| 3 | 9 | 9 | 0 | 0 | 100.0% | 100.0% | — |
| 4 | 11 | 11 | 0 | 0 | 100.0% | 100.0% | — |
| 5 | 13 | 13 | 0 | 0 | 100.0% | 100.0% | — |
| 6 | 13 | 13 | 0 | 0 | 100.0% | 100.0% | — |
| 7 | 9 | 9 | 0 | 0 | 100.0% | 100.0% | — |
| 8 | 8 | 6 | 0 | 0 | 75.0% | 100.0% | `fractional_linear_equation`, `absolute_value_equation` |
| 9 | 19 | 14 | 0 | 0 | 73.7% | 100.0% | `fractional_linear_equation`, `absolute_value_equation`, `biquadratic_equation`, `radical_equation`, `rational_equation` |

## Family matrix

| Family | Grades | Domain | Status | Current renderer | Material gap |
|---|---|---|---|---|---|
| `place_value_read_write` | 1, 2, 3, 5 | number | implemented_sft | `place_value` | — |
| `number_ordering_rounding` | 1, 3, 6 | number | implemented_sft | `number_compare` | — |
| `concrete_addition_word_problem` | 1, 2 | arithmetic | implemented_sft | `object_group` | — |
| `concrete_subtraction_word_problem` | 1, 2 | arithmetic | implemented_sft | `object_group` | — |
| `column_arithmetic_regrouping` | 1, 2, 3, 5 | arithmetic | implemented_sft | `column_algorithm` | — |
| `missing_number_equation` | 1, 2 | arithmetic | implemented_sft | `part_whole` | — |
| `shape_recognition_counting_pattern` | 1, 2 | geometry_2d | implemented_sft | `shape_pattern` | — |
| `time_calendar_duration` | 1, 3, 5 | time | implemented_sft | `calendar` | — |
| `measurement_conversion_comparison` | 2, 4, 5 | measurement | implemented_sft | `unit_scale` | — |
| `multiplication_equal_groups` | 2, 3 | arithmetic | implemented_sft | `grouping` | — |
| `division_equal_groups` | 2, 3 | arithmetic | implemented_sft | `grouping` | — |
| `picture_bar_chart_reading` | 2, 9 | statistics | implemented_sft | `data_chart` | — |
| `rectangle_perimeter` | 3 | geometry_2d | implemented_sft | `geometry_2d` | — |
| `circle_radius_diameter` | 3, 5 | geometry_2d | implemented_sft | `geometry_2d` | — |
| `multi_step_arithmetic_word` | 3 | arithmetic | implemented_sft | `bar_model` | — |
| `fraction_equivalence` | 4 | fraction | implemented_sft | `fraction` | — |
| `fraction_addition` | 4, 6 | fraction | implemented_sft | `fraction` | — |
| `fraction_subtraction` | 4, 6 | fraction | implemented_sft | `fraction` | — |
| `fraction_multiplication` | 4, 6 | fraction | implemented_sft | `fraction` | — |
| `fraction_division` | 4, 6 | fraction | implemented_sft | `fraction` | — |
| `ratio_total_parts` | 4 | ratio | implemented_sft | `bar_model` | — |
| `map_scale` | 4 | ratio | implemented_sft | `unit_scale` | — |
| `arithmetic_mean` | 4 | statistics | implemented_sft | `bar_model` | — |
| `rhombus_parallelogram_area_properties` | 4 | geometry_2d | implemented_sft | `geometry_2d` | — |
| `divisibility_common_multiple` | 4 | number | implemented_sft | `factor_lattice` | — |
| `decimal_read_write` | 5 | number | implemented_sft | `place_value` | — |
| `decimal_arithmetic` | 5, 6 | arithmetic | implemented_sft | `column_algorithm` | — |
| `percentage_part_whole` | 5, 6 | ratio | implemented_sft | `percent_grid` | — |
| `triangle_area` | 5 | geometry_2d | implemented_sft | `geometry_2d` | — |
| `circle_area` | 5 | geometry_2d | implemented_sft | `circle_model` | — |
| `cuboid_volume` | 5 | geometry_3d | implemented_sft | `geometry_3d` | — |
| `single_leg_motion` | 5 | motion | implemented_sft | `motion_path` | — |
| `signed_decimal_fraction_ordering` | 6 | number | implemented_sft | `number_compare` | — |
| `mixed_rational_arithmetic_percent` | 6 | fraction | implemented_sft | `expression_tree` | — |
| `linear_equation` | 6, 8 | algebra | implemented_sft | `balance` | — |
| `discount_tax_percentage` | 6 | ratio | implemented_sft | `percent_grid` | — |
| `ray_segment_midpoint` | 6 | geometry_2d | implemented_sft | `geometry_2d` | — |
| `polynomial_evaluate_reorder` | 7 | algebra | implemented_sft | `algebra_tiles` | — |
| `proportional_system_two_variables` | 7 | ratio | implemented_sft | `bar_model` | — |
| `multi_segment_equal_distance_motion` | 7 | motion | implemented_sft | `motion_path` | — |
| `polynomial_add_subtract` | 7 | algebra | implemented_sft | `algebra_tiles` | — |
| `algebraic_expression_modeling` | 7 | algebra | implemented_sft | `algebra_tiles` | — |
| `triangle_congruence_centroid_proof` | 7 | geometry_2d | implemented_sft | `geometry_2d` | — |
| `linear_function` | 8 | algebra | implemented_sft | `coordinate_graph` | — |
| `compound_linear_equation` | 8 | algebra | implemented_sft | `balance` | — |
| `word_equation_rectangle` | 8 | algebra | implemented_sft | `balance` | — |
| `experimental_probability` | 8 | probability | implemented_sft | `probability_simulator` | — |
| `triangle_similarity_metric_relation` | 8 | geometry_2d | implemented_sft | `geometry_2d` | — |
| `quadratic_function_graph` | 9 | algebra | implemented_sft | `coordinate_graph` | — |
| `quadratic_equation_vieta` | 9 | algebra | implemented_sft | `coordinate_graph` | — |
| `statistics_probability_from_chart` | 9 | statistics | implemented_sft | `data_chart` | — |
| `cylinder_cone_sphere_volume` | 9 | geometry_3d | implemented_sft | `geometry_3d` | — |
| `circle_tangent_cyclic_proof` | 9 | geometry_2d | implemented_sft | `circle_model` | — |
| `angle_bisector` | 7 | geometry_2d | implemented_sft | `geometry_2d` | — |
| `sequential_fraction_remainder_ratio` | 7 | ratio | implemented_sft | `bar_model` | — |
| `sequential_fraction_remainder_quantity` | 6 | ratio | implemented_sft | `bar_model` | — |
| `fraction_power` | 7 | algebra | implemented_sft | `power_model` | — |
| `work_rate_with_variable_people` | 5 | ratio | implemented_sft | `bar_model` | — |
| `linear_inequality_one_variable` | 9 | algebra | implemented_sft | `solution_set` | — |
| `product_equation_roots` | 9 | algebra | implemented_sft | `solution_set` | — |
| `rational_equation_domain` | 9 | algebra | implemented_sft | `solution_set` | — |
| `fractional_linear_equation` | 8, 9 | algebra | renderer_ready | `balance` | Chưa có họ dữ liệu SFT riêng; parser, bộ giải và renderer xác định đã sẵn sàng. |
| `absolute_value_equation` | 8, 9 | algebra | renderer_ready | `solution_set` | Chưa có họ dữ liệu SFT riêng; parser, bộ giải và renderer xác định đã sẵn sàng. |
| `biquadratic_equation` | 9 | algebra | renderer_ready | `solution_set` | Chưa có họ dữ liệu SFT riêng; parser, bộ giải và renderer xác định đã sẵn sàng. |
| `radical_equation` | 9 | algebra | renderer_ready | `solution_set` | Chưa có họ dữ liệu SFT riêng; parser, bộ giải và renderer xác định đã sẵn sàng. |
| `rational_equation` | 9 | algebra | renderer_ready | `solution_set` | Parser hiện hỗ trợ tối đa hai mẫu thức tuyến tính khác nhau và tử sau quy đồng có bậc không quá hai. |
| `angle_of_depression_distance` | 9 | geometry_2d | implemented_sft | `geometry_2d` | — |
| `oblique_triangle_altitude_solution` | 9 | geometry_2d | implemented_sft | `geometry_2d` | — |
| `parallelogram_perpendicular_diagonal_area` | 9 | geometry_2d | implemented_sft | `geometry_2d` | — |
| `two_item_discount_system` | 9 | algebra | implemented_sft | `percent_grid` | — |
| `quadratic_surface_three_variables` | 9 | geometry_3d | implemented_sft | `geometry_3d` | — |

Status meanings come from the catalog. `implemented_sft` requires both an exact
generated semantic family and a structurally appropriate renderer; a related
fallback is only `partial`.
