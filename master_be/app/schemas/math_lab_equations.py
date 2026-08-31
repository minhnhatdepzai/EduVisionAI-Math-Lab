"""Strict parsers for the remaining grade 8-9 equation families.

The visual lab must only solve an equation after it has consumed the complete
printed expression.  These parsers therefore cover a deliberately small,
auditable grammar for fractional linear, absolute-value, biquadratic, radical
and rational equations.  Unsupported operators are refused instead of being
silently discarded and turned into a different problem.
"""

from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass
from fractions import Fraction

from app.schemas.math_lab_input import canonicalize_typed_math


_TOLERANCE = 1e-10
_NUMBER = r"(?:\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)?)"


@dataclass(frozen=True, slots=True)
class FractionalLinearEquation:
    symbol: str
    coefficient: float
    result: float
    denominators: tuple[int, ...]
    stages: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AbsoluteValueEquation:
    symbol: str
    coefficient: float
    constant: float
    right_side: float


@dataclass(frozen=True, slots=True)
class BiquadraticEquation:
    symbol: str
    quartic_coefficient: float
    quadratic_coefficient: float
    constant: float


@dataclass(frozen=True, slots=True)
class RadicalEquation:
    symbol: str
    radicand_coefficient: float
    radicand_constant: float
    right_coefficient: float
    right_constant: float


@dataclass(frozen=True, slots=True)
class RationalEquation:
    symbol: str
    numerator_coefficients: tuple[float, float, float]
    denominators: tuple[tuple[float, float], ...]


def _fold(text: str) -> str:
    normalized = (
        canonicalize_typed_math(text).lower()
        .replace("−", "-")
        .replace("–", "-")
        .replace("—", "-")
        .replace("×", "*")
        .replace("·", "*")
        .replace("÷", "/")
        .replace("²", "^2")
        .replace("³", "^3")
        .replace("⁴", "^4")
        .replace("（", "(")
        .replace("）", ")")
        .replace("＝", "=")
    )
    return "".join(
        character
        for character in unicodedata.normalize("NFD", normalized)
        if unicodedata.category(character) != "Mn"
    ).replace("đ", "d")


def _stem(text: str | None) -> str | None:
    if not text:
        return None
    folded = _fold(text).strip().rstrip(".?!")
    folded = re.sub(
        r"^(?:hay\s+)?(?:(?:giai|xet)\s+(?:bat\s+)?phuong\s+trinh|"
        r"tim\s+(?:cac\s+)?nghiem(?:\s+cua)?(?:\s+(?:bat\s+)?phuong\s+trinh)?|"
        r"cho\s+phuong\s+trinh|phuong\s+trinh)\s*:?\s*",
        "",
        folded,
    )
    return re.sub(r"\s+", "", folded) or None


def _value(text: str) -> Fraction:
    return Fraction(text)


def _format(value: Fraction | float) -> str:
    number = value if isinstance(value, Fraction) else Fraction(value).limit_denominator(1000)
    if number.denominator == 1:
        return str(number.numerator)
    return f"{number.numerator}/{number.denominator}"


def _format_linear(coefficient: Fraction, constant: Fraction, symbol: str) -> str:
    pieces: list[str] = []
    if coefficient:
        magnitude = abs(coefficient)
        term = symbol if magnitude == 1 else f"{_format(magnitude)}{symbol}"
        pieces.append(f"{'-' if coefficient < 0 else ''}{term}")
    if constant:
        magnitude = _format(abs(constant))
        if pieces:
            pieces.append(f" {'-' if constant < 0 else '+'} {magnitude}")
        else:
            pieces.append(f"{'-' if constant < 0 else ''}{magnitude}")
    return "".join(pieces) or "0"


def _strip_group(text: str) -> str:
    if text.startswith("(") and text.endswith(")"):
        depth = 0
        for index, character in enumerate(text):
            depth += character == "("
            depth -= character == ")"
            if depth == 0 and index != len(text) - 1:
                return text
        return text[1:-1]
    return text


