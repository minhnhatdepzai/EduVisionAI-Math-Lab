"""General canonicalizer for printed linear expressions, equations and systems.

Earlier releases matched a separate regular expression per shape: ``ax+b=c``,
``ax+by=c`` and ``ax+by+cz=d``. Anything the templates did not anticipate --
``3x+y=z`` with a variable on the right, ``y=2x+1``, a system on one line --
fell through to the vision model and usually surfaced as ``unsupported``.

This module parses both sides of the input into ``Σ coefficient · variable +
constant`` and subtracts them, so any linear input reaches one canonical form:

    3x + y = z   ->   3x + y - z = 0
    y = 2x + 1   ->   -2x + y = 1

Only coefficients that are actually printed are copied. Nothing here solves for
an unknown, and a nonlinear input (``x^2``, ``xy``, ``2/x``) is rejected rather
than being flattened into a linear shape it does not have.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from fractions import Fraction

from app.schemas.math_lab_input import canonicalize_typed_math

#: Symbols accepted as variable names. Restricted on purpose: the parser must
#: consume the whole stem, so a Vietnamese word can never be read as a product
#: of variables.
VARIABLE_SYMBOLS = frozenset("abcdefghijklmnopqrstuvwxyz")

#: Ordering used when a family needs positional coefficients (Oxy, Oxyz).
PREFERRED_VARIABLE_ORDER = ("x", "y", "z", "t", "u", "v", "w")

_TOLERANCE = 1e-9

_LEAD_IN_PHRASES = (
    "giaiphuongtrinh",
    "giaihephuongtrinh",
    "giaihe",
    "hephuongtrinh",
    "phuongtrinh",
    "vedothihamso",
    "vedothi",
    "dothihamso",
    "dothi",
    "bieudien",
    "mohinhhoa",
    "vehinh",
    "ve",
    "rutgon",
    "tinhgiatribieuthuc",
    "bieuthuc",
    "tinh",
    "timx",
    "tim",
    "cho",
)

_TRAILING_PHRASES = (
    "bangmay",
    "bangbaonhieu",
    "labaonhieu",
    "lagi",
    "bangmaya",
    "banggi",
)

_SYSTEM_SEPARATORS = re.compile(r"[;\n]|(?<=[0-9a-z)])\s*,\s*(?=[-+0-9a-z])| va ")

_NONLINEAR_MARKERS = (
    "^",
    "²",
    "³",
    "√",
    "sqrt",
    "sin",
    "cos",
    "tan",
    "log",
    "!",
    "%",
)


@dataclass(frozen=True, slots=True)
class LinearSide:
    """One printed side of an equation, before canonicalization."""

    coefficients: dict[str, float]
    constant: float

    def variables(self) -> tuple[str, ...]:
        return tuple(
            name
            for name in _sorted_variables(self.coefficients)
            if abs(self.coefficients[name]) > _TOLERANCE
        )


@dataclass(frozen=True, slots=True)
class LinearForm:
    """A linear input reduced to ``Σ coefficients[v] · v = constant``.

    ``left``/``right`` keep the printed sides so a balance scene can show the
    identical operation applied to each side instead of a pre-solved result.
    """

    coefficients: dict[str, float]
    constant: float
    left: LinearSide
    right: LinearSide | None
    source: str

    @property
    def is_equation(self) -> bool:
        return self.right is not None

    @property
    def variables(self) -> tuple[str, ...]:
        return tuple(
            name
            for name in _sorted_variables(self.coefficients)
            if abs(self.coefficients[name]) > _TOLERANCE
        )

    @property
    def needs_expansion(self) -> bool:
        """True when the printed equation has brackets to distribute.

        Stage count cannot decide this: a Vietnamese lead-in already makes the
        printed line differ from the parsed one without any algebra happening.
        """

        return "(" in _fold(str(self.source))

    @property
    def degenerate(self) -> bool:
        """True when every variable cancelled, e.g. ``x + 1 = x + 1``."""

        return not self.variables

    @property
    def contradictory(self) -> bool:
        return self.degenerate and abs(self.constant) > _TOLERANCE

    def coefficient(self, name: str) -> float:
        return self.coefficients.get(name, 0.0)

    def ordered_coefficients(self) -> tuple[tuple[str, float], ...]:
        return tuple((name, self.coefficients[name]) for name in self.variables)

    def satisfies(self, assignment: dict[str, float], tolerance: float = 1e-6) -> bool:
        total = sum(
            self.coefficient(name) * value for name, value in assignment.items()
        )
        return abs(total - self.constant) <= tolerance


@dataclass(frozen=True, slots=True)
class LinearSystem:
    """A fully consumed linear system with two or three variables.

    ``intersection`` remains available for the established two-line renderer.
    ``solution`` and the rank fields describe the general system, including a
    three-plane system and overdetermined systems.  Exact fraction strings are
    kept beside floats so the teaching UI never turns ``15/16`` into a vague
    rounded answer.
    """

    forms: tuple[LinearForm, ...]
    variables: tuple[str, ...]
    state: str
    intersection: tuple[float, float] | None
    source: str
    solution: tuple[float, ...] | None = None
    solution_exact: tuple[str, ...] | None = None
    coefficient_rank: int = 0
    augmented_rank: int = 0
    elimination_steps: tuple[dict[str, object], ...] = ()


@dataclass(frozen=True, slots=True)
class LinearClassification:
    """Family decision derived only from the printed structure."""

    kind: str
    form: LinearForm | None = None
    system: LinearSystem | None = None

    @property
    def variable_count(self) -> int:
        if self.system is not None:
            return len(self.system.variables)
        return len(self.form.variables) if self.form else 0


def _sorted_variables(coefficients: dict[str, float]) -> tuple[str, ...]:
    def key(name: str) -> tuple[int, str]:
        try:
            return (PREFERRED_VARIABLE_ORDER.index(name), name)
        except ValueError:
            return (len(PREFERRED_VARIABLE_ORDER), name)

    return tuple(sorted(coefficients, key=key))


def _fold(text: str) -> str:
    """Accent-insensitive, symbol-normalized lowercase copy."""

    normalized = (
        canonicalize_typed_math(text).lower()
        .replace("−", "-")
        .replace("–", "-")
        .replace("—", "-")
        .replace("×", "*")
        .replace("·", "*")
        .replace("⋅", "*")
        .replace("∙", "*")
        .replace("÷", "/")
        .replace("≡", "=")
        .replace("＝", "=")
        .replace("（", "(")
        .replace("）", ")")
        .replace("[", "(")
        .replace("]", ")")
        .replace("{", "(")
        .replace("}", ")")
    )
    decomposed = unicodedata.normalize("NFD", normalized)
    stripped = "".join(
        character
        for character in decomposed
        if unicodedata.category(character) != "Mn"
    )
    return stripped.replace("đ", "d")


def _strip_phrases(stem: str) -> str:
    """Remove known Vietnamese lead-ins and trailing question phrases."""

    working = stem
    changed = True
    while changed:
        changed = False
        for phrase in _LEAD_IN_PHRASES:
            if working.startswith(phrase) and len(working) > len(phrase):
                working = working[len(phrase) :]
                changed = True
                break
    changed = True
    while changed:
        changed = False
        working = working.rstrip("?.:").rstrip()
        for phrase in _TRAILING_PHRASES:
            if working.endswith(phrase) and len(working) > len(phrase):
                working = working[: -len(phrase)]
                changed = True
                break
    return working


def _prepare(text: str | None) -> str | None:
    if not text:
        return None
    folded = _fold(text)
    # OCR frequently prints a decimal comma; a comma between two equations is
    # handled before this point by the system splitter.
    compact = re.sub(r"(?<=\d),(?=\d)", ".", folded)
    compact = re.sub(r"\s+", "", compact)
    if not compact:
        return None
    return _strip_phrases(compact)


_TERM_PATTERN = re.compile(
    r"(?P<sign>[+-])?"
    r"(?:(?P<numerator>\d+(?:\.\d+)?)(?:/(?P<denominator>\d+(?:\.\d+)?))?)?"
    r"\*?"
    r"(?P<variable>[a-z])?"
    r"$"
)


def _expand_parentheses(expression: str) -> str | None:
    """Distribute a numeric multiplier over one level of parentheses.

    ``3(x+2)`` becomes ``3x+6`` and ``-2(3x-1)`` becomes ``-6x+2``. Nested or
    variable-multiplied groups are rejected: distributing ``x(x+1)`` would
    produce a quadratic this module has no right to model as linear.
    """

    # A variable or a second group multiplying a group is not linear:
    # ``x(x+1)`` and ``(x+1)(x+2)`` are quadratics, and distributing them as if
    # the factor were 1 would silently produce a wrong linear model.
    if re.search(r"[a-z]\(", expression) or ")(" in expression:
        return None
    working = expression
    for _ in range(4):
        match = re.search(
            r"(?P<sign>[+-])?(?P<factor>\d+(?:\.\d+)?)?\*?\((?P<body>[^()]*)\)",
            working,
        )
        if match is None:
            return working
        body = match.group("body")
        if not body or "(" in body:
            return None
        inner = _parse_side(body)
        if inner is None:
            return None
        sign = -1.0 if match.group("sign") == "-" else 1.0
        factor = sign * (1.0 if match.group("factor") is None else float(match.group("factor")))
        distributed = _render_side(
            {name: value * factor for name, value in inner.coefficients.items()},
            inner.constant * factor,
        )
        prefix = working[: match.start()]
        suffix = working[match.end() :]
        # "t5(x+2)" is a word fragment followed by a group, not a product.
        if prefix and prefix[-1].isalpha():
            return None
        # The distributed group already carries its own sign, so an explicit
        # leading "+" is only needed when it follows another term.
        if prefix and not distributed.startswith("-"):
            distributed = f"+{distributed}"
        working = f"{prefix}{distributed}{suffix}"
    return None


def _render_side(coefficients: dict[str, float], constant: float) -> str:
    """Serialize coefficients back into the compact grammar's own syntax."""

    pieces: list[str] = []
    for name in _sorted_variables(coefficients):
        value = coefficients[name]
        if abs(value) <= _TOLERANCE:
            continue
        magnitude = abs(value)
        # A coefficient of 1 is not written on a blackboard, and re-parsing
        # "x" gives the same value back, so the round trip stays exact.
        body = name if abs(magnitude - 1) <= _TOLERANCE else f"{magnitude:g}{name}"
        pieces.append(f"{'-' if value < 0 else '+'}{body}")
    if abs(constant) > _TOLERANCE:
        pieces.append(f"{'-' if constant < 0 else '+'}{abs(constant):g}")
    if not pieces:
        return "0"
    joined = "".join(pieces)
    return joined[1:] if joined.startswith("+") else joined


