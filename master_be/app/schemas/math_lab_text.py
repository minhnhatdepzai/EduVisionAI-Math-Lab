from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from app.schemas.math_lab_input import canonicalize_typed_math
from app.schemas.math_lab_linear import (
    LinearForm,
    LinearSystem,
    classify_linear,
)


@dataclass(frozen=True, slots=True)
class VariablePeopleWorkRateOperands:
    initial_workers: int
    planned_days: int
    worker_change: int


@dataclass(frozen=True, slots=True)
class BasicArithmeticOperands:
    left: int
    right: int
    operation: str


@dataclass(frozen=True, slots=True)
class FactorialOperand:
    value: int


@dataclass(frozen=True, slots=True)
class DirectProportionDistanceTimeOperands:
    """Printed values in a constant-rate distance/time word problem."""

    known_duration: float
    known_duration_unit: str
    known_distance: float
    known_distance_unit: str
    target_duration: float
    target_duration_unit: str


@dataclass(frozen=True, slots=True)
class ParenthesizedMultiplicationOperands:
    """Three printed operands in ``(a +/- b) × c``."""

    inner_left: int
    inner_right: int
    inner_operation: str
    multiplier: int


@dataclass(frozen=True, slots=True)
class BinaryFractionOperands:
    left_numerator: int
    left_denominator: int
    right_numerator: int
    right_denominator: int
    operation: str


@dataclass(frozen=True, slots=True)
class RectangleOperands:
    length: float
    width: float
    unit: str


@dataclass(frozen=True, slots=True)
class LinearEquationOperands:
    coefficient: float
    constant: float
    result: float


@dataclass(frozen=True, slots=True)
class TwoVariableLinearEquationOperands:
    x_coefficient: float
    y_coefficient: float
    result: float
    slope: float
    intercept: float
    #: Printed variable names, so a line drawn from ``2a + b = 6`` can label
    #: its axes with the learner's own symbols instead of forcing x and y.
    x_symbol: str = "x"
    y_symbol: str = "y"


@dataclass(frozen=True, slots=True)
class ThreeVariableLinearEquationOperands:
    x_coefficient: float
    y_coefficient: float
    z_coefficient: float
    result: float
    x_symbol: str = "x"
    y_symbol: str = "y"
    z_symbol: str = "z"


@dataclass(frozen=True, slots=True)
class SingleVariableLinearExpressionOperands:
    coefficient: float
    constant: float
    symbol: str = "x"


@dataclass(frozen=True, slots=True)
class RightTriangleOperands:
    first_leg: float
    second_leg: float
    unit: str


@dataclass(frozen=True, slots=True)
class RightTriangleFacts:
    """Every printed fact of a right triangle, whichever sides are given.

    "Giải tam giác ABC vuông tại A" gives two sides and asks for the third plus
    both acute angles. The older grammar only understood "two legs, find the
    hypotenuse", so this shape lost its operands entirely and the lab abstained
    on a completely ordinary grade-9 exercise.
    """

    vertices: str
    right_vertex: str
    #: Printed segment lengths, keyed by the normalized segment name (``AB``).
    sides: dict[str, float]
    unit: str
    #: Printed acute angles in degrees, keyed by vertex.
    angles: dict[str, float]
    solve_all: bool
    round_to_minute: bool

    @property
    def hypotenuse_name(self) -> str:
        """The side opposite the right angle: the one without that vertex."""

        return "".join(sorted(set(self.vertices) - {self.right_vertex}))

    @property
    def leg_names(self) -> tuple[str, str]:
        others = sorted(set(self.vertices) - {self.right_vertex})
        return (
            "".join(sorted(self.right_vertex + others[0])),
            "".join(sorted(self.right_vertex + others[1])),
        )

    @property
    def acute_vertices(self) -> tuple[str, str]:
        others = sorted(set(self.vertices) - {self.right_vertex})
        return (others[0], others[1])


@dataclass(frozen=True, slots=True)
class AngleOfDepressionFacts:
    """A vertical observation height and the printed angle of depression."""

    height: float
    angle: float
    unit: str
    landmark: str


@dataclass(frozen=True, slots=True)
class ObliqueTriangleAltitudeFacts:
    """A triangle split into two right triangles by a printed altitude."""

    vertices: str
    apex: str
    foot: str
    height: float
    unit: str
    base_angles: dict[str, float]


@dataclass(frozen=True, slots=True)
class PerpendicularDiagonalParallelogramFacts:
    """A parallelogram whose diagonal is perpendicular to one adjacent side."""

    vertices: str
    diagonal: str
    side: str
    side_length: float
    angle_vertex: str
    angle: float
    unit: str


@dataclass(frozen=True, slots=True)
class TwoItemDiscountSystemFacts:
    """Two unknown list prices constrained by two different discounts."""

    list_total: float
    paid_total: float
    first_discount: float
    second_discount: float
    first_label: str
    second_label: str
    first_symbol: str = "x"
    second_symbol: str = "y"
    claimed_first: float | None = None
    claimed_second: float | None = None


def _fold_vietnamese(text: str) -> str:
    """Return a spacing-normalized, accent-insensitive matching copy."""

    normalized = re.sub(
        r"\s+",
        " ",
        text.lower()
        .replace("−", "-")
        .replace("–", "-")
        .replace(",", ".")
        .strip(),
    )
    return "".join(
        character
        for character in unicodedata.normalize("NFD", normalized)
        if unicodedata.category(character) != "Mn"
    ).replace("đ", "d")