def _split_terms(expression: str) -> list[str] | None:
    terms: list[str] = []
    start = 0
    depth = 0
    for index, character in enumerate(expression):
        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth < 0:
                return None
        elif character in "+-" and index > start and depth == 0:
            terms.append(expression[start:index])
            start = index
    if depth != 0:
        return None
    terms.append(expression[start:])
    return terms if all(term and term not in {"+", "-"} for term in terms) else None


def _top_level_slash(expression: str) -> int | None:
    depth = 0
    found: int | None = None
    for index, character in enumerate(expression):
        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
        elif character == "/" and depth == 0:
            if found is not None:
                return None
            found = index
    return found


def _linear_atom(expression: str) -> tuple[str | None, Fraction, Fraction] | None:
    """Return ``symbol, coefficient, constant`` for one complete linear atom."""

    body = _strip_group(expression)
    if not body or any(token in body for token in ("^", "√", "sqrt", "|", "/", "*")):
        return None
    terms = _split_terms(body)
    if terms is None:
        return None
    symbol: str | None = None
    coefficient = Fraction(0)
    constant = Fraction(0)
    for term in terms:
        sign = -1 if term.startswith("-") else 1
        unsigned = term[1:] if term[:1] in "+-" else term
        match = re.fullmatch(rf"({_NUMBER})?([a-z])", unsigned)
        if match:
            printed_coefficient, term_symbol = match.groups()
            if symbol is not None and term_symbol != symbol:
                return None
            symbol = term_symbol
            coefficient += sign * (_value(printed_coefficient) if printed_coefficient else 1)
            continue
        if not re.fullmatch(_NUMBER, unsigned):
            return None
        constant += sign * _value(unsigned)
    return symbol, coefficient, constant


def _fractional_side(expression: str) -> tuple[str | None, Fraction, Fraction, list[int]] | None:
    terms = _split_terms(expression)
    if terms is None:
        return None
    symbol: str | None = None
    coefficient = Fraction(0)
    constant = Fraction(0)
    denominators: list[int] = []
    for term in terms:
        sign = -1 if term.startswith("-") else 1
        unsigned = term[1:] if term[:1] in "+-" else term
        slash = _top_level_slash(unsigned)
        denominator = 1
        numerator = unsigned
        if slash is not None:
            numerator, denominator_text = unsigned[:slash], unsigned[slash + 1:]
            if not re.fullmatch(r"\d+", denominator_text):
                return None
            denominator = int(denominator_text)
            if denominator == 0:
                return None
            denominators.append(denominator)
        atom = _linear_atom(numerator)
        if atom is None:
            return None
        term_symbol, term_coefficient, term_constant = atom
        if term_symbol is not None:
            if symbol is not None and symbol != term_symbol:
                return None
            symbol = term_symbol
        coefficient += sign * term_coefficient / denominator
        constant += sign * term_constant / denominator
    return symbol, coefficient, constant, denominators


def parse_fractional_linear_equation(text: str | None) -> FractionalLinearEquation | None:
    compact = _stem(text)
    if compact is None or compact.count("=") != 1:
        return None
    left_text, right_text = compact.split("=", 1)
    left = _fractional_side(left_text)
    right = _fractional_side(right_text)
    if left is None or right is None:
        return None
    denominators = left[3] + right[3]
    # This family exists for a printed numeric denominator. Ordinary decimal
    # or integer linear equations remain in the established balance parser.
    if not denominators:
        return None
    symbols = {item for item in (left[0], right[0]) if item is not None}
    if len(symbols) != 1:
        return None
    symbol = symbols.pop()
    coefficient = left[1] - right[1]
    result = right[2] - left[2]
    if coefficient == 0:
        return None
    lcm = math.lcm(*denominators)
    cleared_left_a, cleared_left_b = left[1] * lcm, left[2] * lcm
    cleared_right_a, cleared_right_b = right[1] * lcm, right[2] * lcm
    stages = (
        str(text).strip().rstrip(".?!"),
        f"{_format_linear(cleared_left_a, cleared_left_b, symbol)} = "
        f"{_format_linear(cleared_right_a, cleared_right_b, symbol)}",
        f"{_format(coefficient * lcm)}{symbol} = {_format(result * lcm)}",
    )
    return FractionalLinearEquation(
        symbol=symbol,
        coefficient=float(coefficient * lcm),
        result=float(result * lcm),
        denominators=tuple(dict.fromkeys(denominators)),
        stages=stages,
    )


