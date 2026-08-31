/**
 * Derivations for the exam families that had no truthful renderer.
 *
 * Each function turns world values into the numbers a scene needs and nothing
 * more: no answer is written into the givens, and a derivation returns `null`
 * rather than substituting a default when an operand is missing. A renderer
 * that received a silent zero would draw a confident wrong picture.
 */

import { rawValue } from "./deriveScene.js";

function boundValues(world, bindings, role) {
  const ids = Array.isArray(bindings?.[role]) ? bindings[role] : [];
  return ids.map((id) => rawValue(world, id)).filter((value) => Number.isFinite(value));
}

function firstBound(world, bindings, ...roles) {
  for (const role of roles) {
    const [value] = boundValues(world, bindings, role);
    if (Number.isFinite(value)) return value;
  }
  return null;
}

function unitOf(world, bindings, role, fallback = "cm") {
  const ids = Array.isArray(bindings?.[role]) ? bindings[role] : [];
  for (const id of ids) {
    const unit = world?.values?.[id]?.unit;
    if (unit && unit !== "one") return unit;
  }
  return fallback;
}

/** The disc, the sectors it is cut into, and the rectangle they re-form. */
export function deriveCircleArea(world, bindings = {}) {
  const radius = firstBound(world, bindings, "radius");
  const diameter = firstBound(world, bindings, "diameter");
  const resolved = Number.isFinite(radius) ? radius : (Number.isFinite(diameter) ? diameter / 2 : null);
  if (!Number.isFinite(resolved) || resolved <= 0) return null;
  const unit = Number.isFinite(radius)
    ? unitOf(world, bindings, "radius")
    : unitOf(world, bindings, "diameter");
  const sectors = 12;
  return {
    radius: resolved,
    fromDiameter: !Number.isFinite(radius),
    diameter: resolved * 2,
    unit,
    sectors,
    circumference: 2 * Math.PI * resolved,
    halfCircumference: Math.PI * resolved,
    area: Math.PI * resolved * resolved,
  };
}

/** A tangent right angle and an inscribed angle that share one arc. */
export function deriveCircleProof(world, bindings = {}) {
  const radius = firstBound(world, bindings, "radius")
    ?? (Number.isFinite(firstBound(world, bindings, "diameter"))
      ? firstBound(world, bindings, "diameter") / 2
      : null);
  const centralAngle = firstBound(world, bindings, "angle");
  if (!Number.isFinite(radius) || radius <= 0) return null;
  if (!Number.isFinite(centralAngle) || centralAngle <= 0 || centralAngle >= 360) return null;
  return {
    radius,
    unit: unitOf(world, bindings, "radius"),
    centralAngle,
    inscribedAngle: centralAngle / 2,
    tangentAngle: 90,
  };
}

/** Two multiple strips over one lattice, plus the multiples they share. */
export function deriveFactorLattice(world, bindings = {}) {
  const first = firstBound(world, bindings, "count_initial");
  const second = firstBound(world, bindings, "count_change");
  if (![first, second].every((value) => Number.isInteger(value) && value > 0)) return null;
  if (first > 24 || second > 24) return null;
  const gcd = (a, b) => (b === 0 ? a : gcd(b, a % b));
  const leastCommonMultiple = (first * second) / gcd(first, second);
  const limit = Math.min(120, Math.max(leastCommonMultiple * 2, first * 6, second * 6));
  const cells = Array.from({ length: limit }, (_, index) => {
    const value = index + 1;
    return {
      value,
      firstMultiple: value % first === 0,
      secondMultiple: value % second === 0,
    };
  });
  return {
    first,
    second,
    limit,
    cells,
    columns: 10,
    commonMultiples: cells.filter((cell) => cell.firstMultiple && cell.secondMultiple).map((cell) => cell.value),
    leastCommonMultiple,
    greatestCommonDivisor: gcd(first, second),
  };
}

/** Any list of values levelled to their own mean, not a fixed three months. */
export function deriveArithmeticMean(world, bindings = {}) {
  const ids = Array.isArray(bindings?.count_change) ? bindings.count_change : [];
  const values = ids
    .map((id) => ({ id, value: rawValue(world, id), label: world?.values?.[id]?.label || "" }))
    .filter((item) => Number.isFinite(item.value));
  if (values.length < 2) return null;
  const total = values.reduce((sum, item) => sum + item.value, 0);
  const mean = total / values.length;
  const highest = Math.max(...values.map((item) => item.value), mean);
  return {
    values,
    count: values.length,
    total,
    mean,
    scaleMax: highest || 1,
    // What each column must give away or receive to reach the level line.
    transfers: values.map((item) => ({ ...item, delta: Number((mean - item.value).toFixed(6)) })),
    unit: unitOf(world, bindings, "count_change", "one"),
  };
}

/** Two quantities in ratio a:b whose difference is printed. */
export function deriveProportionalDifference(world, bindings = {}) {
  const difference = firstBound(world, bindings, "count_change", "total");
  const firstParts = firstBound(world, bindings, "numerator");
  const secondParts = firstBound(world, bindings, "denominator");
  if (![firstParts, secondParts].every((value) => Number.isInteger(value) && value > 0)) return null;
  if (!Number.isFinite(difference) || difference <= 0) return null;
  const partGap = Math.abs(firstParts - secondParts);
  if (partGap === 0 || difference % partGap !== 0) return null;
  const onePart = difference / partGap;
  return {
    difference,
    firstParts,
    secondParts,
    partGap,
    onePart,
    first: firstParts * onePart,
    second: secondParts * onePart,
    total: (firstParts + secondParts) * onePart,
    unit: unitOf(world, bindings, "count_change", "one"),
  };
}

/** Two dependent operations on one running total. */
export function deriveMultiStepArithmetic(world, bindings = {}, problemType = "") {
  const start = firstBound(world, bindings, "count_initial", "total");
  const changes = boundValues(world, bindings, "count_change");
  if (!Number.isFinite(start) || changes.length < 2) return null;
  const type = String(problemType).toLowerCase();
  // The stem's family name carries the operation order; the renderer never
  // guesses it from the numbers alone.
  const operations = type.includes("subtract_then_divide")
    ? ["subtract", "divide"]
    : type.includes("add_then_multiply")
      ? ["add", "multiply"]
      : type.includes("multiply_then_subtract")
        ? ["multiply", "subtract"]
        : ["subtract", "add"];
  const stages = [];
  let running = start;
  for (let index = 0; index < 2; index += 1) {
    const operand = changes[index];
    const operation = operations[index];
    if (!Number.isFinite(operand)) return null;
    if (operation === "divide" && (operand === 0 || running % operand !== 0)) return null;
    const next = operation === "add" ? running + operand
      : operation === "subtract" ? running - operand
        : operation === "multiply" ? running * operand
          : running / operand;
    if (!Number.isFinite(next) || next < 0) return null;
    stages.push({
      operation,
      symbol: { add: "+", subtract: "−", multiply: "×", divide: "÷" }[operation],
      operand,
      before: running,
      after: next,
    });
    running = next;
  }
  return { start, stages, result: running, scaleMax: Math.max(start, ...stages.map((s) => s.after)) || 1 };
}