def extract_two_item_discount_system(
    text: str | None,
) -> TwoItemDiscountSystemFacts | None:
    """Read a two-book list-price system without accepting the printed claim.

    The family needs four independent printed operands: the combined list
    price, two item-specific discount rates and the combined amount paid.  A
    final true/false assertion may also be present; it travels as a claim to
    check, never as a known price or an answer quantity.
    """

    if not text:
        return None
    stem = _fold_vietnamese(text)
    money = r"(\d{1,3}(?:[ .]\d{3})+|\d+)"

    # Requiring both named books and their own discount phrases prevents a
    # normal one-item sale from being widened into a two-variable system.
    first_discount_match = re.search(
        r"(?:quyen\s+)?sach[^.;!?]{0,90}?\btoan\b[^.;!?]{0,90}?"
        r"(?:duoc\s+)?giam(?:\s+gia)?\s+(\d+(?:\.\d+)?)\s*%",
        stem,
    )
    second_discount_match = re.search(
        r"(?:quyen\s+)?sach[^.;!?]{0,90}?\bngu\s+van\b[^.;!?]{0,90}?"
        r"(?:duoc\s+)?giam(?:\s+gia)?\s+(\d+(?:\.\d+)?)\s*%",
        stem,
    )
    list_total_match = re.search(
        rf"tong\s+(?:so\s+)?tien[^.?!]{{0,100}}?gia\s+niem\s+yet"
        rf"[^.?!]{{0,35}}?(?:la|:)\s*{money}\s*(?:dong|d|vnd)\b",
        stem,
    ) or re.search(
        rf"tong\s+gia\s+niem\s+yet[^.?!]{{0,45}}?(?:la|:)\s*"
        rf"{money}\s*(?:dong|d|vnd)\b",
        stem,
    )
    paid_total_match = re.search(
        rf"(?:chi\s+can\s+)?(?:phai\s+)?tra\s+{money}\s*(?:dong|d|vnd)\b",
        stem,
    ) or re.search(
        rf"tong\s+(?:so\s+)?tien[^.?!]{{0,70}}?thanh\s+toan"
        rf"[^.?!]{{0,25}}?(?:la|:)\s*{money}\s*(?:dong|d|vnd)\b",
        stem,
    )
    if not all((
        first_discount_match,
        second_discount_match,
        list_total_match,
        paid_total_match,
    )):
        return None

    def read_money(match: re.Match[str]) -> float:
        return float(re.sub(r"[ .]", "", match.group(1)))

    list_total = read_money(list_total_match)
    paid_total = read_money(paid_total_match)
    first_discount = float(first_discount_match.group(1))
    second_discount = float(second_discount_match.group(1))
    if (
        list_total <= 0
        or paid_total <= 0
        or paid_total >= list_total
        or not 0 < first_discount < 100
        or not 0 < second_discount < 100
        or abs(first_discount - second_discount) < 1e-9
    ):
        return None

    claim = re.search(
        rf"gia\s+niem\s+yet\s+cua[^.?!]{{0,90}}?\btoan\b"
        rf"[^.?!]{{0,45}}?(?:la|:)\s*{money}\s*(?:dong|d|vnd)"
        rf"[^.?!]{{0,120}}?\bngu\s+van\b[^.?!]{{0,45}}?(?:la|:)\s*"
        rf"{money}\s*(?:dong|d|vnd)",
        stem,
    )
    claimed_first = read_money(claim) if claim else None
    claimed_second = (
        float(re.sub(r"[ .]", "", claim.group(2))) if claim else None
    )
    return TwoItemDiscountSystemFacts(
        list_total=list_total,
        paid_total=paid_total,
        first_discount=first_discount,
        second_discount=second_discount,
        first_label="Sách Toán",
        second_label="Sách Ngữ Văn",
        claimed_first=claimed_first,
        claimed_second=claimed_second,
    )


def extract_parenthesized_multiplication(
    text: str | None,
) -> ParenthesizedMultiplicationOperands | None:
    """Recognize a small integer expression with one parenthesized operation.

    The grammar accepts common Vietnamese OCR/typing variants such as ``x``
    for multiplication and ``bầng`` for ``bằng``. It only copies a, b and c;
    neither the value inside the parentheses nor the final answer is stored.
    """

    if not text:
        return None
    stem = re.sub(
        r"\s+",
        " ",
        text.lower().replace("−", "-").replace("–", "-").strip(),
    )
    # Match the structure, not one exact Vietnamese spelling. Teachers often
    # type without an IME (``bang may``, ``nhan``), while OCR may return a
    # near-accent such as ``bầng``. Folding accents keeps those variants on the
    # same deterministic path without widening the accepted math grammar.
    stem = "".join(
        character
        for character in unicodedata.normalize("NFD", stem)
        if unicodedata.category(character) != "Mn"
    ).replace("đ", "d")
    match = re.fullmatch(
        r"(?:tinh|ket\s+qua(?:\s+cua)?)?\s*"
        r"\(\s*(\d+)\s*(\+|-)\s*(\d+)\s*\)\s*"
        r"(?:×|x|\*|nhan)\s*(\d+)\s*"
        r"(?:(?:=|bang)\s*(?:\?|may|bao\s+nhieu)?)?\s*[.!?]?",
        stem,
        re.IGNORECASE,
    )
    if not match:
        return None
    left, operator, right, multiplier = (
        int(match.group(1)),
        match.group(2),
        int(match.group(3)),
        int(match.group(4)),
    )
    inner_value = left + right if operator == "+" else left - right
    if (
        max(left, right, multiplier) > 144
        or multiplier <= 0
        or inner_value <= 0
        or inner_value * multiplier > 144
    ):
        return None
    return ParenthesizedMultiplicationOperands(
        inner_left=left,
        inner_right=right,
        inner_operation="addition" if operator == "+" else "subtraction",
        multiplier=multiplier,
    )