def _parse_side(expression: str) -> LinearSide | None:
    """Parse ``3x+y-2`` into coefficients and a constant, or reject it."""

    if not expression:
        return None
    if any(marker in expression for marker in _NONLINEAR_MARKERS):
        return None
    if "(" in expression or ")" in expression:
        expanded = _expand_parentheses(expression)
        if expanded is None or "(" in expanded:
            return None
        expression = expanded

    # Split on top-level +/- while keeping the sign with its term.
    pieces: list[str] = []
    current = ""
    for index, character in enumerate(expression):
        if character in "+-" and index > 0 and expression[index - 1] not in "*/":
            pieces.append(current)
            current = character
        else:
            current += character
    pieces.append(current)

    coefficients: dict[str, float] = {}
    constant = 0.0
    for piece in pieces:
        if not piece or piece in "+-":
            return None
        match = _TERM_PATTERN.fullmatch(piece)
        if not match:
            return None
        sign = -1.0 if match.group("sign") == "-" else 1.0
        numerator = match.group("numerator")
        denominator = match.group("denominator")
        variable = match.group("variable")
        if numerator is None and variable is None:
            return None
        if denominator is not None and float(denominator) == 0:
            return None
        magnitude = 1.0 if numerator is None else float(numerator)
        if denominator is not None:
            magnitude /= float(denominator)
        value = sign * magnitude
        if variable is None:
            constant += value
            continue
        if variable not in VARIABLE_SYMBOLS:
            return None
        coefficients[variable] = coefficients.get(variable, 0.0) + value
    return LinearSide(coefficients=coefficients, constant=constant)