def parse_absolute_value_equation(text: str | None) -> AbsoluteValueEquation | None:
    compact = _stem(text)
    if compact is None or compact.count("=") != 1:
        return None
    match = re.fullmatch(r"\|([^|]+)\|=([+-]?\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)?)", compact)
    if not match:
        return None
    atom = _linear_atom(match.group(1))
    if atom is None or atom[0] is None or atom[1] == 0:
        return None
    right = _value(match.group(2))
    return AbsoluteValueEquation(atom[0], float(atom[1]), float(atom[2]), float(right))


def _polynomial_coefficients(expression: str, max_degree: int) -> tuple[str, list[Fraction]] | None:
    terms = _split_terms(expression)
    if terms is None:
        return None
    symbol: str | None = None
    coefficients = [Fraction(0) for _ in range(max_degree + 1)]
    for term in terms:
        sign = -1 if term.startswith("-") else 1
        unsigned = term[1:] if term[:1] in "+-" else term
        match = re.fullmatch(rf"({_NUMBER})?([a-z])(?:\^([1-{max_degree}]))?", unsigned)
        if match:
            printed, term_symbol, exponent_text = match.groups()
            if symbol is not None and symbol != term_symbol:
                return None
            symbol = term_symbol
            exponent = int(exponent_text or "1")
            coefficients[exponent] += sign * (_value(printed) if printed else 1)
        elif re.fullmatch(_NUMBER, unsigned):
            coefficients[0] += sign * _value(unsigned)
        else:
            return None
    return (symbol, coefficients) if symbol is not None else None


def parse_biquadratic_equation(text: str | None) -> BiquadraticEquation | None:
    compact = _stem(text)
    if compact is None or compact.count("=") != 1:
        return None
    left_text, right_text = compact.split("=", 1)
    left = _polynomial_coefficients(left_text, 4)
    right = _polynomial_coefficients(right_text, 4)
    if left is None or right is None or left[0] != right[0]:
        # Permit a constant-only right side.
        if left is None:
            return None
        right_atom = _linear_atom(right_text)
        if right_atom is None or right_atom[0] is not None:
            return None
        right = (left[0], [right_atom[2], Fraction(0), Fraction(0), Fraction(0), Fraction(0)])
    values = [left[1][index] - right[1][index] for index in range(5)]
    if values[4] == 0 or values[3] != 0 or values[1] != 0:
        return None
    return BiquadraticEquation(left[0], float(values[4]), float(values[2]), float(values[0]))


def parse_radical_equation(text: str | None) -> RadicalEquation | None:
    compact = _stem(text)
    if compact is None or compact.count("=") != 1:
        return None
    compact = compact.replace("sqrt", "√")
    match = re.fullmatch(r"√\(([^()]+)\)=([^=]+)", compact)
    if not match:
        # Also accept the school notation √x without redundant parentheses.
        match = re.fullmatch(r"√([a-z])=([^=]+)", compact)
    if not match:
        return None
    radicand = _linear_atom(match.group(1))
    right = _linear_atom(match.group(2))
    if (
        radicand is None or right is None or radicand[0] is None
        or radicand[1] == 0 or right[0] not in {None, radicand[0]}
    ):
        return None
    return RadicalEquation(
        symbol=radicand[0],
        radicand_coefficient=float(radicand[1]),
        radicand_constant=float(radicand[2]),
        right_coefficient=float(right[1]),
        right_constant=float(right[2]),
    )