_TIME_UNITS = {
    "giờ": "hour",
    "gio": "hour",
    "phút": "minute",
    "phut": "minute",
}
_DISTANCE_UNITS = {
    "km": "km",
    "m": "m",
}


def extract_direct_proportion_distance_time(
    text: str | None,
) -> DirectProportionDistanceTimeOperands | None:
    """Extract the three stated operands of a direct distance/time problem.

    This grammar deliberately requires one complete known pair and a separate
    question asking for the distance at another duration.  It copies only the
    printed durations and distance; the unit rate and requested distance are
    left for the deterministic visual renderer to derive step by step.
    """

    if not text:
        return None
    stem = re.sub(
        r"\s+",
        " ",
        text.lower().replace("−", "-").replace("–", "-").replace(",", "."),
    ).strip()
    number = r"(\d+(?:\.\d+)?)"
    time_unit = r"(giờ|gio|phút|phut)"
    distance_unit = r"(km|m)"

    # Most Vietnamese primary-school stems use “đi trong 5 giờ được 225 km”.
    known = re.search(
        rf"(?:đi|chạy)[^.?!]{{0,50}}?trong\s+{number}\s*{time_unit}"
        rf"[^.?!]{{0,50}}?(?:được|đi\s+được)\s+{number}\s*{distance_unit}\b",
        stem,
        re.IGNORECASE,
    )
    reverse = False
    if not known:
        # Also accept “đi được 225 km trong 5 giờ”.
        known = re.search(
            rf"(?:đi|chạy)[^.?!]{{0,50}}?(?:được\s+)?{number}\s*{distance_unit}"
            rf"[^.?!]{{0,50}}?trong\s+{number}\s*{time_unit}\b",
            stem,
            re.IGNORECASE,
        )
        reverse = bool(known)
    if not known:
        return None

    if reverse:
        known_distance, known_distance_unit, known_duration, known_duration_unit = known.groups()
    else:
        known_duration, known_duration_unit, known_distance, known_distance_unit = known.groups()

    # Keep the target tied to an explicit distance question. This prevents an
    # unrelated second time mention from being treated as the requested input.
    target = re.search(
        rf"(?:trong|sau)\s+{number}\s*{time_unit}[^.?!]{{0,100}}?"
        r"(?:quãng\s+đường[^.?!]{0,45}?(?:bao\s+nhiêu|là\s+bao\s+nhiêu)"
        r"|(?:đi|chạy)\s+được[^.?!]{0,35}?bao\s+nhiêu\s*(?:km|m)?)",
        stem[known.end():],
        re.IGNORECASE,
    )
    if not target:
        return None

    target_duration, target_duration_unit = target.groups()
    known_duration_value = float(known_duration)
    known_distance_value = float(known_distance)
    target_duration_value = float(target_duration)
    normalized_known_time = _TIME_UNITS[known_duration_unit]
    normalized_target_time = _TIME_UNITS[target_duration_unit]
    normalized_distance = _DISTANCE_UNITS[known_distance_unit]
    if (
        known_duration_value <= 0
        or known_distance_value <= 0
        or target_duration_value <= 0
        or normalized_known_time != normalized_target_time
        or max(known_duration_value, target_duration_value) > 10_000
        or known_distance_value > 10_000_000
    ):
        return None
    return DirectProportionDistanceTimeOperands(
        known_duration=known_duration_value,
        known_duration_unit=normalized_known_time,
        known_distance=known_distance_value,
        known_distance_unit=normalized_distance,
        target_duration=target_duration_value,
        target_duration_unit=normalized_target_time,
    )


def extract_basic_arithmetic(text: str | None) -> BasicArithmeticOperands | None:
    """Extract two printed non-negative integer operands from a short expression.

    This intentionally accepts only an expression-shaped input such as
    ``4+3=?``, ``8 chia 2 bằng mấy`` or its unaccented ``2 nhan 4 bang may?``.
    It must not mine arbitrary numbers from a word problem, and it never
    calculates or stores the requested answer. Fraction slashes are excluded so
    ``1/2 + 1/3`` remains a fraction family.
    """

    if not text:
        return None
    # Teachers often type without an IME, and OCR drops accents, so the same
    # expression arrives as "bằng mấy", "bang may" or "bầng mấy". Folding keeps
    # those on the deterministic path without widening the accepted grammar.
    stem = _fold_vietnamese(text).strip()
    match = re.fullmatch(
        r"(?:tinh|ket\s+qua(?:\s+cua)?|calculate)?\s*"
        r"(\d+)\s*(?:\\)?(\+|-|×|·|⋅|x|\*|÷|:|cong|tru|nhan|chia)\s*(\d+)"
        r"\s*(?:(?:=|bang)\s*(?:\?|may|bao\s+nhieu)?|\?)?\s*[.!?]*",
        stem,
        re.IGNORECASE,
    )
    if not match:
        return None
    left, operator, right = int(match.group(1)), match.group(2), int(match.group(3))
    operation = {
        "+": "addition",
        "cong": "addition",
        "-": "subtraction",
        "tru": "subtraction",
        "×": "multiplication",
        "·": "multiplication",
        "⋅": "multiplication",
        "x": "multiplication",
        "*": "multiplication",
        "nhan": "multiplication",
        "÷": "division",
        ":": "division",
        "chia": "division",
    }[operator.lower()]
    max_exact_integer = 9_007_199_254_740_991
    if left > max_exact_integer or right > max_exact_integer:
        return None
    if operation == "division" and right == 0:
        return None
    if operation == "multiplication" and left * right > max_exact_integer:
        return None
    if operation == "addition" and left + right > max_exact_integer:
        return None
    return BasicArithmeticOperands(left=left, right=right, operation=operation)


