from __future__ import annotations

from enum import Enum
from math import isfinite
from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

from app.schemas.math_lab_input import canonical_problem_type
from app.schemas.math_lab_linear import classify_linear, format_canonical, transformation_stages
from app.schemas.math_lab_equations import parse_fractional_linear_equation
from app.schemas.math_lab_nonlinear import parse_quadratic_surface
from app.schemas.math_lab_text import (
    extract_angle_of_depression,
    extract_basic_arithmetic,
    extract_binary_fraction,
    extract_direct_proportion_distance_time,
    extract_factorial,
    extract_linear_equation,
    extract_linear_system,
    extract_parenthesized_multiplication,
    extract_oblique_triangle_altitude,
    extract_perpendicular_diagonal_parallelogram,
    extract_primary_word_arithmetic,
    extract_rectangle_dimensions,
    extract_right_triangle,
    extract_right_triangle_legs,
    extract_sequential_fraction_remainder_area,
    extract_single_variable_linear_expression,
    extract_three_variable_linear_equation,
    extract_two_item_discount_system,
    extract_two_variable_linear_equation,
    extract_variable_people_work_rate,
)


SCHEMA_VERSION = "1.0"
Identifier = str
VerbatimText = Annotated[str, StringConstraints(strip_whitespace=False)]
MathUnit = Literal[
    "one", "mm", "cm", "dm", "m", "km", "g", "kg", "second", "minute",
    "hour", "day", "cm2", "m2", "cm3", "m3", "liter", "ml", "m/s", "km/h",
    "degree",
]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class EvidenceStatus(str, Enum):
    EXPLICIT = "explicit"
    INFERRED = "inferred"
    UNCERTAIN = "uncertain"


class EvidenceSource(str, Enum):
    TEXT_INPUT = "text_input"
    VISION_OCR = "vision_ocr"
    HANDWRITING = "handwriting"
    DIAGRAM = "diagram"
    TEACHER = "teacher"
    SYSTEM = "system"
    VISION_INFERENCE = "vision_inference"


class MathDomain(str, Enum):
    ARITHMETIC = "arithmetic"
    NUMBER = "number"
    FRACTION = "fraction"
    RATIO = "ratio"
    MEASUREMENT = "measurement"
    TIME = "time"
    MOTION = "motion"
    ALGEBRA = "algebra"
    GEOMETRY_2D = "geometry_2d"
    COORDINATE = "coordinate"
    GEOMETRY_3D = "geometry_3d"
    PROBABILITY = "probability"
    STATISTICS = "statistics"
    UNKNOWN = "unknown"


class VisualizationId(str, Enum):
    UNSUPPORTED = "unsupported"
    OBJECT_GROUP = "object_group"
    NUMBER_LINE = "number_line"
    GROUPING = "grouping"
    BAR_MODEL = "bar_model"
    FRACTION = "fraction"
    POWER_MODEL = "power_model"
    CLOCK = "clock"
    TIMELINE = "timeline"
    MOTION_PATH = "motion_path"
    BALANCE = "balance"
    GEOMETRY_2D = "geometry_2d"
    COORDINATE_GRAPH = "coordinate_graph"
    GEOMETRY_3D = "geometry_3d"
    PLACE_VALUE = "place_value"
    COLUMN_ALGORITHM = "column_algorithm"
    UNIT_SCALE = "unit_scale"
    DATA_CHART = "data_chart"
    NUMBER_COMPARE = "number_compare"
    PROBABILITY_SIMULATOR = "probability_simulator"
    PERCENT_GRID = "percent_grid"
    ALGEBRA_TILES = "algebra_tiles"
    PART_WHOLE = "part_whole"
    SHAPE_PATTERN = "shape_pattern"
    CIRCLE_MODEL = "circle_model"
    FACTOR_LATTICE = "factor_lattice"
    EXPRESSION_TREE = "expression_tree"
    CALENDAR = "calendar"
    SOLUTION_SET = "solution_set"


class VisualConceptType(str, Enum):
    PART_WHOLE = "part_whole"
    EQUAL_GROUPS = "equal_groups"
    CHANGE_OVER_TIME = "change_over_time"
    RATIO_PROPORTION = "ratio_proportion"
    FRACTION_PARTITION = "fraction_partition"
    OPERATION_ON_NUMBER_LINE = "operation_on_number_line"
    MEASUREMENT = "measurement"
    GEOMETRY_CONSTRUCTION = "geometry_construction"
    COORDINATE_RELATION = "coordinate_relation"
    STATISTICS_PROBABILITY = "statistics_probability"
    ALGEBRA_TRANSFORM = "algebra_transform"
    SPATIAL_3D = "spatial_3d"
    UNSUPPORTED = "unsupported"


class VisualPrimitive(str, Enum):
    OBJECT_ARRAY = "object_array"
    NUMBER_LINE = "number_line"
    BAR_MODEL = "bar_model"
    FRACTION_STRIP = "fraction_strip"
    RATIO_TABLE = "ratio_table"
    COORDINATE_PLANE = "coordinate_plane"
    GEOMETRY_CONSTRUCTION = "geometry_construction"
    CHART = "chart"
    PROBABILITY_SIMULATION = "probability_simulation"
    UNIT_LADDER = "unit_ladder"
    CLOCK_TIMELINE = "clock_timeline"
    BALANCE_SCALE = "balance_scale"
    ALGEBRA_TILES = "algebra_tiles"
    AREA_VOLUME_MODEL = "area_volume_model"
    TEXT_OVERLAY = "text_overlay"


class MathQuantityRole(str, Enum):
    COUNT = "count"
    COUNT_INITIAL = "count_initial"
    COUNT_CHANGE = "count_change"
    TOTAL = "total"
    DISTANCE = "distance"
    SPEED = "speed"
    DURATION = "duration"
    START_TIME = "start_time"
    END_TIME = "end_time"
    NUMERATOR = "numerator"
    DENOMINATOR = "denominator"
    TARGET_DENOMINATOR = "target_denominator"
    ADDEND_NUMERATOR = "addend_numerator"
    ADDEND_DENOMINATOR = "addend_denominator"
    EXPONENT = "exponent"
    LENGTH = "length"
    WIDTH = "width"
    HEIGHT = "height"
    RADIUS = "radius"
    DIAMETER = "diameter"
    MASS = "mass"
    CAPACITY = "capacity"
    AREA = "area"
    VOLUME = "volume"
    ANGLE = "angle"
    VARIABLE = "variable"
    COEFFICIENT = "coefficient"
    CONSTANT = "constant"
    RESULT = "result"
    X_VALUE = "x_value"
    Y_VALUE = "y_value"
    CATEGORY = "category"
    FREQUENCY = "frequency"
    PROBABILITY = "probability"