def parse_linear_form(text: str | None) -> LinearForm | None:
    """Canonicalize one printed linear expression or equation.

    A Vietnamese lead-in is dropped by trying each later start position and
    keeping the first one the grammar consumes completely. That is stricter
    than it sounds: prose cannot parse, because a term may hold at most one
    variable letter, so ``timxbiet`` never becomes a product of variables.

    Returns ``None`` for anything not fully consumed, so prose and nonlinear
    algebra keep flowing to the vision model.
    """

    if _has_blank_placeholder(text):
        return None
    compact = _prepare(text)
    if compact is None:
        return None
    form = _build_form(compact, text)
    if form is not None:
        return form
    # Drop leading words, never leading characters. Scanning by character let
    # "2/x = 4" restart at "x = 4" and "x^2 + 1 = 0" restart at "+ 1 = 0",
    # turning refused nonlinear input into a confident linear scene. A word is
    # only droppable while it carries no mathematics of its own.
    for candidate in _word_boundary_candidates(text):
        form = _build_form(candidate, text, require_digit=True)
        if form is not None:
            return form
    return None


def _has_blank_placeholder(text: str | None) -> bool:
    """True for a fill-in-the-blank question such as ``? + 6 = 12``.

    The blank is an operand the learner must supply, so this module has no
    right to read the remaining terms as a complete equation. Checked on the
    whole input: dropping a leading word would otherwise discard the blank and
    leave a perfectly parsable -- and completely wrong -- ``6 = 12``.
    """

    body = re.sub(r"[?.\s]+$", "", _fold(str(text or "")))
    return any(marker in body for marker in ("?", "_", "…", "□", "▢"))