def _poly_add(left: list[Fraction], right: list[Fraction]) -> list[Fraction]:
    size = max(len(left), len(right))
    return [
        (left[index] if index < len(left) else 0)
        + (right[index] if index < len(right) else 0)
        for index in range(size)
    ]


def _poly_multiply(left: list[Fraction], right: list[Fraction]) -> list[Fraction]:
    result = [Fraction(0)] * (len(left) + len(right) - 1)
    for first_index, first in enumerate(left):
        for second_index, second in enumerate(right):
            result[first_index + second_index] += first * second
    return result


def _denominator_key(coefficient: Fraction, constant: Fraction) -> tuple[Fraction, Fraction]:
    # Proportional linear expressions have the same forbidden root and are the
    # same factor for the purpose of a common denominator.
    return (Fraction(1), constant / coefficient)


def parse_rational_equation(text: str | None) -> RationalEquation | None:
    compact = _stem(text)
    if compact is None or compact.count("=") != 1:
        return None
    left_text, right_text = compact.split("=", 1)
    parsed_terms: list[tuple[int, list[Fraction], tuple[Fraction, Fraction] | None]] = []
    symbols: set[str] = set()
    printed_variable_denominator = False
    for side_sign, expression in ((1, left_text), (-1, right_text)):
        terms = _split_terms(expression)
        if terms is None:
            return None
        for term in terms:
            term_sign = -1 if term.startswith("-") else 1
            unsigned = term[1:] if term[:1] in "+-" else term
            slash = _top_level_slash(unsigned)
            numerator_text = unsigned if slash is None else unsigned[:slash]
            denominator_text = None if slash is None else unsigned[slash + 1:]
            numerator = _linear_atom(numerator_text)
            if numerator is None:
                return None
            if numerator[0] is not None:
                symbols.add(numerator[0])
            denominator: tuple[Fraction, Fraction] | None = None
            if denominator_text is not None:
                denominator_atom = _linear_atom(denominator_text)
                if denominator_atom is None or denominator_atom[0] is None or denominator_atom[1] == 0:
                    return None
                symbols.add(denominator_atom[0])
                denominator = _denominator_key(denominator_atom[1], denominator_atom[2])
                printed_variable_denominator = True
            parsed_terms.append((
                side_sign * term_sign,
                [numerator[2], numerator[1]],
                denominator,
            ))
    if not printed_variable_denominator or len(symbols) != 1:
        return None
    denominators = tuple(dict.fromkeys(
        denominator for _sign, _numerator, denominator in parsed_terms if denominator is not None
    ))
    if not denominators or len(denominators) > 2:
        return None
    common = [Fraction(1)]
    for denominator in denominators:
        common = _poly_multiply(common, [denominator[1], denominator[0]])
    combined = [Fraction(0)]
    for sign, numerator, denominator in parsed_terms:
        multiplier = [Fraction(1)]
        for candidate in denominators:
            if candidate != denominator:
                multiplier = _poly_multiply(multiplier, [candidate[1], candidate[0]])
        contribution = [sign * value for value in _poly_multiply(numerator, multiplier)]
        combined = _poly_add(combined, contribution)
    while len(combined) > 1 and combined[-1] == 0:
        combined.pop()
    if len(combined) > 3 or all(value == 0 for value in combined):
        return None
    padded = combined + [Fraction(0)] * (3 - len(combined))
    # Public coefficient order is conventional: ax² + bx + c.
    coefficients = (float(padded[2]), float(padded[1]), float(padded[0]))
    public_denominators = tuple((float(item[0]), float(item[1])) for item in denominators)
    return RationalEquation(symbols.pop(), coefficients, public_denominators)