def extract_factorial(text: str | None) -> FactorialOperand | None:
    """Read an explicit non-negative factorial without evaluating it.

    The cap prevents a typed expression from asking the browser to allocate an
    unbounded result.  ``500!`` already has 1,135 digits, which is more than
    enough for a school-facing explanation while remaining cheap to render.
    """

    if not text:
        return None
    stem = _fold_vietnamese(text).strip()
    match = re.fullmatch(
        r"(?:tinh|calculate)?\s*"
        r"(?:(\d+)\s*!|giai\s+thua(?:\s+cua)?\s+(\d+)|(\d+)\s+giai\s+thua)"
        r"\s*(?:(?:=|bang)\s*(?:\?|may|bao\s+nhieu)?|\?)?\s*[.!?]*",
        stem,
        re.IGNORECASE,
    )
    if not match:
        return None
    value = int(next(group for group in match.groups() if group is not None))
    if value > 500:
        return None
    return FactorialOperand(value=value)


def extract_primary_word_arithmetic(text: str | None) -> BasicArithmeticOperands | None:
    """Extract operands from conservative primary-school word-problem cues.

    The grammar requires both an operation phrase and a matching question
    phrase. It therefore does not treat every pair of integers in prose as an
    arithmetic problem, and it never calculates the requested result.
    """

    if not text:
        return None
    stem = _fold_vietnamese(text)
    # A stem that states a fraction is not whole-number primary arithmetic.
    # Without this guard "ngày 2 bán 3/4 phần còn lại" read the numerator 3 as
    # the amount removed and produced a confident subtraction scene.
    if re.search(r"\d+\s*/\s*\d+", stem):
        return None

    initial = re.search(r"\bco\s+(\d+)\b", stem)
    added = re.search(r"\b(?:duoc\s+)?(?:cho\s+)?them\s+(\d+)\b", stem)
    asks_total = bool(re.search(r"\b(?:tat\s+ca|tong\s+cong|co\s+bao\s+nhieu)\b", stem))
    if initial and added and asks_total:
        return BasicArithmeticOperands(
            left=int(initial.group(1)),
            right=int(added.group(1)),
            operation="addition",
        )

    removed_before_number = re.search(
        r"\b(?:bot|cho|ban|an|lay\s+di|bo\s+di|cho\s+di|mang\s+di|chuyen\s+di"
        r"|bay\s+di|ra\s+ve)\s+(\d+)(?!\s*/)\b",
        stem,
    )
    # Vietnamese primary-school problems also commonly put the count before
    # the leaving action: "Có 38 chiếc xe rời bãi". Require an object counter,
    # a leaving verb and a remainder question so an arbitrary second number is
    # never treated as the subtrahend.
    removed_after_number = re.search(
        r"\b(\d+)\s+(?:chiec|cai|con|qua|ban|nguoi|xe)\b"
        r"[^.?!]{0,40}?\b(?:roi\s+(?:bai|di|khoi)|bo\s+di|chuyen\s+di|bay\s+di|ra\s+ve)\b",
        stem,
    )
    removed_value = (
        int(removed_before_number.group(1))
        if removed_before_number
        else int(removed_after_number.group(1))
        if removed_after_number
        else None
    )
    # Both cues present means two dependent operations, not one. Reading only
    # the removal turned "bán 45 quyển, nhập thêm 30 quyển" into a plain
    # subtraction and silently dropped the second step from the scene.
    if added and removed_value is not None:
        return None
    asks_remainder = bool(re.search(r"\b(?:con\s+lai|con\s+bao\s+nhieu)\b", stem))
    if initial and removed_value is not None and asks_remainder:
        return BasicArithmeticOperands(
            left=int(initial.group(1)),
            right=removed_value,
            operation="subtraction",
        )

    division = re.search(
        r"\bco\s+(\d+)\b[^.?!]{0,90}?\bchia\s+deu\s+(?:cho\s+)?(\d+)\b",
        stem,
    )
    asks_each = bool(re.search(r"\b(?:moi|mỗi)\b[^.?!]{0,45}?\b(?:bao\s+nhieu|duoc)\b", stem))
    if division and asks_each and int(division.group(2)) > 0:
        return BasicArithmeticOperands(
            left=int(division.group(1)),
            right=int(division.group(2)),
            operation="division",
        )

    multiplication = re.search(
        r"\bco\s+(\d+)\s+(?:nhom|hop|tui|ro)\b[^.?!]{0,70}?"
        r"\b(?:moi|mỗi)\s+(?:nhom|hop|tui|ro)?\s*(?:co\s+)?(\d+)\b",
        stem,
    )
    if multiplication and asks_total:
        return BasicArithmeticOperands(
            left=int(multiplication.group(1)),
            right=int(multiplication.group(2)),
            operation="multiplication",
        )
    return None