_OPERATOR_TOKEN = re.compile(r"^[+\-*/=<>≤≥]+$")


def _word_boundary_candidates(text: str | None) -> list[str]:
    tokens = _fold(str(text or "")).split()
    candidates: list[str] = []
    for index, token in enumerate(tokens[:-1]):
        if re.search(r"[\d=()^²³√/*<>≤≥]", token):
            break
        # A word standing immediately before an operator is an operand, not a
        # lead-in: dropping the "x" of "x + y > 8" would delete a whole term
        # and leave a one-variable inequality that was never written.
        if _OPERATOR_TOKEN.match(tokens[index + 1]):
            break
        remainder = _prepare(" ".join(tokens[index + 1 :]))
        if remainder:
            candidates.append(remainder)
    return candidates


def _build_form(
    compact: str,
    source: str | None,
    require_digit: bool = False,
) -> LinearForm | None:
    if len(compact) < 2:
        return None
    # A fragment taken from the middle of a sentence must show a number.
    # Without this the trailing "i" of a Vietnamese word parsed as the
    # expression "1·i" and prose became an algebra scene. The rule does not
    # apply to the whole input, where "x + y = z" is perfectly valid algebra.
    if require_digit:
        # A fragment lifted out of a sentence must look like algebra on its
        # own: it must print a number, and it must be an equation or have more
        # than one term. Without the second rule the tail of "bán kính 12 m"
        # parsed as the expression 12·m and became an algebra-tiles scene.
        if not any(character.isdigit() for character in compact):
            return None
        if "=" not in compact and not re.search(r"(?<=.)[+-]", compact):
            return None
    if compact.count("=") > 1:
        return None
    if "=" in compact:
        left_text, right_text = compact.split("=")
        left = _parse_side(left_text)
        right = _parse_side(right_text)
        if left is None or right is None:
            return None
        coefficients = {
            name: left.coefficients.get(name, 0.0) - right.coefficients.get(name, 0.0)
            for name in set(left.coefficients) | set(right.coefficients)
        }
        constant = right.constant - left.constant
    else:
        left = _parse_side(compact)
        if left is None:
            return None
        right = None
        coefficients = dict(left.coefficients)
        constant = -left.constant
    pruned = {
        name: value
        for name, value in coefficients.items()
        if abs(value) > _TOLERANCE
    }
    if not pruned and right is None:
        # A bare number is arithmetic, not an algebraic expression.
        return None
    return LinearForm(
        coefficients=pruned,
        constant=0.0 if abs(constant) <= _TOLERANCE else constant,
        left=left,
        right=right,
        source=str(source),
    )


