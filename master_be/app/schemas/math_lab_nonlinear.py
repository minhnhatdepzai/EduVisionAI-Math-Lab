"""Strict parsers for low-degree polynomial equations used in Math Lab.

The linear canonicalizer intentionally rejects powers.  This module handles
the next safe families without weakening that guard: one-variable quadratic
and cubic equations, plus the existing one-square Oxyz surface.  Every printed
character is consumed. Cross-products, roots, functions and powers above three
remain unsupported instead of being flattened into the wrong graph.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from fractions import Fraction

from app.schemas.math_lab_input import canonicalize_typed_math


@dataclass(frozen=True, slots=True)
class QuadraticSurfaceForm:
    squared_symbol: str
    squared_coefficient: float
    linear_coefficients: dict[str, float]
    right_side: float
    output_symbol: str

    @property
    def symbols(self) -> tuple[str, str, str]:
        names = set(self.linear_coefficients) | {self.squared_symbol}
        return tuple(symbol for symbol in ("x", "y", "z") if symbol in names)  # type: ignore[return-value]


@dataclass(frozen=True, slots=True)
class QuadraticEquationForm:
    """One printed equation reduced to ``ax² + bx + c = 0``.

    The coefficients are copied from the complete printed equation.  Roots are
    deliberately not stored here: they are derived later by the deterministic
    graph/oracle layer and therefore never leak into the known quantities.
    """

    symbol: str
    quadratic_coefficient: float
    linear_coefficient: float
    constant: float


@dataclass(frozen=True, slots=True)
class CubicEquationForm:
    """One printed equation reduced to ``ax³ + bx² + cx + d = 0``."""

    symbol: str
    cubic_coefficient: float
    quadratic_coefficient: float
    linear_coefficient: float
    constant: float


_NUMBER = r"\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)?"
_TOKEN = re.compile(rf"[+-]?(?:(?:{_NUMBER})?[a-z](?:\^2)?|{_NUMBER})")
_POLYNOMIAL_TOKEN = re.compile(
    rf"[+-]?(?:(?:{_NUMBER})?[a-z](?:\^[123])?|{_NUMBER})"
)


def _fold(text: str) -> str:
    normalized = (
        canonicalize_typed_math(text).lower()
        .replace("−", "-")
        .replace("–", "-")
        .replace(",", ".")
        .replace("²", "^2")
        .replace("³", "^3")
        .strip()
    )
    return "".join(
        character
        for character in unicodedata.normalize("NFD", normalized)
        if unicodedata.category(character) != "Mn"
    ).replace("đ", "d")


def _number(value: str) -> float:
    return float(Fraction(value)) if "/" in value else float(value)


def _parse_side(side: str) -> tuple[dict[str, float], dict[str, float], float] | None:
    compact = re.sub(r"\s+", "", side)
    if not compact:
        return None
    tokens = [match.group(0) for match in _TOKEN.finditer(compact)]
    if not tokens or "".join(tokens) != compact:
        return None
    squared: dict[str, float] = {}
    linear: dict[str, float] = {}
    constant = 0.0
    for token in tokens:
        sign = -1.0 if token.startswith("-") else 1.0
        body = token[1:] if token[:1] in "+-" else token
        exponent = 2 if body.endswith("^2") else 1
        if exponent == 2:
            body = body[:-2]
        if body and body[-1].isalpha():
            symbol = body[-1]
            coefficient_text = body[:-1]
            coefficient = sign * (_number(coefficient_text) if coefficient_text else 1.0)
            target = squared if exponent == 2 else linear
            target[symbol] = target.get(symbol, 0.0) + coefficient
        else:
            if exponent != 1:
                return None
            constant += sign * _number(body)
    return squared, linear, constant


def _parse_polynomial_side(side: str) -> tuple[dict[tuple[str, int], float], float] | None:
    """Consume one side made only from degree-0..3 monomials.

    Multiplication signs, cross-products, functions and powers above three are
    intentionally rejected.  This keeps the deterministic path narrow enough
    that it can never turn prose or a different equation family into a graph.
    """

    compact = re.sub(r"\s+", "", side)
    if not compact:
        return None
    tokens = [match.group(0) for match in _POLYNOMIAL_TOKEN.finditer(compact)]
    if not tokens or "".join(tokens) != compact:
        return None
    terms: dict[tuple[str, int], float] = {}
    constant = 0.0
    for token in tokens:
        sign = -1.0 if token.startswith("-") else 1.0
        body = token[1:] if token[:1] in "+-" else token
        match = re.fullmatch(rf"({_NUMBER})?([a-z])(?:\^([123]))?", body)
        if match:
            coefficient_text, symbol, exponent_text = match.groups()
            coefficient = sign * (_number(coefficient_text) if coefficient_text else 1.0)
            exponent = int(exponent_text or "1")
            key = (symbol, exponent)
            terms[key] = terms.get(key, 0.0) + coefficient
        else:
            constant += sign * _number(body)
    return terms, constant


def _polynomial_coefficients(text: str | None) -> tuple[str, tuple[float, float, float, float]] | None:
    """Return coefficients indexed by exponent for one complete equation."""

    if not text:
        return None
    stem = _fold(text).rstrip(".?!")
    stem = re.sub(
        r"^(?:hay\s+)?(?:(?:giai|xet)\s+phuong\s+trinh|"
        r"tim\s+(?:cac\s+|ba\s+|hai\s+)?nghiem(?:\s+cua)?\s+phuong\s+trinh|"
        r"cho\s+phuong\s+trinh|phuong\s+trinh)\s*:?\s*",
        "",
        stem,
    )
    if stem.count("=") != 1:
        return None
    left_text, right_text = stem.split("=", 1)
    try:
        left = _parse_polynomial_side(left_text)
        right = _parse_polynomial_side(right_text)
    except (ValueError, ZeroDivisionError):
        return None
    if left is None or right is None:
        return None

    terms = dict(left[0])
    for key, value in right[0].items():
        terms[key] = terms.get(key, 0.0) - value
    terms = {key: value for key, value in terms.items() if abs(value) > 1e-12}
    symbols = {symbol for symbol, _exponent in terms}
    if len(symbols) != 1:
        return None
    symbol = next(iter(symbols))
    coefficients = [left[1] - right[1], 0.0, 0.0, 0.0]
    for (term_symbol, exponent), value in terms.items():
        if term_symbol != symbol or exponent < 1 or exponent > 3:
            return None
        coefficients[exponent] += value
    return symbol, tuple(coefficients)  # type: ignore[return-value]


def parse_quadratic_surface(text: str | None) -> QuadraticSurfaceForm | None:
    """Parse ``q·u² + ax + by + cz = d`` with exactly three variables."""

    if not text:
        return None
    stem = _fold(text).rstrip(".?!")
    # Remove only known instructional prefixes.  Arbitrary prose is not
    # scanned character by character because that once turned words into
    # fictitious algebraic variables.
    stem = re.sub(
        r"^(?:hay\s+)?(?:ve\s+(?:mat|do\s+thi)|bieu\s+dien|"
        r"cho\s+phuong\s+trinh|phuong\s+trinh)\s*:?\s*",
        "",
        stem,
    )
    if stem.count("=") != 1:
        return None
    left_text, right_text = stem.split("=", 1)
    left = _parse_side(left_text)
    right = _parse_side(right_text)
    if left is None or right is None:
        return None

    squared: dict[str, float] = dict(left[0])
    linear: dict[str, float] = dict(left[1])
    for symbol, value in right[0].items():
        squared[symbol] = squared.get(symbol, 0.0) - value
    for symbol, value in right[1].items():
        linear[symbol] = linear.get(symbol, 0.0) - value
    squared = {name: value for name, value in squared.items() if abs(value) > 1e-12}
    linear = {name: value for name, value in linear.items() if abs(value) > 1e-12}
    if len(squared) != 1:
        return None
    squared_symbol, squared_coefficient = next(iter(squared.items()))
    symbols = set(linear) | {squared_symbol}
    if symbols != {"x", "y", "z"}:
        return None
    output_candidates = [
        symbol for symbol in ("z", "y", "x")
        if symbol != squared_symbol and abs(linear.get(symbol, 0.0)) > 1e-12
    ]
    if not output_candidates:
        return None
    return QuadraticSurfaceForm(
        squared_symbol=squared_symbol,
        squared_coefficient=squared_coefficient,
        linear_coefficients=linear,
        right_side=right[2] - left[2],
        output_symbol=output_candidates[0],
    )


def parse_quadratic_equation(text: str | None) -> QuadraticEquationForm | None:
    """Parse a complete one-variable quadratic equation.

    Accepted inputs may put terms on either side, for example ``x² = 4`` or
    ``2x² + 3 = 5x``.  The parser consumes the whole equation and rejects
    additional variables, products, roots and higher powers rather than
    flattening them into a misleading parabola.
    """

    if not text:
        return None
    stem = _fold(text).rstrip(".?!")
    stem = re.sub(
        r"^(?:hay\s+)?(?:(?:giai|xet)\s+phuong\s+trinh|"
        r"tim\s+(?:cac\s+|hai\s+)?nghiem(?:\s+cua)?\s+phuong\s+trinh|"
        r"cho\s+phuong\s+trinh|phuong\s+trinh)\s*:?\s*",
        "",
        stem,
    )
    if stem.count("=") != 1:
        return None
    left_text, right_text = stem.split("=", 1)
    try:
        left = _parse_side(left_text)
        right = _parse_side(right_text)
    except (ValueError, ZeroDivisionError):
        return None
    if left is None or right is None:
        return None

    squared: dict[str, float] = dict(left[0])
    linear: dict[str, float] = dict(left[1])
    for symbol, value in right[0].items():
        squared[symbol] = squared.get(symbol, 0.0) - value
    for symbol, value in right[1].items():
        linear[symbol] = linear.get(symbol, 0.0) - value
    squared = {name: value for name, value in squared.items() if abs(value) > 1e-12}
    linear = {name: value for name, value in linear.items() if abs(value) > 1e-12}

    if len(squared) != 1:
        return None
    symbol, quadratic_coefficient = next(iter(squared.items()))
    if symbol != "x" or any(name != symbol for name in linear):
        return None
    return QuadraticEquationForm(
        symbol=symbol,
        quadratic_coefficient=quadratic_coefficient,
        linear_coefficient=linear.get(symbol, 0.0),
        constant=left[2] - right[2],
    )


def parse_cubic_equation(text: str | None) -> CubicEquationForm | None:
    """Parse a complete one-variable cubic equation.

    Terms may occur on either side and missing lower-degree coefficients are
    kept as zero, for example ``x³ = 8`` becomes ``x³ - 8 = 0``.  The parser
    refuses multivariable input and every operator outside a sum of monomials.
    """

    parsed = _polynomial_coefficients(text)
    if parsed is None:
        return None
    symbol, coefficients = parsed
    constant, linear, quadratic, cubic = coefficients
    if abs(cubic) <= 1e-12:
        return None
    return CubicEquationForm(
        symbol=symbol,
        cubic_coefficient=cubic,
        quadratic_coefficient=quadratic,
        linear_coefficient=linear,
        constant=constant,
    )