def extract_binary_fraction(text: str | None) -> BinaryFractionOperands | None:
    """Copy two printed fractions and their printed operation."""

    if not text:
        return None
    # This extractor owns short fraction operations, so spoken keyboard forms
    # such as "ba phần năm cộng một phần năm" are safe to canonicalize here.
    stem = _fold_vietnamese(canonicalize_typed_math(text))
    match = re.search(
        r"(?<![\w])([+-]?\d+)\s*/\s*(\d+)\s*"
        r"(\+|-|×|x|\*|÷|:|cong|tru|nhan|chia)\s*"
        r"([+-]?\d+)\s*/\s*(\d+)(?![\w])",
        stem,
    )
    if not match:
        return None
    # This family is exactly two fractions. A third operand or a percentage
    # makes it a mixed expression whose value depends on precedence, and
    # reading only the first pair would show the wrong operation entirely.
    remainder = stem[match.end():]
    if re.search(r"(\+|-|×|x|\*|÷|:|cong|tru|nhan|chia)\s*[+-]?\d", remainder):
        return None
    if "%" in stem:
        return None
    left_numerator = int(match.group(1))
    left_denominator = int(match.group(2))
    operator = match.group(3)
    right_numerator = int(match.group(4))
    right_denominator = int(match.group(5))
    if (
        left_denominator <= 0
        or right_denominator <= 0
        or max(abs(left_numerator), left_denominator, abs(right_numerator), right_denominator) > 1_000
    ):
        return None
    operation = {
        "+": "addition", "cong": "addition",
        "-": "subtraction", "tru": "subtraction",
        "×": "multiplication", "x": "multiplication", "*": "multiplication", "nhan": "multiplication",
        "÷": "division", ":": "division", "chia": "division",
    }[operator]
    return BinaryFractionOperands(
        left_numerator=left_numerator,
        left_denominator=left_denominator,
        right_numerator=right_numerator,
        right_denominator=right_denominator,
        operation=operation,
    )


def extract_rectangle_dimensions(text: str | None) -> RectangleOperands | None:
    """Extract printed length and width when a rectangle area is requested."""

    if not text:
        return None
    stem = _fold_vietnamese(text)
    length = re.search(r"\b(?:chieu\s+)?dai\s+(?:la\s+)?(\d+(?:\.\d+)?)\s*(mm|cm|dm|m|km)\b", stem)
    width = re.search(r"\b(?:chieu\s+)?rong\s+(?:la\s+)?(\d+(?:\.\d+)?)\s*(mm|cm|dm|m|km)\b", stem)
    asks_area = bool(re.search(r"\b(?:tinh|hoi)[^.?!]{0,70}?\bdien\s+tich\b", stem))
    if (
        not length
        or not width
        or not asks_area
        or length.group(2) != width.group(2)
        or length.group(2) not in {"cm", "m"}
    ):
        return None
    return RectangleOperands(float(length.group(1)), float(width.group(1)), length.group(2))


def extract_linear_equation(text: str | None) -> LinearEquationOperands | None:
    """Extract a one-variable linear equation without solving for the unknown.

    The classic printed shape ``ax + b = c`` keeps its printed operands so the
    balance scene shows what the learner actually sees. When the variable also
    appears on the right (``5x = 2x + 9``) the canonical form is used instead,
    because that collection step is itself part of the lesson.
    """

    classification = classify_linear(text)
    if classification is None or classification.kind != "equation_one_variable":
        return None
    form = classification.form
    assert form is not None and form.right is not None
    name = form.variables[0]
    if not form.right.coefficients:
        coefficient = form.left.coefficients.get(name, 0.0)
        if coefficient == 0:
            return None
        return LinearEquationOperands(
            coefficient=coefficient,
            constant=form.left.constant,
            result=form.right.constant,
        )
    return LinearEquationOperands(
        coefficient=form.coefficient(name),
        constant=0.0,
        result=form.constant,
    )


def extract_two_variable_linear_equation(
    text: str | None,
) -> TwoVariableLinearEquationOperands | None:
    """Canonicalize ``ax + by = c`` (any side) and normalize it to ``y = mx + n``.

    The normalized slope/intercept are inferred renderer state; the parser does
    not claim a unique x or y because one equation in two variables describes
    a line of solutions.
    """

    classification = classify_linear(text)
    if classification is None or classification.kind != "equation_two_variables":
        return None
    form = classification.form
    assert form is not None
    first_name, second_name = form.variables
    x_coefficient = form.coefficient(first_name)
    y_coefficient = form.coefficient(second_name)
    if y_coefficient == 0:
        return None
    return TwoVariableLinearEquationOperands(
        x_coefficient=x_coefficient,
        y_coefficient=y_coefficient,
        result=form.constant,
        slope=-x_coefficient / y_coefficient,
        intercept=form.constant / y_coefficient,
        x_symbol=first_name,
        y_symbol=second_name,
    )


def extract_three_variable_linear_equation(
    text: str | None,
) -> ThreeVariableLinearEquationOperands | None:
    """Canonicalize ``ax + by + cz = d`` for an Oxyz plane.

    ``3x + y = z`` reaches this family too: collecting both sides gives
    ``3x + y - z = 0``, a plane through the origin with normal ``(3, 1, -1)``.
    """

    classification = classify_linear(text)
    if classification is None or classification.kind != "equation_three_variables":
        return None
    form = classification.form
    assert form is not None
    first_name, second_name, third_name = form.variables
    return ThreeVariableLinearEquationOperands(
        x_coefficient=form.coefficient(first_name),
        y_coefficient=form.coefficient(second_name),
        z_coefficient=form.coefficient(third_name),
        result=form.constant,
        x_symbol=first_name,
        y_symbol=second_name,
        z_symbol=third_name,
    )