def _split_system(text: str) -> list[str]:
    # Collapse runs of spaces but keep newlines: a system is often typed one
    # equation per line, and that line break is the separator.
    folded = _fold(str(text))
    # Protect Vietnamese decimal commas before treating other commas as
    # equation separators: ``0,5x`` is one coefficient, not two equations.
    folded = re.sub(r"(?<=\d),(?=\d)", ".", folded)
    normalized = re.sub(r"[^\S\n]+", " ", folded).strip()
    parts = [part.strip() for part in _SYSTEM_SEPARATORS.split(normalized)]
    parts = [part for part in parts if part]
    if len(parts) < 2:
        return parts
    # A handwritten/typed system is commonly introduced by one large brace.
    # `_fold` maps braces to parentheses; remove only unmatched outer markers,
    # never parentheses that belong to an equation such as 2(x + y) = 4.
    if parts[0].count("(") > parts[0].count(")"):
        parts[0] = parts[0].lstrip("(").strip()
    if parts[-1].count(")") > parts[-1].count("("):
        parts[-1] = parts[-1].rstrip(")").strip()
    return parts


def _fraction(value: float) -> Fraction:
    """Recover the decimal/fraction the learner printed, without float noise."""

    return Fraction(str(value)).limit_denominator(1_000_000)