/** A map length, its scale, and the real length the two rulers agree on. */
export function deriveMapScale(world, bindings = {}) {
  const mapLength = firstBound(world, bindings, "length");
  const denominator = firstBound(world, bindings, "coefficient", "denominator");
  if (!Number.isFinite(mapLength) || mapLength <= 0) return null;
  if (!Number.isFinite(denominator) || denominator <= 1) return null;
  const mapUnit = unitOf(world, bindings, "length", "cm");
  const realInMapUnit = mapLength * denominator;
  // Present the real distance in the largest unit that keeps it readable.
  const ladder = mapUnit === "cm"
    ? [{ unit: "cm", factor: 1 }, { unit: "m", factor: 100 }, { unit: "km", factor: 100000 }]
    : [{ unit: mapUnit, factor: 1 }];
  const chosen = [...ladder].reverse().find((step) => realInMapUnit / step.factor >= 1) || ladder[0];
  return {
    mapLength,
    mapUnit,
    denominator,
    realInMapUnit,
    realLength: realInMapUnit / chosen.factor,
    realUnit: chosen.unit,
    ticks: Array.from({ length: 5 }, (_, index) => ({
      map: Number(((mapLength * index) / 4).toFixed(4)),
      real: Number((((realInMapUnit / chosen.factor) * index) / 4).toFixed(4)),
    })),
  };
}

/** Long multiplication: one partial product per digit of the multiplier. */
export function deriveLongMultiplication(world, bindings = {}) {
  const values = boundValues(world, bindings, "count_initial")
    .concat(boundValues(world, bindings, "count_change"));
  const [originalLeft, originalRight] = values;
  if (![originalLeft, originalRight].every((value) => Number.isSafeInteger(value) && value > 0)) return null;
  if (!Number.isSafeInteger(originalLeft * originalRight)) return null;
  let left = originalLeft;
  let right = originalRight;
  let swapped = false;
  if (String(right).length > String(left).length) {
    [left, right] = [right, left];
    swapped = true;
  }
  const multiplierDigits = String(right).split("").map(Number).reverse();
  const partials = multiplierDigits.map((digit, position) => ({
    digit,
    position,
    // The shift is what makes a partial product belong to its place value.
    value: left * digit * 10 ** position,
    raw: left * digit,
    shift: position,
  }));
  return {
    originalLeft,
    originalRight,
    left,
    right,
    swapped,
    partials,
    result: left * right,
    // A single-digit multiplier has no partial products to add.
    needsSum: partials.length > 1,
  };
}

/** Long division: bring one digit down at a time, quotient digit by digit. */
export function deriveLongDivision(world, bindings = {}) {
  const values = boundValues(world, bindings, "count_initial")
    .concat(boundValues(world, bindings, "count_change"));
  const [dividend, divisor] = values;
  if (![dividend, divisor].every((value) => Number.isSafeInteger(value) && value > 0)) return null;
  const digits = String(dividend).split("").map(Number);
  const steps = [];
  let remainder = 0;
  let quotientText = "";
  digits.forEach((digit, index) => {
    const current = remainder * 10 + digit;
    const quotientDigit = Math.floor(current / divisor);
    const product = quotientDigit * divisor;
    remainder = current - product;
    // Leading zeros in the quotient are not written down, exactly as on paper.
    if (quotientText || quotientDigit > 0 || index === digits.length - 1) {
      quotientText += String(quotientDigit);
    }
    steps.push({ index, broughtDown: digit, current, quotientDigit, product, remainder });
  });
  return {
    dividend,
    divisor,
    steps,
    quotient: Math.floor(dividend / divisor),
    remainder,
    exact: remainder === 0,
  };
}

/** Exact factorial checkpoints use BigInt so 92! never becomes scientific notation. */
export function deriveFactorial(world, bindings = {}) {
  const value = firstBound(world, bindings, "count_initial", "count");
  if (!Number.isInteger(value) || value < 0 || value > 500) return null;
  let product = 1n;
  const checkpoints = [];
  for (let factor = 1; factor <= value; factor += 1) {
    product *= BigInt(factor);
    if (factor <= 5 || factor === 10 || factor % 10 === 0 || factor === value) {
      checkpoints.push({ factor, value: product.toString() });
    }
  }
  const leading = Array.from({ length: Math.min(value, 5) }, (_, index) => value - index);
  const trailing = value > 5 ? [3, 2, 1].filter((factor) => factor <= value) : [];
  let trailingZeros = 0;
  for (let divisor = 5; divisor <= value; divisor *= 5) {
    trailingZeros += Math.floor(value / divisor);
  }
  const result = product.toString();
  return {
    input: value,
    expression: value <= 5
      ? Array.from({ length: value }, (_, index) => value - index).join(" × ") || "1"
      : `${leading.join(" × ")} × … × ${trailing.join(" × ")}`,
    checkpoints,
    result,
    digits: result.length,
    trailingZeros,
  };
}

/** Decimal multiplication and division, taught through the shifted point. */
export function deriveDecimalScaling(world, bindings = {}, problemType = "") {
  const values = boundValues(world, bindings, "count_initial")
    .concat(boundValues(world, bindings, "count_change"));
  const [left, right] = values;
  if (![left, right].every(Number.isFinite) || right === 0) return null;
  const divide = /division|divide|chia/i.test(String(problemType));
  const decimals = (value) => {
    const text = String(value);
    return text.includes(".") ? text.split(".")[1].length : 0;
  };
  const leftPlaces = decimals(left);
  const rightPlaces = decimals(right);
  const leftWhole = Math.round(left * 10 ** leftPlaces);
  const rightWhole = Math.round(right * 10 ** rightPlaces);
  if (divide) {
    // Scale both sides by the same power of ten: the quotient is unchanged.
    const shift = Math.max(leftPlaces, rightPlaces);
    const scaledLeft = Math.round(left * 10 ** shift);
    const scaledRight = Math.round(right * 10 ** shift);
    if (scaledRight === 0) return null;
    return {
      operation: "divide",
      left,
      right,
      shift,
      scaledLeft,
      scaledRight,
      wholeResult: scaledLeft / scaledRight,
      result: left / right,
      resultPlaces: 0,
    };
  }
  const wholeResult = leftWhole * rightWhole;
  const resultPlaces = leftPlaces + rightPlaces;
  return {
    operation: "multiply",
    left,
    right,
    leftPlaces,
    rightPlaces,
    leftWhole,
    rightWhole,
    wholeResult,
    resultPlaces,
    result: wholeResult / 10 ** resultPlaces,
  };
}

const PRECEDENCE = { "×": 2, "÷": 2, "+": 1, "−": 1 };

function applyOperator(left, operator, right) {
  if (operator === "+") return left + right;
  if (operator === "−") return left - right;
  if (operator === "×") return left * right;
  if (operator === "÷") return right === 0 ? null : left / right;
  return null;
}

