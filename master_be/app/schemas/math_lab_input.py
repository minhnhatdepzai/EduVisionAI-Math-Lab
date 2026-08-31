"""Conservative normalization for formulas typed on an ordinary keyboard.

Vietnamese pupils rarely type textbook Unicode.  This module accepts the
unambiguous phrases they naturally use while deliberately leaving ambiguous
text untouched, so a strict downstream parser can ask for clarification
instead of solving a different expression.
"""

from __future__ import annotations

import re
import unicodedata


_SMALL_NUMBER_WORDS = {
    "khong": "0",
    "mot": "1",
    "hai": "2",
    "ba": "3",
    "bon": "4",
    "tu": "4",
    "nam": "5",
    "sau": "6",
    "bay": "7",
    "tam": "8",
    "chin": "9",
    "muoi": "10",
}
_NUMBER_WORD = "(?:" + "|".join(_SMALL_NUMBER_WORDS) + ")"
_NUMBER = rf"(?:\d+(?:[.,]\d+)?|{_NUMBER_WORD})"
_ATOM = rf"(?:\([^()]+\)|{_NUMBER}|[a-z])"


def _ascii_lower(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text.lower())
    return "".join(
        character
        for character in normalized
        if unicodedata.category(character) != "Mn"
    ).replace("đ", "d")


def _number_token(token: str) -> str:
    return _SMALL_NUMBER_WORDS.get(token.strip(), token.strip().replace(",", "."))


def _math_atom(token: str) -> str:
    stripped = token.strip()
    if stripped in _SMALL_NUMBER_WORDS:
        return _SMALL_NUMBER_WORDS[stripped]
    if stripped.startswith("(") and stripped.endswith(")"):
        inside = stripped[1:-1].strip()
        if inside in _SMALL_NUMBER_WORDS:
            return _SMALL_NUMBER_WORDS[inside]
    return stripped


def canonicalize_typed_math(text: str | None) -> str:
    """Return a parser-friendly copy without guessing ambiguous notation.

    Examples: ``x mũ 3`` -> ``x^3``; ``3 phần 5`` -> ``(3)/(5)``;
    ``căn bậc hai của (x+1)`` -> ``sqrt(x+1)``.  A mixed number requires the
    word ``và``: ``3 và 2 phần 5``.  The ambiguous ``3 2 phần 5`` is retained
    and therefore rejected by the strict expression grammar.
    """

    if not text:
        return ""
    value = _ascii_lower(text)
    value = (
        value.replace("−", "-")
        .replace("–", "-")
        .replace("—", "-")
        .replace("×", "*")
        .replace("·", "*")
        .replace("⋅", "*")
        .replace("÷", "/")
        .replace("＝", "=")
        .replace("（", "(")
        .replace("）", ")")
    )
    value = re.sub(r"[^\S\r\n]+", " ", value).strip()

    # Explicit mixed number only.  Requiring "va" prevents "3 2 phan 5"
    # from being silently interpreted as either a product or 3 + 2/5.
    value = re.sub(
        rf"\b({_NUMBER})\s+va\s+({_NUMBER})\s+phan\s+({_NUMBER})\b",
        lambda match: (
            f"({_number_token(match.group(1))}+"
            f"{_number_token(match.group(2))}/{_number_token(match.group(3))})"
        ),
        value,
    )

    # Powers in the two common spoken orders.
    value = re.sub(
        rf"\b(?:luy thua|mu)\s+(?:bac\s+)?({_NUMBER})\s+cua\s+({_ATOM})",
        lambda match: f"{match.group(2)}^{_number_token(match.group(1))}",
        value,
    )
    value = re.sub(
        rf"({_ATOM})\s+(?:mu|luy thua(?:\s+bac)?)\s*\(?({_NUMBER})\)?",
        lambda match: f"{match.group(1)}^{_number_token(match.group(2))}",
        value,
    )

    # Square-root phrases. A different printed degree remains untouched.
    value = re.sub(
        rf"\bcan\s+bac\s+(?:hai|2)\s+(?:cua\s+)?({_ATOM})",
        lambda match: f"sqrt{match.group(1)}" if match.group(1).startswith("(") else f"sqrt({match.group(1)})",
        value,
    )
    value = re.sub(
        rf"\bcan\s+(?!bac\b)(?:cua\s+)?({_ATOM})",
        lambda match: f"sqrt{match.group(1)}" if match.group(1).startswith("(") else f"sqrt({match.group(1)})",
        value,
    )

    # Absolute value written in words.
    value = re.sub(
        rf"\bgia tri tuyet doi\s+(?:cua\s+)?({_ATOM})",
        lambda match: f"|{match.group(1)[1:-1] if match.group(1).startswith('(') else match.group(1)}|",
        value,
    )

    # A spoken fraction must have one clear atom on each side of "phan".
    value = re.sub(
        rf"({_ATOM})\s+phan\s+({_ATOM})",
        lambda match: f"{_math_atom(match.group(1))}/{_math_atom(match.group(2))}",
        value,
    )

    # Operators typed as words. Multiplication letter x is converted only
    # between numeric atoms with surrounding whitespace; 3x stays a variable.
    value = re.sub(r"(?<=\d)\s+x\s+(?=\d)", " * ", value)
    value = re.sub(r"\s+chia\s+cho\s+|\s+chia\s+", " / ", value)
    value = re.sub(r"\s+nhan\s+(?:voi\s+)?", " * ", value)
    value = re.sub(r"\s+cong\s+", " + ", value)
    value = re.sub(r"\s+tru\s+", " - ", value)
    value = re.sub(r"\s+bang\s+", " = ", value)
    value = re.sub(r"(?<=\d)\s*:\s*(?=\d)", "/", value)
    return re.sub(r"[^\S\r\n]+", " ", value).strip()


def canonical_problem_type(value: str) -> str:
    """Canonicalize provider labels such as ``cubic equation`` to a slug."""

    folded = _ascii_lower(str(value)).strip()
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", folded)).strip("_")
