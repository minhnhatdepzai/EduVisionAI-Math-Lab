from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass
from typing import Annotated, Any, Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, ValidationError, field_validator, model_validator

from app.core.config import Settings
from app.schemas.math_lab import (
    Evidence,
    EvidenceSource,
    EvidenceStatus,
    MathDocumentAnalysis,
    MathDomain,
    MathLabCapabilities,
    MathQuantity,
    MathQuantityRole,
    MathQuestionAnalysis,
    MathSemanticModel,
    MathSubquestionAnalysis,
    MathUnit,
    MathUnknown,
    QuestionFormat,
    SemanticConstraint,
    SemanticEntity,
    SemanticRelation,
    TimeContext,
)
from app.schemas.math_lab_input import canonical_problem_type
from app.schemas.math_lab_linear import (
    LinearSystem,
    classify_linear,
    format_canonical,
    parse_linear_inequality,
    parse_product_equation,
    parse_rational_domain,
    transformation_stages,
)
from app.schemas.math_lab_equations import (
    AbsoluteValueEquation,
    BiquadraticEquation,
    FractionalLinearEquation,
    RadicalEquation,
    RationalEquation,
    parse_absolute_value_equation,
    parse_biquadratic_equation,
    parse_fractional_linear_equation,
    parse_radical_equation,
    parse_rational_equation,
)
from app.schemas.math_lab_nonlinear import (
    CubicEquationForm,
    QuadraticEquationForm,
    QuadraticSurfaceForm,
    parse_cubic_equation,
    parse_quadratic_equation,
    parse_quadratic_surface,
)
from app.schemas.math_lab_text import (
    AngleOfDepressionFacts,
    ObliqueTriangleAltitudeFacts,
    PerpendicularDiagonalParallelogramFacts,
    RightTriangleFacts,
    TwoItemDiscountSystemFacts,
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
from app.services.math_lab.units import UnitConversionError, canonicalize


ACCEPTED_IMAGE_TYPES = ("image/jpeg", "image/png", "image/webp")


def _angle_of_depression_semantics(
    facts: "AngleOfDepressionFacts",
) -> tuple[list["ProviderQuantity"], list["ProviderUnknown"], "ProviderRelation"]:
    explicit = ProviderEvidence(confidence=1.0, status=EvidenceStatus.EXPLICIT)
    quantities = [
        ProviderQuantity(
            role=MathQuantityRole.HEIGHT,
            value=facts.height,
            unit=facts.unit,
            label="Chiều cao điểm quan sát",
            evidence=explicit,
        ),
        ProviderQuantity(
            role=MathQuantityRole.ANGLE,
            value=facts.angle,
            unit="degree",
            label="Góc nghiêng xuống",
            evidence=explicit,
        ),
    ]
    unknowns = [ProviderUnknown(
        role=MathQuantityRole.RESULT,
        kind="distance",
        unit=facts.unit,
        label="Khoảng cách ngang đến chân công trình",
    )]
    relation = ProviderRelation(
        type="trigonometric_geometry",
        participant_roles={"height": "height", "angle": "angle"},
        parameters={
            "kind": "angle_of_depression",
            "height": facts.height,
            "angle": facts.angle,
            "unit": facts.unit,
            "landmark": facts.landmark,
        },
        evidence=explicit,
    )
    return quantities, unknowns, relation


def _oblique_triangle_altitude_semantics(
    facts: "ObliqueTriangleAltitudeFacts",
) -> tuple[list["ProviderQuantity"], list["ProviderUnknown"], "ProviderRelation"]:
    explicit = ProviderEvidence(confidence=1.0, status=EvidenceStatus.EXPLICIT)
    quantities = [ProviderQuantity(
        role=MathQuantityRole.HEIGHT,
        value=facts.height,
        unit=facts.unit,
        label=f"Đường cao {facts.apex}{facts.foot}",
        evidence=explicit,
    )]
    quantities.extend(
        ProviderQuantity(
            role=MathQuantityRole.ANGLE,
            value=value,
            unit="degree",
            label=f"Góc {vertex}",
            evidence=explicit,
        )
        for vertex, value in facts.base_angles.items()
    )
    unknowns = [
        ProviderUnknown(
            role=MathQuantityRole.RESULT,
            kind="length",
            unit=facts.unit,
            label=f"Độ dài cạnh {name}",
        )
        for name in (
            "".join(sorted(facts.apex + vertex))
            for vertex in facts.vertices
            if vertex != facts.apex
        )
    ]
    base = "".join(vertex for vertex in facts.vertices if vertex != facts.apex)
    unknowns.append(ProviderUnknown(
        role=MathQuantityRole.RESULT,
        kind="length",
        unit=facts.unit,
        label=f"Độ dài cạnh {base}",
    ))
    relation = ProviderRelation(
        type="trigonometric_geometry",
        participant_roles={
            "height": "height",
            "first_angle": "angle[1]",
            "second_angle": "angle[2]",
        },
        parameters={
            "kind": "oblique_triangle_altitude",
            "vertices": facts.vertices,
            "apex": facts.apex,
            "foot": facts.foot,
            "height": facts.height,
            "angles": facts.base_angles,
            "unit": facts.unit,
        },
        evidence=explicit,
    )
    return quantities, unknowns, relation


def _parallelogram_diagonal_semantics(
    facts: "PerpendicularDiagonalParallelogramFacts",
) -> tuple[list["ProviderQuantity"], list["ProviderUnknown"], "ProviderRelation"]:
    explicit = ProviderEvidence(confidence=1.0, status=EvidenceStatus.EXPLICIT)
    length_role = (
        MathQuantityRole.LENGTH if facts.unit != "one" else MathQuantityRole.COUNT_INITIAL
    )
    quantities = [
        ProviderQuantity(
            role=length_role,
            value=facts.side_length,
            unit=facts.unit,
            label=f"Độ dài cạnh {facts.side}",
            evidence=explicit,
        ),
        ProviderQuantity(
            role=MathQuantityRole.ANGLE,
            value=facts.angle,
            unit="degree",
            label=f"Góc {facts.angle_vertex}",
            evidence=explicit,
        ),
    ]
    unknowns = [ProviderUnknown(
        role=MathQuantityRole.RESULT,
        kind="area",
        unit=f"{facts.unit}2" if facts.unit != "one" else "one",
        label="Diện tích hình bình hành",
    )]
    relation = ProviderRelation(
        type="trigonometric_geometry",
        participant_roles={"side": length_role.value, "angle": "angle"},
        parameters={
            "kind": "parallelogram_perpendicular_diagonal",
            "vertices": facts.vertices,
            "diagonal": facts.diagonal,
            "side": facts.side,
            "side_length": facts.side_length,
            "angle_vertex": facts.angle_vertex,
            "angle": facts.angle,
            "unit": facts.unit,
        },
        evidence=explicit,
    )
    return quantities, unknowns, relation


def _two_item_discount_system_semantics(
    facts: "TwoItemDiscountSystemFacts",
) -> tuple[list["ProviderQuantity"], list["ProviderUnknown"], "ProviderRelation"]:
    """Keep only the four printed constraints; both prices stay unknown."""

    explicit = ProviderEvidence(confidence=1.0, status=EvidenceStatus.EXPLICIT)
    quantities = [
        ProviderQuantity(
            role=MathQuantityRole.TOTAL,
            value=facts.list_total,
            unit="one",
            label="Tổng giá niêm yết của hai quyển sách (đồng)",
            evidence=explicit,
        ),
        ProviderQuantity(
            role=MathQuantityRole.TOTAL,
            value=facts.paid_total,
            unit="one",
            label="Tổng số tiền thực trả (đồng)",
            evidence=explicit,
        ),
        ProviderQuantity(
            role=MathQuantityRole.PROBABILITY,
            value=facts.first_discount,
            unit="one",
            label=f"Mức giảm của {facts.first_label} (%)",
            evidence=explicit,
        ),
        ProviderQuantity(
            role=MathQuantityRole.PROBABILITY,
            value=facts.second_discount,
            unit="one",
            label=f"Mức giảm của {facts.second_label} (%)",
            evidence=explicit,
        ),
    ]
    unknowns = [
        ProviderUnknown(
            role=MathQuantityRole.VARIABLE,
            kind="money",
            unit="one",
            label=f"Giá niêm yết {facts.first_label} ({facts.first_symbol}, đồng)",
        ),
        ProviderUnknown(
            role=MathQuantityRole.VARIABLE,
            kind="money",
            unit="one",
            label=f"Giá niêm yết {facts.second_label} ({facts.second_symbol}, đồng)",
        ),
    ]
    relation = ProviderRelation(
        type="two_item_discount_system",
        participant_roles={
            "list_total": "total[1]",
            "paid_total": "total[2]",
            "first_discount": "probability[1]",
            "second_discount": "probability[2]",
            "first_price": "variable[1]",
            "second_price": "variable[2]",
        },
        parameters={
            "first_label": facts.first_label,
            "second_label": facts.second_label,
            "first_symbol": facts.first_symbol,
            "second_symbol": facts.second_symbol,
            "claimed_first": facts.claimed_first,
            "claimed_second": facts.claimed_second,
        },
        evidence=explicit,
    )
    return quantities, unknowns, relation


def _quadratic_surface_semantics(
    surface: "QuadraticSurfaceForm",
) -> tuple[list["ProviderQuantity"], list["ProviderUnknown"], "ProviderRelation"]:
    explicit = ProviderEvidence(confidence=1.0, status=EvidenceStatus.EXPLICIT)
    coefficient_terms = [
        (surface.squared_symbol, 2, surface.squared_coefficient),
        *[
            (symbol, 1, surface.linear_coefficients[symbol])
            for symbol in ("x", "y", "z")
            if abs(surface.linear_coefficients.get(symbol, 0.0)) > 1e-12
        ],
    ]
    quantities = [
        ProviderQuantity(
            role=MathQuantityRole.COEFFICIENT,
            value=value,
            unit="one",
            label=f"Hệ số của {symbol}{'²' if exponent == 2 else ''}",
            evidence=explicit,
        )
        for symbol, exponent, value in coefficient_terms
    ]
    quantities.append(ProviderQuantity(
        role=MathQuantityRole.CONSTANT,
        value=surface.right_side,
        unit="one",
        label="Vế phải sau khi chuyển vế",
        evidence=explicit,
    ))
    unknowns = [ProviderUnknown(
        role=MathQuantityRole.RESULT,
        kind="quadratic_surface",
        unit="one",
        label="Mặt cong biểu diễn tập nghiệm trên Oxyz",
    )]
    relation = ProviderRelation(
        type="quadratic_surface",
        participant_roles={
            **{
                f"term_{index}": f"coefficient[{index}]"
                for index in range(1, len(coefficient_terms) + 1)
            },
            "right_side": "constant",
        },
        parameters={
            "squared_symbol": surface.squared_symbol,
            "squared_coefficient": surface.squared_coefficient,
            "linear_coefficients": surface.linear_coefficients,
            "right_side": surface.right_side,
            "output_symbol": surface.output_symbol,
            "coordinate_system": "Oxyz",
        },
        evidence=explicit,
    )
    return quantities, unknowns, relation


def _quadratic_equation_semantics(
    equation: "QuadraticEquationForm",
) -> tuple[list["ProviderQuantity"], list["ProviderUnknown"], "ProviderRelation"]:
    explicit = ProviderEvidence(confidence=1.0, status=EvidenceStatus.EXPLICIT)
    quantities = [
        ProviderQuantity(
            role=MathQuantityRole.COEFFICIENT,
            value=equation.quadratic_coefficient,
            unit="one",
            label="Hệ số a của x²",
            evidence=explicit,
        ),
        ProviderQuantity(
            role=MathQuantityRole.COEFFICIENT,
            value=equation.linear_coefficient,
            unit="one",
            label="Hệ số b của x",
            evidence=explicit,
        ),
        ProviderQuantity(
            role=MathQuantityRole.CONSTANT,
            value=equation.constant,
            unit="one",
            label="Hệ số tự do c",
            evidence=explicit,
        ),
    ]
    unknowns = [ProviderUnknown(
        role=MathQuantityRole.RESULT,
        kind="roots",
        unit="one",
        label=f"Nghiệm của {equation.symbol}",
    )]
    relation = ProviderRelation(
        type="quadratic_equation",
        participant_roles={
            "quadratic_coefficient": "coefficient[1]",
            "linear_coefficient": "coefficient[2]",
            "constant": "constant",
            "roots": "result",
        },
        parameters={
            "symbol": equation.symbol,
            "canonical_form": "ax^2+bx+c=0",
        },
        evidence=explicit,
    )
    return quantities, unknowns, relation


def _cubic_equation_semantics(
    equation: "CubicEquationForm",
) -> tuple[list["ProviderQuantity"], list["ProviderUnknown"], "ProviderRelation"]:
    """Copy ``a, b, c, d``; roots stay derived by the deterministic renderer."""

    explicit = ProviderEvidence(confidence=1.0, status=EvidenceStatus.EXPLICIT)
    terms = (
        (equation.cubic_coefficient, "Hệ số a của x³"),
        (equation.quadratic_coefficient, "Hệ số b của x²"),
        (equation.linear_coefficient, "Hệ số c của x"),
    )
    quantities = [
        ProviderQuantity(
            role=MathQuantityRole.COEFFICIENT,
            value=value,
            unit="one",
            label=label.replace("x", equation.symbol),
            evidence=explicit,
        )
        for value, label in terms
    ]
    quantities.append(ProviderQuantity(
        role=MathQuantityRole.CONSTANT,
        value=equation.constant,
        unit="one",
        label="Hệ số tự do d",
        evidence=explicit,
    ))
    unknowns = [ProviderUnknown(
        role=MathQuantityRole.RESULT,
        kind="roots",
        unit="one",
        label=f"Các nghiệm thực của {equation.symbol}",
    )]
    relation = ProviderRelation(
        type="polynomial_equation",
        participant_roles={
            "cubic_coefficient": "coefficient[1]",
            "quadratic_coefficient": "coefficient[2]",
            "linear_coefficient": "coefficient[3]",
            "constant": "constant",
            "roots": "result",
        },
        parameters={
            "degree": 3,
            "symbol": equation.symbol,
            "canonical_form": "ax^3+bx^2+cx+d=0",
        },
        evidence=explicit,
    )
    return quantities, unknowns, relation


def _fractional_linear_semantics(
    equation: "FractionalLinearEquation",
) -> tuple[list["ProviderQuantity"], list["ProviderUnknown"], "ProviderRelation"]:
    explicit = ProviderEvidence(confidence=1.0, status=EvidenceStatus.EXPLICIT)
    inferred = ProviderEvidence(confidence=1.0, status=EvidenceStatus.INFERRED)
    quantities = [
        ProviderQuantity(
            role=MathQuantityRole.COEFFICIENT,
            value=equation.coefficient,
            unit="one",
            label=f"Hệ số của {equation.symbol} sau khi khử mẫu",
            evidence=inferred,
        ),
        ProviderQuantity(
            role=MathQuantityRole.CONSTANT,
            value=0,
            unit="one",
            label="Hằng số ở vế trái sau khi thu gọn",
            evidence=inferred,
        ),
        ProviderQuantity(
            role=MathQuantityRole.RESULT,
            value=equation.result,
            unit="one",
            label="Vế phải sau khi khử mẫu và chuyển vế",
            evidence=inferred,
        ),
    ]
    unknowns = [ProviderUnknown(
        role=MathQuantityRole.VARIABLE,
        kind="variable",
        unit="one",
        label=f"Giá trị của {equation.symbol}",
    )]
    relation = ProviderRelation(
        type="linear_equation_stages",
        participant_roles={
            "coefficient": "coefficient",
            "constant": "constant",
            "result": "result",
        },
        parameters={
            "kind": "fractional_linear",
            "symbol": equation.symbol,
            "denominators": list(equation.denominators),
            "stages": list(equation.stages),
            "stage_labels": ["Đề bài", "Nhân hai vế với BCNN", "Thu gọn"],
        },
        evidence=explicit,
    )
    return quantities, unknowns, relation


def _solution_equation_semantics(
    equation: "AbsoluteValueEquation | BiquadraticEquation | RadicalEquation | RationalEquation",
) -> tuple[str, list["ProviderQuantity"], list["ProviderUnknown"], "ProviderRelation"]:
    """Expose printed/derived coefficients but keep every root as an unknown."""

    explicit = ProviderEvidence(confidence=1.0, status=EvidenceStatus.EXPLICIT)
    inferred = ProviderEvidence(confidence=1.0, status=EvidenceStatus.INFERRED)
    if isinstance(equation, AbsoluteValueEquation):
        problem_type = "absolute_value_equation"
        values = (
            (MathQuantityRole.COEFFICIENT, equation.coefficient, f"Hệ số của {equation.symbol}"),
            (MathQuantityRole.CONSTANT, equation.constant, "Hằng số trong dấu giá trị tuyệt đối"),
            (MathQuantityRole.CONSTANT, equation.right_side, "Vế phải"),
        )
        parameters = {
            "kind": "absolute_value",
            "symbol": equation.symbol,
            "coefficient": equation.coefficient,
            "constant": equation.constant,
            "right_side": equation.right_side,
        }
        evidence = explicit
    elif isinstance(equation, BiquadraticEquation):
        problem_type = "biquadratic_equation"
        values = (
            (MathQuantityRole.COEFFICIENT, equation.quartic_coefficient, f"Hệ số của {equation.symbol}⁴"),
            (MathQuantityRole.COEFFICIENT, equation.quadratic_coefficient, f"Hệ số của {equation.symbol}²"),
            (MathQuantityRole.CONSTANT, equation.constant, "Hệ số tự do"),
        )
        parameters = {
            "kind": "biquadratic",
            "symbol": equation.symbol,
            "coefficients": [
                equation.quartic_coefficient,
                equation.quadratic_coefficient,
                equation.constant,
            ],
        }
        evidence = explicit
    elif isinstance(equation, RadicalEquation):
        problem_type = "radical_equation"
        values = (
            (MathQuantityRole.COEFFICIENT, equation.radicand_coefficient, f"Hệ số của {equation.symbol} trong căn"),
            (MathQuantityRole.CONSTANT, equation.radicand_constant, "Hằng số trong căn"),
            (MathQuantityRole.COEFFICIENT, equation.right_coefficient, f"Hệ số của {equation.symbol} ở vế phải"),
            (MathQuantityRole.CONSTANT, equation.right_constant, "Hằng số ở vế phải"),
        )
        parameters = {
            "kind": "radical",
            "symbol": equation.symbol,
            "radicand": [equation.radicand_coefficient, equation.radicand_constant],
            "right": [equation.right_coefficient, equation.right_constant],
        }
        evidence = explicit
    else:
        problem_type = "rational_equation"
        a, b, c = equation.numerator_coefficients
        values = (
            (MathQuantityRole.COEFFICIENT, a, f"Hệ số của {equation.symbol}² sau khi quy đồng"),
            (MathQuantityRole.COEFFICIENT, b, f"Hệ số của {equation.symbol} sau khi quy đồng"),
            (MathQuantityRole.CONSTANT, c, "Hệ số tự do sau khi quy đồng"),
        )
        parameters = {
            "kind": "rational",
            "symbol": equation.symbol,
            "numerator_coefficients": list(equation.numerator_coefficients),
            "denominators": [list(item) for item in equation.denominators],
        }
        # These three coefficients are the exact result of multiplying by the
        # common denominator, rather than three numbers printed next to x.
        evidence = inferred
    quantities = [
        ProviderQuantity(role=role, value=value, unit="one", label=label, evidence=evidence)
        for role, value, label in values
    ]
    unknowns = [ProviderUnknown(
        role=MathQuantityRole.VARIABLE,
        kind="solution_set",
        unit="one",
        label=f"Tập nghiệm của {equation.symbol}",
    )]
    relation = ProviderRelation(
        type="solution_set",
        # The full structural data lives in parameters.  These two anchors
        # keep the relation attached to unambiguous semantic nodes even when a
        # family has several printed coefficients/constants.
        participant_roles={
            "first_coefficient": "coefficient[1]",
            "first_constant": "constant[1]",
        },
        parameters=parameters,
        evidence=evidence,
    )
    return problem_type, quantities, unknowns, relation


def _right_triangle_semantics(
    triangle: "RightTriangleFacts",
) -> tuple[str, list["ProviderQuantity"], list["ProviderUnknown"], "ProviderRelation"]:
    """Copy the printed sides of a right triangle and name what is sought.

    Two legs with only the hypotenuse asked stays the narrower Pythagoras
    family. Anything else -- a printed hypotenuse, or "giải tam giác", which
    also asks for both acute angles -- is the general solution family.
    """

    explicit = ProviderEvidence(confidence=1.0, status=EvidenceStatus.EXPLICIT)
    hypotenuse = triangle.hypotenuse_name
    known = sorted(triangle.sides)
    known_hypotenuse = hypotenuse in triangle.sides
    # One side and one acute angle also determine the triangle, through the
    # trigonometric ratios rather than through Pythagoras.
    from_angle = len(known) == 1 and bool(triangle.angles)
    missing = next(
        (name for name in (*triangle.leg_names, hypotenuse) if name not in triangle.sides),
        None,
    )
    missing_sides = [
        name for name in (*triangle.leg_names, hypotenuse) if name not in triangle.sides
    ]
    solve_all = triangle.solve_all or known_hypotenuse or from_angle

    roles = (MathQuantityRole.LENGTH, MathQuantityRole.HEIGHT)
    quantities = [
        ProviderQuantity(
            role=roles[index],
            value=triangle.sides[name],
            unit=triangle.unit,
            label=(
                f"Cạnh huyền {name}" if name == hypotenuse
                else f"Cạnh góc vuông {name}"
            ),
            evidence=explicit,
        )
        for index, name in enumerate(known[:2])
    ]
    quantities.extend(
        ProviderQuantity(
            role=MathQuantityRole.ANGLE,
            value=degrees,
            unit="degree",
            label=f"Góc {vertex}",
            evidence=explicit,
        )
        for vertex, degrees in sorted(triangle.angles.items())
    )

    unknowns: list[ProviderUnknown] = [
        ProviderUnknown(
            role=MathQuantityRole.RESULT,
            kind="length",
            unit=triangle.unit,
            label=(
                f"Độ dài cạnh huyền {name}" if name == hypotenuse
                else f"Độ dài cạnh góc vuông {name}"
            ),
        )
        for name in missing_sides
    ]
    del missing
    if solve_all:
        unknowns.extend(
            ProviderUnknown(
                role=MathQuantityRole.ANGLE,
                kind="angle",
                unit="degree",
                label=f"Số đo góc {vertex}",
            )
            for vertex in triangle.acute_vertices
            if vertex not in triangle.angles
        )
    if not unknowns:
        unknowns.append(ProviderUnknown(
            role=MathQuantityRole.RESULT,
            kind="length",
            unit=triangle.unit,
            label="Yếu tố còn lại của tam giác",
        ))

    relation = ProviderRelation(
        type="right_triangle",
        participant_roles={"first_side": "length", "second_side": "height"},
        parameters={
            "vertices": triangle.vertices,
            "right_vertex": triangle.right_vertex,
            "hypotenuse": hypotenuse,
            "legs": list(triangle.leg_names),
            "known_sides": {name: triangle.sides[name] for name in known[:2]},
            "unit": triangle.unit,
            "known_angles": dict(triangle.angles),
            "solve_all": solve_all,
            "round_to_minute": triangle.round_to_minute,
        },
        evidence=explicit,
    )
    family = (
        "right_triangle_solution" if solve_all else "right_triangle_hypotenuse"
    )
    return family, quantities, unknowns, relation



def _linear_system_quantities(
    system: LinearSystem,
    evidence: "ProviderEvidence",
) -> list["ProviderQuantity"]:
    """Copy every printed equation into one canonical coefficient matrix.

    Missing terms are explicit zeroes in the matrix, not missing data.  Thus
    ``6y = 9`` inside an x/y/z system truthfully contributes ``0x+6y+0z=9``.
    """

    quantities: list[ProviderQuantity] = []
    for index, form in enumerate(system.forms, start=1):
        for name in system.variables:
            quantities.append(ProviderQuantity(
                role=MathQuantityRole.COEFFICIENT,
                value=form.coefficient(name),
                unit="one",
                label=f"Hệ số của {name} ở phương trình {index}",
                evidence=evidence,
            ))
        quantities.append(ProviderQuantity(
            role=MathQuantityRole.CONSTANT,
            value=form.constant,
            unit="one",
            label=f"Vế phải của phương trình {index}",
            evidence=evidence,
        ))
    return quantities


def _linear_system_unknowns(system: LinearSystem) -> list["ProviderUnknown"]:
    """Expose variable unknowns only when the system has one verified tuple."""

    if system.state not in {"intersecting", "unique"}:
        return [ProviderUnknown(
            role=MathQuantityRole.RESULT,
            kind="solution_set",
            unit="one",
            label="Tập nghiệm của hệ phương trình",
        )]
    return [
        ProviderUnknown(
            role=MathQuantityRole.VARIABLE,
            kind="variable",
            unit="one",
            label=f"Giá trị của {name}",
        )
        for name in system.variables
    ]


def _linear_system_relation(
    system: LinearSystem,
    evidence: "ProviderEvidence",
) -> "ProviderRelation":
    participant_roles: dict[str, str] = {}
    for equation_index, _form in enumerate(system.forms, start=1):
        for variable_index, name in enumerate(system.variables, start=1):
            coefficient_index = (equation_index - 1) * len(system.variables) + variable_index
            participant_roles[f"equation_{equation_index}_{name}"] = f"coefficient[{coefficient_index}]"
        participant_roles[f"equation_{equation_index}_right_side"] = f"constant[{equation_index}]"
    # Preserve the established names consumed by older two-line clients.
    if len(system.forms) == 2 and len(system.variables) == 2:
        participant_roles.update({
            "first_x": "coefficient[1]",
            "first_y": "coefficient[2]",
            "first_right_side": "constant[1]",
            "second_x": "coefficient[3]",
            "second_y": "coefficient[4]",
            "second_right_side": "constant[2]",
        })
    return ProviderRelation(
        type="linear_system",
        participant_roles=participant_roles,
        parameters={
            "coordinate_system": "Oxyz" if len(system.variables) == 3 else "Oxy",
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
            "first_canonical": format_canonical(system.forms[0]),
            "second_canonical": format_canonical(system.forms[1]),
        },
        evidence=evidence,
    )


UNITLESS_ROLES = {
    MathQuantityRole.COUNT,
    MathQuantityRole.COUNT_INITIAL,
    MathQuantityRole.COUNT_CHANGE,
    MathQuantityRole.TOTAL,
    MathQuantityRole.NUMERATOR,
    MathQuantityRole.DENOMINATOR,
    MathQuantityRole.TARGET_DENOMINATOR,
    MathQuantityRole.ADDEND_NUMERATOR,
    MathQuantityRole.ADDEND_DENOMINATOR,
    MathQuantityRole.EXPONENT,
    MathQuantityRole.VARIABLE,
    MathQuantityRole.COEFFICIENT,
    MathQuantityRole.CONSTANT,
    MathQuantityRole.CATEGORY,
    MathQuantityRole.FREQUENCY,
    MathQuantityRole.PROBABILITY,
}
LENGTH_ROLES = {
    MathQuantityRole.LENGTH,
    MathQuantityRole.WIDTH,
    MathQuantityRole.HEIGHT,
    MathQuantityRole.RADIUS,
    MathQuantityRole.DIAMETER,
}
LENGTH_UNITS = {"mm", "cm", "dm", "m", "km"}
AREA_ROLES = {MathQuantityRole.AREA}
AREA_UNITS = {"cm2", "m2"}
VOLUME_ROLES = {MathQuantityRole.VOLUME}
VOLUME_UNITS = {"cm3", "m3"}
ANGLE_ROLES = {MathQuantityRole.ANGLE}
ANGLE_UNITS = {"degree"}
MASS_ROLES = {MathQuantityRole.MASS}
MASS_UNITS = {"g", "kg"}


@dataclass(slots=True)
class MathAnalysisError(Exception):
    message: str
    status_code: int = 502

    def __str__(self) -> str:
        return self.message


class ProviderModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


ProviderVerbatimText = Annotated[str, StringConstraints(strip_whitespace=False)]


class ProviderEvidence(ProviderModel):
    confidence: float = Field(ge=0, le=1)
    status: EvidenceStatus


class ProviderEntity(ProviderModel):
    role: str = Field(min_length=1, max_length=64)
    type: str = Field(min_length=1, max_length=64)
    label: str = Field(min_length=1, max_length=160)
    evidence: ProviderEvidence


class ProviderQuantity(ProviderModel):
    role: MathQuantityRole
    value: float
    unit: MathUnit
    label: str = Field(min_length=1, max_length=160)
    evidence: ProviderEvidence

    @model_validator(mode="after")
    def unit_matches_semantic_role(self) -> "ProviderQuantity":
        if self.role in UNITLESS_ROLES and self.unit != "one":
            raise ValueError(f"Role {self.role.value} must use unit=one")
        if self.role in LENGTH_ROLES and self.unit not in LENGTH_UNITS:
            raise ValueError(f"Role {self.role.value} must use a length unit")
        if self.role in AREA_ROLES and self.unit not in AREA_UNITS:
            raise ValueError(f"Role {self.role.value} must use an area unit")
        if self.role in VOLUME_ROLES and self.unit not in VOLUME_UNITS:
            raise ValueError(f"Role {self.role.value} must use a volume unit")
        if self.role in ANGLE_ROLES and self.unit not in ANGLE_UNITS:
            raise ValueError(f"Role {self.role.value} must use unit=degree")
        if self.role in MASS_ROLES and self.unit not in MASS_UNITS:
            raise ValueError(f"Role {self.role.value} must use a mass unit")
        return self


class ProviderUnknown(ProviderModel):
    role: MathQuantityRole
    kind: str = Field(min_length=1, max_length=64)
    unit: MathUnit | None = None
    label: str = Field(min_length=1, max_length=160)

    @model_validator(mode="after")
    def unit_matches_semantic_role(self) -> "ProviderUnknown":
        if self.role in UNITLESS_ROLES and self.unit not in (None, "one"):
            raise ValueError(f"Unknown role {self.role.value} must use unit=one")
        if self.role in LENGTH_ROLES and self.unit not in (None, *LENGTH_UNITS):
            raise ValueError(f"Unknown role {self.role.value} must use a length unit")
        if self.role in AREA_ROLES and self.unit not in (None, *AREA_UNITS):
            raise ValueError(f"Unknown role {self.role.value} must use an area unit")
        if self.role in VOLUME_ROLES and self.unit not in (None, *VOLUME_UNITS):
            raise ValueError(f"Unknown role {self.role.value} must use a volume unit")
        if self.role in ANGLE_ROLES and self.unit not in (None, *ANGLE_UNITS):
            raise ValueError(f"Unknown role {self.role.value} must use unit=degree")
        if self.role in MASS_ROLES and self.unit not in (None, *MASS_UNITS):
            raise ValueError(f"Unknown role {self.role.value} must use a mass unit")
        return self


class ProviderConstraint(ProviderModel):
    type: str = Field(min_length=1, max_length=64)
    target_roles: list[str] = Field(min_length=1, max_length=12)
    locked: bool
    evidence: ProviderEvidence


class ProviderRelation(ProviderModel):
    type: str = Field(min_length=1, max_length=64)
    participant_roles: dict[str, str] = Field(min_length=1, max_length=12)
    parameters: dict[str, Any] = Field(default_factory=dict)
    evidence: ProviderEvidence


class ProviderSubquestion(ProviderModel):
    label: str = Field(min_length=1, max_length=64)
    text: str = Field(min_length=1, max_length=10_000)


class ProviderQuestion(ProviderModel):
    question_number: str = Field(min_length=1, max_length=32)
    stem: ProviderVerbatimText = Field(min_length=1, max_length=20_000)
    question_format: QuestionFormat
    choices: list[str] = Field(default_factory=list, max_length=12)
    subquestions: list[ProviderSubquestion] = Field(default_factory=list, max_length=20)
    grade: int = Field(ge=1, le=9)
    domain: MathDomain
    problem_type: str = Field(min_length=1, max_length=96)
    entities: list[ProviderEntity] = Field(default_factory=list, max_length=30)
    # Symbolic proofs/constructions may contain no explicit numeric quantity.
    # Requiring one coerces a VLM into inventing values (for example treating
    # the exponent in ``(x+3)^2`` as a denominator).
    quantities: list[ProviderQuantity] = Field(default_factory=list, max_length=50)
    unknowns: list[ProviderUnknown] = Field(min_length=1, max_length=20)
    relationships: list[ProviderRelation] = Field(default_factory=list, max_length=30)
    constraints: list[ProviderConstraint] = Field(default_factory=list, max_length=30)
    start_time: str | None = Field(default=None, pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    end_time: str | None = Field(default=None, pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    confidence: float = Field(ge=0, le=1)
    requires_review: bool
    review_notes: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("problem_type", mode="before")
    @classmethod
    def normalize_problem_type(cls, value: Any) -> str:
        return canonical_problem_type(str(value))

    @field_validator("start_time", "end_time", mode="before")
    @classmethod
    def empty_clock_is_missing(cls, value: Any) -> Any:
        """Compact VLMs commonly encode an absent optional clock as ``""``.

        Blank is semantically identical to JSON null here.  Normalizing it at
        the provider boundary prevents an otherwise valid question from
        failing the strict HH:MM pattern and triggering three pointless VLM
        retries followed by HTTP 502.
        """

        return None if isinstance(value, str) and not value.strip() else value

    @model_validator(mode="after")
    def must_not_fill_the_requested_unknown(self) -> "ProviderQuestion":
        unknown_roles = {item.role for item in self.unknowns}
        # Small local models often solve a short expression even when the
        # prompt explicitly forbids it, sometimes even labelling that invented
        # answer ``explicit``. A value cannot be a stated result while the same
        # question still asks for result, so always remove that collision.
        # Other roles are removed only when the model admits they are inferred;
        # explicit variable/operand collisions remain validation errors.
        self.quantities = [
            item
            for item in self.quantities
            if not (
                item.role in unknown_roles
                and (
                    item.role == MathQuantityRole.RESULT
                    or item.evidence.status != EvidenceStatus.EXPLICIT
                )
            )
        ]
        explicit_unknown_collisions = {
            item.role
            for item in self.quantities
            if item.role in unknown_roles
            and item.role in {
                MathQuantityRole.COUNT_CHANGE,
                MathQuantityRole.NUMERATOR,
                MathQuantityRole.DENOMINATOR,
                MathQuantityRole.VARIABLE,
            }
        }
        if explicit_unknown_collisions:
            roles = ", ".join(sorted(item.value for item in explicit_unknown_collisions))
            raise ValueError(
                "A requested result must not reuse an already-known semantic role; "
                f"use role=result for the unknown instead: {roles}"
            )

        factorial = extract_factorial(self.stem)
        basic_arithmetic = (
            extract_basic_arithmetic(self.stem)
            or extract_primary_word_arithmetic(self.stem)
        )
        if factorial:
            self.problem_type = "factorial"
            self.domain = MathDomain.NUMBER
            self.quantities = [ProviderQuantity(
                role=MathQuantityRole.COUNT_INITIAL,
                value=factorial.value,
                unit="one",
                label="Số cần tính giai thừa",
                evidence=ProviderEvidence(confidence=1.0, status=EvidenceStatus.EXPLICIT),
            )]
            self.unknowns = [ProviderUnknown(
                role=MathQuantityRole.RESULT,
                kind="number",
                unit="one",
                label="Giá trị giai thừa",
            )]
            self.relationships = []
            self.requires_review = False
            self.review_notes = []
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
                ProviderQuantity(
                    role=MathQuantityRole.COUNT_INITIAL,
                    value=basic_arithmetic.left,
                    unit="one",
                    label=left_label,
                    evidence=ProviderEvidence(confidence=1.0, status=EvidenceStatus.EXPLICIT),
                ),
                ProviderQuantity(
                    role=MathQuantityRole.COUNT_CHANGE,
                    value=basic_arithmetic.right,
                    unit="one",
                    label=right_label,
                    evidence=ProviderEvidence(confidence=1.0, status=EvidenceStatus.EXPLICIT),
                ),
            ]
            self.unknowns = [ProviderUnknown(
                role=MathQuantityRole.RESULT,
                kind="number",
                unit="one",
                label=result_label,
            )]
            self.requires_review = False
            self.review_notes = []

        binary_fraction = extract_binary_fraction(self.stem)
        if binary_fraction:
            self.problem_type = f"fraction_{binary_fraction.operation}"
            self.domain = MathDomain.FRACTION
            explicit = ProviderEvidence(confidence=1.0, status=EvidenceStatus.EXPLICIT)
            self.quantities = [
                ProviderQuantity(
                    role=MathQuantityRole.NUMERATOR,
                    value=binary_fraction.left_numerator,
                    unit="one",
                    label="Tử số phân số thứ nhất",
                    evidence=explicit,
                ),
                ProviderQuantity(
                    role=MathQuantityRole.DENOMINATOR,
                    value=binary_fraction.left_denominator,
                    unit="one",
                    label="Mẫu số phân số thứ nhất",
                    evidence=explicit,
                ),
                ProviderQuantity(
                    role=MathQuantityRole.ADDEND_NUMERATOR,
                    value=binary_fraction.right_numerator,
                    unit="one",
                    label="Tử số phân số thứ hai",
                    evidence=explicit,
                ),
                ProviderQuantity(
                    role=MathQuantityRole.ADDEND_DENOMINATOR,
                    value=binary_fraction.right_denominator,
                    unit="one",
                    label="Mẫu số phân số thứ hai",
                    evidence=explicit,
                ),
            ]
            self.unknowns = [ProviderUnknown(
                role=MathQuantityRole.RESULT,
                kind="fraction",
                unit="one",
                label="Kết quả phép tính phân số",
            )]
            self.requires_review = False
            self.review_notes = []

        parenthesized = extract_parenthesized_multiplication(self.stem)
        if parenthesized:
            self.problem_type = f"parenthesized_{parenthesized.inner_operation}_multiplication"
            self.domain = MathDomain.ARITHMETIC
            explicit = ProviderEvidence(confidence=1.0, status=EvidenceStatus.EXPLICIT)
            inferred = ProviderEvidence(confidence=1.0, status=EvidenceStatus.INFERRED)
            self.quantities = [
                ProviderQuantity(
                    role=MathQuantityRole.COUNT_INITIAL,
                    value=parenthesized.inner_left,
                    unit="one",
                    label="Số thứ nhất trong ngoặc",
                    evidence=explicit,
                ),
                ProviderQuantity(
                    role=MathQuantityRole.COUNT_CHANGE,
                    value=parenthesized.inner_right,
                    unit="one",
                    label="Số thứ hai trong ngoặc",
                    evidence=explicit,
                ),
                ProviderQuantity(
                    role=MathQuantityRole.COEFFICIENT,
                    value=parenthesized.multiplier,
                    unit="one",
                    label="Thừa số ngoài ngoặc",
                    evidence=explicit,
                ),
            ]
            self.unknowns = [ProviderUnknown(
                role=MathQuantityRole.RESULT,
                kind="number",
                unit="one",
                label="Kết quả biểu thức",
            )]
            self.relationships = [ProviderRelation(
                type="operation_tree",
                participant_roles={
                    "inner_left": "count_initial",
                    "inner_right": "count_change",
                    "multiplier": "coefficient",
                    "result": "result",
                },
                parameters={
                    "inner_operation": parenthesized.inner_operation,
                    "outer_operation": "multiplication",
                    "order": "parentheses_first",
                },
                evidence=inferred,
            )]
            self.requires_review = False
            self.review_notes = []

        direct_distance = extract_direct_proportion_distance_time(self.stem)
        if direct_distance:
            self.problem_type = "distance_time_direct_proportion"
            self.domain = MathDomain.RATIO
            explicit = ProviderEvidence(confidence=1.0, status=EvidenceStatus.EXPLICIT)
            inferred = ProviderEvidence(confidence=0.98, status=EvidenceStatus.INFERRED)
            self.quantities = [
                ProviderQuantity(
                    role=MathQuantityRole.DURATION,
                    value=direct_distance.known_duration,
                    unit=direct_distance.known_duration_unit,
                    label="Thời gian đã biết",
                    evidence=explicit,
                ),
                ProviderQuantity(
                    role=MathQuantityRole.DISTANCE,
                    value=direct_distance.known_distance,
                    unit=direct_distance.known_distance_unit,
                    label="Quãng đường đã biết",
                    evidence=explicit,
                ),
                ProviderQuantity(
                    role=MathQuantityRole.DURATION,
                    value=direct_distance.target_duration,
                    unit=direct_distance.target_duration_unit,
                    label="Thời gian cần tính quãng đường",
                    evidence=explicit,
                ),
            ]
            self.unknowns = [ProviderUnknown(
                role=MathQuantityRole.RESULT,
                kind="distance",
                unit=direct_distance.known_distance_unit,
                label="Quãng đường trong thời gian mới",
            )]
            self.relationships = [ProviderRelation(
                type="direct_proportion",
                participant_roles={
                    "known_duration": "duration[1]",
                    "known_distance": "distance",
                    "target_duration": "duration[2]",
                    "target_distance": "result",
                },
                parameters={"invariant": "distance_per_unit_time"},
                evidence=inferred,
            )]
            self.requires_review = False
            self.review_notes = []

        discount_system = extract_two_item_discount_system(self.stem)
        if discount_system:
            self.problem_type = "two_item_discount_system"
            self.domain = MathDomain.ALGEBRA
            self.quantities, self.unknowns, relation = (
                _two_item_discount_system_semantics(discount_system)
            )
            self.relationships = [relation]
            self.requires_review = False
            self.review_notes = []

        rectangle = extract_rectangle_dimensions(self.stem)
        if rectangle:
            self.problem_type = "rectangle_area"
            self.domain = MathDomain.GEOMETRY_2D
            explicit = ProviderEvidence(confidence=1.0, status=EvidenceStatus.EXPLICIT)
            self.quantities = [
                ProviderQuantity(
                    role=MathQuantityRole.LENGTH,
                    value=rectangle.length,
                    unit=rectangle.unit,
                    label="Chiều dài hình chữ nhật",
                    evidence=explicit,
                ),
                ProviderQuantity(
                    role=MathQuantityRole.WIDTH,
                    value=rectangle.width,
                    unit=rectangle.unit,
                    label="Chiều rộng hình chữ nhật",
                    evidence=explicit,
                ),
            ]
            self.unknowns = [ProviderUnknown(
                role=MathQuantityRole.RESULT,
                kind="area",
                unit=f"{rectangle.unit}2",
                label="Diện tích hình chữ nhật",
            )]
            self.requires_review = False
            self.review_notes = []

        inequality = parse_linear_inequality(self.stem)
        if inequality:
            self.problem_type = "linear_inequality_one_variable"
            self.domain = MathDomain.ALGEBRA
            explicit = ProviderEvidence(confidence=1.0, status=EvidenceStatus.EXPLICIT)
            self.quantities = [
                ProviderQuantity(
                    role=MathQuantityRole.COEFFICIENT,
                    value=inequality.coefficient,
                    unit="one",
                    label=f"Hệ số của {inequality.symbol}",
                    evidence=explicit,
                ),
                ProviderQuantity(
                    role=MathQuantityRole.CONSTANT,
                    value=inequality.constant,
                    unit="one",
                    label="Vế phải sau khi chuyển vế",
                    evidence=explicit,
                ),
            ]
            self.unknowns = [ProviderUnknown(
                role=MathQuantityRole.VARIABLE,
                kind="solution_set",
                unit="one",
                label=f"Tập nghiệm của {inequality.symbol}",
            )]
            self.relationships = [ProviderRelation(
                type="solution_set",
                participant_roles={"coefficient": "coefficient", "constant": "constant"},
                parameters={
                    "kind": "inequality",
                    "symbol": inequality.symbol,
                    "operator": inequality.operator,
                    "strict": inequality.strict,
                },
                evidence=explicit,
            )]
            self.requires_review = False
            self.review_notes = []

        product = parse_product_equation(self.stem)
        if product:
            self.problem_type = "product_equation_roots"
            self.domain = MathDomain.ALGEBRA
            explicit = ProviderEvidence(confidence=1.0, status=EvidenceStatus.EXPLICIT)
            self.quantities = [
                ProviderQuantity(
                    role=role,
                    value=value,
                    unit="one",
                    label=label.format(index=index + 1),
                    evidence=explicit,
                )
                for index, (coefficient, constant) in enumerate(product.factors)
                for role, value, label in (
                    (MathQuantityRole.COEFFICIENT, coefficient, "Hệ số của {index}"),
                    (MathQuantityRole.CONSTANT, constant, "Hằng số của thừa số {index}"),
                )
            ]
            self.unknowns = [ProviderUnknown(
                role=MathQuantityRole.VARIABLE,
                kind="solution_set",
                unit="one",
                label=f"Các nghiệm của {product.symbol}",
            )]
            self.relationships = [ProviderRelation(
                type="solution_set",
                participant_roles={"coefficient": "coefficient", "constant": "constant"},
                parameters={
                    "kind": "product_roots",
                    "symbol": product.symbol,
                    "factors": [list(factor) for factor in product.factors],
                },
                evidence=explicit,
            )]
            self.requires_review = False
            self.review_notes = []

        domain_condition = parse_rational_domain(self.stem)
        if domain_condition:
            self.problem_type = "rational_equation_domain"
            self.domain = MathDomain.ALGEBRA
            explicit = ProviderEvidence(confidence=1.0, status=EvidenceStatus.EXPLICIT)
            self.quantities = [
                ProviderQuantity(
                    role=role,
                    value=value,
                    unit="one",
                    label=label.format(index=index + 1),
                    evidence=explicit,
                )
                for index, (coefficient, constant) in enumerate(domain_condition.denominators)
                for role, value, label in (
                    (MathQuantityRole.COEFFICIENT, coefficient, "Hệ số của mẫu thức {index}"),
                    (MathQuantityRole.CONSTANT, constant, "Hằng số của mẫu thức {index}"),
                )
            ]
            self.unknowns = [ProviderUnknown(
                role=MathQuantityRole.VARIABLE,
                kind="solution_set",
                unit="one",
                label=f"Điều kiện xác định của {domain_condition.symbol}",
            )]
            self.relationships = [ProviderRelation(
                type="solution_set",
                participant_roles={"coefficient": "coefficient", "constant": "constant"},
                parameters={
                    "kind": "excluded_values",
                    "symbol": domain_condition.symbol,
                    "denominators": [list(item) for item in domain_condition.denominators],
                },
                evidence=explicit,
            )]
            self.requires_review = False
            self.review_notes = []

        system = extract_linear_system(self.stem)
        if system:
            three_variables = len(system.variables) == 3
            self.problem_type = (
                "linear_system_three_variables_planes"
                if three_variables
                else "linear_system_two_variables_graph"
            )
            self.domain = MathDomain.GEOMETRY_3D if three_variables else MathDomain.COORDINATE
            explicit = ProviderEvidence(confidence=1.0, status=EvidenceStatus.EXPLICIT)
            self.quantities = _linear_system_quantities(system, explicit)
            self.unknowns = _linear_system_unknowns(system)
            self.relationships = [_linear_system_relation(system, explicit)]
            self.requires_review = False
            self.review_notes = []

        degenerate = classify_linear(self.stem)
        if degenerate and degenerate.kind in {"identity", "contradiction"}:
            self.problem_type = f"linear_{degenerate.kind}"
            self.domain = MathDomain.ALGEBRA
            self.quantities = []
            self.unknowns = [ProviderUnknown(
                role=MathQuantityRole.RESULT,
                kind="solution_set",
                unit="one",
                label="Kết luận về tập nghiệm",
            )]
            self.relationships = []
            self.requires_review = False
            self.review_notes = []

        equation = extract_linear_equation(self.stem)
        if equation and not parse_fractional_linear_equation(self.stem):
            equation_form = classify_linear(self.stem)
            stages = (
                transformation_stages(equation_form.form)
                if equation_form and equation_form.form
                else []
            )
            # A one-step ``ax + b = c`` and a bracketed multi-step equation are
            # different lessons: the second must show the expansion it needs.
            self.problem_type = (
                "compound_linear_equation"
                if equation_form and equation_form.form and equation_form.form.needs_expansion
                else "linear_equation"
            )
            self.domain = MathDomain.ALGEBRA
            explicit = ProviderEvidence(confidence=1.0, status=EvidenceStatus.EXPLICIT)
            self.quantities = [
                ProviderQuantity(
                    role=MathQuantityRole.COEFFICIENT,
                    value=equation.coefficient,
                    unit="one",
                    label="Hệ số của x",
                    evidence=explicit,
                ),
                ProviderQuantity(
                    role=MathQuantityRole.CONSTANT,
                    value=equation.constant,
                    unit="one",
                    label="Hằng số ở vế trái",
                    evidence=explicit,
                ),
                ProviderQuantity(
                    role=MathQuantityRole.RESULT,
                    value=equation.result,
                    unit="one",
                    label="Giá trị vế phải",
                    evidence=explicit,
                ),
            ]
            self.unknowns = [ProviderUnknown(
                role=MathQuantityRole.VARIABLE,
                kind="variable",
                unit="one",
                label="Giá trị của x",
            )]
            self.relationships = [ProviderRelation(
                type="linear_equation_stages",
                participant_roles={
                    "coefficient": "coefficient",
                    "constant": "constant",
                    "result": "result",
                },
                parameters={"stages": stages},
                evidence=explicit,
            )]
            self.requires_review = False
            self.review_notes = []

        two_variable_equation = extract_two_variable_linear_equation(self.stem)
        already_a_linear_function = (
            self.problem_type.lower() == "linear_function"
            and any(item.role == MathQuantityRole.COEFFICIENT for item in self.quantities)
            and any(item.role == MathQuantityRole.CONSTANT for item in self.quantities)
        )
        if two_variable_equation and not already_a_linear_function:
            self.problem_type = "linear_equation_two_variables_graph"
            self.domain = MathDomain.COORDINATE
            inferred = ProviderEvidence(confidence=1.0, status=EvidenceStatus.INFERRED)
            self.quantities = [
                ProviderQuantity(
                    role=MathQuantityRole.COEFFICIENT,
                    value=two_variable_equation.slope,
                    unit="one",
                    label="Hệ số góc sau khi đưa về y = mx + b",
                    evidence=inferred,
                ),
                ProviderQuantity(
                    role=MathQuantityRole.CONSTANT,
                    value=two_variable_equation.intercept,
                    unit="one",
                    label="Tung độ gốc sau khi đưa về y = mx + b",
                    evidence=inferred,
                ),
            ]
            self.unknowns = [ProviderUnknown(
                role=MathQuantityRole.RESULT,
                kind="graph",
                unit="one",
                label="Đường thẳng biểu diễn tập nghiệm trên Oxy",
            )]
            self.relationships = [ProviderRelation(
                type="equivalent_linear_form",
                participant_roles={
                    "slope": "coefficient",
                    "intercept": "constant",
                },
                parameters={
                    "x_coefficient": two_variable_equation.x_coefficient,
                    "y_coefficient": two_variable_equation.y_coefficient,
                    "right_side": two_variable_equation.result,
                },
                evidence=inferred,
            )]
            self.requires_review = False
            self.review_notes = []

        three_variable_equation = extract_three_variable_linear_equation(self.stem)
        if three_variable_equation:
            self.problem_type = "linear_equation_three_variables_plane"
            self.domain = MathDomain.GEOMETRY_3D
            explicit = ProviderEvidence(confidence=1.0, status=EvidenceStatus.EXPLICIT)
            self.quantities = [
                ProviderQuantity(role=MathQuantityRole.COEFFICIENT, value=three_variable_equation.x_coefficient, unit="one", label="Hệ số của x", evidence=explicit),
                ProviderQuantity(role=MathQuantityRole.COEFFICIENT, value=three_variable_equation.y_coefficient, unit="one", label="Hệ số của y", evidence=explicit),
                ProviderQuantity(role=MathQuantityRole.COEFFICIENT, value=three_variable_equation.z_coefficient, unit="one", label="Hệ số của z", evidence=explicit),
                ProviderQuantity(role=MathQuantityRole.CONSTANT, value=three_variable_equation.result, unit="one", label="Vế phải d", evidence=explicit),
            ]
            self.unknowns = [ProviderUnknown(
                role=MathQuantityRole.RESULT,
                kind="plane",
                unit="one",
                label="Mặt phẳng biểu diễn tập nghiệm trên Oxyz",
            )]
            self.relationships = [ProviderRelation(
                type="plane_equation",
                participant_roles={"x": "coefficient[1]", "y": "coefficient[2]", "z": "coefficient[3]", "right_side": "constant"},
                parameters={"coordinate_system": "Oxyz"},
                evidence=explicit,
            )]
            self.requires_review = False
            self.review_notes = []

        quadratic_surface = parse_quadratic_surface(self.stem)
        if quadratic_surface:
            self.problem_type = "quadratic_surface_three_variables"
            self.domain = MathDomain.GEOMETRY_3D
            self.quantities, self.unknowns, relation = _quadratic_surface_semantics(
                quadratic_surface
            )
            self.relationships = [relation]
            self.requires_review = False
            self.review_notes = []

        quadratic_equation = parse_quadratic_equation(self.stem)
        if quadratic_equation:
            self.problem_type = "quadratic_equation"
            self.domain = MathDomain.ALGEBRA
            self.quantities, self.unknowns, relation = _quadratic_equation_semantics(
                quadratic_equation
            )
            self.relationships = [relation]
            self.requires_review = False
            self.review_notes = []

        cubic_equation = parse_cubic_equation(self.stem)
        if cubic_equation:
            self.problem_type = "cubic_equation"
            self.domain = MathDomain.ALGEBRA
            self.quantities, self.unknowns, relation = _cubic_equation_semantics(
                cubic_equation
            )
            self.relationships = [relation]
            self.requires_review = False
            self.review_notes = []

        fractional_linear = parse_fractional_linear_equation(self.stem)
        if fractional_linear:
            self.problem_type = "fractional_linear_equation"
            self.domain = MathDomain.ALGEBRA
            self.quantities, self.unknowns, relation = _fractional_linear_semantics(
                fractional_linear
            )
            self.relationships = [relation]
            self.requires_review = False
            self.review_notes = []

        for special_equation in (
            parse_absolute_value_equation(self.stem),
            parse_biquadratic_equation(self.stem),
            parse_radical_equation(self.stem),
            parse_rational_equation(self.stem),
        ):
            if special_equation is None:
                continue
            self.problem_type, self.quantities, self.unknowns, relation = (
                _solution_equation_semantics(special_equation)
            )
            self.domain = MathDomain.ALGEBRA
            self.relationships = [relation]
            self.requires_review = False
            self.review_notes = []
            break

        linear_expression = extract_single_variable_linear_expression(self.stem)
        if linear_expression and not any((fractional_linear, *(
            parse_absolute_value_equation(self.stem),
            parse_biquadratic_equation(self.stem),
            parse_radical_equation(self.stem),
            parse_rational_equation(self.stem),
        ))):
            self.problem_type = "polynomial_evaluate_reorder"
            self.domain = MathDomain.ALGEBRA
            explicit = ProviderEvidence(confidence=1.0, status=EvidenceStatus.EXPLICIT)
            self.quantities = [
                ProviderQuantity(role=MathQuantityRole.COEFFICIENT, value=linear_expression.coefficient, unit="one", label="Hệ số của hạng tử x", evidence=explicit),
                ProviderQuantity(role=MathQuantityRole.EXPONENT, value=1, unit="one", label="Bậc của hạng tử x", evidence=explicit),
                ProviderQuantity(role=MathQuantityRole.COEFFICIENT, value=linear_expression.constant, unit="one", label="Hệ số của hạng tử đơn vị", evidence=explicit),
                ProviderQuantity(role=MathQuantityRole.EXPONENT, value=0, unit="one", label="Bậc của hạng tử đơn vị", evidence=explicit),
            ]
            self.unknowns = [ProviderUnknown(
                role=MathQuantityRole.RESULT,
                kind="expression_model",
                unit="one",
                label="Mô hình tile của biểu thức",
            )]
            self.requires_review = False
            self.review_notes = []

        triangle = extract_right_triangle(self.stem)
        if triangle and (
            len(triangle.sides) >= 2
            or (len(triangle.sides) >= 1 and len(triangle.angles) >= 1)
        ):
            self.problem_type, self.quantities, self.unknowns, relation = (
                _right_triangle_semantics(triangle)
            )
            self.domain = MathDomain.GEOMETRY_2D
            self.relationships = [relation]
            self.requires_review = False
            self.review_notes = []

        angle_of_depression = extract_angle_of_depression(self.stem)
        if angle_of_depression:
            self.problem_type = "angle_of_depression_distance"
            self.domain = MathDomain.GEOMETRY_2D
            self.quantities, self.unknowns, relation = _angle_of_depression_semantics(
                angle_of_depression
            )
            self.relationships = [relation]
            self.requires_review = False
            self.review_notes = []

        oblique_triangle = extract_oblique_triangle_altitude(self.stem)
        if oblique_triangle:
            self.problem_type = "oblique_triangle_altitude_solution"
            self.domain = MathDomain.GEOMETRY_2D
            self.quantities, self.unknowns, relation = (
                _oblique_triangle_altitude_semantics(oblique_triangle)
            )
            self.relationships = [relation]
            self.requires_review = False
            self.review_notes = []

        parallelogram = extract_perpendicular_diagonal_parallelogram(self.stem)
        if parallelogram:
            self.problem_type = "parallelogram_perpendicular_diagonal_area"
            self.domain = MathDomain.GEOMETRY_2D
            self.quantities, self.unknowns, relation = (
                _parallelogram_diagonal_semantics(parallelogram)
            )
            self.relationships = [relation]
            self.requires_review = False
            self.review_notes = []

        # A superscript/exponent is not a denominator. Small VLMs sometimes
        # turn ``(x + 3)^2`` into the fictitious fraction 3/2. Fraction roles
        # are only admissible when the original stem contains actual fraction
        # notation or explicitly names a fraction.
        # A printed ratio is evidence too: "tỉ số 4 : 6" and "tỉ lệ với 2 và 3"
        # state two comparable parts as plainly as ``4/6`` does. Only invented
        # fractions are being guarded against here.
        has_fraction_evidence = bool(
            re.search(r"(?<![\w)])[-+]?\d+\s*/\s*\d+(?![\w])", self.stem)
            or re.search(r"\b(phân\s*số|tử\s*số|mẫu\s*số|fraction)\b", self.stem, re.IGNORECASE)
            or re.search(r"\b(t[ỉỷiy]\s*(?:s[ốô]|l[ệê])|ratio)\b", self.stem, re.IGNORECASE)
        )
        fraction_roles = {
            MathQuantityRole.NUMERATOR,
            MathQuantityRole.DENOMINATOR,
            MathQuantityRole.TARGET_DENOMINATOR,
            MathQuantityRole.ADDEND_NUMERATOR,
            MathQuantityRole.ADDEND_DENOMINATOR,
        }
        if not has_fraction_evidence and self.domain != MathDomain.FRACTION:
            self.quantities = [
                item for item in self.quantities if item.role not in fraction_roles
            ]

        # Preserve a printed fractional power even when a compact VLM returns
        # only the stem. This grammar extracts operands; it does not solve the
        # requested result. Superscript OCR (for example ³) and caret notation
        # are both accepted.
        normalized_stem = self.stem.replace("−", "-").replace("–", "-")
        superscript_digits = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")
        fractional_power = re.search(
            r"\(\s*([+-]?\d+)\s*/\s*(\d+)\s*\)\s*"
            r"(?:\^\s*\{?\s*(\d+)\s*\}?|([⁰¹²³⁴⁵⁶⁷⁸⁹]+))",
            normalized_stem,
        )
        if fractional_power:
            numerator = float(fractional_power.group(1))
            denominator = float(fractional_power.group(2))
            exponent_text = fractional_power.group(3) or fractional_power.group(4).translate(superscript_digits)
            exponent = float(exponent_text)
            self.problem_type = "fraction_power"
            existing_roles = {item.role for item in self.quantities}
            recovered = (
                (MathQuantityRole.NUMERATOR, numerator, "Tử số của cơ số"),
                (MathQuantityRole.DENOMINATOR, denominator, "Mẫu số của cơ số"),
                (MathQuantityRole.EXPONENT, exponent, "Số mũ"),
            )
            for role, value, label in recovered:
                if role not in existing_roles:
                    self.quantities.append(ProviderQuantity(
                        role=role,
                        value=value,
                        unit="one",
                        label=label,
                        evidence=ProviderEvidence(confidence=1.0, status=EvidenceStatus.EXPLICIT),
                    ))

        # Recover literal y=mx+b operands with a deterministic grammar. This
        # is not solving the question: it preserves coefficients printed in
        # the source when a small VLM classifies the function correctly but
        # returns an empty quantities array.
        if self.problem_type.lower() == "linear_function":
            normalized_stem = self.stem.replace("−", "-").replace(",", ".")
            function = re.search(
                r"\by\s*=\s*([+-]?(?:\d+(?:\.\d+)?)?)\s*\*?\s*x"
                r"(?:\s*([+-])\s*(\d+(?:\.\d+)?))?",
                normalized_stem,
                re.IGNORECASE,
            )
            existing_roles = {item.role for item in self.quantities}
            if function and MathQuantityRole.COEFFICIENT not in existing_roles:
                coefficient_text = function.group(1)
                coefficient = -1.0 if coefficient_text == "-" else (
                    1.0 if coefficient_text in {"", "+"} else float(coefficient_text)
                )
                self.quantities.append(ProviderQuantity(
                    role=MathQuantityRole.COEFFICIENT,
                    value=coefficient,
                    unit="one",
                    label="Hệ số góc m",
                    evidence=ProviderEvidence(
                        confidence=1.0 if coefficient_text not in {"", "+", "-"} else 0.98,
                        status=(
                            EvidenceStatus.EXPLICIT
                            if coefficient_text not in {"", "+", "-"}
                            else EvidenceStatus.INFERRED
                        ),
                    ),
                ))
            if function and MathQuantityRole.CONSTANT not in existing_roles:
                sign, magnitude = function.group(2), function.group(3)
                constant = (1 if sign != "-" else -1) * float(magnitude) if magnitude else 0.0
                self.quantities.append(ProviderQuantity(
                    role=MathQuantityRole.CONSTANT,
                    value=constant,
                    unit="one",
                    label="Tung độ gốc b",
                    evidence=ProviderEvidence(
                        confidence=1.0 if magnitude else 0.98,
                        status=EvidenceStatus.EXPLICIT if magnitude else EvidenceStatus.INFERRED,
                    ),
                ))

        # Preserve a printed angle measure for a bisector problem even when a
        # compact VLM identifies the family but omits its quantity. This only
        # copies a number explicitly tied to an angle and never computes the
        # requested half-angle.
        if "angle_bisector" in self.problem_type.lower():
            normalized_angle_stem = (
                self.stem.replace("∠", "góc ")
                .replace("−", "-")
                .replace(",", ".")
            )
            printed_angle = re.search(
                r"(?:góc\s*[A-Za-zÀ-ỹ]{0,12}|[A-Za-z]{3})\s*(?:=|bằng)\s*"
                r"(\d+(?:\.\d+)?)\s*(?:°|độ|degrees?|deg)(?:\s|[.,;:]|$)",
                normalized_angle_stem,
                re.IGNORECASE,
            )
            existing_roles = {item.role for item in self.quantities}
            if printed_angle and MathQuantityRole.ANGLE not in existing_roles:
                self.quantities.append(ProviderQuantity(
                    role=MathQuantityRole.ANGLE,
                    value=float(printed_angle.group(1)),
                    unit="degree",
                    label="Số đo góc ban đầu",
                    evidence=ProviderEvidence(
                        confidence=1.0,
                        status=EvidenceStatus.EXPLICIT,
                    ),
                ))

        # A frequent Vietnamese primary/lower-secondary word problem applies a
        # fraction to the original total, then another fraction to the
        # remainder, and finally asks for a ratio between two days. Compact
        # vision models often flatten this into a generic ``ratio calculation``
        # and drop the operands, which previously made the bar renderer fall
        # through to an unrelated average model. This narrow grammar copies only
        # values literally printed in the stem; every intermediate result stays
        # out of quantities and is derived deterministically by the renderer.
        normalized_ratio_stem = (
            self.stem.lower()
            .replace("−", "-")
            .replace("–", "-")
            .replace(",", ".")
        )
        total_mass = re.search(
            r"\bcó\s+(\d+(?:\.\d+)?)\s*(kg|g)\s+gạo\b",
            normalized_ratio_stem,
            re.IGNORECASE,
        )
        first_day = re.search(
            r"ngày\s+thứ\s+nhất[^.?!]*?(\d+)\s*/\s*(\d+)\s+số\s+gạo",
            normalized_ratio_stem,
            re.IGNORECASE,
        )
        second_day = re.search(
            r"ngày\s+thứ\s+hai[^.?!]*?(\d+)\s*/\s*(\d+)\s+số\s+gạo\s+còn\s+lại",
            normalized_ratio_stem,
            re.IGNORECASE,
        )
        asks_day_ratio = (
            bool(re.search(r"\b(?:tỉ|tỷ)\s+số\b", normalized_ratio_stem))
            and "ngày thứ ba" in normalized_ratio_stem
            and "ngày thứ nhất" in normalized_ratio_stem
        )
        if total_mass and first_day and second_day and asks_day_ratio:
            self.problem_type = "sequential_fraction_remainder_ratio"
            self.domain = MathDomain.RATIO
            exact_roles = {
                MathQuantityRole.MASS,
                MathQuantityRole.NUMERATOR,
                MathQuantityRole.DENOMINATOR,
                MathQuantityRole.ADDEND_NUMERATOR,
                MathQuantityRole.ADDEND_DENOMINATOR,
            }
            self.quantities = [
                item for item in self.quantities if item.role not in exact_roles
            ]
            recovered_operands = (
                (
                    MathQuantityRole.MASS,
                    float(total_mass.group(1)),
                    total_mass.group(2),
                    "Tổng số gạo ban đầu",
                ),
                (
                    MathQuantityRole.NUMERATOR,
                    float(first_day.group(1)),
                    "one",
                    "Tử số phần gạo bán ngày thứ nhất",
                ),
                (
                    MathQuantityRole.DENOMINATOR,
                    float(first_day.group(2)),
                    "one",
                    "Mẫu số phần gạo bán ngày thứ nhất",
                ),
                (
                    MathQuantityRole.ADDEND_NUMERATOR,
                    float(second_day.group(1)),
                    "one",
                    "Tử số phần gạo bán ngày thứ hai",
                ),
                (
                    MathQuantityRole.ADDEND_DENOMINATOR,
                    float(second_day.group(2)),
                    "one",
                    "Mẫu số phần gạo bán ngày thứ hai",
                ),
            )
            self.quantities.extend(
                ProviderQuantity(
                    role=role,
                    value=value,
                    unit=unit,
                    label=label,
                    evidence=ProviderEvidence(
                        confidence=1.0,
                        status=EvidenceStatus.EXPLICIT,
                    ),
                )
                for role, value, unit, label in recovered_operands
            )
            self.unknowns = [ProviderUnknown(
                role=MathQuantityRole.RESULT,
                kind="ratio",
                unit="one",
                label="Tỉ số số gạo ngày thứ ba và ngày thứ nhất",
            )]
            self.requires_review = False
            self.review_notes = []

        # This is the same semantic operation as the rice example above, but
        # the requested result is a remaining quantity rather than a ratio.
        # OCR commonly flattens stacked 2/5 and 1/3 into separate lines, while
        # a compact VLM may then mislabel square metres as kilograms. Recover
        # the general operation roles and normalize only the printed area
        # components to m²; the final remainder is still an unknown.
        area_remainder = extract_sequential_fraction_remainder_area(self.stem)
        if area_remainder:
            self.problem_type = "sequential_fraction_remainder_quantity"
            self.domain = MathDomain.RATIO
            self.quantities = []
            for component in area_remainder.area_components:
                printed = f"{component.printed_value:g} {component.printed_unit}²"
                normalized = f"{component.value_m2:g} m²"
                self.quantities.append(ProviderQuantity(
                    role=MathQuantityRole.AREA,
                    value=component.value_m2,
                    unit="m2",
                    label=(
                        f"{printed} = {normalized}"
                        if component.printed_unit != "m"
                        else printed
                    ),
                    evidence=ProviderEvidence(
                        confidence=1.0,
                        status=(
                            EvidenceStatus.INFERRED
                            if component.printed_unit != "m"
                            else EvidenceStatus.EXPLICIT
                        ),
                    ),
                ))
            self.quantities.extend([
                ProviderQuantity(
                    role=MathQuantityRole.NUMERATOR,
                    value=area_remainder.first_numerator,
                    unit="one",
                    label="Tử số phần diện tích dùng lần thứ nhất",
                    evidence=ProviderEvidence(confidence=1.0, status=EvidenceStatus.EXPLICIT),
                ),
                ProviderQuantity(
                    role=MathQuantityRole.DENOMINATOR,
                    value=area_remainder.first_denominator,
                    unit="one",
                    label="Mẫu số phần diện tích dùng lần thứ nhất",
                    evidence=ProviderEvidence(confidence=1.0, status=EvidenceStatus.EXPLICIT),
                ),
                ProviderQuantity(
                    role=MathQuantityRole.ADDEND_NUMERATOR,
                    value=area_remainder.second_numerator,
                    unit="one",
                    label="Tử số phần diện tích dùng từ phần còn lại",
                    evidence=ProviderEvidence(confidence=1.0, status=EvidenceStatus.EXPLICIT),
                ),
                ProviderQuantity(
                    role=MathQuantityRole.ADDEND_DENOMINATOR,
                    value=area_remainder.second_denominator,
                    unit="one",
                    label="Mẫu số phần diện tích dùng từ phần còn lại",
                    evidence=ProviderEvidence(confidence=1.0, status=EvidenceStatus.EXPLICIT),
                ),
            ])
            self.unknowns = [ProviderUnknown(
                role=MathQuantityRole.RESULT,
                kind="area",
                unit="m2",
                label="Diện tích phần đất còn lại cuối cùng",
            )]
            self.requires_review = False
            self.review_notes = []

        # Reverse-discount checkout problems have a very different state
        # transition from the sequential-remainder family above. A compact
        # model can overfit the shared words "thứ nhất/thứ hai/thứ ba" and
        # incorrectly return the rice-sale family (and even kg/g units). This
        # narrow grammar recognizes only three-item checkout statements with
        # explicit prices, discounts and a final amount paid. It copies those
        # printed operands and leaves the requested third original price as an
        # unknown; the renderer performs every calculation visibly.
        discount_stem = self.stem.lower().replace("−", "-").replace("–", "-")

        def money_after(ordinal: str) -> float | None:
            match = re.search(
                rf"món(?:\s+hàng)?\s+thứ\s+{ordinal}[^.?!]*?"
                r"giá\s+(\d{1,3}(?:[ .]\d{3})+|\d+)\s*(?:đồng|đ|vnd)",
                discount_stem,
                re.IGNORECASE,
            )
            if not match and ordinal == "nhất":
                match = re.search(
                    r"món(?:\s+hàng)?\s+giá\s+"
                    r"(\d{1,3}(?:[ .]\d{3})+|\d+)\s*(?:đồng|đ|vnd)",
                    discount_stem,
                    re.IGNORECASE,
                )
            return float(re.sub(r"[ .]", "", match.group(1))) if match else None

        def discount_after(ordinal: str) -> float | None:
            match = re.search(
                rf"món(?:\s+hàng)?\s+thứ\s+{ordinal}[^.?!]*?"
                r"giảm(?:\s+giá)?\s+(\d+(?:[.,]\d+)?)\s*%",
                discount_stem,
                re.IGNORECASE,
            )
            if not match and ordinal == "nhất":
                match = re.search(
                    r"món(?:\s+hàng)?[^.?!]*?"
                    r"giảm(?:\s+giá)?\s+(\d+(?:[.,]\d+)?)\s*%",
                    discount_stem,
                    re.IGNORECASE,
                )
            return float(match.group(1).replace(",", ".")) if match else None

        first_price = money_after("nhất")
        second_price = money_after("hai")
        first_discount = discount_after("nhất")
        second_discount = discount_after("hai")
        third_discount = discount_after("ba")
        paid_total_match = re.search(
            r"(?:tổng\s+số\s+tiền[^.?!]*?|thanh\s+toán[^.?!]*?|hóa\s+đơn[^.?!]*?)"
            r"(?:là|:|hết|tổng cộng)?\s*(\d{1,3}(?:[ .]\d{3})+|\d+)\s*(?:đồng|đ|vnd)",
            discount_stem,
            re.IGNORECASE,
        )
        paid_total = (
            float(re.sub(r"[ .]", "", paid_total_match.group(1)))
            if paid_total_match
            else None
        )
        asks_original_third = (
            bool(re.search(r"món(?:\s+hàng)?\s+thứ\s+ba", discount_stem))
            and bool(re.search(r"(?:lúc\s+chưa\s+giảm|giá\s+gốc|trước\s+khi\s+giảm)", discount_stem))
        )
        discount_operands = (
            first_price,
            second_price,
            first_discount,
            second_discount,
            third_discount,
            paid_total,
        )
        if asks_original_third and all(value is not None for value in discount_operands):
            self.problem_type = "multi_item_reverse_discount"
            self.domain = MathDomain.RATIO
            printed_values = (
                (MathQuantityRole.COUNT_INITIAL, first_price, "Giá gốc món hàng thứ nhất (đồng)"),
                (MathQuantityRole.COUNT_INITIAL, second_price, "Giá gốc món hàng thứ hai (đồng)"),
                (MathQuantityRole.PROBABILITY, first_discount, "Mức giảm món hàng thứ nhất (%)"),
                (MathQuantityRole.PROBABILITY, second_discount, "Mức giảm món hàng thứ hai (%)"),
                (MathQuantityRole.PROBABILITY, third_discount, "Mức giảm món hàng thứ ba (%)"),
                (MathQuantityRole.TOTAL, paid_total, "Tổng số tiền đã thanh toán (đồng)"),
            )
            self.quantities = [
                ProviderQuantity(
                    role=role,
                    value=float(value),
                    unit="one",
                    label=label,
                    evidence=ProviderEvidence(
                        confidence=1.0,
                        status=EvidenceStatus.EXPLICIT,
                    ),
                )
                for role, value, label in printed_values
            ]
            self.unknowns = [ProviderUnknown(
                role=MathQuantityRole.RESULT,
                kind="money",
                unit="one",
                label="Giá gốc món hàng thứ ba (đồng)",
            )]
            self.requires_review = False
            self.review_notes = []

        # In inverse work-rate problems the completed job is the invariant:
        # workers × days stays constant when every worker has equal output.
        # Compact VLMs often recognize the family but classify it as
        # probability and omit all operands. This narrow Vietnamese grammar
        # copies only the initial workers, planned days and the printed worker
        # adjustment; it never stores the requested completion time.
        work_rate = extract_variable_people_work_rate(self.stem)
        if work_rate:
            self.problem_type = "work_rate_with_variable_people"
            self.domain = MathDomain.RATIO
            self.quantities = [
                ProviderQuantity(
                    role=MathQuantityRole.COUNT_INITIAL,
                    value=work_rate.initial_workers,
                    unit="one",
                    label="Số người ban đầu",
                    evidence=ProviderEvidence(
                        confidence=1.0,
                        status=EvidenceStatus.EXPLICIT,
                    ),
                ),
                ProviderQuantity(
                    role=MathQuantityRole.DURATION,
                    value=work_rate.planned_days,
                    # This family counts discrete school-problem days. Keep it
                    # dimensionless for compatibility with earlier clients.
                    unit="one",
                    label="Số ngày dự định",
                    evidence=ProviderEvidence(
                        confidence=1.0,
                        status=EvidenceStatus.EXPLICIT,
                    ),
                ),
                ProviderQuantity(
                    role=MathQuantityRole.COUNT_CHANGE,
                    value=work_rate.worker_change,
                    unit="one",
                    label=(
                        "Số người được bổ sung"
                        if work_rate.worker_change > 0
                        else "Số người rút bớt"
                    ),
                    evidence=ProviderEvidence(
                        confidence=1.0,
                        status=EvidenceStatus.EXPLICIT,
                    ),
                ),
            ]
            self.unknowns = [ProviderUnknown(
                role=MathQuantityRole.RESULT,
                kind="duration",
                unit="one",
                label="Số ngày hoàn thành sau khi thay đổi số người",
            )]
            self.requires_review = False
            self.review_notes = []

        # Very short primary-school expressions are common in live demos, but
        # a VLM can still classify them correctly while returning no operands.
        # Copy the two integers printed on either side of the operator so the
        # deterministic renderer always has actual groups to draw. This is an
        # extraction repair only: the product/quotient remains an unknown and
        # is never stored as a supplied fact.
        basic_stem = (
            self.stem.lower()
            .replace("−", "-")
            .replace("–", "-")
            .replace("×", " nhân ")
            .replace("÷", " chia ")
        )
        compact_stem = re.sub(r"\s+", " ", basic_stem).strip()
        # Guard the repair to genuinely short expressions. Applied to a whole
        # word problem it hijacked stems such as "theo tỉ số 4 : 6" and drew a
        # division scene for a ratio question.
        looks_like_short_expression = (
            # This repair only fills in missing operands. A question that
            # already carries both numbers keeps its own family, so "Đặt tính
            # rồi tính: 543 × 87" stays a column algorithm instead of being
            # relabelled as a bare multiplication.
            len([item for item in self.quantities if item.value is not None]) < 2
            and len(compact_stem.split()) <= 8
            and len(re.findall(r"\d+", compact_stem)) <= 2
            and not re.search(r"t[ỉỷiy]\s*(?:s[ốô]|l[ệê])|bản\s*đồ|ratio", compact_stem, re.IGNORECASE)
        )
        basic_operation = re.search(
            r"(?<![\w/])([+-]?\d+)\s*(nhân|x|\*|chia|:)\s*([+-]?\d+)(?![\w/])",
            compact_stem,
            re.IGNORECASE,
        ) if looks_like_short_expression else None
        if basic_operation:
            left = float(basic_operation.group(1))
            operator = basic_operation.group(2).lower()
            right = float(basic_operation.group(3))
            is_division = operator in {"chia", ":"}
            if left > 0 and right > 0 and left.is_integer() and right.is_integer():
                self.problem_type = "division_basic" if is_division else "multiplication_basic"
                self.domain = MathDomain.ARITHMETIC
                self.quantities = [
                    ProviderQuantity(
                        role=MathQuantityRole.COUNT_INITIAL,
                        value=left,
                        unit="one",
                        label="Tổng số cần chia" if is_division else "Số nhóm",
                        evidence=ProviderEvidence(
                            confidence=1.0,
                            status=EvidenceStatus.EXPLICIT,
                        ),
                    ),
                    ProviderQuantity(
                        role=MathQuantityRole.COUNT_CHANGE,
                        value=right,
                        unit="one",
                        label="Số phần tử mỗi nhóm",
                        evidence=ProviderEvidence(
                            confidence=1.0,
                            status=EvidenceStatus.EXPLICIT,
                        ),
                    ),
                ]
                self.unknowns = [ProviderUnknown(
                    role=MathQuantityRole.RESULT,
                    kind="number",
                    unit="one",
                    label="Kết quả của phép chia" if is_division else "Kết quả của phép nhân",
                )]
                self.requires_review = False
                self.review_notes = []
        return self


class ProviderDocument(ProviderModel):
    extracted_text: ProviderVerbatimText = Field(min_length=1, max_length=100_000)
    questions: list[ProviderQuestion] = Field(min_length=1, max_length=100)
    confidence: float = Field(ge=0, le=1)
    requires_review: bool


class OllamaMathVisionProvider:
    """Structured text and image analysis through Ollama's local REST API."""

    name = "ollama"

    def __init__(self, settings: Settings, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.settings = settings
        self.base_url = settings.math_lab_ollama_url.rstrip("/")
        self.model = settings.math_lab_ollama_model
        self.transport = transport

    async def available(self) -> bool:
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.settings.math_lab_capability_timeout_seconds,
                transport=self.transport,
            ) as client:
                response = await client.get("/api/tags")
                response.raise_for_status()
                names = {item.get("name") for item in response.json().get("models", [])}
                return self.model in names
        except (httpx.HTTPError, ValueError, TypeError):
            return False

    async def analyze_text(self, text: str, grade_hint: int | None) -> ProviderDocument:
        prompt = self._prompt("text", grade_hint, text)
        output_tokens = min(
            self.settings.math_lab_ollama_output_tokens,
            max(4096, 2048 + len(text)),
        )
        return await self._request(prompt, max_output_tokens=output_tokens)

    async def analyze_image(
        self,
        image: bytes,
        media_type: str,
        grade_hint: int | None,
    ) -> ProviderDocument:
        prompt = self._prompt(
            "image",
            grade_hint,
            "Đọc toàn bộ chữ và cấu trúc câu hỏi trong ảnh. Không bỏ qua câu nhỏ a), b), c). "
            "Nếu có A./B./C./D., bắt buộc chép từng phương án vào choices theo đúng thứ tự.",
        )
        encoded = base64.b64encode(image).decode("ascii")
        result = await self._request(
            prompt,
            images=[encoded],
            max_output_tokens=self.settings.math_lab_ollama_output_tokens,
        )
        missing_choices = [
            index
            for index, question in enumerate(result.questions)
            if question.question_format == QuestionFormat.MULTIPLE_CHOICE and not question.choices
        ]
        if not missing_choices:
            return result

        # A compact VLM can classify a page as multiple choice yet omit the
        # answer rows. Retry only that incomplete case while the image remains
        # hot in the provider. Never fabricate options in deterministic code.
        recovery_prompt = self._prompt(
            "image",
            grade_hint,
            "Đây là lượt đọc bù phương án trắc nghiệm. Quan sát lại toàn bộ ảnh, đặc biệt từng dòng "
            "A., B., C., D. Chép nguyên văn tất cả phương án vào choices theo đúng thứ tự; "
            "vẫn trả toàn bộ JSON ProviderDocument và không giải bài.",
        )
        recovered = await self._request(
            recovery_prompt,
            images=[encoded],
            max_output_tokens=self.settings.math_lab_ollama_output_tokens,
        )
        recovered_by_number = {item.question_number: item for item in recovered.questions}
        for index in missing_choices:
            question = result.questions[index]
            candidate = recovered_by_number.get(question.question_number)
            if candidate and candidate.choices:
                question.choices = candidate.choices
        if len(recovered.extracted_text) > len(result.extracted_text):
            result.extracted_text = recovered.extracted_text
        return result

    async def _request(
        self,
        prompt: str,
        images: list[str] | None = None,
        max_output_tokens: int = 2048,
    ) -> ProviderDocument:
        messages: list[dict[str, Any]] = [{
            "role": "user",
            "content": prompt,
            **({"images": images} if images else {}),
        }]
        schema = self._grammar_schema(ProviderDocument.model_json_schema())

        async with httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.settings.math_lab_analysis_timeout_seconds,
            transport=self.transport,
        ) as client:
            for attempt in range(3):
                content = ""
                try:
                    content_parts: list[str] = []
                    thinking_parts: list[str] = []
                    async with client.stream("POST", "/api/chat", json={
                        "model": self.model,
                        "messages": messages,
                        "stream": True,
                        "format": schema,
                        "options": {
                            "temperature": 0,
                            "num_ctx": self.settings.math_lab_ollama_context_tokens,
                            "num_predict": max_output_tokens,
                            "num_gpu": self.settings.math_lab_ollama_gpu_layers,
                        },
                        "keep_alive": "10m",
                    }) as response:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            if not line:
                                continue
                            event = json.loads(line)
                            message = event.get("message", {})
                            content_parts.append(message.get("content", ""))
                            thinking_parts.append(message.get("thinking", ""))
                    content_output = "".join(content_parts)
                    thinking_output = "".join(thinking_parts)
                    content = content_output or thinking_output
                except httpx.TimeoutException as exc:
                    raise MathAnalysisError("Bộ phân tích Toán đã hết thời gian chờ", 504) from exc
                except httpx.ConnectError as exc:
                    raise MathAnalysisError("Không kết nối được Math Vision provider", 503) from exc
                except httpx.HTTPStatusError as exc:
                    status = 429 if exc.response.status_code == 429 else 502
                    raise MathAnalysisError("Math Vision provider từ chối yêu cầu", status) from exc
                except httpx.HTTPError as exc:
                    raise MathAnalysisError("Math Vision provider không phản hồi", 502) from exc

                try:
                    # Qwen3-VL on Ollama can place schema-constrained JSON in
                    # the dedicated thinking field even when think=false.
                    # Both fields are first-class API response fields; either
                    # candidate is still validated as JSON by Pydantic below.
                    if not content:
                        raise ValueError("provider returned no structured content")
                    validation_error: Exception | None = None
                    for candidate in (content_output, thinking_output):
                        if not candidate:
                            continue
                        try:
                            return self._validated_document(candidate)
                        except (TypeError, ValueError, ValidationError) as exc:
                            validation_error = exc
                    if validation_error:
                        raise validation_error
                    raise ValueError("provider returned no structured content")
                except (KeyError, TypeError, ValueError, ValidationError) as exc:
                    if attempt == 2:
                        raise MathAnalysisError("Kết quả AI không đúng cấu trúc Math Lab", 502) from exc
                    messages.extend([
                        {
                            "role": "assistant",
                            "content": content,
                        },
                        {
                            "role": "user",
                            "content": (
                                "Kết quả trên không vượt qua Pydantic validation. "
                                "Hãy trả lại toàn bộ JSON đúng schema, không thêm giải thích. "
                                f"Lỗi: {str(exc)[:1200]}"
                            ),
                        },
                    ])

        raise MathAnalysisError("Math Vision provider không tạo được kết quả", 502)

    @staticmethod
    def _validated_document(raw: str) -> ProviderDocument:
        """Validate schema JSON even when a model leaks reasoning wrappers.

        Some Ollama vision models stream structured output through the
        ``thinking`` field and may include a ``<think>`` prefix despite
        ``think=false``. A model can also emit an intermediate JSON object
        before its final object. We never accept prose or partial objects as
        data: each candidate still has to pass the strict Pydantic schema.
        """
        decoder = json.JSONDecoder()
        validation_error: Exception | None = None
        document_error: ValidationError | None = None
        for index, character in enumerate(raw):
            if character != "{":
                continue
            try:
                candidate, _ = decoder.raw_decode(raw[index:])
            except json.JSONDecodeError as exc:
                validation_error = exc
                continue
            try:
                return ProviderDocument.model_validate(candidate)
            except ValidationError as exc:
                validation_error = exc
                if isinstance(candidate, dict) and (
                    "questions" in candidate or "extracted_text" in candidate
                ):
                    document_error = exc
        if document_error:
            raise document_error
        if validation_error:
            raise validation_error
        raise ValueError("provider returned no JSON object")

    @staticmethod
    def _grammar_schema(value: Any) -> Any:
        """Keep the structural JSON schema subset Ollama's grammar accepts.

        Length, range and regex constraints are enforced by Pydantic after
        generation. Ollama 0.30 rejects those annotation keywords while
        initializing the qwen3-vl instruct grammar, so passing them would
        fail before the model sees the request.
        """
        unsupported = {
            "title",
            "maxLength",
            "minLength",
            "maxItems",
            "minItems",
            "maximum",
            "minimum",
            "pattern",
            "default",
        }
        if isinstance(value, dict):
            return {
                key: OllamaMathVisionProvider._grammar_schema(item)
                for key, item in value.items()
                if key not in unsupported
            }
        if isinstance(value, list):
            return [OllamaMathVisionProvider._grammar_schema(item) for item in value]
        return value

    @staticmethod
    def _prompt(source_type: Literal["text", "image"], grade_hint: int | None, content: str) -> str:
        grade_rule = (
            f"Giáo viên đã xác nhận đây là lớp {grade_hint}; dùng đúng grade={grade_hint}."
            if grade_hint
            else "Tự ước lượng grade từ 1 đến 9 và đánh dấu requires_review nếu không chắc."
        )
        return f"""
Bạn là Math Problem Analyzer cho chương trình Toán phổ thông Việt Nam lớp 1-9.
Đầu vào là {"văn bản giáo viên nhập" if source_type == "text" else "ảnh đề toán thật"}.
{grade_rule}

Nhiệm vụ:
1. Tách đầy đủ từng Câu/Bài thành questions riêng. Giữ a), b), c) trong subquestions.
2. Phân loại question_format. Các phương án A/B/C/D là choices, KHÔNG phải dữ kiện toán học.
3. Với mỗi câu tạo dữ liệu semantic đúng schema. Không giải thay unknown và không bịa dữ kiện.
   Nếu đề có dấu "?" hoặc yêu cầu tính, TUYỆT ĐỐI không tạo quantity cho đáp số;
   chỉ tạo unknown role=result. Không tính nhẩm kết quả dù bài rất ngắn.
4. Ý nghĩa mỗi đại lượng bắt buộc nằm ở quantity.role; ID ổn định sẽ do server tạo.
	5. Dùng role phù hợp: count_initial/count_change, distance/speed/duration,
	   numerator/denominator, addend_numerator/addend_denominator, exponent,
	   target_denominator, length/width/height/radius/angle, mass/capacity/area/volume/total,
   variable/coefficient/constant, x_value/y_value, category/frequency/probability.
6. entity.role dùng moving_entity/origin/destination/shape/point khi phù hợp.
7. Dữ kiện có nguyên văn là evidence explicit. Suy ra trung gian phải là inferred.
   Điều không chắc phải là uncertain, locked=false và requires_review=true.
8. Không tạo perpendicular/right-angle nếu chữ hoặc ký hiệu góc vuông không nêu rõ.
9. Giữ nguyên đơn vị được hỗ trợ trong schema. Nếu đơn vị không rõ, ghi review_notes,
   không tự đoán.
   - Bắt buộc dùng unit="one" cho số đếm, phân số và đại số không có đơn vị.
   - length/width/height/radius/diameter chỉ dùng đơn vị độ dài.
	   - angle luôn dùng unit="degree"; ký hiệu ° là độ, không bỏ mất số đo góc.
	   - mass chỉ dùng unit="g" hoặc "kg"; tổng khối lượng ban đầu dùng role=mass.
	   - diện tích dùng role=area với unit="cm2" hoặc "m2"; tuyệt đối không đổi diện tích thành mass/kg.
	   - diện tích hỗn hợp như 10dam² 80m² được chuẩn hóa từng thành phần sang m² với evidence inferred và giữ phép đổi trong label.
   - Đại lượng cần tìm dùng role=result nếu role cụ thể đó đã xuất hiện trong dữ kiện.
   - Không tạo quantity giả (ví dụ variable x=0) để đại diện cho unknown.
10. stem phải là nguyên văn câu tương ứng.
11. confidence phản ánh chất lượng đọc/hiểu thật, không mặc định 1.
12. Phân loại problem_type đủ cụ thể để hệ trực quan dựng đúng phép biến đổi:
   - a/b + c/d -> fraction_addition; a/b - c/d -> fraction_subtraction.
   - a/b × c/d -> fraction_multiplication.
   - (a/b)^n hoặc (a/b)ⁿ -> fraction_power; numerator=a, denominator=b, exponent=n.
   - ax + b = c -> linear_equation; y = mx + b -> linear_function.
   - (a+b)^2 hoặc khai triển hằng đẳng thức -> binomial_expansion.
   - thể tích hình hộp -> cuboid_volume; điểm/đường trên hệ trục -> coordinate_plot.
	   - tia phân giác của một góc -> angle_bisector; số đo góc đã cho dùng role=angle,
	     unit=degree; góc cần tìm chỉ là unknown role=result.
	   - ngày 1 lấy a/b của toàn bộ, ngày 2 lấy c/d của phần còn lại rồi hỏi tỉ số
	     ngày 3/ngày 1 -> sequential_fraction_remainder_ratio; tổng dùng mass (hoặc
	     count_initial nếu là số lượng), a/b dùng numerator/denominator, c/d dùng
	     addend_numerator/addend_denominator; không tự tính lượng của từng ngày.
	   - một tổng đại lượng, dùng a/b toàn bộ rồi dùng c/d của phần còn lại và hỏi
	     lượng cuối cùng -> sequential_fraction_remainder_quantity; tổng dùng role
	     đúng đại lượng (area/mass/count_initial/total), hai phân số giữ
	     numerator/denominator và addend_numerator/addend_denominator; không tính phần cuối.
	   - ba món hàng có giá/giảm giá, biết tổng tiền đã trả và hỏi giá gốc món thứ ba
	     -> multi_item_reverse_discount; hai giá gốc đã biết dùng count_initial theo
	     đúng thứ tự, ba mức giảm (%) dùng probability theo đúng thứ tự, tổng tiền
	     thanh toán dùng total; giá gốc món thứ ba chỉ là unknown role=result.
	   - một tổ có a người dự định làm xong trong b ngày, sau đó thêm/bớt c người,
	     năng suất mỗi người như nhau và hỏi số ngày mới -> work_rate_with_variable_people;
	     a dùng count_initial, b dùng duration unit=one (đếm số ngày), c dùng count_change (âm nếu
	     rút bớt); số ngày mới chỉ là unknown role=result. Không tính đáp số trong analyzer.
13. Với hai phân số: phân số thứ nhất bắt buộc dùng numerator/denominator;
   phân số thứ hai dùng addend_numerator/addend_denominator, kể cả phép nhân.
   target_denominator chỉ ghi khi đề bài nêu sẵn; hệ thống sẽ tự tính mẫu chung nếu không nêu.
14. Với y = mx + b: m dùng coefficient và b dùng constant. Với ax+b=c:
   a dùng coefficient, b dùng constant, c dùng result, còn x là unknown variable.
15. Với điểm tọa độ, tạo x_value và y_value theo cùng thứ tự để ghép thành từng cặp.
16. Mục tiêu là dữ liệu cho mô phỏng từng bước: giữ nguyên mọi số hạng, dấu phép toán,
   kích thước và quan hệ được nêu; không rút gọn chúng thành riêng đáp số.
17. Ghi cấu trúc toán vào relationships thay vì chỉ liệt kê số. participant_roles
   trỏ tới role duy nhất; khi một role lặp lại, dùng role[1], role[2] theo thứ tự
   nguồn. Dùng các type như part_whole, equal_groups, remaining_of,
   proportional_to, inverse_proportional_to, distance_speed_time,
   angle_bisector, function_of, equivalent_measure hoặc motion. Nếu participant
   còn mơ hồ thì không tạo quan hệ và phải bật requires_review.

Ví dụ ánh xạ ngắn:
- "1/2 + 1/3" -> fraction_addition; numerator=1, denominator=2,
  addend_numerator=1, addend_denominator=3; unknown result.
- "2 nhân 4 bằng mấy?" -> multiplication_basic; count_initial=2,
  count_change=4; unknown result; relationship equal_groups. Không được bỏ hai toán hạng vì phép tính ngắn.
- "12 chia 3 bằng mấy?" -> division_basic; count_initial=12,
  count_change=3; unknown result.
- "(-2/5)^3" -> fraction_power; numerator=-2, denominator=5, exponent=3; unknown result.
- "2x + 3 = 9" -> linear_equation; coefficient=2, constant=3, result=9; unknown variable.
- "y = 2x + 1" -> linear_function; coefficient=2, constant=1.
	- "hộp dài 4, rộng 3, cao 2 cm" -> cuboid_volume; length=4, width=3, height=2.
	- "Có 160kg; ngày 1 bán 3/8; ngày 2 bán 1/4 số còn lại; hỏi tỉ số ngày 3/ngày 1"
	  -> sequential_fraction_remainder_ratio; mass=160kg, numerator=3, denominator=8,
	  addend_numerator=1, addend_denominator=4; unknown result.
	- "Đất 10dam² 80m²; dùng 2/5 làm nhà; dùng 1/3 phần còn lại trồng hoa; hỏi phần cuối"
	  -> sequential_fraction_remainder_quantity; area=[1000m2,80m2], numerator=2,
	  denominator=5, addend_numerator=1, addend_denominator=3; unknown result m2.
	- "Món 1 giá 125 000 giảm 30%, món 2 giá 300 000 giảm 15%, món 3 giảm 12,5%,
	  tổng trả 692 500; hỏi giá gốc món 3" -> multi_item_reverse_discount;
	  count_initial=[125000,300000], probability=[30,15,12.5], total=692500;
	  unknown result. Không gán đơn vị g/kg cho tiền.
	- "Tổ 8 người làm trong 6 ngày, bổ sung thêm 4 người; năng suất như nhau"
	  -> work_rate_with_variable_people; count_initial=8, duration=6 unit=one,
	  count_change=4; unknown result.

Chỉ trả JSON theo schema được ép bởi trường format. Không Markdown, không lời giải.

Nội dung đầu vào:
{content}
""".strip()


class MathProblemAnalyzer:
    def __init__(
        self,
        settings: Settings,
        provider: OllamaMathVisionProvider | None = None,
    ) -> None:
        self.settings = settings
        self.provider = provider or (
            OllamaMathVisionProvider(settings)
            if settings.math_lab_provider == "ollama"
            else None
        )

    async def capabilities(self) -> MathLabCapabilities:
        configured = self.provider is not None
        available = configured and await self.provider.available()
        return MathLabCapabilities(
            text_analysis=bool(available),
            image_analysis=bool(available),
            provider_configured=configured,
            provider_available=bool(available),
            provider=self.provider.name if self.provider else None,
            model=self.provider.model if self.provider else None,
            accepted_image_types=list(ACCEPTED_IMAGE_TYPES),
            max_image_bytes=self.settings.math_lab_max_image_bytes,
            message=(
                None
                if available
                else "AI Vision chưa được cấu hình hoặc model chưa sẵn sàng."
            ),
        )

    async def analyze_text(self, text: str, grade_hint: int | None) -> MathDocumentAnalysis:
        deterministic = self._deterministic_text_draft(text, grade_hint)
        if deterministic is not None:
            return self._finalize(deterministic, "text", grade_hint)
        provider = await self._ready_provider()
        draft = await provider.analyze_text(text, grade_hint)
        # For one-question text input the browser already supplied the exact
        # source. Do not let a language model introduce OCR-like spelling
        # changes (for example “xong” -> “xonh”) into the displayed problem.
        # Revalidation also lets the deterministic operand recoveries inspect
        # the authoritative source instead of the model's paraphrase.
        payload = draft.model_dump(mode="json")
        # The request body is the only authority for typed text.  Provider
        # output may classify or split it, but may never rewrite the original
        # input shown back to the teacher.
        payload["extracted_text"] = text
        if len(draft.questions) == 1:
            payload["questions"][0]["stem"] = text
        draft = ProviderDocument.model_validate(payload)
        return self._finalize(draft, "text", grade_hint)

    @staticmethod
    def _deterministic_text_draft(
        text: str,
        grade_hint: int | None,
    ) -> ProviderDocument | None:
        """Bypass the VLM only for strict, fully recognized text grammars.

        This is intentionally narrow. It removes model latency and schema
        variance from a small set of unambiguous classroom expressions while
        still sending every other text and every image through AI Vision.
        """

        direct_distance = extract_direct_proportion_distance_time(text)
        discount_system = extract_two_item_discount_system(text)
        parenthesized = extract_parenthesized_multiplication(text)
        factorial = extract_factorial(text)
        basic_expression = extract_basic_arithmetic(text)
        primary_word = extract_primary_word_arithmetic(text)
        basic = basic_expression or primary_word
        binary_fraction = extract_binary_fraction(text)
        rectangle = extract_rectangle_dimensions(text)
        equation = extract_linear_equation(text)
        system = extract_linear_system(text)
        inequality = parse_linear_inequality(text)
        product = parse_product_equation(text)
        domain_condition = parse_rational_domain(text)
        fractional_linear = parse_fractional_linear_equation(text)
        absolute_value = parse_absolute_value_equation(text)
        biquadratic = parse_biquadratic_equation(text)
        radical = parse_radical_equation(text)
        rational_equation = parse_rational_equation(text)
        degenerate = classify_linear(text)
        degenerate_kind = (
            degenerate.kind
            if degenerate and degenerate.kind in {"identity", "contradiction"}
            else None
        )
        two_variable_equation = extract_two_variable_linear_equation(text)
        three_variable_equation = extract_three_variable_linear_equation(text)
        quadratic_surface = parse_quadratic_surface(text)
        quadratic_equation = parse_quadratic_equation(text)
        cubic_equation = parse_cubic_equation(text)
        linear_expression = extract_single_variable_linear_expression(text)
        right_triangle = extract_right_triangle(text)
        if right_triangle and not (
            len(right_triangle.sides) >= 2
            or (right_triangle.sides and right_triangle.angles)
        ):
            right_triangle = None
        angle_of_depression = extract_angle_of_depression(text)
        oblique_triangle = extract_oblique_triangle_altitude(text)
        parallelogram = extract_perpendicular_diagonal_parallelogram(text)
        area_remainder = extract_sequential_fraction_remainder_area(text)
        work_rate = extract_variable_people_work_rate(text)
        if not any((
            direct_distance,
            discount_system,
            parenthesized,
            factorial,
            basic,
            binary_fraction,
            rectangle,
            equation,
            system,
            inequality,
            product,
            domain_condition,
            fractional_linear,
            absolute_value,
            biquadratic,
            radical,
            rational_equation,
            degenerate_kind,
            two_variable_equation,
            three_variable_equation,
            quadratic_surface,
            quadratic_equation,
            cubic_equation,
            linear_expression,
            right_triangle,
            angle_of_depression,
            oblique_triangle,
            parallelogram,
            area_remainder,
            work_rate,
        )):
            return None

        if discount_system:
            problem_type, domain, default_grade = "two_item_discount_system", "algebra", 9
        elif direct_distance:
            problem_type, domain, default_grade = "distance_time_direct_proportion", "ratio", 5
        elif parenthesized:
            problem_type = f"parenthesized_{parenthesized.inner_operation}_multiplication"
            domain, default_grade = "arithmetic", 3
        elif factorial:
            problem_type, domain, default_grade = "factorial", "number", 9
        elif basic:
            problem_type, domain, default_grade = f"{basic.operation}_basic", "arithmetic", 2
        elif binary_fraction:
            problem_type, domain, default_grade = f"fraction_{binary_fraction.operation}", "fraction", 4
        elif rectangle:
            problem_type, domain, default_grade = "rectangle_area", "geometry_2d", 4
        elif fractional_linear:
            problem_type, domain, default_grade = "fractional_linear_equation", "algebra", 8
        elif absolute_value:
            problem_type, domain, default_grade = "absolute_value_equation", "algebra", 8
        elif biquadratic:
            problem_type, domain, default_grade = "biquadratic_equation", "algebra", 9
        elif radical:
            problem_type, domain, default_grade = "radical_equation", "algebra", 9
        elif rational_equation:
            problem_type, domain, default_grade = "rational_equation", "algebra", 9
        elif inequality:
            problem_type, domain, default_grade = "linear_inequality_one_variable", "algebra", 9
        elif product:
            problem_type, domain, default_grade = "product_equation_roots", "algebra", 9
        elif domain_condition:
            problem_type, domain, default_grade = "rational_equation_domain", "algebra", 9
        elif system:
            problem_type, domain, default_grade = (
                ("linear_system_three_variables_planes", "geometry_3d", 9)
                if len(system.variables) == 3
                else ("linear_system_two_variables_graph", "coordinate", 9)
            )
        elif degenerate_kind:
            problem_type, domain, default_grade = f"linear_{degenerate_kind}", "algebra", 8
        elif three_variable_equation:
            problem_type, domain, default_grade = "linear_equation_three_variables_plane", "geometry_3d", 9
        elif quadratic_surface:
            problem_type, domain, default_grade = "quadratic_surface_three_variables", "geometry_3d", 9
        elif quadratic_equation:
            problem_type, domain, default_grade = "quadratic_equation", "algebra", 9
        elif cubic_equation:
            problem_type, domain, default_grade = "cubic_equation", "algebra", 9
        elif two_variable_equation:
            problem_type, domain, default_grade = "linear_equation_two_variables_graph", "coordinate", 7
        elif linear_expression:
            problem_type, domain, default_grade = "polynomial_evaluate_reorder", "algebra", 7
        elif equation:
            problem_type, domain, default_grade = "linear_equation", "algebra", 8
        elif right_triangle:
            problem_type, domain, default_grade = (
                "right_triangle_solution"
                if (
                    right_triangle.solve_all
                    or right_triangle.hypotenuse_name in right_triangle.sides
                    or (len(right_triangle.sides) == 1 and right_triangle.angles)
                )
                else "right_triangle_hypotenuse"
            ), "geometry_2d", 9
        elif angle_of_depression:
            problem_type, domain, default_grade = "angle_of_depression_distance", "geometry_2d", 9
        elif oblique_triangle:
            problem_type, domain, default_grade = "oblique_triangle_altitude_solution", "geometry_2d", 9
        elif parallelogram:
            problem_type, domain, default_grade = "parallelogram_perpendicular_diagonal_area", "geometry_2d", 9
        elif area_remainder:
            problem_type, domain, default_grade = "sequential_fraction_remainder_quantity", "ratio", 6
        else:
            problem_type, domain, default_grade = "work_rate_with_variable_people", "ratio", 5

        is_word_problem = any((
            direct_distance,
            discount_system,
            primary_word,
            rectangle,
            right_triangle,
            angle_of_depression,
            oblique_triangle,
            parallelogram,
            area_remainder,
            work_rate,
        ))
        return ProviderDocument.model_validate({
            "extracted_text": text,
            "confidence": 1.0,
            "requires_review": False,
            "questions": [{
                "question_number": "1",
                "stem": text,
                "question_format": "word_problem" if is_word_problem else "short_answer",
                "choices": [],
                "subquestions": [],
                "grade": grade_hint or default_grade,
                "domain": domain,
                "problem_type": problem_type,
                "entities": [{
                    "role": "moving_entity",
                    "type": "vehicle",
                    "label": "Ô tô",
                    "evidence": {"confidence": 1.0, "status": "explicit"},
                }] if direct_distance else [],
                "quantities": [],
                "unknowns": [{
                    "role": "result",
                    "kind": "distance" if direct_distance else "number",
                    "unit": None,
                    "label": "Quãng đường trong thời gian mới" if direct_distance else "Kết quả biểu thức",
                }],
                "relationships": [],
                "constraints": [],
                "start_time": None,
                "end_time": None,
                "confidence": 1.0,
                "requires_review": False,
                "review_notes": [],
            }],
        })

    async def analyze_image(
        self,
        image: bytes,
        media_type: str,
        grade_hint: int | None,
    ) -> MathDocumentAnalysis:
        provider = await self._ready_provider()
        draft = await provider.analyze_image(image, media_type, grade_hint)
        # The vision model often splits a true/false worksheet into the story
        # and four statements a-d, leaving each fragment without the operands
        # required by a renderer.  When the OCR text contains the complete
        # two-item discount system, collapse only this strict family back to
        # one mathematical question before finalizing the scene.
        recognized_text = draft.extracted_text
        if not extract_two_item_discount_system(recognized_text):
            recognized_text = "\n".join(question.stem for question in draft.questions)
        if extract_two_item_discount_system(recognized_text):
            repaired = self._deterministic_text_draft(recognized_text, grade_hint)
            if repaired is not None:
                draft = repaired
        return self._finalize(draft, "image", grade_hint)

    async def _ready_provider(self) -> OllamaMathVisionProvider:
        if self.provider is None:
            raise MathAnalysisError("AI Vision chưa được cấu hình", 503)
        if not await self.provider.available():
            raise MathAnalysisError("Math Vision model chưa sẵn sàng", 503)
        return self.provider

    def _finalize(
        self,
        draft: ProviderDocument,
        source_type: Literal["text", "image"],
        grade_hint: int | None,
    ) -> MathDocumentAnalysis:
        questions: list[MathQuestionAnalysis] = []
        for question_index, question in enumerate(draft.questions, start=1):
            role_ids: dict[str, list[str]] = {}
            entities: list[SemanticEntity] = []
            quantities: list[MathQuantity] = []
            unknowns: list[MathUnknown] = []

            for index, item in enumerate(question.entities, start=1):
                identifier = f"entity_{index}"
                role_ids.setdefault(item.role, []).append(identifier)
                entities.append(SemanticEntity(
                    id=identifier,
                    type=item.type,
                    label=item.label,
                    role=item.role,
                    evidence=self._evidence(item.evidence, source_type),
                ))
            for index, item in enumerate(question.quantities, start=1):
                identifier = f"quantity_{index}"
                role_ids.setdefault(item.role.value, []).append(identifier)
                quantities.append(MathQuantity(
                    id=identifier,
                    role=item.role,
                    value=item.value,
                    unit=item.unit,
                    label=item.label,
                    evidence=self._evidence(item.evidence, source_type),
                    editable=True,
                ))
            for index, item in enumerate(question.unknowns, start=1):
                identifier = f"unknown_{index}"
                role_ids.setdefault(item.role.value, []).append(identifier)
                unknowns.append(MathUnknown(
                    id=identifier,
                    role=item.role,
                    kind=item.kind,
                    unit=item.unit,
                    label=item.label,
                ))

            roles = {item.role for item in quantities}
            unknown_roles = {item.role for item in unknowns}
            if (
                question.domain == MathDomain.MOTION
                and MathQuantityRole.SPEED not in roles
                and MathQuantityRole.SPEED not in unknown_roles
                and MathQuantityRole.DISTANCE in roles
                and MathQuantityRole.DURATION in roles
            ):
                distance = next(item for item in quantities if item.role == MathQuantityRole.DISTANCE)
                duration = next(item for item in quantities if item.role == MathQuantityRole.DURATION)
                try:
                    distance_value, distance_unit = canonicalize(distance.value, distance.unit)
                    duration_value, duration_unit = canonicalize(duration.value, duration.unit)
                    if distance_unit == "m" and duration_unit == "second" and duration_value > 0:
                        identifier = f"quantity_{len(quantities) + 1}"
                        role_ids.setdefault(MathQuantityRole.SPEED.value, []).append(identifier)
                        quantities.append(MathQuantity(
                            id=identifier,
                            role=MathQuantityRole.SPEED,
                            value=distance_value / duration_value,
                            unit="m/s",
                            label="Vận tốc suy ra từ dữ kiện",
                            editable=True,
                            evidence=Evidence(
                                confidence=min(distance.evidence.confidence, duration.evidence.confidence),
                                status=EvidenceStatus.INFERRED,
                                source=(
                                    EvidenceSource.SYSTEM
                                    if source_type == "text"
                                    else EvidenceSource.VISION_INFERENCE
                                ),
                            ),
                        ))
                except UnitConversionError:
                    pass

            review_notes = list(question.review_notes)
            relations: list[SemanticRelation] = []
            for index, item in enumerate(question.relationships, start=1):
                participants: dict[str, str] = {}
                unresolved = False
                for participant, role_reference in item.participant_roles.items():
                    match = re.fullmatch(r"(.+?)(?:\[(\d+)\])?", role_reference)
                    role = match.group(1) if match else role_reference
                    requested_index = int(match.group(2)) - 1 if match and match.group(2) else None
                    candidates = role_ids.get(role, [])
                    if requested_index is None:
                        if len(candidates) != 1:
                            unresolved = True
                            break
                        participants[participant] = candidates[0]
                    elif 0 <= requested_index < len(candidates):
                        participants[participant] = candidates[requested_index]
                    else:
                        unresolved = True
                        break
                if unresolved:
                    review_notes.append(
                        f"Quan hệ {item.type} thiếu hoặc mơ hồ đối tượng tham chiếu; đã bỏ khỏi graph."
                    )
                    continue
                relations.append(SemanticRelation(
                    id=f"relation_{index}",
                    type=item.type,
                    participants=participants,
                    parameters=item.parameters,
                    evidence=self._evidence(item.evidence, source_type),
                ))
            constraints: list[SemanticConstraint] = []
            for index, item in enumerate(question.constraints, start=1):
                target_ids = [role_ids[role][0] for role in item.target_roles if role_ids.get(role)]
                if len(target_ids) != len(item.target_roles):
                    review_notes.append(
                        f"Ràng buộc {item.type} thiếu đối tượng được tham chiếu; cần giáo viên kiểm tra."
                    )
                    continue
                evidence = self._evidence(item.evidence, source_type)
                constraints.append(SemanticConstraint(
                    id=f"constraint_{index}",
                    type=item.type,
                    target_ids=target_ids,
                    locked=item.locked
                    and evidence.status != EvidenceStatus.UNCERTAIN
                    and evidence.confidence >= 0.75,
                    evidence=evidence,
                ))

            model = MathSemanticModel(
                id=f"analysis_question_{question_index}",
                grade=grade_hint or question.grade,
                domain=question.domain,
                problem_type=question.problem_type,
                source_text=question.stem,
                choices=question.choices,
                entities=entities,
                quantities=quantities,
                unknowns=unknowns,
                relations=relations,
                constraints=constraints,
                time=TimeContext(start=question.start_time, end=question.end_time)
                if question.start_time or question.end_time
                else None,
            )

            uncertain = any(
                item.evidence.status == EvidenceStatus.UNCERTAIN
                for collection in (model.entities, model.quantities, model.relations, model.constraints)
                for item in collection
            )
            requires_review = (
                question.requires_review
                or question.confidence < 0.8
                or uncertain
                or bool(review_notes)
            )
            questions.append(MathQuestionAnalysis(
                id=f"question_{question_index}",
                question_number=question.question_number,
                stem=question.stem,
                question_format=question.question_format,
                choices=question.choices,
                subquestions=[
                    MathSubquestionAnalysis(
                        id=f"question_{question_index}_part_{part_index}",
                        label=part.label,
                        text=part.text,
                    )
                    for part_index, part in enumerate(question.subquestions, start=1)
                ],
                semantic_model=model,
                confidence=question.confidence,
                requires_review=requires_review,
                review_notes=review_notes,
            ))

        return MathDocumentAnalysis(
            source_type=source_type,
            provider=self.provider.name if self.provider else "disabled",
            model=self.provider.model if self.provider else "",
            extracted_text=draft.extracted_text,
            questions=questions,
            confidence=draft.confidence,
            requires_review=draft.requires_review or any(item.requires_review for item in questions),
        )

    @staticmethod
    def _evidence(item: ProviderEvidence, source_type: Literal["text", "image"]) -> Evidence:
        status = item.status
        if status == EvidenceStatus.EXPLICIT and item.confidence < 0.65:
            status = EvidenceStatus.UNCERTAIN
        if source_type == "text":
            source = EvidenceSource.TEXT_INPUT if status == EvidenceStatus.EXPLICIT else EvidenceSource.SYSTEM
        else:
            source = EvidenceSource.VISION_OCR if status == EvidenceStatus.EXPLICIT else EvidenceSource.VISION_INFERENCE
        return Evidence(confidence=item.confidence, status=status, source=source)