/**
 * A mixed expression as the tree its precedence actually builds.
 *
 * A fraction renderer can only show one operation between two fractions. An
 * expression like `3/4 + 1/2 × 2/3` is wrong unless the multiplication is
 * resolved first, so the tree — not a left-to-right strip — is the model.
 */
export function deriveExpressionTree(world, bindings = {}, relations = []) {
  const ids = Array.isArray(bindings?.count) ? bindings.count : [];
  const values = ids.map((id) => rawValue(world, id));
  const relation = (relations || []).find((item) => item?.type === "expression_tree");
  const operators = relation?.parameters?.operators;
  const labels = relation?.parameters?.operand_labels;
  if (!Array.isArray(operators) || values.length < 2) return null;
  if (operators.length !== values.length - 1) return null;
  if (!values.every(Number.isFinite)) return null;
  if (!operators.every((operator) => operator in PRECEDENCE)) return null;

  const operandLabels = Array.isArray(labels) && labels.length === values.length
    ? labels
    : values.map((value) => String(value));

  // Shunting-yard by precedence, recording each reduction as its own step.
  const nodes = values.map((value, index) => ({ value, label: operandLabels[index] }));
  const pending = [...operators];
  const steps = [];
  for (const level of [2, 1]) {
    let index = 0;
    while (index < pending.length) {
      if (PRECEDENCE[pending[index]] !== level) {
        index += 1;
        continue;
      }
      const operator = pending[index];
      const left = nodes[index];
      const right = nodes[index + 1];
      const value = applyOperator(left.value, operator, right.value);
      if (value === null || !Number.isFinite(value)) return null;
      const node = { value, label: `(${left.label} ${operator} ${right.label})` };
      steps.push({
        operator,
        left: left.label,
        right: right.label,
        leftValue: left.value,
        rightValue: right.value,
        value,
        level,
      });
      nodes.splice(index, 2, node);
      pending.splice(index, 1);
    }
  }
  if (nodes.length !== 1) return null;
  return {
    operands: values.map((value, index) => ({ value, label: operandLabels[index] })),
    operators,
    steps,
    result: nodes[0].value,
    expression: operandLabels.reduce(
      (text, label, index) => (index ? `${text} ${operators[index - 1]} ${label}` : label),
      "",
    ),
  };
}

/** Price states from list price through discount to tax, each one visible. */
export function derivePercentWaterfall(world, bindings = {}) {
  const original = firstBound(world, bindings, "count_initial", "total");
  const percentages = boundValues(world, bindings, "probability");
  if (!Number.isFinite(original) || original <= 0) return null;
  if (percentages.length < 1) return null;
  const [discount, tax = 0] = percentages;
  if (!Number.isFinite(discount) || discount < 0 || discount >= 100) return null;
  if (!Number.isFinite(tax) || tax < 0 || tax >= 100) return null;
  const discountAmount = (original * discount) / 100;
  const afterDiscount = original - discountAmount;
  const taxAmount = (afterDiscount * tax) / 100;
  const final = afterDiscount + taxAmount;
  const scale = Math.max(original, final) || 1;
  return {
    original,
    discount,
    discountAmount,
    afterDiscount,
    tax,
    taxAmount,
    final,
    hasTax: tax > 0,
    stages: [
      { id: "list", label: "Giá niêm yết", value: original, delta: 0 },
      { id: "discount", label: `Giảm ${discount}%`, value: afterDiscount, delta: -discountAmount },
      ...(tax > 0
        ? [{ id: "tax", label: `Thuế ${tax}%`, value: final, delta: taxAmount }]
        : []),
    ].map((stage) => ({ ...stage, percent: (stage.value / scale) * 100 })),
  };
}

/** Solve two unknown list prices from their total and discounted total. */
export function deriveTwoItemDiscountSystem(world, bindings = {}, relations = []) {
  const totals = boundValues(world, bindings, "total");
  const discounts = boundValues(world, bindings, "probability");
  if (totals.length < 2 || discounts.length < 2) return null;
  const [listTotal, paidTotal] = totals;
  const [firstDiscount, secondDiscount] = discounts;
  if (
    ![listTotal, paidTotal, firstDiscount, secondDiscount].every(Number.isFinite)
    || listTotal <= 0
    || paidTotal <= 0
    || paidTotal >= listTotal
    || firstDiscount <= 0
    || firstDiscount >= 100
    || secondDiscount <= 0
    || secondDiscount >= 100
  ) return null;
  const firstRate = 1 - firstDiscount / 100;
  const secondRate = 1 - secondDiscount / 100;
  const coefficientDifference = firstRate - secondRate;
  if (Math.abs(coefficientDifference) < 1e-10) return null;
  const scaledListTotal = secondRate * listTotal;
  const differencePaid = paidTotal - scaledListTotal;
  // Decimal percentage coefficients (0.9, 0.8, ...) introduce harmless IEEE
  // tails such as 120000.00000000003.  Normalize at sub-dong precision so the
  // shared world state, assertions and labels all carry the same exact money.
  const cleanMoney = (value) => Math.round(value * 1e6) / 1e6;
  const firstPrice = cleanMoney(differencePaid / coefficientDifference);
  const secondPrice = cleanMoney(listTotal - firstPrice);
  if (![firstPrice, secondPrice].every((value) => Number.isFinite(value) && value > 0)) return null;
  const paidFirst = cleanMoney(firstRate * firstPrice);
  const paidSecond = cleanMoney(secondRate * secondPrice);
  const parameters = relations.find((item) => item?.type === "two_item_discount_system")?.parameters || {};
  const rawClaimedFirst = parameters.claimed_first;
  const rawClaimedSecond = parameters.claimed_second;
  const claimedFirst = Number(rawClaimedFirst);
  const claimedSecond = Number(rawClaimedSecond);
  const hasClaim = rawClaimedFirst != null && rawClaimedSecond != null
    && Number.isFinite(claimedFirst) && Number.isFinite(claimedSecond);
  const close = (left, right) => Math.abs(left - right) < 0.01;
  return {
    listTotal,
    paidTotal,
    firstDiscount,
    secondDiscount,
    firstRate,
    secondRate,
    firstRetainedPercent: firstRate * 100,
    secondRetainedPercent: secondRate * 100,
    coefficientDifference,
    scaledListTotal,
    differencePaid,
    firstPrice,
    secondPrice,
    paidFirst,
    paidSecond,
    firstLabel: parameters.first_label || "Món hàng thứ nhất",
    secondLabel: parameters.second_label || "Món hàng thứ hai",
    firstSymbol: parameters.first_symbol || "x",
    secondSymbol: parameters.second_symbol || "y",
    claimedFirst: hasClaim ? claimedFirst : null,
    claimedSecond: hasClaim ? claimedSecond : null,
    claimCorrect: hasClaim ? close(claimedFirst, firstPrice) && close(claimedSecond, secondPrice) : null,
  };
}