def extract_single_variable_linear_expression(
    text: str | None,
) -> SingleVariableLinearExpressionOperands | None:
    """Copy the two printed terms of a standalone expression such as ``2x + 1``."""

    classification = classify_linear(text)
    if classification is None or classification.kind != "expression_one_variable":
        return None
    form = classification.form
    assert form is not None
    name = form.variables[0]
    return SingleVariableLinearExpressionOperands(
        coefficient=form.left.coefficients.get(name, 0.0),
        constant=form.left.constant,
        symbol=name,
    )


def extract_linear_system(text: str | None) -> LinearSystem | None:
    """Parse a complete two- or three-variable linear system."""

    classification = classify_linear(text)
    if classification is None or classification.kind not in {
        "system_two_variables",
        "system_three_variables",
    }:
        return None
    return classification.system


def extract_linear_form(text: str | None) -> LinearForm | None:
    """Expose the canonical form for callers that need the raw structure."""

    classification = classify_linear(text)
    return classification.form if classification else None


def extract_right_triangle(text: str | None) -> RightTriangleFacts | None:
    """Read every printed side and angle of a right triangle.

    This is deliberately broader than "two legs, find the hypotenuse": the
    common grade-9 instruction is "giải tam giác ABC vuông tại A", which gives
    any two sides and asks for the third plus both acute angles. Only printed
    values are copied; nothing is solved here.
    """

    if not text:
        return None
    stem = _fold_vietnamese(text)
    header = re.search(
        r"\btam\s+giac\s+([a-z]{3})\b[^.?!]{0,60}?\bvuong\s+tai\s+([a-z])\b",
        stem,
    )
    if not header:
        return None
    vertices = header.group(1).upper()
    right_vertex = header.group(2).upper()
    if len(set(vertices)) != 3 or right_vertex not in vertices:
        return None

    sides: dict[str, float] = {}
    unit = ""
    for name, value, found_unit in re.findall(
        r"\b([a-z]{2})\s*=\s*(\d+(?:\.\d+)?)\s*(mm|cm|dm|m|km)\b", stem
    ):
        segment = "".join(sorted(name.upper()))
        if set(segment) - set(vertices) or len(set(segment)) != 2:
            continue
        # Mixed units would need a conversion this grammar does not perform.
        if unit and found_unit != unit:
            return None
        unit = found_unit
        sides[segment] = float(value)

    angles: dict[str, float] = {}
    for vertex, value in re.findall(
        r"\bgoc\s+([a-z])\s*(?:bang\s*)?=?\s*(\d+(?:\.\d+)?)\s*(?:do|°)", stem
    ):
        if vertex.upper() in vertices and vertex.upper() != right_vertex:
            angles[vertex.upper()] = float(value)

    if not sides:
        return None
    solve_all = bool(
        re.search(r"\bgiai\s+tam\s+giac\b", stem)
        or re.search(r"\bgoc\b[^.?!]{0,40}?\b(?:lam\s+tron|bang\s+bao\s+nhieu|so\s+do)\b", stem)
        or re.search(r"\btinh\b[^.?!]{0,40}?\bcac\s+goc\b", stem)
    )
    return RightTriangleFacts(
        vertices=vertices,
        right_vertex=right_vertex,
        sides=sides,
        unit=unit or "cm",
        angles=angles,
        solve_all=solve_all,
        round_to_minute=bool(re.search(r"\blam\s+tron\b[^.?!]{0,30}?\bphut\b", stem)),
    )


def extract_right_triangle_legs(text: str | None) -> RightTriangleOperands | None:
    """Extract the two printed legs of a right triangle hypotenuse problem."""

    if not text:
        return None
    stem = _fold_vietnamese(text)
    if not re.search(r"\btam\s+giac\b[^.?!]{0,80}?\bvuong\s+tai\b", stem):
        return None
    segments = re.findall(
        r"\b([a-z]{2})\s*=\s*(\d+(?:\.\d+)?)\s*(mm|cm|dm|m|km)\b",
        stem,
    )
    target = re.search(r"\b(?:tinh|tim)[^.?!]{0,60}?\b(?:do\s+dai\s+)?([a-z]{2})\b", stem)
    if len(segments) < 2 or not target:
        return None
    target_name = target.group(1)
    known = [(name, float(value), unit) for name, value, unit in segments if name != target_name]
    if len(known) < 2 or known[0][2] != known[1][2]:
        return None
    return RightTriangleOperands(known[0][1], known[1][1], known[0][2])


def extract_angle_of_depression(text: str | None) -> AngleOfDepressionFacts | None:
    """Read a lighthouse/tower height and an angle of depression.

    The horizontal distance remains unknown.  This grammar accepts accented,
    unaccented and common OCR spacing, but requires both the vertical landmark
    and an explicit request for the distance to its foot.
    """

    if not text:
        return None
    stem = _fold_vietnamese(text)
    landmark_match = re.search(r"\b(dai\s+hai\s+dang|hai\s+dang|toa\s+nha|thap)\b", stem)
    if not landmark_match:
        return None
    height = re.search(
        r"\bcao\s+(\d+(?:\.\d+)?)\s*(mm|cm|dm|m|km)\b",
        stem,
    )
    angle = re.search(
        r"\bgoc\s+(?:nghieng\s+xuong(?:\s+dat)?|ha)"
        r"[^.?!]{0,45}?(\d+(?:\.\d+)?)\s*(?:do|°)",
        stem,
    )
    asks_horizontal_distance = bool(re.search(
        r"\b(?:khoang\s+)?cach\s+"
        r"(?:tu\s+[^.?!]{1,45}?\s+den\s+|(?:den\s+)?)"
        r"chan\s+(?:dai\s+)?(?:hai\s+dang|toa\s+nha|thap)"
        r"[^.?!]{0,35}?(?:bao\s+nhieu|la\s+bao\s+nhieu)?",
        stem,
    ))
    if not height or not angle or not asks_horizontal_distance:
        return None
    height_value = float(height.group(1))
    angle_value = float(angle.group(1))
    if height_value <= 0 or not 0 < angle_value < 90:
        return None
    return AngleOfDepressionFacts(
        height=height_value,
        angle=angle_value,
        unit=height.group(2),
        landmark=landmark_match.group(1).replace(" ", "_"),
    )