class QuestionFormat(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"
    WORD_PROBLEM = "word_problem"
    PROOF = "proof"
    CONSTRUCTION = "construction"
    DATA_QUESTION = "data_question"
    UNKNOWN = "unknown"


class Evidence(StrictModel):
    confidence: float = Field(default=1.0, ge=0, le=1)
    source: EvidenceSource = EvidenceSource.TEXT_INPUT
    status: EvidenceStatus = EvidenceStatus.EXPLICIT
    source_ref: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def uncertain_inferences_are_not_hard_facts(self) -> "Evidence":
        if self.confidence < 0.65 and self.status == EvidenceStatus.EXPLICIT:
            raise ValueError("Low-confidence evidence cannot be explicit")
        return self


class SemanticEntity(StrictModel):
    id: Identifier = Field(pattern=r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")
    type: str = Field(min_length=1, max_length=64)
    label: str = Field(min_length=1, max_length=160)
    role: str | None = Field(default=None, max_length=64)
    attributes: dict[str, Any] = Field(default_factory=dict)
    evidence: Evidence = Field(default_factory=Evidence)


class MathQuantity(StrictModel):
    id: Identifier = Field(pattern=r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")
    value: float
    unit: MathUnit = "one"
    label: str | None = Field(default=None, max_length=160)
    role: MathQuantityRole | None = None
    editable: bool = False
    evidence: Evidence = Field(default_factory=Evidence)

    @model_validator(mode="after")
    def finite_value(self) -> "MathQuantity":
        if not isfinite(self.value):
            raise ValueError("Quantity value must be finite")
        return self


class MathUnknown(StrictModel):
    id: Identifier = Field(pattern=r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")
    kind: str = Field(min_length=1, max_length=64)
    unit: MathUnit | None = None
    label: str | None = Field(default=None, max_length=160)
    role: MathQuantityRole | None = None


class SemanticRelation(StrictModel):
    id: Identifier = Field(pattern=r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")
    type: str = Field(min_length=1, max_length=64)
    participants: dict[str, Identifier] = Field(min_length=1)
    parameters: dict[str, Any] = Field(default_factory=dict)
    evidence: Evidence = Field(default_factory=Evidence)


class SemanticConstraint(StrictModel):
    id: Identifier = Field(pattern=r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")
    type: str = Field(min_length=1, max_length=64)
    target_ids: list[Identifier] = Field(min_length=1)
    parameters: dict[str, Any] = Field(default_factory=dict)
    locked: bool = True
    evidence: Evidence = Field(default_factory=Evidence)

    @model_validator(mode="after")
    def uncertain_constraints_are_not_locked(self) -> "SemanticConstraint":
        if self.locked and (
            self.evidence.status == EvidenceStatus.UNCERTAIN
            or self.evidence.confidence < 0.75
        ):
            raise ValueError("An uncertain relation cannot become a locked constraint")
        return self


class TimeContext(StrictModel):
    start: str | None = Field(default=None, pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    end: str | None = Field(default=None, pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    timezone: str | None = Field(default=None, max_length=64)

    @field_validator("start", "end", mode="before")
    @classmethod
    def empty_clock_is_missing(cls, value: Any) -> Any:
        return None if isinstance(value, str) and not value.strip() else value


class MathSemanticModel(StrictModel):
    schema_version: Literal["1.0"] = SCHEMA_VERSION
    id: Identifier = Field(default="semantic_model", pattern=r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")
    grade: int = Field(ge=1, le=9)
    domain: MathDomain
    problem_type: str = Field(min_length=1, max_length=96)
    source_text: VerbatimText | None = Field(default=None, max_length=20_000)
    choices: list[str] = Field(default_factory=list, max_length=12)
    entities: list[SemanticEntity] = Field(default_factory=list)
    quantities: list[MathQuantity] = Field(default_factory=list)
    unknowns: list[MathUnknown] = Field(default_factory=list)
    relations: list[SemanticRelation] = Field(default_factory=list)
    constraints: list[SemanticConstraint] = Field(default_factory=list)
    time: TimeContext | None = None
    tags: list[str] = Field(default_factory=list, max_length=32)

    @field_validator("problem_type", mode="before")
    @classmethod
    def normalize_problem_type(cls, value: Any) -> str:
        return canonical_problem_type(str(value))

    @model_validator(mode="after")
    def validate_ids_and_references(self) -> "MathSemanticModel":
        factorial = extract_factorial(self.source_text)
        basic_arithmetic = (
            extract_basic_arithmetic(self.source_text)
            or extract_primary_word_arithmetic(self.source_text)
        )
        if factorial:
            self.problem_type = "factorial"
            self.domain = MathDomain.NUMBER
            self.quantities = [MathQuantity(
                id="factorial_operand",
                value=factorial.value,
                unit="one",
                role=MathQuantityRole.COUNT_INITIAL,
                label="Số cần tính giai thừa",
            )]
            self.unknowns = [MathUnknown(
                id="factorial_result",
                kind="number",
                unit="one",
                role=MathQuantityRole.RESULT,
                label="Giá trị giai thừa",
            )]
            self.relations = []
        elif basic_arithmetic:
            operation_labels = {
                "addition": ("Số lượng ban đầu", "Số lượng thêm vào", "Kết quả phép cộng"),
                "subtraction": ("Số lượng ban đầu", "Số lượng bớt đi", "Kết quả phép trừ"),
                "multiplication": ("Số nhóm", "Số phần tử mỗi nhóm", "Kết quả phép nhân"),
                "division": ("Tổng số cần chia", "Số phần tử mỗi nhóm", "Kết quả phép chia"),
            }
            left_label, right_label, result_label = operation_labels[basic_arithmetic.operation]
            self.problem_type = f"{basic_arithmetic.operation}_basic"
            self.domain = MathDomain.ARITHMETIC
            self.quantities = [
                MathQuantity(
                    id="left_operand",
                    value=basic_arithmetic.left,
                    unit="one",
                    role=MathQuantityRole.COUNT_INITIAL,
                    label=left_label,
                ),
                MathQuantity(
                    id="right_operand",
                    value=basic_arithmetic.right,
                    unit="one",
                    role=MathQuantityRole.COUNT_CHANGE,
                    label=right_label,
                ),
            ]
            self.unknowns = [MathUnknown(
                id="arithmetic_result",
                kind="number",
                unit="one",
                role=MathQuantityRole.RESULT,
                label=result_label,
            )]
            relation_type = (
                "equal_groups"
                if basic_arithmetic.operation in {"multiplication", "division"}
                else "part_whole"
            )
            participant_roles = {
                "addition": {
                    "part_a": "left_operand",
                    "part_b": "right_operand",
                    "whole": "arithmetic_result",
                },
                "subtraction": {
                    "whole": "left_operand",
                    "removed_part": "right_operand",
                    "remaining_part": "arithmetic_result",
                },
                "multiplication": {
                    "groups": "left_operand",
                    "group_size": "right_operand",
                    "total": "arithmetic_result",
                },
                "division": {
                    "total": "left_operand",
                    "group_size": "right_operand",
                    "groups": "arithmetic_result",
                },
            }
            self.relations = [SemanticRelation(
                id="basic_operation_relation",
                type=relation_type,
                participants=participant_roles[basic_arithmetic.operation],
                parameters={"operator": basic_arithmetic.operation},
                evidence=Evidence(
                    confidence=1.0,
                    source=EvidenceSource.SYSTEM,
                    status=EvidenceStatus.INFERRED,
                ),
            )]

        parenthesized = extract_parenthesized_multiplication(self.source_text)
        if parenthesized:
            self.problem_type = f"parenthesized_{parenthesized.inner_operation}_multiplication"
            self.domain = MathDomain.ARITHMETIC
            self.quantities = [
                MathQuantity(
                    id="inner_left",
                    value=parenthesized.inner_left,
                    unit="one",
                    role=MathQuantityRole.COUNT_INITIAL,
                    label="Số thứ nhất trong ngoặc",
                ),
                MathQuantity(
                    id="inner_right",
                    value=parenthesized.inner_right,
                    unit="one",
                    role=MathQuantityRole.COUNT_CHANGE,
                    label="Số thứ hai trong ngoặc",
                ),
                MathQuantity(
                    id="outer_multiplier",
                    value=parenthesized.multiplier,
                    unit="one",
                    role=MathQuantityRole.COEFFICIENT,
                    label="Thừa số ngoài ngoặc",
                ),
            ]
            self.unknowns = [MathUnknown(
                id="expression_result",
                kind="number",
                unit="one",
                role=MathQuantityRole.RESULT,
                label="Kết quả biểu thức",
            )]
            self.relations = [SemanticRelation(
                id="parenthesized_operation_tree",
                type="operation_tree",
                participants={
                    "inner_left": "inner_left",
                    "inner_right": "inner_right",
                    "multiplier": "outer_multiplier",
                    "result": "expression_result",
                },
                parameters={
                    "inner_operation": parenthesized.inner_operation,
                    "outer_operation": "multiplication",
                    "order": "parentheses_first",
                },
                evidence=Evidence(
                    confidence=1.0,
                    source=EvidenceSource.SYSTEM,
                    status=EvidenceStatus.INFERRED,
                ),
            )]

        direct_distance = extract_direct_proportion_distance_time(self.source_text)
        if direct_distance:
            # Migrate both fresh analysis and five-item history written before
            # this renderer existed. Values below are the three numbers printed
            # in the stem; unit rate and target distance remain derived state.
            self.problem_type = "distance_time_direct_proportion"
            self.domain = MathDomain.RATIO
            self.quantities = [
                MathQuantity(
                    id="known_duration",
                    value=direct_distance.known_duration,
                    unit=direct_distance.known_duration_unit,
                    role=MathQuantityRole.DURATION,
                    label="Thời gian đã biết",
                ),
                MathQuantity(
                    id="known_distance",
                    value=direct_distance.known_distance,
                    unit=direct_distance.known_distance_unit,
                    role=MathQuantityRole.DISTANCE,
                    label="Quãng đường đã biết",
                ),
                MathQuantity(
                    id="target_duration",
                    value=direct_distance.target_duration,
                    unit=direct_distance.target_duration_unit,
                    role=MathQuantityRole.DURATION,
                    label="Thời gian cần tính quãng đường",
                ),
            ]
            self.unknowns = [MathUnknown(
                id="target_distance",
                kind="distance",
                unit=direct_distance.known_distance_unit,
                role=MathQuantityRole.RESULT,
                label="Quãng đường trong thời gian mới",
            )]
            self.relations = [SemanticRelation(
                id="distance_time_direct_proportion",
                type="direct_proportion",
                participants={
                    "known_duration": "known_duration",
                    "known_distance": "known_distance",
                    "target_duration": "target_duration",
                    "target_distance": "target_distance",
                },
                parameters={"invariant": "distance_per_unit_time"},
                evidence=Evidence(
                    confidence=0.98,
                    source=EvidenceSource.SYSTEM,
                    status=EvidenceStatus.INFERRED,
                ),
            )]

        binary_fraction = extract_binary_fraction(self.source_text)
        if binary_fraction:
            self.problem_type = f"fraction_{binary_fraction.operation}"
            self.domain = MathDomain.FRACTION
            self.quantities = [
                MathQuantity(id="left_numerator", value=binary_fraction.left_numerator, unit="one", role=MathQuantityRole.NUMERATOR, label="Tử số phân số thứ nhất"),
                MathQuantity(id="left_denominator", value=binary_fraction.left_denominator, unit="one", role=MathQuantityRole.DENOMINATOR, label="Mẫu số phân số thứ nhất"),
                MathQuantity(id="right_numerator", value=binary_fraction.right_numerator, unit="one", role=MathQuantityRole.ADDEND_NUMERATOR, label="Tử số phân số thứ hai"),
                MathQuantity(id="right_denominator", value=binary_fraction.right_denominator, unit="one", role=MathQuantityRole.ADDEND_DENOMINATOR, label="Mẫu số phân số thứ hai"),
            ]
            self.unknowns = [MathUnknown(
                id="fraction_result",
                kind="fraction",
                unit="one",
                role=MathQuantityRole.RESULT,
                label="Kết quả phép tính phân số",
            )]

        rectangle = extract_rectangle_dimensions(self.source_text)
        if rectangle:
            self.problem_type = "rectangle_area"
            self.domain = MathDomain.GEOMETRY_2D
            self.quantities = [
                MathQuantity(id="rectangle_length", value=rectangle.length, unit=rectangle.unit, role=MathQuantityRole.LENGTH, label="Chiều dài hình chữ nhật"),
                MathQuantity(id="rectangle_width", value=rectangle.width, unit=rectangle.unit, role=MathQuantityRole.WIDTH, label="Chiều rộng hình chữ nhật"),
            ]
            self.unknowns = [MathUnknown(id="rectangle_area", kind="area", unit=f"{rectangle.unit}2", role=MathQuantityRole.RESULT, label="Diện tích hình chữ nhật")]

        equation = extract_linear_equation(self.source_text)
        if equation and not parse_fractional_linear_equation(self.source_text):
            equation_form = classify_linear(self.source_text)
            stages = (
                transformation_stages(equation_form.form)
                if equation_form and equation_form.form
                else []
            )
            self.problem_type = (
                "compound_linear_equation"
                if equation_form and equation_form.form and equation_form.form.needs_expansion
                else "linear_equation"
            )
            self.domain = MathDomain.ALGEBRA
            self.quantities = [
                MathQuantity(id="equation_coefficient", value=equation.coefficient, unit="one", role=MathQuantityRole.COEFFICIENT, label="Hệ số của x"),
                MathQuantity(id="equation_constant", value=equation.constant, unit="one", role=MathQuantityRole.CONSTANT, label="Hằng số ở vế trái"),
                MathQuantity(id="equation_right_side", value=equation.result, unit="one", role=MathQuantityRole.RESULT, label="Giá trị vế phải"),
            ]
            self.unknowns = [MathUnknown(id="equation_variable", kind="variable", unit="one", role=MathQuantityRole.VARIABLE, label="Giá trị của x")]
            self.relations = [SemanticRelation(
                id="linear_equation_stages",
                type="linear_equation_stages",
                participants={
                    "coefficient": "equation_coefficient",
                    "constant": "equation_constant",
                    "result": "equation_right_side",
                },
                parameters={"stages": stages},
                evidence=Evidence(
                    confidence=1.0,
                    source=EvidenceSource.SYSTEM,
                    status=EvidenceStatus.INFERRED,
                ),
            )]

        system = extract_linear_system(self.source_text)
        if system:
            three_variables = len(system.variables) == 3
            self.problem_type = (
                "linear_system_three_variables_planes"
                if three_variables
                else "linear_system_two_variables_graph"
            )
            self.domain = MathDomain.GEOMETRY_3D if three_variables else MathDomain.COORDINATE
            explicit = Evidence(
                confidence=1.0,
                source=EvidenceSource.SYSTEM,
                status=EvidenceStatus.EXPLICIT,
            )
            quantities: list[MathQuantity] = []
            participants: dict[str, str] = {}
            for index, form in enumerate(system.forms, start=1):
                names = tuple(
                    (
                        f"system_{index}_{name}",
                        name,
                        MathQuantityRole.COEFFICIENT,
                        form.coefficient(name),
                    )
                    for name in system.variables
                ) + ((f"system_{index}_right", "vế phải", MathQuantityRole.CONSTANT, form.constant),)
                for identifier, symbol, role, value in names:
                    quantities.append(MathQuantity(
                        id=identifier,
                        value=value,
                        unit="one",
                        role=role,
                        label=f"Hệ số của {symbol} ở phương trình {index}"
                        if role == MathQuantityRole.COEFFICIENT
                        else f"Vế phải của phương trình {index}",
                        evidence=explicit,
                    ))
                    participants[identifier] = identifier
            self.quantities = quantities
            self.unknowns = (
                [
                    MathUnknown(id=f"system_{name}", kind="variable", unit="one", role=MathQuantityRole.VARIABLE, label=f"Giá trị của {name}")
                    for name in system.variables
                ]
                if system.state in {"intersecting", "unique"}
                else [MathUnknown(id="system_state", kind="solution_set", unit="one", role=MathQuantityRole.RESULT, label="Tập nghiệm của hệ phương trình")]
            )
            self.relations = [SemanticRelation(
                id="linear_system",
                type="linear_system",
                participants=participants,
                parameters={
                    "coordinate_system": "Oxyz" if three_variables else "Oxy",
                    "symbols": list(system.variables),
                    "first_symbol": system.variables[0],
                    "second_symbol": system.variables[1],
                    "state": system.state,
                    "coefficient_rank": system.coefficient_rank,
                    "augmented_rank": system.augmented_rank,
                    "equations": [
                        [form.coefficient(name) for name in system.variables] + [form.constant]
                        for form in system.forms
                    ],
                    "canonical_forms": [format_canonical(form) for form in system.forms],
                    "solution": list(system.solution) if system.solution is not None else None,
                    "solution_exact": list(system.solution_exact) if system.solution_exact is not None else None,
                    "elimination_steps": list(system.elimination_steps),
                },
                evidence=explicit,
            )]

        degenerate = classify_linear(self.source_text)
        if degenerate and degenerate.kind in {"identity", "contradiction"}:
            self.problem_type = f"linear_{degenerate.kind}"
            self.domain = MathDomain.ALGEBRA
            self.quantities = []
            self.unknowns = [MathUnknown(
                id="linear_solution_set",
                kind="solution_set",
                unit="one",
                role=MathQuantityRole.RESULT,
                label="Kết luận về tập nghiệm",
            )]
            self.relations = []

        two_variable_equation = extract_two_variable_linear_equation(self.source_text)
        already_a_linear_function = (
            self.problem_type.lower() == "linear_function"
            and any(item.role == MathQuantityRole.COEFFICIENT for item in self.quantities)
            and any(item.role == MathQuantityRole.CONSTANT for item in self.quantities)
        )
        if two_variable_equation and not already_a_linear_function:
            self.problem_type = "linear_equation_two_variables_graph"
            self.domain = MathDomain.COORDINATE
            inferred = Evidence(
                confidence=1.0,
                source=EvidenceSource.SYSTEM,
                status=EvidenceStatus.INFERRED,
            )
            self.quantities = [
                MathQuantity(id="line_slope", value=two_variable_equation.slope, unit="one", role=MathQuantityRole.COEFFICIENT, label="Hệ số góc sau khi đưa về y = mx + b", evidence=inferred),
                MathQuantity(id="line_intercept", value=two_variable_equation.intercept, unit="one", role=MathQuantityRole.CONSTANT, label="Tung độ gốc sau khi đưa về y = mx + b", evidence=inferred),
            ]
            self.unknowns = [MathUnknown(
                id="line_solution_set",
                kind="graph",
                unit="one",
                role=MathQuantityRole.RESULT,
                label="Đường thẳng biểu diễn tập nghiệm trên Oxy",
            )]
            self.relations = [SemanticRelation(
                id="equivalent_linear_form",
                type="equivalent_linear_form",
                participants={"slope": "line_slope", "intercept": "line_intercept"},
                parameters={
                    "x_coefficient": two_variable_equation.x_coefficient,
                    "y_coefficient": two_variable_equation.y_coefficient,
                    "right_side": two_variable_equation.result,
                },
                evidence=inferred,
            )]

        three_variable_equation = extract_three_variable_linear_equation(self.source_text)
        if three_variable_equation:
            self.problem_type = "linear_equation_three_variables_plane"
            self.domain = MathDomain.GEOMETRY_3D
            self.quantities = [
                MathQuantity(id="plane_x_coefficient", value=three_variable_equation.x_coefficient, unit="one", role=MathQuantityRole.COEFFICIENT, label="Hệ số của x"),
                MathQuantity(id="plane_y_coefficient", value=three_variable_equation.y_coefficient, unit="one", role=MathQuantityRole.COEFFICIENT, label="Hệ số của y"),
                MathQuantity(id="plane_z_coefficient", value=three_variable_equation.z_coefficient, unit="one", role=MathQuantityRole.COEFFICIENT, label="Hệ số của z"),
                MathQuantity(id="plane_right_side", value=three_variable_equation.result, unit="one", role=MathQuantityRole.CONSTANT, label="Vế phải d"),
            ]
            self.unknowns = [MathUnknown(
                id="plane_solution_set",
                kind="plane",
                unit="one",
                role=MathQuantityRole.RESULT,
                label="Mặt phẳng biểu diễn tập nghiệm trên Oxyz",
            )]
            self.relations = [SemanticRelation(
                id="plane_equation",
                type="plane_equation",
                participants={"x": "plane_x_coefficient", "y": "plane_y_coefficient", "z": "plane_z_coefficient", "right_side": "plane_right_side"},
                parameters={"coordinate_system": "Oxyz"},
                evidence=Evidence(confidence=1.0, source=EvidenceSource.SYSTEM, status=EvidenceStatus.INFERRED),
            )]

        quadratic_surface = parse_quadratic_surface(self.source_text)
        if quadratic_surface:
            self.problem_type = "quadratic_surface_three_variables"
            self.domain = MathDomain.GEOMETRY_3D
            coefficient_terms = [
                (
                    f"surface_{quadratic_surface.squared_symbol}_squared",
                    quadratic_surface.squared_symbol,
                    2,
                    quadratic_surface.squared_coefficient,
                ),
                *[
                    (f"surface_{symbol}_linear", symbol, 1, quadratic_surface.linear_coefficients[symbol])
                    for symbol in ("x", "y", "z")
                    if abs(quadratic_surface.linear_coefficients.get(symbol, 0.0)) > 1e-12
                ],
            ]
            self.quantities = [
                MathQuantity(
                    id=identifier,
                    value=value,
                    unit="one",
                    role=MathQuantityRole.COEFFICIENT,
                    label=f"Hệ số của {symbol}{'²' if exponent == 2 else ''}",
                )
                for identifier, symbol, exponent, value in coefficient_terms
            ] + [MathQuantity(
                id="surface_right_side",
                value=quadratic_surface.right_side,
                unit="one",
                role=MathQuantityRole.CONSTANT,
                label="Vế phải sau khi chuyển vế",
            )]
            self.unknowns = [MathUnknown(
                id="quadratic_surface_solution",
                kind="quadratic_surface",
                unit="one",
                role=MathQuantityRole.RESULT,
                label="Mặt cong biểu diễn tập nghiệm trên Oxyz",
            )]
            self.relations = [SemanticRelation(
                id="quadratic_surface",
                type="quadratic_surface",
                participants={
                    **{f"term_{index}": item[0] for index, item in enumerate(coefficient_terms, start=1)},
                    "right_side": "surface_right_side",
                },
                parameters={
                    "squared_symbol": quadratic_surface.squared_symbol,
                    "squared_coefficient": quadratic_surface.squared_coefficient,
                    "linear_coefficients": quadratic_surface.linear_coefficients,
                    "right_side": quadratic_surface.right_side,
                    "output_symbol": quadratic_surface.output_symbol,
                    "coordinate_system": "Oxyz",
                },
                evidence=Evidence(
                    confidence=1.0,
                    source=EvidenceSource.SYSTEM,
                    status=EvidenceStatus.EXPLICIT,
                ),
            )]

        linear_expression = extract_single_variable_linear_expression(self.source_text)
        if linear_expression:
            self.problem_type = "polynomial_evaluate_reorder"
            self.domain = MathDomain.ALGEBRA
            self.quantities = [
                MathQuantity(id="linear_x_coefficient", value=linear_expression.coefficient, unit="one", role=MathQuantityRole.COEFFICIENT, label="Hệ số của hạng tử x"),
                MathQuantity(id="linear_x_exponent", value=1, unit="one", role=MathQuantityRole.EXPONENT, label="Bậc của hạng tử x"),
                MathQuantity(id="linear_constant_coefficient", value=linear_expression.constant, unit="one", role=MathQuantityRole.COEFFICIENT, label="Hệ số của hạng tử đơn vị"),
                MathQuantity(id="linear_constant_exponent", value=0, unit="one", role=MathQuantityRole.EXPONENT, label="Bậc của hạng tử đơn vị"),
            ]
            self.unknowns = [MathUnknown(
                id="expression_model",
                kind="expression_model",
                unit="one",
                role=MathQuantityRole.RESULT,
                label="Mô hình tile của biểu thức",
            )]
            self.relations = []

        triangle = extract_right_triangle(self.source_text)
        if triangle and (
            len(triangle.sides) >= 2
            or (len(triangle.sides) >= 1 and len(triangle.angles) >= 1)
        ):
            hypotenuse = triangle.hypotenuse_name
            known = sorted(triangle.sides)[:2]
            missing = next(
                (name for name in (*triangle.leg_names, hypotenuse) if name not in triangle.sides),
                None,
            )
            from_angle = len(known) == 1 and bool(triangle.angles)
            solve_all = triangle.solve_all or hypotenuse in triangle.sides or from_angle
            self.problem_type = (
                "right_triangle_solution" if solve_all else "right_triangle_hypotenuse"
            )
            self.domain = MathDomain.GEOMETRY_2D
            roles = (MathQuantityRole.LENGTH, MathQuantityRole.HEIGHT)
            identifiers = ("right_triangle_side_a", "right_triangle_side_b")
            self.quantities = [
                MathQuantity(
                    id=identifiers[index],
                    value=triangle.sides[name],
                    unit=triangle.unit,
                    role=roles[index],
                    label=(
                        f"Cạnh huyền {name}" if name == hypotenuse
                        else f"Cạnh góc vuông {name}"
                    ),
                )
                for index, name in enumerate(known)
            ] + [
                MathQuantity(
                    id=f"right_triangle_given_angle_{vertex.lower()}",
                    value=degrees,
                    unit="degree",
                    role=MathQuantityRole.ANGLE,
                    label=f"Góc {vertex}",
                )
                for vertex, degrees in sorted(triangle.angles.items())
            ]
            missing_sides = [
                name for name in (*triangle.leg_names, hypotenuse) if name not in triangle.sides
            ]
            unknowns: list[MathUnknown] = [
                MathUnknown(
                    id=f"right_triangle_missing_{name.lower()}",
                    kind="length",
                    unit=triangle.unit,
                    role=MathQuantityRole.RESULT,
                    label=(
                        f"Độ dài cạnh huyền {name}" if name == hypotenuse
                        else f"Độ dài cạnh góc vuông {name}"
                    ),
                )
                for name in missing_sides
            ]
            if solve_all:
                unknowns.extend(
                    MathUnknown(
                        id=f"right_triangle_angle_{vertex.lower()}",
                        kind="angle",
                        unit="degree",
                        role=MathQuantityRole.ANGLE,
                        label=f"Số đo góc {vertex}",
                    )
                    for vertex in triangle.acute_vertices
                    if vertex not in triangle.angles
                )
            self.unknowns = unknowns or [MathUnknown(
                id="right_triangle_missing_side",
                kind="length",
                unit=triangle.unit,
                role=MathQuantityRole.RESULT,
                label="Yếu tố còn lại của tam giác",
            )]
            self.relations = [SemanticRelation(
                id="right_triangle",
                type="right_triangle",
                participants={
                    f"side_{index}": identifiers[index]
                    for index in range(len(known))
                },
                parameters={
                    "vertices": triangle.vertices,
                    "right_vertex": triangle.right_vertex,
                    "hypotenuse": hypotenuse,
                    "legs": list(triangle.leg_names),
                    "known_sides": {name: triangle.sides[name] for name in known},
                    "known_angles": dict(triangle.angles),
                    "unit": triangle.unit,
                    "solve_all": solve_all,
                    "round_to_minute": triangle.round_to_minute,
                },
                evidence=Evidence(
                    confidence=1.0,
                    source=EvidenceSource.SYSTEM,
                    status=EvidenceStatus.EXPLICIT,
                ),
            )]
        elif "right_triangle" in self.problem_type.lower() and len(self.quantities) >= 2:
            # Legacy fixtures/history may carry two explicit side values but no
            # semantic roles. Assign only the two printed legs; no hypotenuse is
            # calculated or stored here.
            self.quantities[0].role = MathQuantityRole.LENGTH
            self.quantities[0].label = self.quantities[0].label or "Cạnh góc vuông thứ nhất"
            self.quantities[1].role = MathQuantityRole.HEIGHT
            self.quantities[1].label = self.quantities[1].label or "Cạnh góc vuông thứ hai"

        angle_of_depression = extract_angle_of_depression(self.source_text)
        if angle_of_depression:
            self.problem_type = "angle_of_depression_distance"
            self.domain = MathDomain.GEOMETRY_2D
            self.quantities = [
                MathQuantity(
                    id="trig_height",
                    value=angle_of_depression.height,
                    unit=angle_of_depression.unit,
                    role=MathQuantityRole.HEIGHT,
                    label="Chiều cao điểm quan sát",
                ),
                MathQuantity(
                    id="trig_angle",
                    value=angle_of_depression.angle,
                    unit="degree",
                    role=MathQuantityRole.ANGLE,
                    label="Góc nghiêng xuống",
                ),
            ]
            self.unknowns = [MathUnknown(
                id="trig_horizontal_distance",
                kind="distance",
                unit=angle_of_depression.unit,
                role=MathQuantityRole.RESULT,
                label="Khoảng cách ngang đến chân công trình",
            )]
            self.relations = [SemanticRelation(
                id="angle_of_depression",
                type="trigonometric_geometry",
                participants={"height": "trig_height", "angle": "trig_angle"},
                parameters={
                    "kind": "angle_of_depression",
                    "height": angle_of_depression.height,
                    "angle": angle_of_depression.angle,
                    "unit": angle_of_depression.unit,
                    "landmark": angle_of_depression.landmark,
                },
                evidence=Evidence(
                    confidence=1.0,
                    source=EvidenceSource.SYSTEM,
                    status=EvidenceStatus.EXPLICIT,
                ),
            )]

        oblique_triangle = extract_oblique_triangle_altitude(self.source_text)
        if oblique_triangle:
            self.problem_type = "oblique_triangle_altitude_solution"
            self.domain = MathDomain.GEOMETRY_2D
            angle_items = list(oblique_triangle.base_angles.items())
            self.quantities = [MathQuantity(
                id="oblique_height",
                value=oblique_triangle.height,
                unit=oblique_triangle.unit,
                role=MathQuantityRole.HEIGHT,
                label=f"Đường cao {oblique_triangle.apex}{oblique_triangle.foot}",
            )] + [
                MathQuantity(
                    id=f"oblique_angle_{vertex.lower()}",
                    value=value,
                    unit="degree",
                    role=MathQuantityRole.ANGLE,
                    label=f"Góc {vertex}",
                )
                for vertex, value in angle_items
            ]
            self.unknowns = [
                MathUnknown(
                    id=f"oblique_side_{index}",
                    kind="length",
                    unit=oblique_triangle.unit,
                    role=MathQuantityRole.RESULT,
                    label=f"Độ dài cạnh {name}",
                )
                for index, name in enumerate((
                    "".join(sorted(oblique_triangle.apex + vertex))
                    for vertex in oblique_triangle.vertices
                    if vertex != oblique_triangle.apex
                ), start=1)
            ]
            base_name = "".join(
                vertex for vertex in oblique_triangle.vertices
                if vertex != oblique_triangle.apex
            )
            self.unknowns.append(MathUnknown(
                id="oblique_base",
                kind="length",
                unit=oblique_triangle.unit,
                role=MathQuantityRole.RESULT,
                label=f"Độ dài cạnh {base_name}",
            ))
            self.relations = [SemanticRelation(
                id="oblique_triangle_altitude",
                type="trigonometric_geometry",
                participants={
                    "height": "oblique_height",
                    "first_angle": f"oblique_angle_{angle_items[0][0].lower()}",
                    "second_angle": f"oblique_angle_{angle_items[1][0].lower()}",
                },
                parameters={
                    "kind": "oblique_triangle_altitude",
                    "vertices": oblique_triangle.vertices,
                    "apex": oblique_triangle.apex,
                    "foot": oblique_triangle.foot,
                    "height": oblique_triangle.height,
                    "angles": oblique_triangle.base_angles,
                    "unit": oblique_triangle.unit,
                },
                evidence=Evidence(
                    confidence=1.0,
                    source=EvidenceSource.SYSTEM,
                    status=EvidenceStatus.EXPLICIT,
                ),
            )]

        parallelogram = extract_perpendicular_diagonal_parallelogram(self.source_text)
        if parallelogram:
            self.problem_type = "parallelogram_perpendicular_diagonal_area"
            self.domain = MathDomain.GEOMETRY_2D
            side_role = (
                MathQuantityRole.LENGTH
                if parallelogram.unit != "one"
                else MathQuantityRole.COUNT_INITIAL
            )
            self.quantities = [
                MathQuantity(
                    id="parallelogram_side",
                    value=parallelogram.side_length,
                    unit=parallelogram.unit,
                    role=side_role,
                    label=f"Độ dài cạnh {parallelogram.side}",
                ),
                MathQuantity(
                    id="parallelogram_angle",
                    value=parallelogram.angle,
                    unit="degree",
                    role=MathQuantityRole.ANGLE,
                    label=f"Góc {parallelogram.angle_vertex}",
                ),
            ]
            self.unknowns = [MathUnknown(
                id="parallelogram_area",
                kind="area",
                unit=(f"{parallelogram.unit}2" if parallelogram.unit != "one" else "one"),
                role=MathQuantityRole.RESULT,
                label="Diện tích hình bình hành",
            )]
            self.relations = [SemanticRelation(
                id="parallelogram_perpendicular_diagonal",
                type="trigonometric_geometry",
                participants={"side": "parallelogram_side", "angle": "parallelogram_angle"},
                parameters={
                    "kind": "parallelogram_perpendicular_diagonal",
                    "vertices": parallelogram.vertices,
                    "diagonal": parallelogram.diagonal,
                    "side": parallelogram.side,
                    "side_length": parallelogram.side_length,
                    "angle_vertex": parallelogram.angle_vertex,
                    "angle": parallelogram.angle,
                    "unit": parallelogram.unit,
                },
                evidence=Evidence(
                    confidence=1.0,
                    source=EvidenceSource.SYSTEM,
                    status=EvidenceStatus.EXPLICIT,
                ),
            )]

        discount_system = extract_two_item_discount_system(self.source_text)
        if discount_system:
            self.problem_type = "two_item_discount_system"
            self.domain = MathDomain.ALGEBRA
            self.quantities = [
                MathQuantity(
                    id="discount_list_total",
                    value=discount_system.list_total,
                    unit="one",
                    role=MathQuantityRole.TOTAL,
                    label="Tổng giá niêm yết của hai quyển sách (đồng)",
                ),
                MathQuantity(
                    id="discount_paid_total",
                    value=discount_system.paid_total,
                    unit="one",
                    role=MathQuantityRole.TOTAL,
                    label="Tổng số tiền thực trả (đồng)",
                ),
                MathQuantity(
                    id="discount_first_rate",
                    value=discount_system.first_discount,
                    unit="one",
                    role=MathQuantityRole.PROBABILITY,
                    label=f"Mức giảm của {discount_system.first_label} (%)",
                ),
                MathQuantity(
                    id="discount_second_rate",
                    value=discount_system.second_discount,
                    unit="one",
                    role=MathQuantityRole.PROBABILITY,
                    label=f"Mức giảm của {discount_system.second_label} (%)",
                ),
            ]
            self.unknowns = [
                MathUnknown(
                    id="discount_first_price",
                    kind="money",
                    unit="one",
                    role=MathQuantityRole.VARIABLE,
                    label=f"Giá niêm yết {discount_system.first_label} (x, đồng)",
                ),
                MathUnknown(
                    id="discount_second_price",
                    kind="money",
                    unit="one",
                    role=MathQuantityRole.VARIABLE,
                    label=f"Giá niêm yết {discount_system.second_label} (y, đồng)",
                ),
            ]
            self.relations = [SemanticRelation(
                id="two_item_discount_system",
                type="two_item_discount_system",
                participants={
                    "list_total": "discount_list_total",
                    "paid_total": "discount_paid_total",
                    "first_discount": "discount_first_rate",
                    "second_discount": "discount_second_rate",
                    "first_price": "discount_first_price",
                    "second_price": "discount_second_price",
                },
                parameters={
                    "first_label": discount_system.first_label,
                    "second_label": discount_system.second_label,
                    "first_symbol": discount_system.first_symbol,
                    "second_symbol": discount_system.second_symbol,
                    "claimed_first": discount_system.claimed_first,
                    "claimed_second": discount_system.claimed_second,
                },
                evidence=Evidence(
                    confidence=1.0,
                    source=EvidenceSource.SYSTEM,
                    status=EvidenceStatus.EXPLICIT,
                ),
            )]

        area_remainder = extract_sequential_fraction_remainder_area(self.source_text)
        if area_remainder:
            # Migrate both fresh compact-model output and history written by an
            # older build. The operation is renderer-generic: a total quantity,
            # a fraction of it, then a fraction of the changing remainder.
            self.problem_type = "sequential_fraction_remainder_quantity"
            self.domain = MathDomain.RATIO
            self.quantities = []
            for index, component in enumerate(area_remainder.area_components, 1):
                printed = f"{component.printed_value:g} {component.printed_unit}²"
                normalized = f"{component.value_m2:g} m²"
                self.quantities.append(MathQuantity(
                    id=f"area_component_{index}",
                    value=component.value_m2,
                    unit="m2",
                    role=MathQuantityRole.AREA,
                    label=(
                        f"{printed} = {normalized}"
                        if component.printed_unit != "m"
                        else printed
                    ),
                    evidence=Evidence(
                        confidence=1.0,
                        status=(
                            EvidenceStatus.INFERRED
                            if component.printed_unit != "m"
                            else EvidenceStatus.EXPLICIT
                        ),
                        source=(
                            EvidenceSource.SYSTEM
                            if component.printed_unit != "m"
                            else EvidenceSource.TEXT_INPUT
                        ),
                    ),
                ))
            self.quantities.extend([
                MathQuantity(
                    id="first_fraction_numerator",
                    value=area_remainder.first_numerator,
                    unit="one",
                    role=MathQuantityRole.NUMERATOR,
                    label="Tử số phần dùng lần thứ nhất",
                ),
                MathQuantity(
                    id="first_fraction_denominator",
                    value=area_remainder.first_denominator,
                    unit="one",
                    role=MathQuantityRole.DENOMINATOR,
                    label="Mẫu số phần dùng lần thứ nhất",
                ),
                MathQuantity(
                    id="remainder_fraction_numerator",
                    value=area_remainder.second_numerator,
                    unit="one",
                    role=MathQuantityRole.ADDEND_NUMERATOR,
                    label="Tử số phần dùng từ phần còn lại",
                ),
                MathQuantity(
                    id="remainder_fraction_denominator",
                    value=area_remainder.second_denominator,
                    unit="one",
                    role=MathQuantityRole.ADDEND_DENOMINATOR,
                    label="Mẫu số phần dùng từ phần còn lại",
                ),
            ])
            result_unknown = next(
                (item for item in self.unknowns if item.role == MathQuantityRole.RESULT),
                None,
            )
            if result_unknown:
                result_unknown.kind = "area"
                result_unknown.unit = "m2"
                result_unknown.label = "Diện tích phần đất còn lại cuối cùng"
            else:
                self.unknowns.append(MathUnknown(
                    id="final_remaining_area",
                    kind="area",
                    unit="m2",
                    role=MathQuantityRole.RESULT,
                    label="Diện tích phần đất còn lại cuối cùng",
                ))

        if "work_rate_with_variable_people" in self.problem_type.lower():
            # History written by the pre-renderer build may contain the correct
            # source stem but an empty quantity list. Recover only the three
            # explicit printed operands; the requested completion time remains
            # unknown and is calculated later by the deterministic renderer.
            work_rate = extract_variable_people_work_rate(self.source_text)
            if work_rate and not self.quantities:
                self.domain = MathDomain.RATIO
                self.quantities = [
                    MathQuantity(
                        id="work_initial_workers",
                        value=work_rate.initial_workers,
                        unit="one",
                        role=MathQuantityRole.COUNT_INITIAL,
                        label="Số người ban đầu",
                    ),
                    MathQuantity(
                        id="work_planned_days",
                        value=work_rate.planned_days,
                        unit="one",
                        role=MathQuantityRole.DURATION,
                        label="Số ngày dự định",
                    ),
                    MathQuantity(
                        id="work_worker_change",
                        value=work_rate.worker_change,
                        unit="one",
                        role=MathQuantityRole.COUNT_CHANGE,
                        label=(
                            "Số người được bổ sung"
                            if work_rate.worker_change > 0
                            else "Số người rút bớt"
                        ),
                    ),
                ]
                result_unknown = next(
                    (item for item in self.unknowns if item.role == MathQuantityRole.RESULT),
                    None,
                )
                if result_unknown:
                    result_unknown.kind = "duration"
                    result_unknown.unit = "one"
                    result_unknown.label = "Số ngày hoàn thành sau khi thay đổi số người"
                else:
                    self.unknowns.append(MathUnknown(
                        id="work_new_days",
                        kind="duration",
                        unit="one",
                        role=MathQuantityRole.RESULT,
                        label="Số ngày hoàn thành sau khi thay đổi số người",
                    ))

        groups = [self.entities, self.quantities, self.unknowns, self.relations, self.constraints]
        ids = [item.id for group in groups for item in group]
        if len(ids) != len(set(ids)):
            raise ValueError("Semantic model IDs must be unique")
        reference_ids = {item.id for item in [*self.entities, *self.quantities, *self.unknowns]}
        for relation in self.relations:
            unknown = set(relation.participants.values()) - reference_ids
            if unknown:
                raise ValueError(f"Relation {relation.id} references unknown IDs: {sorted(unknown)}")
        for constraint in self.constraints:
            unknown = set(constraint.target_ids) - reference_ids
            if unknown:
                raise ValueError(f"Constraint {constraint.id} references unknown IDs: {sorted(unknown)}")

        # A work-rate scene treats days as discrete columns in a conserved
        # worker-day grid, not as seconds on a physical timeline.  Early Math
        # Lab clients did not yet include `day` in their unit allow-list.  This
        # migration also repairs already-saved history entries so an old tab can
        # consume the API response instead of failing before it asks for a plan.
        if "work_rate_with_variable_people" in self.problem_type.lower():
            for quantity in self.quantities:
                if quantity.role == MathQuantityRole.DURATION and quantity.unit == "day":
                    quantity.unit = "one"
            for unknown in self.unknowns:
                if unknown.kind.lower() == "duration" and unknown.unit == "day":
                    unknown.unit = "one"
        return self


class WorldValue(StrictModel):
    value: float | str | bool | None = None
    unit: str = Field(default="one", min_length=1, max_length=32)
    label: str | None = Field(default=None, max_length=160)
    canonical_value: float | None = None
    canonical_unit: str | None = Field(default=None, max_length=32)
    editable: bool = False
    minimum: float | None = None
    maximum: float | None = None
    step: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def valid_range(self) -> "WorldValue":
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise ValueError("World value minimum cannot exceed maximum")
        if isinstance(self.value, (int, float)):
            if self.minimum is not None and self.value < self.minimum:
                raise ValueError("World value is below minimum")
            if self.maximum is not None and self.value > self.maximum:
                raise ValueError("World value is above maximum")
        return self


class MathWorldState(StrictModel):
    revision: int = Field(default=0, ge=0)
    values: dict[Identifier, WorldValue] = Field(default_factory=dict)


class MathSceneObject(StrictModel):
    id: Identifier = Field(pattern=r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")
    type: str = Field(min_length=1, max_length=64)
    label: str | None = Field(default=None, max_length=160)
    semantic_ref: Identifier | None = None
    properties: dict[str, Any] = Field(default_factory=dict)


class VisualizationDescriptor(StrictModel):
    id: Identifier = Field(pattern=r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")
    type: VisualizationId
    bindings: dict[str, list[Identifier]] = Field(default_factory=dict)
    options: dict[str, Any] = Field(default_factory=dict)
    visible: bool = True


class SceneConstraint(StrictModel):
    id: Identifier = Field(pattern=r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")
    type: str = Field(min_length=1, max_length=64)
    target_ids: list[Identifier] = Field(min_length=1)
    parameters: dict[str, Any] = Field(default_factory=dict)
    locked: bool = True
    # Carried through from the semantic constraint so a renderer can tell a
    # stated fact from a guess. Without it a vision model's inference reaches
    # the screen looking exactly like something the problem said, which is the
    # one thing a teacher must never have to take on trust.
    evidence: Evidence = Field(default_factory=Evidence)


class MathStep(StrictModel):
    id: Identifier = Field(pattern=r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")
    action: Literal["show", "hide", "set", "transform", "highlight", "explain"]
    target_ids: list[Identifier] = Field(default_factory=list)
    changes: dict[str, Any] = Field(default_factory=dict)
    explanation: str | None = Field(default=None, max_length=1000)


class SceneAction(StrictModel):
    id: Identifier = Field(pattern=r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")
    type: Literal["play", "pause", "reset", "next", "previous", "why", "what_if", "set_value"]
    target_ids: list[Identifier] = Field(default_factory=list)
    parameters: dict[str, Any] = Field(default_factory=dict)


class MathScene(StrictModel):
    schema_version: Literal["1.0"] = SCHEMA_VERSION
    id: Identifier = Field(default="math_scene", pattern=r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")
    kind: str = Field(min_length=1, max_length=64)
    grade: int = Field(ge=1, le=9)
    semantic_model_id: Identifier
    world: MathWorldState
    objects: list[MathSceneObject] = Field(default_factory=list)
    visualizations: list[VisualizationDescriptor] = Field(min_length=1)
    constraints: list[SceneConstraint] = Field(default_factory=list)
    steps: list[MathStep] = Field(default_factory=list)
    actions: list[SceneAction] = Field(default_factory=list)
    verification_status: Literal["verified", "unverified", "failed"] = "unverified"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def unique_scene_ids(self) -> "MathScene":
        ids = [item.id for item in [*self.objects, *self.visualizations, *self.constraints, *self.steps, *self.actions]]
        if len(ids) != len(set(ids)):
            raise ValueError("MathScene IDs must be unique")
        object_ids = {item.id for item in self.objects}
        semantic_refs = {item.semantic_ref for item in self.objects if item.semantic_ref}
        known_targets = object_ids | semantic_refs | set(self.world.values)
        for constraint in self.constraints:
            unknown = set(constraint.target_ids) - known_targets
            if unknown:
                raise ValueError(f"Scene constraint {constraint.id} has unknown targets: {sorted(unknown)}")
        return self


class VisualizationDecision(StrictModel):
    visualization: VisualizationId
    score: float = Field(ge=0, le=1)
    reason: str = Field(min_length=1, max_length=500)
    source: Literal["rule", "teacher", "ai_suggestion"] = "rule"


class PedagogyRevealStep(StrictModel):
    id: Identifier = Field(pattern=r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")
    title: str = Field(min_length=1, max_length=160)
    goal: str = Field(min_length=1, max_length=500)
    visualization_ids: list[VisualizationId] = Field(default_factory=list)


class PedagogyPlan(StrictModel):
    grade_band: Literal["1-2", "3-4", "5-6", "7-9"]
    representation_level: Literal["concrete", "model", "symbol", "dynamic"]
    primary_visualization: VisualizationId
    supporting_visualizations: list[VisualizationId] = Field(default_factory=list)
    explanation_strategy: str = Field(min_length=1, max_length=500)
    interaction_strategy: list[str] = Field(default_factory=list)
    reveal_steps: list[PedagogyRevealStep] = Field(default_factory=list)


class VisualConcept(StrictModel):
    id: Identifier = Field(pattern=r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")
    type: VisualConceptType
    relationship_refs: list[Identifier] = Field(default_factory=list)
    quantity_refs: list[Identifier] = Field(default_factory=list)
    unknown_refs: list[Identifier] = Field(default_factory=list)
    explanation: str = Field(min_length=1, max_length=500)


class VisualPlanStage(StrictModel):
    id: Identifier = Field(pattern=r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")
    title: str = Field(min_length=1, max_length=160)
    goal: str = Field(min_length=1, max_length=500)
    primitive: VisualPrimitive
    bindings: dict[str, list[Identifier]] = Field(default_factory=dict)
    state_delta: dict[str, Any] = Field(default_factory=dict)
    oracle_checks: list[str] = Field(default_factory=list)


class VisualPlan(StrictModel):
    schema_version: Literal["1.0"] = SCHEMA_VERSION
    semantic_model_id: Identifier
    concepts: list[VisualConcept] = Field(min_length=1)
    stages: list[VisualPlanStage] = Field(min_length=1)
    primary_renderer: VisualizationId
    fallback_renderers: list[VisualizationId] = Field(default_factory=list)
    status: Literal["ready", "blocked"]
    verification_requirements: list[str] = Field(default_factory=list)


class MathLabPlanRequest(StrictModel):
    semantic_model: MathSemanticModel
    requested_visualizations: list[VisualizationId] | None = None


class MathLabPlanResponse(StrictModel):
    semantic_model: MathSemanticModel
    decisions: list[VisualizationDecision]
    pedagogy: PedagogyPlan
    visual_plan: VisualPlan
    scene: MathScene
    warnings: list[str] = Field(default_factory=list)


class MathLabCapabilities(StrictModel):
    text_analysis: bool
    image_analysis: bool
    provider_configured: bool
    provider_available: bool
    provider: str | None = None
    model: str | None = None
    accepted_image_types: list[str] = Field(default_factory=list)
    max_image_bytes: int = Field(ge=1)
    message: str | None = None


class MathTextAnalysisRequest(StrictModel):
    text: VerbatimText = Field(min_length=3, max_length=20_000)
    grade_hint: int | None = Field(default=None, ge=1, le=9)

    @field_validator("text")
    @classmethod
    def text_must_contain_visible_content(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text must contain visible content")
        return value


class MathSubquestionAnalysis(StrictModel):
    id: Identifier = Field(pattern=r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")
    label: str = Field(min_length=1, max_length=64)
    text: str = Field(min_length=1, max_length=10_000)


class MathQuestionAnalysis(StrictModel):
    id: Identifier = Field(pattern=r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")
    question_number: str = Field(min_length=1, max_length=32)
    stem: VerbatimText = Field(min_length=1, max_length=20_000)
    question_format: QuestionFormat
    choices: list[str] = Field(default_factory=list, max_length=12)
    subquestions: list[MathSubquestionAnalysis] = Field(default_factory=list, max_length=20)
    semantic_model: MathSemanticModel
    confidence: float = Field(ge=0, le=1)
    requires_review: bool = False
    review_notes: list[str] = Field(default_factory=list, max_length=20)


class MathDocumentDraft(StrictModel):
    extracted_text: VerbatimText = Field(min_length=1, max_length=100_000)
    questions: list[MathQuestionAnalysis] = Field(min_length=1, max_length=100)
    confidence: float = Field(ge=0, le=1)
    requires_review: bool = False


class MathDocumentAnalysis(MathDocumentDraft):
    source_type: Literal["text", "image"]
    provider: str
    model: str


class MathLabHistoryCreate(StrictModel):
    source_type: Literal["text", "image"]
    semantic_model: MathSemanticModel


class MathLabHistoryEntry(StrictModel):
    id: UUID
    created_at: datetime
    source_type: Literal["text", "image"]
    source_text: str | None = Field(default=None, max_length=20_000)
    grade: int = Field(ge=1, le=9)
    domain: MathDomain
    problem_type: str = Field(min_length=1, max_length=96)
    semantic_model: MathSemanticModel

    @model_validator(mode="after")
    def sync_summary_with_repaired_semantics(self) -> "MathLabHistoryEntry":
        """Keep legacy history labels aligned with the repaired semantic payload."""

        self.source_text = self.semantic_model.source_text
        self.grade = self.semantic_model.grade
        self.domain = self.semantic_model.domain
        self.problem_type = self.semantic_model.problem_type
        return self


class MathLabHistoryList(StrictModel):
    items: list[MathLabHistoryEntry] = Field(max_length=5)


class MathLabFeedbackCreate(StrictModel):
    history_id: UUID | None = None
    rating: Literal["correct", "partly_correct", "incorrect"]
    category: Literal[
        "ocr", "classification", "calculation", "visualization", "pedagogy", "other"
    ]
    comment: str | None = Field(default=None, max_length=4_000)
    expected_correction: str | None = Field(default=None, max_length=4_000)
    semantic_model: MathSemanticModel
    scene: MathScene


class MathLabFeedbackReceipt(StrictModel):
    id: UUID
    status: Literal["pending_review"]
    created_at: datetime
    message: str