/** A route split into legs, each with its own speed and its own duration. */
export function deriveSegmentedMotion(world, bindings = {}) {
  const distances = boundValues(world, bindings, "distance");
  const speeds = boundValues(world, bindings, "speed");
  if (speeds.length < 2) return null;
  if (!speeds.every((speed) => Number.isFinite(speed) && speed > 0)) return null;
  // One printed distance means both legs cover it; two means one each.
  const legDistances = distances.length >= speeds.length
    ? distances.slice(0, speeds.length)
    : Array.from({ length: speeds.length }, () => distances[0]);
  if (!legDistances.every((distance) => Number.isFinite(distance) && distance > 0)) return null;
  let elapsed = 0;
  const legs = speeds.map((speed, index) => {
    const distance = legDistances[index];
    const duration = distance / speed;
    const startTime = elapsed;
    elapsed += duration;
    return { index, distance, speed, duration, startTime, endTime: elapsed };
  });
  const totalDistance = legs.reduce((sum, leg) => sum + leg.distance, 0);
  return {
    legs,
    totalDistance,
    totalDuration: elapsed,
    averageSpeed: totalDistance / elapsed,
    distanceUnit: unitOf(world, bindings, "distance", "km"),
  };
}

/**
 * Two similar triangles and the metric relation their ratio proves.
 *
 * Drawing one triangle cannot show similarity. Both triangles, their marked
 * corresponding sides and the single scale factor between them are what makes
 * the unknown side follow rather than be asserted.
 */
export function deriveTriangleSimilarity(world, bindings = {}) {
  const lengths = boundValues(world, bindings, "length");
  const heights = boundValues(world, bindings, "height");
  const [firstSide, secondSide] = lengths;
  const [correspondingSide] = heights;
  if (![firstSide, secondSide, correspondingSide].every((value) => Number.isFinite(value) && value > 0)) {
    return null;
  }
  const scale = correspondingSide / firstSide;
  if (!Number.isFinite(scale) || scale <= 0) return null;
  return {
    small: { a: firstSide, b: secondSide },
    large: { a: correspondingSide, b: secondSide * scale },
    scale,
    unit: unitOf(world, bindings, "length"),
    // The proof is the equal ratio, not the arithmetic that follows from it.
    ratioText: `${correspondingSide} : ${firstSide} = ${secondSide * scale} : ${secondSide}`,
  };
}

/**
 * A median/centroid configuration with its 2:1 division made measurable.
 *
 * The centroid claim is only believable when the two parts of each median are
 * drawn and labelled, so the learner can read 2 : 1 instead of trusting it.
 */
export function deriveCentroidProof(world, bindings = {}) {
  const medians = boundValues(world, bindings, "length");
  const median = medians[0];
  if (!Number.isFinite(median) || median <= 0) return null;
  return {
    median,
    unit: unitOf(world, bindings, "length"),
    longPart: (median * 2) / 3,
    shortPart: median / 3,
    ratio: "2 : 1",
    // Vertices of a triangle whose median from A is drawn to the midpoint of BC.
    vertices: { a: [40, 30], b: [10, 170], c: [190, 170] },
  };
}

/** A rectangle whose changed dimensions are described by one equation. */
export function deriveRectangleEquation(world, bindings = {}) {
  const length = firstBound(world, bindings, "length");
  const width = firstBound(world, bindings, "width");
  const change = firstBound(world, bindings, "count_change");
  const perimeter = firstBound(world, bindings, "total", "count_initial");
  if (!Number.isFinite(change) || !Number.isFinite(perimeter) || perimeter <= 0) return null;
  // The stem states that the length exceeds the width by `change` and gives the
  // perimeter; both dimensions follow from that pair alone.
  const derivedWidth = (perimeter / 2 - change) / 2;
  const derivedLength = derivedWidth + change;
  if (!(derivedWidth > 0 && derivedLength > 0)) return null;
  return {
    change,
    perimeter,
    width: Number.isFinite(width) ? width : derivedWidth,
    length: Number.isFinite(length) ? length : derivedLength,
    halfPerimeter: perimeter / 2,
    area: derivedLength * derivedWidth,
    unit: unitOf(world, bindings, "length", "m"),
    equation: `x + (x + ${change}) = ${perimeter / 2}`,
  };
}

/** A worded quantity turned into one algebraic expression, term by term. */
export function deriveExpressionModel(world, bindings = {}, relations = []) {
  const coefficient = firstBound(world, bindings, "coefficient");
  const constant = firstBound(world, bindings, "constant");
  if (!Number.isFinite(coefficient) || !Number.isFinite(constant)) return null;
  const relation = (relations || []).find((item) => item?.type === "expression_model");
  const symbol = relation?.parameters?.symbol || "x";
  const subjectLabel = relation?.parameters?.subject || "đại lượng đã biết";
  const resultLabel = relation?.parameters?.result || "đại lượng cần tìm";
  const sign = constant < 0 ? "−" : "+";
  return {
    coefficient,
    constant,
    symbol,
    subjectLabel,
    resultLabel,
    expression: `${coefficient === 1 ? "" : coefficient}${symbol} ${sign} ${Math.abs(constant)}`,
    // Each phrase maps to exactly one term; that mapping is the lesson.
    mapping: [
      { phrase: `gấp ${coefficient} lần ${subjectLabel}`, term: `${coefficient === 1 ? "" : coefficient}${symbol}` },
      { phrase: constant < 0 ? `kém ${Math.abs(constant)} đơn vị` : `hơn ${Math.abs(constant)} đơn vị`, term: `${sign} ${Math.abs(constant)}` },
    ],
    samples: [1, 2, 5].map((value) => ({ value, evaluated: coefficient * value + constant })),
  };
}

const WEEKDAY_NAMES = ["Chủ nhật", "Thứ hai", "Thứ ba", "Thứ tư", "Thứ năm", "Thứ sáu", "Thứ bảy"];
const DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];

/** A calendar span: a start date, a duration in days and the date it lands on. */
export function deriveCalendarDuration(world, bindings = {}, relations = []) {
  const startDay = firstBound(world, bindings, "count_initial");
  const duration = firstBound(world, bindings, "duration", "count_change");
  const relation = (relations || []).find((item) => item?.type === "calendar_span");
  const month = Number(relation?.parameters?.month);
  const startWeekday = Number(relation?.parameters?.start_weekday);
  if (![startDay, duration].every((value) => Number.isInteger(value) && value > 0)) return null;
  if (!Number.isInteger(month) || month < 1 || month > 12) return null;
  const daysInMonth = DAYS_IN_MONTH[month - 1];
  if (startDay > daysInMonth) return null;
  const endDayRaw = startDay + duration;
  const rolledOver = endDayRaw > daysInMonth;
  const endDay = rolledOver ? endDayRaw - daysInMonth : endDayRaw;
  const endMonth = rolledOver ? (month % 12) + 1 : month;
  const weekdayKnown = Number.isInteger(startWeekday) && startWeekday >= 0 && startWeekday <= 6;
  return {
    month,
    daysInMonth,
    startDay,
    duration,
    endDay,
    endMonth,
    rolledOver,
    startWeekday: weekdayKnown ? WEEKDAY_NAMES[startWeekday] : null,
    endWeekday: weekdayKnown ? WEEKDAY_NAMES[(startWeekday + duration) % 7] : null,
    cells: Array.from({ length: daysInMonth }, (_, index) => {
      const day = index + 1;
      return {
        day,
        inSpan: day >= startDay && day <= Math.min(daysInMonth, endDayRaw),
        isStart: day === startDay,
        isEnd: !rolledOver && day === endDay,
      };
    }),
  };
}