def extract_oblique_triangle_altitude(
    text: str | None,
) -> ObliqueTriangleAltitudeFacts | None:
    """Read an altitude and the two base angles of an oblique triangle."""

    if not text:
        return None
    stem = _fold_vietnamese(text)
    header = re.search(r"\btam\s+giac\s+([a-z]{3})\b", stem)
    altitude = re.search(
        r"\bduong\s+cao\s+([a-z])\s*([a-z])\s*=\s*"
        r"(\d+(?:\.\d+)?)\s*(mm|cm|dm|m|km)\b",
        stem,
    )
    if not header or not altitude:
        return None
    vertices = header.group(1).upper()
    apex, foot = altitude.group(1).upper(), altitude.group(2).upper()
    if len(set(vertices)) != 3 or apex not in vertices or foot in vertices:
        return None
    base_vertices = [vertex for vertex in vertices if vertex != apex]
    angles: dict[str, float] = {}
    for vertex, value in re.findall(
        r"(?:\bgoc\s+|ˆ\s*)?([a-z])\s*=\s*(\d+(?:\.\d+)?)\s*(?:do|°)",
        stem,
    ):
        name = vertex.upper()
        if name in base_vertices:
            angles[name] = float(value)
    if set(angles) != set(base_vertices):
        return None
    if any(not 0 < value < 90 for value in angles.values()):
        return None
    height = float(altitude.group(3))
    if height <= 0 or sum(angles.values()) >= 180:
        return None
    if not re.search(r"\b(?:tinh|tim)\b[^.?!]{0,80}?\b(?:do\s+dai\s+)?cac\s+canh\b", stem):
        return None
    return ObliqueTriangleAltitudeFacts(
        vertices=vertices,
        apex=apex,
        foot=foot,
        height=height,
        unit=altitude.group(4),
        base_angles=angles,
    )


def extract_perpendicular_diagonal_parallelogram(
    text: str | None,
) -> PerpendicularDiagonalParallelogramFacts | None:
    """Read a parallelogram area problem reduced to right triangle ACD."""

    if not text:
        return None
    stem = _fold_vietnamese(text)
    header = re.search(r"\bhinh\s+binh\s+hanh\s+([a-z]{4})\b", stem)
    perpendicular = re.search(
        r"\b([a-z])\s*([a-z])\s*(?:⊥|⟂|vuong\s+goc\s+voi)\s*"
        r"([a-z])\s*([a-z])\b",
        stem,
    )
    if not header or not perpendicular:
        return None
    vertices = header.group(1).upper()
    if len(set(vertices)) != 4:
        return None
    first = "".join(sorted((perpendicular.group(1) + perpendicular.group(2)).upper()))
    second = "".join(sorted((perpendicular.group(3) + perpendicular.group(4)).upper()))
    if set(first + second) - set(vertices):
        return None
    # In this family one perpendicular segment is a diagonal and the other an
    # adjacent side.  The diagonal connects vertices two positions apart.
    diagonal_names = {
        "".join(sorted(vertices[0] + vertices[2])),
        "".join(sorted(vertices[1] + vertices[3])),
    }
    diagonal = first if first in diagonal_names else second if second in diagonal_names else ""
    side = second if diagonal == first else first if diagonal == second else ""
    if not diagonal or not side:
        return None

    side_pattern = (
        rf"\b{side[0].lower()}\s*{side[1].lower()}\s*=\s*"
        r"(\d+(?:\.\d+)?)\s*(mm|cm|dm|m|km)?\b"
    )
    side_value = re.search(side_pattern, stem)
    angle = re.search(
        r"(?:\bgoc\s+|ˆ\s*)?([a-z])\s*=\s*(\d+(?:\.\d+)?)\s*(?:do|°)",
        stem,
    )
    if not side_value or not angle or not re.search(r"\b(?:dien\s+tich|tinh\s+dien\s+tich)\b", stem):
        return None
    angle_vertex = angle.group(1).upper()
    angle_value = float(angle.group(2))
    length_value = float(side_value.group(1))
    if angle_vertex not in vertices or length_value <= 0 or not 0 < angle_value < 90:
        return None
    return PerpendicularDiagonalParallelogramFacts(
        vertices=vertices,
        diagonal=diagonal,
        side=side,
        side_length=length_value,
        angle_vertex=angle_vertex,
        angle=angle_value,
        unit=side_value.group(2) or "one",
    )


@dataclass(frozen=True, slots=True)
class AreaComponent:
    printed_value: float
    printed_unit: str
    value_m2: float


@dataclass(frozen=True, slots=True)
class SequentialFractionRemainderAreaOperands:
    area_components: tuple[AreaComponent, ...]
    first_numerator: int
    first_denominator: int
    second_numerator: int
    second_denominator: int


_AREA_TO_M2 = {
    "mm": 0.000001,
    "cm": 0.0001,
    "dm": 0.01,
    "m": 1.0,
    "dam": 100.0,
    "hm": 10_000.0,
    "km": 1_000_000.0,
}