def _fraction_text(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _matrix_payload(matrix: list[list[Fraction]]) -> list[list[str]]:
    return [[_fraction_text(value) for value in row] for row in matrix]


def _solve_linear_system(
    forms: tuple[LinearForm, ...],
    variables: tuple[str, ...],
) -> tuple[str, tuple[float, ...] | None, tuple[str, ...] | None, int, int, tuple[dict[str, object], ...]]:
    """Reduce an augmented matrix exactly and retain visible row operations."""

    variable_count = len(variables)
    matrix = [
        [_fraction(form.coefficient(name)) for name in variables] + [_fraction(form.constant)]
        for form in forms
    ]
    steps: list[dict[str, object]] = [{
        "operation": "Lập ma trận mở rộng từ đúng các hệ số đã cho",
        "matrix": _matrix_payload(matrix),
    }]
    pivot_row = 0
    pivot_columns: list[int] = []
    for column in range(variable_count):
        pivot = next(
            (row for row in range(pivot_row, len(matrix)) if matrix[row][column] != 0),
            None,
        )
        if pivot is None:
            continue
        if pivot != pivot_row:
            matrix[pivot_row], matrix[pivot] = matrix[pivot], matrix[pivot_row]
            steps.append({
                "operation": f"Đổi hàng {pivot_row + 1} với hàng {pivot + 1}",
                "matrix": _matrix_payload(matrix),
            })
        pivot_value = matrix[pivot_row][column]
        if pivot_value != 1:
            matrix[pivot_row] = [value / pivot_value for value in matrix[pivot_row]]
            steps.append({
                "operation": f"Chia hàng {pivot_row + 1} cho {_fraction_text(pivot_value)}",
                "matrix": _matrix_payload(matrix),
            })
        for row in range(len(matrix)):
            if row == pivot_row or matrix[row][column] == 0:
                continue
            factor = matrix[row][column]
            matrix[row] = [
                value - factor * pivot_value
                for value, pivot_value in zip(matrix[row], matrix[pivot_row], strict=True)
            ]
            sign = "−" if factor > 0 else "+"
            steps.append({
                "operation": f"Hàng {row + 1} {sign} {_fraction_text(abs(factor))} × hàng {pivot_row + 1}",
                "matrix": _matrix_payload(matrix),
            })
        pivot_columns.append(column)
        pivot_row += 1
        if pivot_row >= len(matrix):
            break

    coefficient_rank = sum(
        any(value != 0 for value in row[:variable_count]) for row in matrix
    )
    augmented_rank = sum(any(value != 0 for value in row) for row in matrix)
    if augmented_rank > coefficient_rank:
        return "inconsistent", None, None, coefficient_rank, augmented_rank, tuple(steps)
    if coefficient_rank < variable_count:
        return "infinite", None, None, coefficient_rank, augmented_rank, tuple(steps)

    solution_fractions = [Fraction(0) for _ in variables]
    for row, column in enumerate(pivot_columns):
        if column < variable_count:
            solution_fractions[column] = matrix[row][-1]
    solution = tuple(float(value) for value in solution_fractions)
    exact = tuple(_fraction_text(value) for value in solution_fractions)
    return "unique", solution, exact, coefficient_rank, augmented_rank, tuple(steps)


def parse_linear_system(text: str | None) -> LinearSystem | None:
    """Parse a complete system of two or three linear equations.

    Systems with two or three variables are accepted.  Every equation and
    every printed term must parse; a fourth equation/variable is refused
    rather than silently discarded.
    """

    if not text:
        return None
    parts = _split_system(text)
    if len(parts) not in {2, 3}:
        return None
    parsed = tuple(parse_linear_form(part) for part in parts)
    if any(form is None for form in parsed):
        return None
    forms = tuple(form for form in parsed if form is not None)
    if not all(form.is_equation for form in forms):
        return None
    variables = tuple(sorted({name for form in forms for name in form.variables}, key=lambda name: (
        PREFERRED_VARIABLE_ORDER.index(name)
        if name in PREFERRED_VARIABLE_ORDER
        else len(PREFERRED_VARIABLE_ORDER)
    )))
    if len(variables) not in {2, 3}:
        return None
    # The existing Oxy scene draws exactly two lines.  Refuse a third
    # two-variable equation until that renderer can show all three; accepting
    # it here and slicing it away in the browser would alter the user's system.
    if len(variables) == 2 and len(forms) != 2:
        return None
    solved_state, solution, exact, coefficient_rank, augmented_rank, steps = _solve_linear_system(
        forms, variables
    )
    state = solved_state
    intersection = None
    # Keep the public state names used by the two-line Oxy renderer.
    if len(forms) == 2 and len(variables) == 2:
        state = {
            "unique": "intersecting",
            "infinite": "coincident",
            "inconsistent": "parallel",
        }[solved_state]
        intersection = solution if solution is not None else None
    return LinearSystem(
        forms=forms,
        variables=variables,
        state=state,
        intersection=intersection,
        source=str(text),
        solution=solution,
        solution_exact=exact,
        coefficient_rank=coefficient_rank,
        augmented_rank=augmented_rank,
        elimination_steps=steps,
    )


def classify_linear(text: str | None) -> LinearClassification | None:
    """Route a printed linear input to the family its structure justifies."""

    if not text:
        return None
    system = parse_linear_system(text)
    if system is not None:
        return LinearClassification(
            kind=f"system_{'two' if len(system.variables) == 2 else 'three'}_variables",
            system=system,
        )
    form = parse_linear_form(text)
    if form is None:
        return None
    if form.contradictory:
        return LinearClassification(kind="contradiction", form=form)
    if form.degenerate:
        return LinearClassification(kind="identity", form=form)
    count = len(form.variables)
    if not form.is_equation:
        if count == 1:
            return LinearClassification(kind="expression_one_variable", form=form)
        return LinearClassification(kind="expression_many_variables", form=form)
    if count == 1:
        return LinearClassification(kind="equation_one_variable", form=form)
    if count == 2:
        return LinearClassification(kind="equation_two_variables", form=form)
    if count == 3:
        return LinearClassification(kind="equation_three_variables", form=form)
    return LinearClassification(kind="equation_many_variables", form=form)


def sample_plane_points(
    form: LinearForm,
    variables: tuple[str, str, str],
    count: int = 4,
) -> list[tuple[float, float, float]]:
    """Generate points that actually satisfy ``ax + by + cz = d``.

    The renderer must never display a "solution" the equation does not accept,
    so each candidate is solved for the variable with the largest coefficient
    and then re-checked against the original form.
    """

    first, second, third = variables
    coefficients = {name: form.coefficient(name) for name in variables}
    solve_for = max(variables, key=lambda name: abs(coefficients[name]))
    if abs(coefficients[solve_for]) <= _TOLERANCE:
        return []
    free = [name for name in variables if name != solve_for]
    seeds = ((0, 0), (1, 0), (0, 1), (1, 1), (2, -1), (-1, 2))
    points: list[tuple[float, float, float]] = []
    for first_value, second_value in seeds[: max(count, 1) + 2]:
        assignment = {free[0]: float(first_value), free[1]: float(second_value)}
        remainder = form.constant - sum(
            coefficients[name] * assignment[name] for name in free
        )
        assignment[solve_for] = remainder / coefficients[solve_for]
        if not form.satisfies(assignment):
            continue
        points.append(
            (assignment[first], assignment[second], assignment[third])
        )
        if len(points) >= count:
            break
    return points


def format_coefficient(value: float) -> str:
    """Render a coefficient the way it is printed on a blackboard."""

    if abs(value - round(value)) <= _TOLERANCE:
        return str(int(round(value)))
    fraction = Fraction(value).limit_denominator(1000)
    if abs(float(fraction) - value) <= 1e-6 and fraction.denominator <= 20:
        return f"{fraction.numerator}/{fraction.denominator}"
    return f"{value:g}"


def _format_terms(coefficients: dict[str, float], order: tuple[str, ...]) -> str:
    pieces: list[str] = []
    for name in order:
        value = coefficients.get(name, 0.0)
        if abs(value) <= _TOLERANCE:
            continue
        sign = "-" if value < 0 else "+"
        magnitude = abs(value)
        body = name if abs(magnitude - 1) <= _TOLERANCE else f"{format_coefficient(magnitude)}{name}"
        if not pieces:
            pieces.append(f"-{body}" if sign == "-" else body)
        else:
            pieces.append(f" {sign} {body}")
    return "".join(pieces)


def format_canonical(form: LinearForm) -> str:
    """Human-readable ``3x + y - z = 0`` for the teaching steps.

    A bare expression keeps its printed constant instead of being pushed to the
    right of an equals sign it never had.
    """

    if not form.is_equation:
        body = _format_terms(form.left.coefficients, _sorted_variables(form.left.coefficients))
        constant = form.left.constant
        if abs(constant) <= _TOLERANCE:
            return body or "0"
        sign = "-" if constant < 0 else "+"
        return f"{body} {sign} {format_coefficient(abs(constant))}" if body else format_coefficient(constant)
    left = _format_terms(form.coefficients, form.variables) or "0"
    return f"{left} = {format_coefficient(form.constant)}"


def format_sides(form: LinearForm) -> str:
    """The equation as the parser understood each printed side."""

    left = _render_side(form.left.coefficients, form.left.constant)
    if form.right is None:
        return left
    right = _render_side(form.right.coefficients, form.right.constant)
    return f"{left} = {right}"


def transformation_stages(form: LinearForm) -> list[str]:
    """Printed form, expanded form and collected form, without solving.

    A balance scene needs the states between the question and the answer.
    Repeated stages are dropped so a step always changes something visible.
    """

    stages: list[str] = []
    printed = re.sub(r"\s+", " ", str(form.source)).strip()
    if printed:
        stages.append(printed)
    expanded = format_sides(form).replace("*", "")
    canonical = format_canonical(form)
    for stage in (expanded, canonical):
        normalized = stage.replace(" ", "")
        if all(normalized != item.replace(" ", "") for item in stages):
            stages.append(stage)
    return stages


@dataclass(frozen=True, slots=True)
class LinearInequality:
    """``ax + b <op> c`` reduced to ``coefficient · v (op) constant``.

    The boundary value is deliberately absent: it is the answer, and deriving
    it belongs to the renderer, not to the extraction of printed facts.
    """

    coefficient: float
    constant: float
    operator: str
    symbol: str
    source: str

    @property
    def strict(self) -> bool:
        return self.operator in {"<", ">"}


@dataclass(frozen=True, slots=True)
class ProductEquation:
    """``(a₁v + b₁)(a₂v + b₂) = 0`` with both printed factors kept apart."""

    factors: tuple[tuple[float, float], ...]
    symbol: str
    source: str


@dataclass(frozen=True, slots=True)
class RationalDomain:
    """Denominators of a rational equation that must not vanish."""

    #: One ``(coefficient, constant)`` pair per printed denominator.
    denominators: tuple[tuple[float, float], ...]
    symbol: str
    source: str


_INEQUALITY_OPERATORS = (
    ("<=", "≤"), ("=<", "≤"), ("≤", "≤"),
    (">=", "≥"), ("=>", "≥"), ("≥", "≥"),
    ("<", "<"), (">", ">"),
)


def _prepared_variants(text: str) -> list[str]:
    """The whole prepared stem, then the same stem with leading words dropped.

    Shares the word-boundary rule used by ``parse_linear_form``: a Vietnamese
    lead-in such as "Bất phương trình" is prose and may be dropped, but a word
    carrying mathematics of its own may not.
    """

    variants: list[str] = []
    compact = _prepare(text)
    if compact:
        variants.append(compact)
    variants.extend(_word_boundary_candidates(text))
    return variants


def parse_linear_inequality(text: str | None) -> LinearInequality | None:
    """Read a one-variable linear inequality without solving it."""

    if not text or _has_blank_placeholder(text):
        return None
    for compact in _prepared_variants(text):
        found = _inequality_from(compact, text)
        if found is not None:
            return found
    return None


def _inequality_from(compact: str, source: str) -> LinearInequality | None:
    for token, operator in _INEQUALITY_OPERATORS:
        if token not in compact:
            continue
        left_text, _, right_text = compact.partition(token)
        left = _parse_side(left_text)
        right = _parse_side(right_text)
        if left is None or right is None:
            return None
        coefficients = {
            name: left.coefficients.get(name, 0.0) - right.coefficients.get(name, 0.0)
            for name in set(left.coefficients) | set(right.coefficients)
        }
        active = [name for name, value in coefficients.items() if abs(value) > _TOLERANCE]
        if len(active) != 1:
            return None
        symbol = active[0]
        return LinearInequality(
            coefficient=coefficients[symbol],
            constant=right.constant - left.constant,
            operator=operator,
            symbol=symbol,
            source=str(source),
        )
    return None


def parse_product_equation(text: str | None) -> ProductEquation | None:
    """Read ``(a₁x + b₁)(a₂x + b₂) = 0`` as its separate printed factors."""

    if not text or _has_blank_placeholder(text):
        return None
    for compact in _prepared_variants(text):
        found = _product_from(compact, text)
        if found is not None:
            return found
    return None


def _product_from(compact: str, source: str) -> ProductEquation | None:
    if "=" not in compact:
        return None
    left_text, _, right_text = compact.partition("=")
    right = _parse_side(right_text)
    # The zero-product rule only applies when the product really equals zero.
    if right is None or right.coefficients or abs(right.constant) > _TOLERANCE:
        return None
    groups = re.findall(r"\(([^()]*)\)", left_text)
    if len(groups) < 2 or re.sub(r"\([^()]*\)|\*", "", left_text):
        return None
    factors: list[tuple[float, float]] = []
    symbols: set[str] = set()
    for group in groups:
        side = _parse_side(group)
        if side is None:
            return None
        active = [
            name for name, value in side.coefficients.items()
            if abs(value) > _TOLERANCE
        ]
        if len(active) != 1:
            return None
        symbols.add(active[0])
        factors.append((side.coefficients[active[0]], side.constant))
    if len(symbols) != 1:
        return None
    return ProductEquation(
        factors=tuple(factors),
        symbol=symbols.pop(),
        source=str(source),
    )


def parse_rational_domain(text: str | None) -> RationalDomain | None:
    """Collect the denominators of a rational equation that contain the unknown.

    Only denominators are read. The excluded values follow from them and are
    derived by the scene, so nothing here states the answer.
    """

    if not text:
        return None
    folded = _fold(str(text))
    # A slash in a measurement unit (km/h, m/s) or in a printed formula such
    # as Viète's ``-b/a`` is not a domain question.  This family exists to
    # visualize excluded values, so claim input only when the wording actually
    # asks about a domain/denominator/rational expression.
    if not re.search(
        r"\b(?:dieu\s+kien\s+xac\s+dinh|dieu\s+kien\s+cua|"
        r"mau\s+thuc|phan\s+thuc|phuong\s+trinh\s+phan\s+thuc)\b",
        folded,
    ):
        return None
    compact = re.sub(r"\s+", "", folded)
    denominators: list[tuple[float, float]] = []
    symbols: set[str] = set()
    for group in re.findall(r"/\(([^()]*)\)", compact):
        side = _parse_side(group)
        if side is None:
            continue
        active = [
            name for name, value in side.coefficients.items()
            if abs(value) > _TOLERANCE
        ]
        if len(active) != 1:
            continue
        symbols.add(active[0])
        denominators.append((side.coefficients[active[0]], side.constant))
    # A bare "/x" denominator excludes zero just as "(x - 0)" would.
    for name in re.findall(r"/([a-z])(?![a-z0-9])", compact):
        symbols.add(name)
        denominators.append((1.0, 0.0))
    if not denominators or len(symbols) != 1:
        return None
    unique = tuple(dict.fromkeys(denominators))
    return RationalDomain(
        denominators=unique,
        symbol=symbols.pop(),
        source=str(text),
    )