/**
 * A right triangle solved from any two printed sides.
 *
 * Which of the two given sides is the hypotenuse decides whether the third
 * side comes from a sum or a difference of squares, so that fact is read from
 * the relation rather than guessed from the numbers. Angles are derived, never
 * supplied, and a set of sides that cannot form a right triangle returns
 * `null` instead of producing an imaginary length.
 */
export function deriveRightTriangle(world, bindings = {}, relations = []) {
  const relation = (relations || []).find((item) => item?.type === "right_triangle");
  const parameters = relation?.parameters;
  if (!parameters) return null;
  const known = parameters.known_sides || {};
  const knownAngles = parameters.known_angles || {};
  const names = Object.keys(known);
  const hypotenuseName = String(parameters.hypotenuse || "");
  const legNames = Array.isArray(parameters.legs) ? parameters.legs : [];
  if (legNames.length !== 2 || !hypotenuseName) return null;
  // Two sides, or one side with one acute angle: either determines the shape.
  if (names.length < 1) return null;
  if (names.length < 2 && Object.keys(knownAngles).length < 1) return null;

  const sides = { ...known };
  for (const value of Object.values(sides)) {
    if (!Number.isFinite(value) || value <= 0) return null;
  }
  const hasHypotenuse = hypotenuseName in sides;
  const missing = [...legNames, hypotenuseName].find((name) => !(name in sides));
  if (!missing) return null;

  if (names.length === 1) {
    // One side plus one acute angle: the two remaining sides come from the
    // trigonometric ratios, not from Pythagoras.
    const [angleVertex, angleValue] = Object.entries(knownAngles)[0] || [];
    const radians = (Number(angleValue) * Math.PI) / 180;
    if (!Number.isFinite(radians) || radians <= 0 || radians >= Math.PI / 2) return null;
    const givenName = names[0];
    // The leg containing the angle's vertex is adjacent to it.
    const adjacentName = legNames.find((name) => name.includes(angleVertex));
    const oppositeName = legNames.find((name) => name !== adjacentName);
    if (!adjacentName || !oppositeName) return null;
    if (givenName === hypotenuseName) {
      sides[oppositeName] = sides[hypotenuseName] * Math.sin(radians);
      sides[adjacentName] = sides[hypotenuseName] * Math.cos(radians);
    } else if (givenName === adjacentName) {
      sides[hypotenuseName] = sides[adjacentName] / Math.cos(radians);
      sides[oppositeName] = sides[adjacentName] * Math.tan(radians);
    } else {
      sides[hypotenuseName] = sides[oppositeName] / Math.sin(radians);
      sides[adjacentName] = sides[oppositeName] / Math.tan(radians);
    }
    if (![...legNames, hypotenuseName].every((name) => Number.isFinite(sides[name]) && sides[name] > 0)) {
      return null;
    }
  } else if (hasHypotenuse) {
    const leg = legNames.find((name) => name in sides);
    if (!leg) return null;
    const squared = sides[hypotenuseName] ** 2 - sides[leg] ** 2;
    // A leg cannot be longer than the hypotenuse.
    if (squared <= 0) return null;
    sides[missing] = Math.sqrt(squared);
  } else {
    sides[missing] = Math.sqrt(legNames.reduce((sum, name) => sum + sides[name] ** 2, 0));
  }

  const [firstLeg, secondLeg] = legNames;
  const rightVertex = String(parameters.right_vertex || "");
  const vertices = String(parameters.vertices || "");
  const acute = [...vertices].filter((vertex) => vertex !== rightVertex);
  // The angle at a vertex is opposite the leg that does not contain it.
  const angleFor = (vertex) => {
    const opposite = legNames.find((name) => !name.includes(vertex));
    return Math.asin(sides[opposite] / sides[hypotenuseName]) * (180 / Math.PI);
  };
  const angles = acute.map((vertex) => ({ vertex, degrees: angleFor(vertex) }));
  if (angles.some((item) => !Number.isFinite(item.degrees))) return null;

  // Keep the exact angle and the degrees-minutes reading side by side: a
  // spread that reused the name "degrees" silently truncated 67.38 to 67.
  const toDegreesMinutes = (degrees) => {
    const whole = Math.floor(degrees);
    const minutes = Math.round((degrees - whole) * 60);
    return minutes === 60
      ? { wholeDegrees: whole + 1, minutes: 0 }
      : { wholeDegrees: whole, minutes };
  };

  return {
    vertices,
    rightVertex,
    hypotenuseName,
    legNames,
    firstLeg,
    secondLeg,
    sides,
    known,
    knownAngles,
    missing,
    fromAngle: names.length === 1,
    hasHypotenuse,
    unit: String(parameters.unit || "cm"),
    roundToMinute: Boolean(parameters.round_to_minute),
    solveAll: Boolean(parameters.solve_all),
    angles: angles.map((item) => ({ ...item, ...toDegreesMinutes(item.degrees) })),
    // Both acute angles of a right triangle are complementary; the scene
    // checks that rather than assuming it.
    angleSum: angles.reduce((sum, item) => sum + item.degrees, 0),
  };
}