def extract_sequential_fraction_remainder_area(
    text: str | None,
) -> SequentialFractionRemainderAreaOperands | None:
    """Extract a mixed-area total followed by two fractions of a remainder.

    Newlines between a numerator and denominator are accepted because OCR from
    stacked textbook fractions commonly produces ``2\n5``. Area components are
    normalized to square metres, but the requested final area is never solved
    here; the renderer derives it visibly from the five printed operands.
    """

    if not text:
        return None
    stem = re.sub(
        r"\s+",
        " ",
        text.lower().replace("−", "-").replace("–", "-").replace(",", "."),
    )
    area_matches = re.findall(
        r"(\d+(?:\.\d+)?)\s*(dam|hm|km|dm|cm|mm|m)\s*(?:\^\s*2|²|2)\b",
        stem,
        re.IGNORECASE,
    )
    fraction = r"(\d+)(?:\s*/\s*|\s+)(\d+)"
    first = re.search(
        rf"(?:sử\s+dụng|dùng|lấy)[^.?!]{{0,45}}?{fraction}\s+"
        r"(?:diện\s+tích|phần\s+đất|khu\s+đất)",
        stem,
        re.IGNORECASE,
    )
    second = re.search(
        rf"(?:và|sau\s+đó|tiếp\s+theo)[^.?!]{{0,45}}?{fraction}\s+"
        r"(?:diện\s+tích|phần)\s+(?:đất\s+)?còn\s+lại",
        stem,
        re.IGNORECASE,
    )
    asks_final_area = bool(
        re.search(
            r"(?:phần\s+(?:đất\s+)?(?:cuối(?:\s+cùng)?|còn\s+lại)|"
            r"đất\s+còn\s+lại|chuồng\s+trại)",
            stem,
        )
        and re.search(
            r"(?:tính|hỏi|bao\s+nhiêu)[^.?!]{0,100}?"
            r"(?:diện\s+tích|(?:dam|hm|km|dm|cm|mm|m)\s*(?:\^\s*2|²|2))",
            stem,
        )
    )
    if not area_matches or not first or not second or not asks_final_area:
        return None

    first_numerator, first_denominator = int(first.group(1)), int(first.group(2))
    second_numerator, second_denominator = int(second.group(1)), int(second.group(2))
    if not (
        0 < first_numerator < first_denominator <= 40
        and 0 < second_numerator < second_denominator <= 40
    ):
        return None

    components = tuple(
        AreaComponent(
            printed_value=float(value),
            printed_unit=unit.lower(),
            value_m2=float(value) * _AREA_TO_M2[unit.lower()],
        )
        for value, unit in area_matches
    )
    if not components or sum(item.value_m2 for item in components) <= 0:
        return None
    return SequentialFractionRemainderAreaOperands(
        area_components=components,
        first_numerator=first_numerator,
        first_denominator=first_denominator,
        second_numerator=second_numerator,
        second_denominator=second_denominator,
    )


def extract_variable_people_work_rate(
    text: str | None,
) -> VariablePeopleWorkRateOperands | None:
    """Copy only explicit operands from a Vietnamese inverse work-rate stem.

    The requested number of days is intentionally not calculated here.  This
    helper is shared by live provider repair and legacy-history migration so
    both paths use exactly the same conservative grammar.
    """

    if not text:
        return None
    stem = re.sub(
        r"\s+",
        " ",
        text.lower().replace("−", "-").replace("–", "-").replace(",", "."),
    )
    initial_workers_match = re.search(
        r"(?:tổ|đội|nhóm)[^.?!]{0,60}?(?:gồm|có)\s+"
        r"(\d+(?:\.\d+)?)\s+(?:người|công\s*nhân)",
        stem,
        re.IGNORECASE,
    )
    planned_days_match = re.search(
        r"(?:trong|hết|mất)\s+(\d+(?:\.\d+)?)\s+ngày",
        stem,
        re.IGNORECASE,
    )
    added_workers_match = re.search(
        r"(?:bổ\s+sung|thêm)\s+(?:thêm\s+)?"
        r"(\d+(?:\.\d+)?)\s+(?:người|công\s*nhân)",
        stem,
        re.IGNORECASE,
    )
    removed_workers_match = re.search(
        r"(?:rút|bớt|giảm)\s+(?:bớt\s+)?"
        r"(\d+(?:\.\d+)?)\s+(?:người|công\s*nhân)",
        stem,
        re.IGNORECASE,
    )
    worker_adjustment_match = added_workers_match or removed_workers_match
    has_work_invariant = bool(re.search(
        r"(?:sức\s+làm\s+việc|năng\s+suất|mức\s+làm\s+việc)[^.?!]{0,80}"
        r"(?:như\s+nhau|bằng\s+nhau)",
        stem,
        re.IGNORECASE,
    ))
    asks_completion_days = bool(re.search(
        r"(?:bao\s+nhiêu|mấy)\s+ngày",
        stem,
        re.IGNORECASE,
    ))
    if not (
        initial_workers_match
        and planned_days_match
        and worker_adjustment_match
        and has_work_invariant
        and asks_completion_days
    ):
        return None

    initial_workers = float(initial_workers_match.group(1))
    planned_days = float(planned_days_match.group(1))
    worker_change = float(worker_adjustment_match.group(1))
    if removed_workers_match:
        worker_change *= -1
    if not (
        initial_workers > 0
        and planned_days > 0
        and initial_workers.is_integer()
        and planned_days.is_integer()
        and worker_change.is_integer()
        and initial_workers + worker_change > 0
    ):
        return None
    return VariablePeopleWorkRateOperands(
        initial_workers=int(initial_workers),
        planned_days=int(planned_days),
        worker_change=int(worker_change),
    )
