from __future__ import annotations

from app.schemas.math_lab import (
    MathDomain,
    MathQuantityRole,
    MathSemanticModel,
    VisualizationDecision,
    VisualizationId,
)
from app.services.math_lab.registry import (
    DEFAULT_VISUALIZATION_REGISTRY,
    VisualizationRegistry,
)


class VisualDecisionEngine:
    def __init__(self, registry: VisualizationRegistry = DEFAULT_VISUALIZATION_REGISTRY) -> None:
        self.registry = registry

    def decide(self, model: MathSemanticModel) -> list[VisualizationDecision]:
        candidates = self._rule_candidates(model)
        supported: list[VisualizationDecision] = []
        seen: set[VisualizationId] = set()
        for candidate in sorted(candidates, key=lambda item: item.score, reverse=True):
            if candidate.visualization in seen:
                continue
            if (
                self.registry.supports(candidate.visualization, model)
                and self._renderer_ready(candidate.visualization, model)
            ):
                supported.append(candidate)
                seen.add(candidate.visualization)
        if not supported:
            supported.append(
                VisualizationDecision(
                    visualization=VisualizationId.UNSUPPORTED,
                    score=1.0,
                    reason=(
                        "Chưa dựng được hình đúng nghĩa cho đề này nên Math Lab "
                        "giữ nguyên dữ kiện thay vì vẽ một hình sai"
                    ),
                )
            )
        return supported

    @staticmethod
    def _renderer_ready(
        visualization: VisualizationId,
        model: MathSemanticModel,
    ) -> bool:
        """Reject a scene before a renderer can receive incomplete operands.

        JSON can be schema-valid while still omitting the numbers needed by a
        particular visual model. These checks are intentionally narrow and
        deterministic; they never solve the problem or invent a value.
        """

        counts: dict[MathQuantityRole, int] = {}
        for quantity in model.quantities:
            if quantity.role:
                counts[quantity.role] = counts.get(quantity.role, 0) + 1

        def has(role: MathQuantityRole, minimum: int = 1) -> bool:
            return counts.get(role, 0) >= minimum

        problem = model.problem_type.lower()
        if visualization in {VisualizationId.OBJECT_GROUP, VisualizationId.NUMBER_LINE}:
            if any(token in problem for token in ("addition", "subtraction", "count")):
                return has(MathQuantityRole.COUNT_INITIAL) and has(MathQuantityRole.COUNT_CHANGE)
        if visualization == VisualizationId.GROUPING:
            if "parenthesized_" in problem and "_multiplication" in problem:
                return all(has(role) for role in (
                    MathQuantityRole.COUNT_INITIAL,
                    MathQuantityRole.COUNT_CHANGE,
                    MathQuantityRole.COEFFICIENT,
                ))
            return has(MathQuantityRole.COUNT_INITIAL) and has(MathQuantityRole.COUNT_CHANGE)
        if visualization == VisualizationId.BAR_MODEL and any(
            token in problem for token in ("multiplication_basic", "division_basic")
        ):
            return has(MathQuantityRole.COUNT_INITIAL) and has(MathQuantityRole.COUNT_CHANGE)
        if visualization == VisualizationId.POWER_MODEL:
            return all(has(role) for role in (
                MathQuantityRole.NUMERATOR,
                MathQuantityRole.DENOMINATOR,
                MathQuantityRole.EXPONENT,
            ))
        if visualization == VisualizationId.BALANCE and "word_equation_rectangle" in problem:
            return has(MathQuantityRole.COUNT_CHANGE) and (
                has(MathQuantityRole.TOTAL) or has(MathQuantityRole.COUNT_INITIAL)
            )
        if visualization == VisualizationId.ALGEBRA_TILES and "algebraic_expression_modeling" in problem:
            return has(MathQuantityRole.COEFFICIENT) and has(MathQuantityRole.CONSTANT)
        if visualization == VisualizationId.ALGEBRA_TILES:
            return (
                has(MathQuantityRole.COEFFICIENT)
                and counts.get(MathQuantityRole.COEFFICIENT, 0)
                == counts.get(MathQuantityRole.EXPONENT, 0)
            )
        if visualization == VisualizationId.PERCENT_GRID:
            if "two_item_discount_system" in problem:
                return (
                    has(MathQuantityRole.TOTAL, 2)
                    and has(MathQuantityRole.PROBABILITY, 2)
                )
            if "multi_item_reverse_discount" in problem:
                return (
                    has(MathQuantityRole.COUNT_INITIAL, 2)
                    and has(MathQuantityRole.PROBABILITY, 3)
                    and has(MathQuantityRole.TOTAL)
                )
            available = sum(has(role) for role in (
                MathQuantityRole.COUNT_INITIAL,
                MathQuantityRole.COUNT_CHANGE,
                MathQuantityRole.PROBABILITY,
            ))
            return available >= 2
        if visualization == VisualizationId.BAR_MODEL and "work_rate_with_variable_people" in problem:
            return all(has(role) for role in (
                MathQuantityRole.COUNT_INITIAL,
                MathQuantityRole.DURATION,
                MathQuantityRole.COUNT_CHANGE,
            ))
        if visualization == VisualizationId.BAR_MODEL and "distance_time_direct_proportion" in problem:
            return (
                has(MathQuantityRole.DURATION, 2)
                and has(MathQuantityRole.DISTANCE)
            )
        sequential_roles_ready = all(has(role) for role in (
            MathQuantityRole.NUMERATOR,
            MathQuantityRole.DENOMINATOR,
            MathQuantityRole.ADDEND_NUMERATOR,
            MathQuantityRole.ADDEND_DENOMINATOR,
        )) and any(has(role) for role in (
            MathQuantityRole.AREA,
            MathQuantityRole.MASS,
            MathQuantityRole.COUNT_INITIAL,
            MathQuantityRole.TOTAL,
        ))
        if visualization == VisualizationId.BAR_MODEL and (
            "sequential_fraction_remainder" in problem or sequential_roles_ready
        ):
            return sequential_roles_ready
        if visualization == VisualizationId.FRACTION:
            if any(token in problem for token in (
                "fraction_addition",
                "fraction_subtraction",
                "fraction_multiplication",
                "fraction_division",
            )):
                return all(has(role) for role in (
                    MathQuantityRole.NUMERATOR,
                    MathQuantityRole.DENOMINATOR,
                    MathQuantityRole.ADDEND_NUMERATOR,
                    MathQuantityRole.ADDEND_DENOMINATOR,
                ))
            return has(MathQuantityRole.NUMERATOR) and has(MathQuantityRole.DENOMINATOR)
        if visualization == VisualizationId.BALANCE and "compound_linear_equation" in problem:
            return has(MathQuantityRole.COEFFICIENT) and has(MathQuantityRole.RESULT)
        if visualization == VisualizationId.BALANCE and "equation" in problem:
            return has(MathQuantityRole.COEFFICIENT) and has(MathQuantityRole.RESULT)
        if visualization == VisualizationId.SOLUTION_SET:
            return has(MathQuantityRole.COEFFICIENT) and has(MathQuantityRole.CONSTANT)
        if visualization == VisualizationId.CALENDAR:
            return has(MathQuantityRole.COUNT_INITIAL) and (
                has(MathQuantityRole.DURATION) or has(MathQuantityRole.COUNT_CHANGE)
            )
        if visualization == VisualizationId.GEOMETRY_2D and "angle_of_depression" in problem:
            return has(MathQuantityRole.HEIGHT) and has(MathQuantityRole.ANGLE)
        if visualization == VisualizationId.GEOMETRY_2D and "oblique_triangle_altitude" in problem:
            return has(MathQuantityRole.HEIGHT) and has(MathQuantityRole.ANGLE, 2)
        if visualization == VisualizationId.GEOMETRY_2D and "parallelogram_perpendicular_diagonal" in problem:
            return (
                has(MathQuantityRole.LENGTH) or has(MathQuantityRole.COUNT_INITIAL)
            ) and has(MathQuantityRole.ANGLE)
        if visualization == VisualizationId.GEOMETRY_2D and "triangle_similarity" in problem:
            return has(MathQuantityRole.LENGTH, 2) and has(MathQuantityRole.HEIGHT)
        if visualization == VisualizationId.GEOMETRY_2D and "centroid" in problem:
            return has(MathQuantityRole.LENGTH)
        if visualization == VisualizationId.EXPRESSION_TREE and "factorial" in problem:
            return has(MathQuantityRole.COUNT_INITIAL)
        if visualization == VisualizationId.EXPRESSION_TREE:
            return counts.get(MathQuantityRole.COUNT, 0) >= 2
        if visualization == VisualizationId.PERCENT_GRID and "discount_tax_percentage" in problem:
            return has(MathQuantityRole.COUNT_INITIAL) and has(MathQuantityRole.PROBABILITY)
        if visualization == VisualizationId.MOTION_PATH and "multi_segment" in problem:
            return has(MathQuantityRole.SPEED, 2) and has(MathQuantityRole.DISTANCE)
        if visualization == VisualizationId.BAR_MODEL and "arithmetic_mean" in problem:
            return has(MathQuantityRole.COUNT_CHANGE, 2)
        if visualization == VisualizationId.BAR_MODEL and "proportional_system_two_variables" in problem:
            return all(has(role) for role in (
                MathQuantityRole.COUNT_CHANGE,
                MathQuantityRole.NUMERATOR,
                MathQuantityRole.DENOMINATOR,
            ))
        if visualization == VisualizationId.BAR_MODEL and "multi_step_arithmetic" in problem:
            return has(MathQuantityRole.COUNT_INITIAL) and has(MathQuantityRole.COUNT_CHANGE, 2)
        if visualization == VisualizationId.BAR_MODEL and "ratio_total_parts" in problem:
            return all(has(role) for role in (
                MathQuantityRole.TOTAL,
                MathQuantityRole.NUMERATOR,
                MathQuantityRole.DENOMINATOR,
            ))
        if visualization == VisualizationId.UNIT_SCALE and "map_scale" in problem:
            return has(MathQuantityRole.LENGTH) and has(MathQuantityRole.COEFFICIENT)
        if visualization == VisualizationId.CIRCLE_MODEL and "circle_area" in problem:
            return has(MathQuantityRole.RADIUS) or has(MathQuantityRole.DIAMETER)
        if visualization == VisualizationId.CIRCLE_MODEL and "circle_tangent_cyclic" in problem:
            return (
                (has(MathQuantityRole.RADIUS) or has(MathQuantityRole.DIAMETER))
                and has(MathQuantityRole.ANGLE)
            )
        if visualization == VisualizationId.FACTOR_LATTICE:
            return has(MathQuantityRole.COUNT_INITIAL) and has(MathQuantityRole.COUNT_CHANGE)
        if visualization == VisualizationId.GEOMETRY_2D and "angle_bisector" in problem:
            return has(MathQuantityRole.ANGLE)
        if visualization == VisualizationId.GEOMETRY_2D and "rectangle" in problem:
            return has(MathQuantityRole.LENGTH) and has(MathQuantityRole.WIDTH)
        if visualization == VisualizationId.GEOMETRY_2D and "right_triangle" in problem:
            # Two printed sides determine the triangle, whichever two they are;
            # so does one side with one acute angle. Which side is the
            # hypotenuse travels in the relation, not in the role.
            return (
                has(MathQuantityRole.LENGTH) and has(MathQuantityRole.HEIGHT)
            ) or (
                has(MathQuantityRole.LENGTH) and has(MathQuantityRole.ANGLE)
            )
        if visualization == VisualizationId.COORDINATE_GRAPH and "linear_system_two_variables" in problem:
            # Two general lines need a, b and c for each equation; a missing
            # coefficient would silently collapse one line onto the other.
            return has(MathQuantityRole.COEFFICIENT, 4) and has(MathQuantityRole.CONSTANT, 2)
        if visualization == VisualizationId.COORDINATE_GRAPH and (
            "linear_function" in problem or "linear_equation_two_variables" in problem
        ):
            return has(MathQuantityRole.COEFFICIENT) and has(MathQuantityRole.CONSTANT)
        if visualization == VisualizationId.COORDINATE_GRAPH and any(
            token in problem for token in ("quadratic_function_graph", "quadratic_equation")
        ):
            return has(MathQuantityRole.COEFFICIENT, 2) and has(MathQuantityRole.CONSTANT)
        if visualization == VisualizationId.COORDINATE_GRAPH and "cubic_equation" in problem:
            return has(MathQuantityRole.COEFFICIENT, 3) and has(MathQuantityRole.CONSTANT)
        if visualization == VisualizationId.GEOMETRY_3D and any(
            token in problem for token in ("cuboid", "rectangular_prism")
        ):
            return all(has(role) for role in (
                MathQuantityRole.LENGTH,
                MathQuantityRole.WIDTH,
                MathQuantityRole.HEIGHT,
            ))
        if visualization == VisualizationId.GEOMETRY_3D and "linear_equation_three_variables" in problem:
            return has(MathQuantityRole.COEFFICIENT, 3) and has(MathQuantityRole.CONSTANT)
        if visualization == VisualizationId.GEOMETRY_3D and "linear_system_three_variables" in problem:
            return has(MathQuantityRole.COEFFICIENT, 6) and has(MathQuantityRole.CONSTANT, 2)
        if visualization == VisualizationId.GEOMETRY_3D and "quadratic_surface" in problem:
            return has(MathQuantityRole.COEFFICIENT, 3) and has(MathQuantityRole.CONSTANT)
        return True

    @staticmethod
    def _rule_candidates(model: MathSemanticModel) -> list[VisualizationDecision]:
        def choice(identifier: VisualizationId, score: float, reason: str) -> VisualizationDecision:
            return VisualizationDecision(visualization=identifier, score=score, reason=reason)

        domain = model.domain
        problem = model.problem_type.lower()
        roles = {item.role for item in model.quantities if item.role}
        sequential_roles = {
            MathQuantityRole.NUMERATOR,
            MathQuantityRole.DENOMINATOR,
            MathQuantityRole.ADDEND_NUMERATOR,
            MathQuantityRole.ADDEND_DENOMINATOR,
        }
        has_sequential_total = bool(roles & {
            MathQuantityRole.AREA,
            MathQuantityRole.MASS,
            MathQuantityRole.COUNT_INITIAL,
            MathQuantityRole.TOTAL,
        })
        if sequential_roles.issubset(roles) and has_sequential_total:
            return [choice(
                VisualizationId.BAR_MODEL,
                0.999,
                "A reusable two-stage remainder strategy repartitions the changing whole before deriving the final quantity",
            )]
        if "fractional_linear_equation" in problem:
            return [choice(
                VisualizationId.BALANCE,
                0.999,
                "The common-denominator transformation is shown before the equivalent balance equation is solved",
            )]
        if "compound_linear_equation" in problem:
            return [choice(
                VisualizationId.BALANCE,
                0.999,
                "The scale keeps both sides equal while the brackets are expanded and like terms collected",
            )]
        if any(token in problem for token in (
            "linear_inequality", "product_equation_roots", "rational_equation_domain",
            "absolute_value_equation", "biquadratic_equation",
            "radical_equation", "rational_equation",
        )):
            return [choice(
                VisualizationId.SOLUTION_SET,
                0.999,
                "The number line distinguishes accepted roots from boundary or forbidden values after each exact algebraic transformation",
            )]
        if "time_calendar_duration" in problem or "calendar" in problem:
            return [choice(
                VisualizationId.CALENDAR,
                0.999,
                "Counting the span on a month grid keeps the month boundary visible instead of implied",
            )]
        if any(token in problem for token in (
            "angle_of_depression",
            "oblique_triangle_altitude",
            "parallelogram_perpendicular_diagonal",
        )):
            return [choice(
                VisualizationId.GEOMETRY_2D,
                0.999,
                "A measured construction exposes the right triangles and the trigonometric ratio behind the result",
            )]
        if "triangle_similarity" in problem:
            return [choice(
                VisualizationId.GEOMETRY_2D,
                0.999,
                "Two marked triangles and one ratio prove the metric relation instead of asserting it",
            )]
        if "centroid" in problem or "triangle_congruence" in problem:
            return [choice(
                VisualizationId.GEOMETRY_2D,
                0.999,
                "Both parts of the median are drawn, so the 2:1 division is measured rather than trusted",
            )]
        if "word_equation_rectangle" in problem:
            return [choice(
                VisualizationId.BALANCE,
                0.999,
                "The rectangle and the equation change together, so each algebraic step has a shape to match",
            )]
        if "algebraic_expression_modeling" in problem:
            return [choice(
                VisualizationId.ALGEBRA_TILES,
                0.999,
                "Each phrase becomes exactly one term, so building the expression is the visible operation",
            )]
        if "factorial" in problem:
            return [choice(
                VisualizationId.EXPRESSION_TREE,
                0.999,
                "Factorial expands into an ordered product whose checkpoints keep a very large exact integer readable",
            )]
        if "mixed_rational" in problem or "expression_tree" in problem:
            return [choice(
                VisualizationId.EXPRESSION_TREE,
                0.999,
                "Precedence decides the answer, so the reduction order is the model rather than a left-to-right strip",
            )]
        if "two_item_discount_system" in problem:
            return [choice(
                VisualizationId.PERCENT_GRID,
                0.999,
                "Two list-price bars and their retained percentages expose both equations before elimination",
            )]
        if "discount_tax_percentage" in problem:
            return [choice(
                VisualizationId.PERCENT_GRID,
                0.999,
                "Each percentage applies to the price state before it, so every state stays on screen",
            )]
        if "multi_segment" in problem:
            return [choice(
                VisualizationId.MOTION_PATH,
                0.999,
                "Separate legs expose why the average speed is not the average of the two speeds",
            )]
        if "arithmetic_mean" in problem:
            return [choice(
                VisualizationId.BAR_MODEL,
                0.999,
                "Levelling uneven columns to one shared height is what an average actually is",
            )]
        if "proportional_system_two_variables" in problem:
            return [choice(
                VisualizationId.BAR_MODEL,
                0.999,
                "Two bars in the printed ratio expose the difference as a whole number of equal parts",
            )]
        if "multi_step_arithmetic" in problem:
            return [choice(
                VisualizationId.BAR_MODEL,
                0.999,
                "One running total carried through both operations keeps the intermediate value visible",
            )]
        if "ratio_total_parts" in problem:
            return [choice(
                VisualizationId.BAR_MODEL,
                0.999,
                "Splitting the total into two bars of equal parts derives one part before either quantity",
            )]
        if "map_scale" in problem:
            return [choice(
                VisualizationId.UNIT_SCALE,
                0.999,
                "Two aligned rulers show the map length and the real distance as one measurement",
            )]
        if "circle_area" in problem:
            return [choice(
                VisualizationId.CIRCLE_MODEL,
                0.999,
                "Unrolling the disc into sectors turns pi*r*r into a rectangle the learner can measure",
            )]
        if "circle_tangent_cyclic" in problem:
            return [choice(
                VisualizationId.CIRCLE_MODEL,
                0.999,
                "A tangent right angle and an inscribed angle share the arc that carries the proof",
            )]
        if "divisibility_common_multiple" in problem:
            return [choice(
                VisualizationId.FACTOR_LATTICE,
                0.999,
                "Two multiple strips on one lattice make the shared multiples and the least one visible",
            )]
        if "linear_system_two_variables" in problem:
            return [choice(
                VisualizationId.COORDINATE_GRAPH,
                0.999,
                "Two lines on shared Oxy axes show whether the system meets at one point, never, or everywhere",
            )]
        if "linear_system_three_variables" in problem:
            return [choice(
                VisualizationId.GEOMETRY_3D,
                0.999,
                "Each equation becomes a plane on shared Oxyz axes; row reduction and the common intersection verify the solution",
            )]
        if "linear_equation_three_variables" in problem:
            return [choice(
                VisualizationId.GEOMETRY_3D,
                0.999,
                "A three-variable linear equation is a plane on shared Oxyz axes",
            )]
        if "quadratic_surface" in problem:
            return [choice(
                VisualizationId.GEOMETRY_3D,
                0.999,
                "The squared variable bends the solution set into a ruled parabolic surface instead of a plane",
            )]
        if "parenthesized_" in problem and "_multiplication" in problem:
            return [choice(
                VisualizationId.GROUPING,
                0.999,
                "An operation tree resolves the parentheses before building the equal-group multiplication",
            )]
        if "distance_time_direct_proportion" in problem:
            return [choice(
                VisualizationId.BAR_MODEL,
                0.999,
                "Equal time blocks expose the unit distance before scaling to the target duration",
            )]
        if "work_rate_with_variable_people" in problem:
            return [choice(
                VisualizationId.BAR_MODEL,
                0.999,
                "A conserved worker-day area shows inverse proportionality when the team size changes",
            )]
        if "multi_item_reverse_discount" in problem:
            return [choice(
                VisualizationId.PERCENT_GRID,
                0.999,
                "A checkout flow exposes each discounted payment, the remaining payment, and the inverse percentage for the unknown original price",
            )]
        if "number_ordering_rounding" in problem or "signed_decimal_fraction_ordering" in problem:
            return [choice(
                VisualizationId.NUMBER_COMPARE,
                0.995,
                "Multiple markers and rounding bounds make order and nearest-place distance visible",
            )]
        if any(token in problem for token in ("place_value", "read_write_number", "decimal_read_write")):
            return [choice(
                VisualizationId.PLACE_VALUE,
                0.995,
                "Place-value columns and base-ten blocks expose every digit's value",
            )]
        if any(token in problem for token in ("column_arithmetic", "regrouping", "decimal_arithmetic")):
            return [choice(
                VisualizationId.COLUMN_ALGORITHM,
                0.995,
                "A column algorithm makes every carry or borrow visible in its place-value column",
            )]
        if any(token in problem for token in ("measurement_conversion", "unit_conversion", "unit_scale")):
            return [choice(
                VisualizationId.UNIT_SCALE,
                0.995,
                "A shared unit ladder shows the scale factor and preserves the measured quantity",
            )]
        if any(token in problem for token in ("picture_bar_chart", "chart_reading", "statistics_probability_from_chart")):
            return [choice(
                VisualizationId.DATA_CHART,
                0.995,
                "Bars are derived from the same frequency table used for comparison and probability",
            )]
        if "experimental_probability" in problem:
            return [choice(
                VisualizationId.PROBABILITY_SIMULATOR,
                0.995,
                "A replayable trial strip connects each outcome to frequency over total trials",
            )]
        if any(token in problem for token in ("percentage_part_whole", "percent_part_whole")):
            return [choice(
                VisualizationId.PERCENT_GRID,
                0.995,
                "A 100-cell grid keeps part, whole and percentage visible in one invariant model",
            )]
        if any(token in problem for token in ("polynomial_evaluate_reorder", "polynomial_add_subtract")):
            return [choice(
                VisualizationId.ALGEBRA_TILES,
                0.995,
                "Algebra tiles preserve degree and sign while like terms are reordered or combined",
            )]
        if "missing_number_equation" in problem:
            return [choice(
                VisualizationId.PART_WHOLE,
                0.995,
                "A part-whole diagram keeps the blank in its actual role instead of guessing an answer",
            )]
        if "shape_recognition_counting_pattern" in problem:
            return [choice(
                VisualizationId.SHAPE_PATTERN,
                0.995,
                "Indexed shape overlays make every counted object and repeating cycle inspectable",
            )]
        if any(token in problem for token in ("fraction_power", "power_of_fraction", "fraction_exponent")):
            return [
                choice(
                    VisualizationId.POWER_MODEL,
                    0.995,
                    "Repeated fraction factors expose the sign and the powers of numerator and denominator",
                )
            ]
        if "sequential_fraction_remainder" in problem:
            return [choice(
                VisualizationId.BAR_MODEL,
                0.999,
                "Two successive equal-part bars preserve the changing remainder before deriving the requested outcome",
            )]
        if "ratio" in problem and domain in {
            MathDomain.ARITHMETIC,
            MathDomain.NUMBER,
            MathDomain.FRACTION,
            MathDomain.RATIO,
        }:
            return [
                choice(
                    VisualizationId.BAR_MODEL,
                    0.99,
                    "Aligned equal-part bars connect the known amount to the requested ratio",
                )
            ]
        if domain in {MathDomain.ARITHMETIC, MathDomain.NUMBER}:
            if any(token in problem for token in ("average", "trung_binh", "mean")):
                return [
                    choice(
                        VisualizationId.BAR_MODEL,
                        0.99,
                        "A month-by-month accumulation and equal-share model exposes the average",
                    )
                ]
            if model.grade <= 3 and any(token in problem for token in ("addition", "subtraction", "count")):
                return [
                    choice(VisualizationId.OBJECT_GROUP, 0.98, "Early-grade counting is concrete first"),
                    choice(VisualizationId.NUMBER_LINE, 0.76, "A number line links objects to symbols"),
                ]
            operands = [
                int(quantity.value)
                for quantity in model.quantities
                if quantity.role in {
                    MathQuantityRole.COUNT_INITIAL,
                    MathQuantityRole.COUNT_CHANGE,
                }
                and float(quantity.value).is_integer()
            ]
            if problem == "division_basic" and len(operands) >= 2 and operands[0] > 144:
                return [choice(
                    VisualizationId.COLUMN_ALGORITHM,
                    0.999,
                    "A large dividend is readable digit by digit instead of as hundreds of repeated objects",
                )]
            if problem == "multiplication_basic" and len(operands) >= 2 and min(operands[:2]) > 12:
                return [choice(
                    VisualizationId.COLUMN_ALGORITHM,
                    0.999,
                    "Two large factors are clearer as shifted partial products than as thousands of equal groups",
                )]
            if any(token in problem for token in ("multiplication", "division", "group")):
                return [
                    choice(VisualizationId.GROUPING, 0.95, "Equal groups expose multiplication or division"),
                    choice(VisualizationId.BAR_MODEL, 0.74, "A bar model supports quantity comparison"),
                ]
            if any(token in problem for token in ("number_line", "integer_addition", "integer_subtraction")):
                return [choice(VisualizationId.NUMBER_LINE, 0.9, "Numbers map directly to a spatial scale")]
            return []
        if domain == MathDomain.FRACTION:
            return [choice(VisualizationId.FRACTION, 0.99, "Equal partitions encode the fraction definition")]
        if domain == MathDomain.RATIO:
            return [
                choice(VisualizationId.BAR_MODEL, 0.94, "Aligned bars make ratios comparable"),
                choice(VisualizationId.FRACTION, 0.7, "Fraction partitions can support part-whole ratios"),
            ]
        if domain == MathDomain.TIME:
            if not any(token in problem for token in ("clock", "elapsed_time", "timeline")):
                return []
            return [
                choice(VisualizationId.CLOCK, 0.96, "Clock state represents time of day"),
                choice(VisualizationId.TIMELINE, 0.85, "A timeline represents elapsed duration"),
            ]
        if domain == MathDomain.MOTION:
            results = [
                choice(VisualizationId.MOTION_PATH, 0.99, "Motion relates an entity, a path and distance"),
                choice(VisualizationId.TIMELINE, 0.9, "Elapsed time shares the same motion state"),
            ]
            if model.time and model.time.start:
                results.append(choice(VisualizationId.CLOCK, 0.92, "The problem includes a start time"))
            if model.grade >= 7:
                results.append(choice(VisualizationId.COORDINATE_GRAPH, 0.78, "Older learners can connect motion to a distance-time graph"))
            return results
        if domain == MathDomain.ALGEBRA:
            if problem.startswith("linear_identity") or problem.startswith("linear_contradiction"):
                # Nothing is being solved: every variable cancelled. Abstaining
                # keeps the lab from drawing a model the statement never had.
                return []
            if any(token in problem for token in ("expansion", "binomial", "algebraic_identity")):
                return [choice(
                    VisualizationId.BAR_MODEL,
                    0.99,
                    "An area partition makes every term in the algebraic identity visible",
                )]
            if (
                "linear_function" in problem
                or "quadratic_function_graph" in problem
                or "quadratic_equation" in problem
                or "cubic_equation" in problem
            ):
                return [choice(
                    VisualizationId.COORDINATE_GRAPH,
                    0.99,
                    "Shared axes expose the function shape and every real root as an x-intercept",
                )]
            if "equation" in problem:
                return [choice(
                    VisualizationId.BALANCE,
                    0.99,
                    "The same transformation on both sides preserves equation balance",
                )]
            return []
        if domain == MathDomain.COORDINATE:
            if any(token in problem for token in (
                "coordinate", "point", "linear_function", "linear_equation_two_variables"
            )):
                return [choice(VisualizationId.COORDINATE_GRAPH, 0.99, "Coordinates require shared axes")]
            return []
        if domain == MathDomain.GEOMETRY_2D:
            if any(token in problem for token in ("rectangle", "triangle_area", "right_triangle", "circle_radius_diameter", "rhombus_", "parallelogram_", "ray_segment_midpoint", "angle_bisector", "triangle_solution")):
                return [choice(VisualizationId.GEOMETRY_2D, 0.99, "Deterministic geometry preserves explicit constraints")]
            return []
        if domain == MathDomain.GEOMETRY_3D:
            if any(token in problem for token in ("cuboid", "cube", "rectangular_prism", "cylinder_volume", "cone_volume", "sphere_volume")):
                return [choice(VisualizationId.GEOMETRY_3D, 0.99, "A spatial solid benefits from bounded rotate and zoom")]
            return []
        if domain == MathDomain.MEASUREMENT:
            if any(token in problem for token in ("volume", "cuboid", "cube", "prism", "cylinder", "cone", "sphere")):
                return [choice(VisualizationId.GEOMETRY_3D, 0.94, "Volume is connected to a spatial solid")]
            if any(token in problem for token in ("rectangle", "triangle_area")):
                return [choice(VisualizationId.GEOMETRY_2D, 0.94, "Measured sides define deterministic geometry")]
            return []
        if domain in {MathDomain.STATISTICS, MathDomain.PROBABILITY}:
            if any(token in problem for token in ("chart", "frequency", "bar_graph")):
                return [choice(VisualizationId.DATA_CHART, 0.99, "A frequency table and chart share one verified dataset")]
            return []
        return []