/** Numeric grade-9 trigonometry reduced to visible right-triangle pieces. */
export function deriveTrigonometricGeometry(world, bindings = {}, relations = []) {
  const relation = (relations || []).find((item) => item?.type === "trigonometric_geometry");
  const parameters = relation?.parameters;
  if (!parameters) return null;
  const angleValues = boundValues(world, bindings, "angle");
  const radians = (value) => (value * Math.PI) / 180;

  if (parameters.kind === "angle_of_depression") {
    const height = firstBound(world, bindings, "height");
    const [angle] = angleValues;
    if (!Number.isFinite(height) || height <= 0 || !Number.isFinite(angle) || angle <= 0 || angle >= 90) {
      return null;
    }
    const distance = height / Math.tan(radians(angle));
    if (!Number.isFinite(distance) || distance <= 0) return null;
    return {
      kind: parameters.kind,
      height,
      angle,
      distance,
      unit: unitOf(world, bindings, "height", String(parameters.unit || "m")),
      landmark: String(parameters.landmark || "dai_hai_dang"),
    };
  }

  if (parameters.kind === "oblique_triangle_altitude") {
    const height = firstBound(world, bindings, "height");
    const angleEntries = Object.entries(parameters.angles || {});
    if (!Number.isFinite(height) || height <= 0 || angleEntries.length !== 2 || angleValues.length < 2) return null;
    const angles = Object.fromEntries(angleEntries.map(([vertex], index) => [vertex, angleValues[index]]));
    if (Object.values(angles).some((value) => !Number.isFinite(value) || value <= 0 || value >= 90)) return null;
    const vertices = String(parameters.vertices || "ABC");
    const apex = String(parameters.apex || vertices[0] || "A");
    const foot = String(parameters.foot || "H");
    const baseVertices = [...vertices].filter((vertex) => vertex !== apex);
    if (baseVertices.length !== 2 || baseVertices.some((vertex) => !(vertex in angles))) return null;
    const baseSegments = Object.fromEntries(baseVertices.map((vertex) => [
      vertex,
      height / Math.tan(radians(angles[vertex])),
    ]));
    const sideLengths = Object.fromEntries(baseVertices.map((vertex) => [
      "".concat(apex, vertex).split("").sort().join(""),
      height / Math.sin(radians(angles[vertex])),
    ]));
    const baseName = baseVertices.join("");
    sideLengths[baseName] = baseSegments[baseVertices[0]] + baseSegments[baseVertices[1]];
    if (Object.values(sideLengths).some((value) => !Number.isFinite(value) || value <= 0)) return null;
    return {
      kind: parameters.kind,
      vertices,
      apex,
      foot,
      baseVertices,
      height,
      angles,
      apexAngle: 180 - Object.values(angles).reduce((sum, value) => sum + value, 0),
      baseSegments,
      sideLengths,
      baseName,
      unit: unitOf(world, bindings, "height", String(parameters.unit || "cm")),
    };
  }

  if (parameters.kind === "parallelogram_perpendicular_diagonal") {
    const sideLength = firstBound(world, bindings, "length", "count_initial");
    const [angle] = angleValues;
    if (!Number.isFinite(sideLength) || sideLength <= 0 || !Number.isFinite(angle) || angle <= 0 || angle >= 90) {
      return null;
    }
    const diagonalLength = sideLength * Math.tan(radians(angle));
    const area = sideLength * diagonalLength;
    if (!Number.isFinite(area) || area <= 0) return null;
    const unit = String(parameters.unit || "one");
    return {
      kind: parameters.kind,
      vertices: String(parameters.vertices || "ABCD"),
      diagonal: String(parameters.diagonal || "AC"),
      side: String(parameters.side || "AD"),
      angleVertex: String(parameters.angle_vertex || "D"),
      sideLength,
      angle,
      diagonalLength,
      area,
      unit: unit === "one" ? "đv" : unit,
      areaUnit: unit === "one" ? "đv²" : `${unit}²`,
    };
  }
  return null;
}

/** A one-square equation sampled as a truthful wireframe on Oxyz. */
export function deriveQuadraticSurface(_world, _bindings = {}, relations = []) {
  const relation = (relations || []).find((item) => item?.type === "quadratic_surface");
  const parameters = relation?.parameters;
  if (!parameters) return null;
  const squaredSymbol = String(parameters.squared_symbol || "");
  const squaredCoefficient = Number(parameters.squared_coefficient);
  const linearCoefficients = parameters.linear_coefficients || {};
  const rightSide = Number(parameters.right_side);
  const outputSymbol = String(parameters.output_symbol || "");
  const outputCoefficient = Number(linearCoefficients[outputSymbol]);
  const symbols = ["x", "y", "z"];
  if (!symbols.includes(squaredSymbol) || !symbols.includes(outputSymbol)
    || squaredSymbol === outputSymbol || !Number.isFinite(squaredCoefficient)
    || squaredCoefficient === 0 || !Number.isFinite(outputCoefficient)
    || outputCoefficient === 0 || !Number.isFinite(rightSide)) return null;
  const inputSymbols = symbols.filter((symbol) => symbol !== outputSymbol);
  if (inputSymbols.length !== 2 || !inputSymbols.includes(squaredSymbol)) return null;

  const pointAt = (first, second) => {
    const values = { x: 0, y: 0, z: 0, [inputSymbols[0]]: first, [inputSymbols[1]]: second };
    let remaining = rightSide - squaredCoefficient * values[squaredSymbol] ** 2;
    for (const symbol of symbols) {
      if (symbol === outputSymbol) continue;
      remaining -= Number(linearCoefficients[symbol] || 0) * values[symbol];
    }
    values[outputSymbol] = remaining / outputCoefficient;
    return [values.x, values.y, values.z];
  };
  const fixedValues = [-2, -1, 0, 1, 2];
  const sweepValues = Array.from({ length: 17 }, (_, index) => -2 + index / 4);
  const gridLines = [
    ...fixedValues.map((fixed) => sweepValues.map((sweep) => pointAt(fixed, sweep))),
    ...fixedValues.map((fixed) => sweepValues.map((sweep) => pointAt(sweep, fixed))),
  ];
  const samplePoints = [pointAt(0, 0), pointAt(1, 0), pointAt(0, 1)];
  if (gridLines.flat(2).some((value) => !Number.isFinite(value))) return null;
  return {
    squaredSymbol,
    squaredCoefficient,
    linearCoefficients,
    rightSide,
    outputSymbol,
    inputSymbols,
    ruledSymbol: inputSymbols.find((symbol) => symbol !== squaredSymbol),
    gridLines,
    samplePoints,
    extent: Math.max(2, ...gridLines.flat(2).map(Math.abs)),
  };
}

/**
 * A subset of the number line, whichever question produced it.
 *
 * An inequality gives a ray, a product equation gives isolated roots, and a
 * rational equation's domain gives points removed from the line. Drawing all
 * three on one axis is what makes "tập nghiệm" a thing the learner can see
 * rather than a sentence to memorise. Every boundary is derived here, so no
 * answer needs to travel in the semantic model.
 */
export function deriveSolutionSet(world, bindings = {}, relations = []) {
  const relation = (relations || []).find((item) => item?.type === "solution_set");
  const parameters = relation?.parameters;
  if (!parameters) return null;
  const symbol = String(parameters.symbol || "x");
  const coefficients = boundValues(world, bindings, "coefficient");
  const constants = boundValues(world, bindings, "constant");

  if (parameters.kind === "inequality") {
    const [coefficient] = coefficients;
    const [constant] = constants;
    if (!Number.isFinite(coefficient) || coefficient === 0) return null;
    if (!Number.isFinite(constant)) return null;
    const boundary = constant / coefficient;
    // Dividing by a negative coefficient reverses the inequality; that flip is
    // the step this family exists to make visible.
    const flipped = coefficient < 0;
    const operator = flipped
      ? { "<": ">", ">": "<", "≤": "≥", "≥": "≤" }[parameters.operator]
      : parameters.operator;
    const strict = operator === "<" || operator === ">";
    return {
      kind: "inequality",
      symbol,
      coefficient,
      constant,
      boundary,
      operator,
      printedOperator: parameters.operator,
      flipped,
      strict,
      direction: operator === ">" || operator === "≥" ? "right" : "left",
      statement: `${symbol} ${operator} ${formatNumber(boundary)}`,
      // A value that must satisfy the result, used as the visible check.
      sample: operator === ">" || operator === "≥" ? boundary + 1 : boundary - 1,
      range: axisRange([boundary]),
    };
  }

  if (parameters.kind === "product_roots" || parameters.kind === "excluded_values") {
    const pairs = [];
    for (let index = 0; index < Math.min(coefficients.length, constants.length); index += 1) {
      const coefficient = coefficients[index];
      const constant = constants[index];
      if (!Number.isFinite(coefficient) || coefficient === 0) return null;
      if (!Number.isFinite(constant)) return null;
      pairs.push({
        coefficient,
        constant,
        value: -constant / coefficient,
        factor: `${coefficient === 1 ? "" : formatNumber(coefficient)}${symbol}${constant < 0 ? " − " : " + "}${formatNumber(Math.abs(constant))}`,
      });
    }
    if (!pairs.length) return null;
    const excluded = parameters.kind === "excluded_values";
    const values = pairs.map((pair) => pair.value);
    return {
      kind: parameters.kind,
      symbol,
      pairs,
      markers: pairs.map((pair) => ({
        ...pair,
        excluded,
        label: `${symbol} ${excluded ? "≠" : "="} ${formatNumber(pair.value)}`,
      })),
      values,
      excluded,
      sum: values.reduce((total, value) => total + value, 0),
      statement: excluded
        ? values.map((value) => `${symbol} ≠ ${formatNumber(value)}`).join(" và ")
        : values.map((value) => `${symbol} = ${formatNumber(value)}`).join("; "),
      range: axisRange(values),
    };
  }

  if (parameters.kind === "absolute_value") {
    const coefficient = Number(parameters.coefficient);
    const constant = Number(parameters.constant);
    const rightSide = Number(parameters.right_side);
    if (![coefficient, constant, rightSide].every(Number.isFinite) || coefficient === 0) return null;
    if (rightSide < 0) {
      return {
        kind: "absolute_value", symbol, markers: [], values: [], rows: [],
        steps: [
          `|${linearText(coefficient, constant, symbol)}| luôn không âm`,
          `${formatNumber(rightSide)} < 0 nên không thể là một giá trị tuyệt đối`,
          "Không có trường hợp nào cần giải",
          "Tập nghiệm rỗng",
        ],
        statement: "S = ∅",
        range: axisRange([]),
      };
    }
    const branches = [rightSide, -rightSide].map((target, index) => ({
      value: (target - constant) / coefficient,
      factor: `${linearText(coefficient, constant, symbol)} = ${formatNumber(target)}`,
      branch: index === 0 ? "Nhánh dương" : "Nhánh đối",
    }));
    const uniqueBranches = uniqueByValue(branches);
    const markers = uniqueBranches.map((branch) => ({
      ...branch,
      excluded: false,
      label: `${symbol} = ${formatNumber(branch.value)}`,
    }));
    const values = markers.map((marker) => marker.value);
    return {
      kind: "absolute_value", symbol, markers, values, excluded: false,
      rows: uniqueBranches.map((branch) => ({
        label: branch.branch,
        expression: branch.factor,
        result: `${symbol} = ${formatNumber(branch.value)}`,
      })),
      steps: [
        `Bước 1 · |${linearText(coefficient, constant, symbol)}| = ${formatNumber(rightSide)} là một khoảng cách`,
        `Bước 2 · Tách thành ${linearText(coefficient, constant, symbol)} = ${formatNumber(rightSide)} hoặc = ${formatNumber(-rightSide)}`,
        "Bước 3 · Giải riêng hai phương trình bậc nhất",
        `Bước 4 · Thay lại và nhận ${solutionStatement(symbol, values)}`,
      ],
      statement: solutionStatement(symbol, values),
      range: axisRange(values),
    };
  }

  if (parameters.kind === "biquadratic") {
    const values = Array.isArray(parameters.coefficients)
      ? parameters.coefficients.map(Number) : [];
    const [a, b, c] = values;
    if (![a, b, c].every(Number.isFinite) || a === 0) return null;
    const tRoots = polynomialRoots(a, b, c);
    const acceptedT = tRoots.filter((value) => value >= -1e-9).map((value) => Math.max(0, value));
    const rejectedT = tRoots.filter((value) => value < -1e-9);
    const roots = uniqueNumbers(acceptedT.flatMap((value) => (
      Math.abs(value) <= 1e-9 ? [0] : [-Math.sqrt(value), Math.sqrt(value)]
    ))).sort((left, right) => left - right);
    const markers = roots.map((value) => ({
      value, excluded: false, label: `${symbol} = ${formatNumber(value)}`,
    }));
    return {
      kind: "biquadratic", symbol, markers, values: roots, excluded: false,
      rows: [
        ...acceptedT.map((value) => ({
          label: `t = ${formatNumber(value)}`,
          expression: `${symbol}² = ${formatNumber(value)}`,
          result: Math.abs(value) <= 1e-9
            ? `${symbol} = 0`
            : `${symbol} = ±${formatNumber(Math.sqrt(value))}`,
        })),
        ...rejectedT.map((value) => ({
          label: `Loại t = ${formatNumber(value)}`,
          expression: `${symbol}² không thể âm`,
          result: "Không sinh nghiệm thực",
          excluded: true,
        })),
      ],
      steps: [
        `Bước 1 · Đặt t = ${symbol}² với điều kiện t ≥ 0`,
        `Bước 2 · Giải ${formatPolynomial(a, b, c, "t")} = 0`,
        `Bước 3 · Nghiệm theo t: ${tRoots.length ? tRoots.map(formatNumber).join("; ") : "không có nghiệm thực"}; chỉ giữ t ≥ 0`,
        `Bước 4 · Trở lại ${symbol}: ${solutionStatement(symbol, roots)}`,
      ],
      statement: solutionStatement(symbol, roots),
      range: axisRange(roots),
    };
  }

  if (parameters.kind === "radical") {
    const [radicandCoefficient, radicandConstant] = (parameters.radicand || []).map(Number);
    const [rightCoefficient, rightConstant] = (parameters.right || []).map(Number);
    if (![radicandCoefficient, radicandConstant, rightCoefficient, rightConstant].every(Number.isFinite)) return null;
    // (cx + d)^2 = ax + b.
    const squared = [
      rightCoefficient ** 2,
      2 * rightCoefficient * rightConstant - radicandCoefficient,
      rightConstant ** 2 - radicandConstant,
    ];
    const candidates = polynomialRoots(...squared);
    const checked = candidates.map((value) => {
      const radicand = radicandCoefficient * value + radicandConstant;
      const right = rightCoefficient * value + rightConstant;
      const accepted = radicand >= -1e-8 && right >= -1e-8
        && Math.abs(Math.sqrt(Math.max(0, radicand)) - right) <= 1e-6;
      return { value, accepted, radicand, right };
    });
    const roots = checked.filter((item) => item.accepted).map((item) => item.value);
    const markers = checked.map((item) => ({
      value: item.value,
      excluded: !item.accepted,
      label: `${symbol} ${item.accepted ? "=" : "≠"} ${formatNumber(item.value)}`,
      reason: item.accepted ? "Thỏa đề gốc" : "Nghiệm ngoại lai",
    }));
    return {
      kind: "radical", symbol, markers, values: roots, excluded: false,
      rows: checked.map((item) => ({
        label: item.accepted ? "Nhận" : "Loại nghiệm ngoại lai",
        expression: `${symbol} = ${formatNumber(item.value)}`,
        result: item.accepted
          ? `√${formatNumber(Math.max(0, item.radicand))} = ${formatNumber(item.right)}`
          : "Không thỏa phương trình ban đầu",
        excluded: !item.accepted,
      })),
      steps: [
        `Bước 1 · Điều kiện: ${linearText(radicandCoefficient, radicandConstant, symbol)} ≥ 0 và ${linearText(rightCoefficient, rightConstant, symbol)} ≥ 0`,
        `Bước 2 · Bình phương: ${formatPolynomial(...squared, symbol)} = 0`,
        `Bước 3 · Nghiệm ứng viên: ${candidates.length ? candidates.map(formatNumber).join("; ") : "không có nghiệm thực"}`,
        `Bước 4 · Thử lại đề gốc: ${solutionStatement(symbol, roots)}`,
      ],
      statement: solutionStatement(symbol, roots),
      range: axisRange(markers.map((marker) => marker.value)),
    };
  }

  if (parameters.kind === "rational") {
    const [a, b, c] = (parameters.numerator_coefficients || []).map(Number);
    const denominators = Array.isArray(parameters.denominators)
      ? parameters.denominators.map((item) => item.map(Number)) : [];
    if (![a, b, c].every(Number.isFinite) || !denominators.length) return null;
    if (denominators.some(([coefficient, constant]) => !Number.isFinite(coefficient)
      || !Number.isFinite(constant) || coefficient === 0)) return null;
    const forbidden = uniqueNumbers(denominators.map(([coefficient, constant]) => -constant / coefficient));
    const candidates = polynomialRoots(a, b, c);
    const roots = candidates.filter((candidate) => (
      forbidden.every((value) => Math.abs(value - candidate) > 1e-7)
    ));
    const markers = [
      ...roots.map((value) => ({ value, excluded: false, label: `${symbol} = ${formatNumber(value)}` })),
      ...forbidden.map((value) => ({ value, excluded: true, label: `${symbol} ≠ ${formatNumber(value)}`, reason: "Làm mẫu bằng 0" })),
    ];
    return {
      kind: "rational", symbol, markers, values: roots, excluded: false,
      rows: [
        ...forbidden.map((value, index) => ({
          label: `Giá trị cấm ${index + 1}`,
          expression: `${symbol} = ${formatNumber(value)}`,
          result: "Loại khỏi miền xác định",
          excluded: true,
        })),
        ...candidates.map((value) => ({
          label: roots.some((root) => Math.abs(root - value) <= 1e-7) ? "Nghiệm nhận" : "Nghiệm bị loại",
          expression: `${symbol} = ${formatNumber(value)}`,
          result: roots.some((root) => Math.abs(root - value) <= 1e-7) ? "Mọi mẫu đều khác 0" : "Làm một mẫu bằng 0",
          excluded: !roots.some((root) => Math.abs(root - value) <= 1e-7),
        })),
      ],
      steps: [
        `Bước 1 · Điều kiện: ${forbidden.map((value) => `${symbol} ≠ ${formatNumber(value)}`).join("; ")}`,
        "Bước 2 · Nhân hai vế với mẫu thức chung trên miền xác định",
        `Bước 3 · Phương trình tử: ${formatPolynomial(a, b, c, symbol)} = 0`,
        `Bước 4 · Đối chiếu giá trị cấm: ${solutionStatement(symbol, roots)}`,
      ],
      statement: solutionStatement(symbol, roots),
      range: axisRange(markers.map((marker) => marker.value)),
    };
  }
  return null;
}

function polynomialRoots(a, b, c) {
  const tolerance = 1e-10;
  if (![a, b, c].every(Number.isFinite)) return [];
  if (Math.abs(a) <= tolerance) {
    return Math.abs(b) <= tolerance ? [] : [-c / b];
  }
  const delta = b * b - 4 * a * c;
  if (delta < -tolerance) return [];
  if (Math.abs(delta) <= tolerance) return [-b / (2 * a)];
  const root = Math.sqrt(Math.max(0, delta));
  // This form avoids losing the small root when |b| is large.
  const q = -0.5 * (b + (b >= 0 ? root : -root));
  return uniqueNumbers([q / a, c / q]).sort((left, right) => left - right);
}

function uniqueNumbers(values) {
  const normalized = values.map((value) => (Math.abs(value) <= 1e-12 ? 0 : value));
  return normalized.filter((value, index, items) => Number.isFinite(value)
    && items.findIndex((candidate) => Math.abs(candidate - value) <= 1e-8) === index);
}

function uniqueByValue(items) {
  return items.filter((item, index) => items.findIndex(
    (candidate) => Math.abs(candidate.value - item.value) <= 1e-8,
  ) === index);
}

function solutionStatement(symbol, values) {
  const unique = uniqueNumbers(values).sort((left, right) => left - right);
  return unique.length
    ? unique.map((value) => `${symbol} = ${formatNumber(value)}`).join("; ")
    : "S = ∅";
}

function linearText(coefficient, constant, symbol) {
  const coefficientText = Math.abs(coefficient) === 1
    ? (coefficient < 0 ? "−" : "")
    : formatNumber(coefficient);
  if (constant === 0) return `${coefficientText}${symbol}`;
  return `${coefficientText}${symbol} ${constant < 0 ? "−" : "+"} ${formatNumber(Math.abs(constant))}`;
}

function formatPolynomial(a, b, c, symbol) {
  const terms = [];
  const add = (coefficient, body) => {
    if (Math.abs(coefficient) <= 1e-10) return;
    const magnitude = Math.abs(coefficient);
    const printedMagnitude = body && magnitude === 1 ? "" : formatNumber(magnitude);
    const printed = `${printedMagnitude}${body}`;
    terms.push(terms.length
      ? `${coefficient < 0 ? "−" : "+"} ${printed}`
      : `${coefficient < 0 ? "−" : ""}${printed}`);
  };
  add(a, `${symbol}²`);
  add(b, symbol);
  add(c, "");
  return terms.join(" ") || "0";
}

function formatNumber(value) {
  return new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 3 }).format(value);
}

/** A tick range that always shows every marked point plus some breathing room. */
function axisRange(values) {
  const finite = values.filter(Number.isFinite);
  if (!finite.length) return { min: -4, max: 4 };
  const min = Math.min(0, ...finite);
  const max = Math.max(0, ...finite);
  const padding = Math.max(1, Math.ceil((max - min) * 0.25));
  return { min: Math.floor(min) - padding, max: Math.ceil(max) + padding };
}
