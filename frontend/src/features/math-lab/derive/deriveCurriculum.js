function knownEntries(world, bindings = {}) {
  const ids = Array.isArray(bindings.quantities)
    ? bindings.quantities
    : Object.keys(world?.values || {});
  return ids.map((id) => ({ id, ...world?.values?.[id] }))
    .filter((item) => Number.isFinite(Number(item.value)));
}

function decimalPlaces(value) {
  const text = String(value);
  if (/e/i.test(text)) return 0;
  return Math.min(3, (text.split(".")[1] || "").length);
}

const WHOLE_PLACES = [
  { power: 5, label: "Trăm nghìn" },
  { power: 4, label: "Chục nghìn" },
  { power: 3, label: "Nghìn" },
  { power: 2, label: "Trăm" },
  { power: 1, label: "Chục" },
  { power: 0, label: "Đơn vị" },
  { power: -1, label: "Phần mười" },
  { power: -2, label: "Phần trăm" },
  { power: -3, label: "Phần nghìn" },
];

export function derivePlaceValue(world, bindings = {}) {
  const entry = knownEntries(world, bindings)[0];
  if (!entry) return null;
  const value = Number(entry.value);
  if (!Number.isFinite(value) || Math.abs(value) >= 1_000_000) return null;
  const places = decimalPlaces(value);
  const [whole, fraction = ""] = Math.abs(value).toFixed(places).split(".");
  const firstPower = Math.max(0, whole.length - 1);
  const digits = `${whole}${fraction}`.split("").map(Number);
  const columns = digits.map((digit, index) => {
    const power = firstPower - index;
    const definition = WHOLE_PLACES.find((item) => item.power === power);
    return {
      digit,
      power,
      label: definition?.label || `10^${power}`,
      placeValue: digit * (10 ** power),
    };
  });
  return {
    value,
    label: entry.label || "Số đã cho",
    columns,
    expanded: columns.filter((item) => item.digit).map((item) => item.placeValue),
    decimalPlaces: places,
  };
}

const COLUMN_LABELS = ["Đơn vị", "Chục", "Trăm", "Nghìn", "Chục nghìn", "Trăm nghìn"];

export function deriveColumnAlgorithm(world, bindings = {}, problemType = "") {
  const entries = knownEntries(world, bindings).slice(0, 2);
  if (entries.length < 2) return null;
  const left = Number(entries[0].value);
  const right = Number(entries[1].value);
  const places = Math.max(decimalPlaces(left), decimalPlaces(right));
  const scale = 10 ** places;
  let top = Math.round(left * scale);
  let bottom = Math.round(right * scale);
  const subtract = /(subtract|subtraction|minus|trừ)/i.test(problemType);
  let sign = 1;
  if (subtract && top < bottom) {
    [top, bottom] = [bottom, top];
    sign = -1;
  }
  const resultInteger = subtract ? top - bottom : top + bottom;
  const width = Math.max(String(Math.abs(top)).length, String(Math.abs(bottom)).length, String(Math.abs(resultInteger)).length);
  const topDigits = String(Math.abs(top)).padStart(width, "0").split("").map(Number);
  const bottomDigits = String(Math.abs(bottom)).padStart(width, "0").split("").map(Number);
  const resultDigits = String(Math.abs(resultInteger)).padStart(width, "0").split("").map(Number);
  const steps = [];
  let carryOrBorrow = 0;
  for (let index = width - 1; index >= 0; index -= 1) {
    const fromRight = width - 1 - index;
    if (subtract) {
      let available = topDigits[index] - carryOrBorrow;
      const borrowed = available < bottomDigits[index] ? 1 : 0;
      if (borrowed) available += 10;
      steps.push({
        index,
        place: COLUMN_LABELS[fromRight - places] || (fromRight < places ? `Phần ${10 ** (places - fromRight)}` : `10^${fromRight - places}`),
        top: topDigits[index],
        bottom: bottomDigits[index],
        incoming: carryOrBorrow,
        regroup: borrowed,
        result: available - bottomDigits[index],
      });
      carryOrBorrow = borrowed;
    } else {
      const sum = topDigits[index] + bottomDigits[index] + carryOrBorrow;
      steps.push({
        index,
        place: COLUMN_LABELS[fromRight - places] || (fromRight < places ? `Phần ${10 ** (places - fromRight)}` : `10^${fromRight - places}`),
        top: topDigits[index],
        bottom: bottomDigits[index],
        incoming: carryOrBorrow,
        regroup: Math.floor(sum / 10),
        result: sum % 10,
      });
      carryOrBorrow = Math.floor(sum / 10);
    }
  }
  return {
    left,
    right,
    top,
    bottom,
    sign,
    subtract,
    decimalPlaces: places,
    scale,
    width,
    topDigits,
    bottomDigits,
    resultDigits,
    steps,
    result: sign * resultInteger / scale,
  };
}

const UNIT_GROUPS = {
  length: { units: ["km", "m", "dm", "cm", "mm"], base: { km: 1000, m: 1, dm: 0.1, cm: 0.01, mm: 0.001 } },
  mass: { units: ["kg", "g"], base: { kg: 1, g: 0.001 } },
  capacity: { units: ["liter", "ml"], base: { liter: 1, ml: 0.001 } },
  area: { units: ["m2", "cm2"], base: { m2: 1, cm2: 0.0001 } },
  volume: { units: ["m3", "cm3"], base: { m3: 1, cm3: 0.000001 } },
  time: { units: ["hour", "minute", "second"], base: { hour: 3600, minute: 60, second: 1 } },
};

export function deriveUnitScale(world, bindings = {}) {
  const entries = knownEntries(world, bindings);
  const source = entries[0];
  const unknownIds = Array.isArray(bindings.unknowns) ? bindings.unknowns : [];
  const targetEntry = unknownIds.map((id) => ({ id, ...world?.values?.[id] }))
    .find((item) => item.unit && item.unit !== "one");
  const targetUnit = targetEntry?.unit || entries[1]?.unit;
  if (!source || !targetUnit || source.unit === targetUnit) return null;
  const group = Object.entries(UNIT_GROUPS).find(([, item]) => source.unit in item.base && targetUnit in item.base);
  if (!group) return null;
  const [kind, definition] = group;
  const factor = definition.base[source.unit] / definition.base[targetUnit];
  return {
    kind,
    sourceValue: Number(source.value),
    sourceUnit: source.unit,
    targetUnit,
    factor,
    result: Number(source.value) * factor,
    units: definition.units,
    sourceIndex: definition.units.indexOf(source.unit),
    targetIndex: definition.units.indexOf(targetUnit),
  };
}

export function deriveDataChart(world, bindings = {}) {
  const frequencyIds = Array.isArray(bindings.frequency) ? bindings.frequency : [];
  const ids = frequencyIds.length ? frequencyIds : (bindings.quantities || []);
  const items = ids.map((id, index) => {
    const entry = world?.values?.[id];
    return {
      id,
      label: entry?.label || `Nhóm ${index + 1}`,
      value: Number(entry?.value),
    };
  }).filter((item) => Number.isFinite(item.value) && item.value >= 0);
  if (items.length < 2) return null;
  const total = items.reduce((sum, item) => sum + item.value, 0);
  const maximum = Math.max(...items.map((item) => item.value), 1);
  const winner = items.reduce((best, item) => item.value > best.value ? item : best, items[0]);
  const scaleId = Array.isArray(bindings.constant) ? bindings.constant[0] : null;
  const iconScale = Math.max(1, Number(world?.values?.[scaleId]?.value) || 1);
  return { items, total, maximum, winner, iconScale };
}

export function deriveQuadraticGraph(world, bindings = {}) {
  const coefficientIds = Array.isArray(bindings.coefficient) ? bindings.coefficient : [];
  const constantIds = Array.isArray(bindings.constant) ? bindings.constant : [];
  const a = Number(world?.values?.[coefficientIds[0]]?.value);
  const b = Number(world?.values?.[coefficientIds[1]]?.value ?? 0);
  const c = Number(world?.values?.[constantIds[0]]?.value ?? 0);
  if (![a, b, c].every(Number.isFinite) || a === 0) return null;
  const vertexX = -b / (2 * a);
  const vertexY = a * vertexX ** 2 + b * vertexX + c;
  const discriminant = b ** 2 - 4 * a * c;
  const roots = discriminant < 0 ? [] : [
    (-b - Math.sqrt(discriminant)) / (2 * a),
    (-b + Math.sqrt(discriminant)) / (2 * a),
  ].filter((value, index, values) => index === 0 || Math.abs(value - values[0]) > 1e-9);
  // Keep the roots and the vertex large enough to read. A fixed ±5 window
  // made steep parabolas look like a flat row of dots near Ox (the curve's
  // far-away arms dominated the y scale).
  const rootDistance = roots.length
    ? Math.max(...roots.map((root) => Math.abs(root - vertexX)))
    : 0;
  const halfSpan = roots.length ? Math.max(2, rootDistance * 1.25 + 0.75) : 3;
  const xMin = Math.floor(vertexX - halfSpan);
  const xMax = Math.ceil(vertexX + halfSpan);
  const points = Array.from({ length: 81 }, (_, index) => {
    const x = xMin + (index / 80) * (xMax - xMin);
    return { x, y: a * x ** 2 + b * x + c };
  });
  const yValues = [0, vertexY, ...roots.map(() => 0), ...points.map((point) => point.y)];
  const yMin = Math.min(...yValues);
  const yMax = Math.max(...yValues);
  return { a, b, c, vertexX, vertexY, discriminant, roots, points, xMin, xMax, yMin, yMax };
}

function uniqueSorted(values, tolerance = 1e-8) {
  return [...values]
    .filter(Number.isFinite)
    .sort((left, right) => left - right)
    .filter((value, index, items) => index === 0 || Math.abs(value - items[index - 1]) > tolerance);
}

/** Real roots of a cubic through the depressed-cubic formula. */
function solveCubicReal(a, b, c, d) {
  const normalizedB = b / a;
  const normalizedC = c / a;
  const normalizedD = d / a;
  const p = normalizedC - (normalizedB ** 2) / 3;
  const q = (2 * normalizedB ** 3) / 27 - (normalizedB * normalizedC) / 3 + normalizedD;
  const discriminant = (q / 2) ** 2 + (p / 3) ** 3;
  const tolerance = 1e-12 * Math.max(1, Math.abs(q) ** 2, Math.abs(p) ** 3);
  const shift = normalizedB / 3;

  if (discriminant > tolerance) {
    const squareRoot = Math.sqrt(discriminant);
    return [Math.cbrt(-q / 2 + squareRoot) + Math.cbrt(-q / 2 - squareRoot) - shift];
  }
  if (Math.abs(discriminant) <= tolerance) {
    const u = Math.cbrt(-q / 2);
    return uniqueSorted([2 * u - shift, -u - shift]);
  }
  const radius = 2 * Math.sqrt(-p / 3);
  const cosine = Math.max(-1, Math.min(1, (-q / 2) / Math.sqrt(-((p / 3) ** 3))));
  const angle = Math.acos(cosine);
  return uniqueSorted([0, 1, 2].map((index) => (
    radius * Math.cos((angle + 2 * Math.PI * index) / 3) - shift
  )));
}

/** One-variable cubic equation reduced to a graph whose Ox crossings are roots. */
export function deriveCubicGraph(world, bindings = {}) {
  const coefficientIds = Array.isArray(bindings.coefficient) ? bindings.coefficient : [];
  const constantIds = Array.isArray(bindings.constant) ? bindings.constant : [];
  const a = Number(world?.values?.[coefficientIds[0]]?.value);
  const b = Number(world?.values?.[coefficientIds[1]]?.value ?? 0);
  const c = Number(world?.values?.[coefficientIds[2]]?.value ?? 0);
  const d = Number(world?.values?.[constantIds[0]]?.value ?? 0);
  if (![a, b, c, d].every(Number.isFinite) || a === 0) return null;

  const evaluate = (x) => ((a * x + b) * x + c) * x + d;
  const roots = solveCubicReal(a, b, c, d);
  const derivativeDiscriminant = (2 * b) ** 2 - 4 * (3 * a) * c;
  const turningPoints = derivativeDiscriminant < 0
    ? []
    : uniqueSorted([
      (-2 * b - Math.sqrt(Math.max(0, derivativeDiscriminant))) / (6 * a),
      (-2 * b + Math.sqrt(Math.max(0, derivativeDiscriminant))) / (6 * a),
    ]);
  const anchors = [...roots, ...turningPoints, -3, 3];
  let xMin = Math.floor(Math.min(...anchors) - 1);
  let xMax = Math.ceil(Math.max(...anchors) + 1);
  if (xMax - xMin < 8) {
    const center = (xMin + xMax) / 2;
    xMin = Math.floor(center - 4);
    xMax = Math.ceil(center + 4);
  }
  const points = Array.from({ length: 161 }, (_, index) => {
    const x = xMin + (index / 160) * (xMax - xMin);
    return { x, y: evaluate(x) };
  });
  const yValues = [0, ...turningPoints.map(evaluate), ...points.map((point) => point.y)];
  const yMin = Math.min(...yValues);
  const yMax = Math.max(...yValues);
  const firstRoot = roots[0];
  const quotient = Number.isFinite(firstRoot) ? [
    a,
    b + a * firstRoot,
    c + (b + a * firstRoot) * firstRoot,
  ] : null;
  return {
    a, b, c, d, roots, turningPoints, points, xMin, xMax, yMin, yMax,
    evaluate,
    quotient,
    quotientRemainder: quotient ? d + quotient[2] * firstRoot : null,
  };
}

export function deriveNumberComparison(world, bindings = {}, problemType = "") {
  const entries = knownEntries(world, bindings);
  const scaleId = Array.isArray(bindings.constant) ? bindings.constant[0] : null;
  const roundingScale = Number(world?.values?.[scaleId]?.value);
  const rounding = /round/i.test(problemType) && Number.isFinite(roundingScale) && roundingScale > 0;
  const numeric = entries.filter((item) => item.id !== scaleId);
  if (!numeric.length) return null;
  if (rounding) {
    const value = Number(numeric[0].value);
    const lower = Math.floor(value / roundingScale) * roundingScale;
    const upper = lower + roundingScale;
    const midpoint = lower + roundingScale / 2;
    return {
      mode: "rounding",
      items: [{ ...numeric[0], value }],
      lower,
      upper,
      midpoint,
      result: value < midpoint ? lower : upper,
      minimum: lower,
      maximum: upper,
      scale: roundingScale,
    };
  }
  if (numeric.length < 2) return null;
  const items = numeric.map((item) => ({ ...item, value: Number(item.value) }));
  const sorted = [...items].sort((left, right) => left.value - right.value);
  const rawMin = sorted[0].value;
  const rawMax = sorted[sorted.length - 1].value;
  const padding = Math.max(1, (rawMax - rawMin) * 0.12);
  return { mode: "ordering", items, sorted, minimum: rawMin - padding, maximum: rawMax + padding };
}

export function deriveProbabilityExperiment(world, bindings = {}) {
  const successId = Array.isArray(bindings.frequency) ? bindings.frequency[0] : null;
  const totalId = Array.isArray(bindings.count) ? bindings.count[0] : null;
  const success = Number(world?.values?.[successId]?.value);
  const total = Number(world?.values?.[totalId]?.value);
  if (!Number.isInteger(success) || !Number.isInteger(total) || total <= 0 || success < 0 || success > total || total > 200) return null;
  const outcomes = Array.from({ length: total }, (_, index) => (
    Math.floor(((index + 1) * success) / total) > Math.floor((index * success) / total)
  ));
  return { success, total, outcomes, probability: success / total };
}

export function deriveSolidRevolution(world, bindings = {}, problemType = "") {
  const radiusId = Array.isArray(bindings.radius) ? bindings.radius[0] : null;
  const heightId = Array.isArray(bindings.height) ? bindings.height[0] : null;
  const radius = Number(world?.values?.[radiusId]?.value);
  const height = Number(world?.values?.[heightId]?.value);
  const kind = /sphere/i.test(problemType) ? "sphere" : /cone/i.test(problemType) ? "cone" : /cylinder/i.test(problemType) ? "cylinder" : null;
  if (!kind || !Number.isFinite(radius) || radius <= 0 || (kind !== "sphere" && (!Number.isFinite(height) || height <= 0))) return null;
  const volume = kind === "sphere" ? (4 / 3) * Math.PI * radius ** 3 : kind === "cone" ? (Math.PI * radius ** 2 * height) / 3 : Math.PI * radius ** 2 * height;
  return { kind, radius, height: kind === "sphere" ? radius * 2 : height, volume, unit: world?.values?.[radiusId]?.unit || "cm" };
}

export function derivePercentModel(world, bindings = {}) {
  const partId = Array.isArray(bindings.count_change) ? bindings.count_change[0] : null;
  const wholeId = Array.isArray(bindings.count_initial) ? bindings.count_initial[0] : null;
  const percentId = Array.isArray(bindings.probability) ? bindings.probability[0] : null;
  let part = Number(world?.values?.[partId]?.value);
  let whole = Number(world?.values?.[wholeId]?.value);
  let percent = Number(world?.values?.[percentId]?.value);
  if (Number.isFinite(part) && Number.isFinite(whole) && whole > 0) percent = (part / whole) * 100;
  else if (Number.isFinite(percent) && Number.isFinite(whole) && whole > 0) part = (percent / 100) * whole;
  else if (Number.isFinite(part) && Number.isFinite(percent) && percent > 0) whole = (part * 100) / percent;
  if (![part, whole, percent].every(Number.isFinite) || whole <= 0 || percent < 0 || percent > 100) return null;
  return { part, whole, percent, decimal: percent / 100, filledCells: Math.round(percent) };
}

export function deriveReverseDiscountModel(world, bindings = {}) {
  const priceIds = Array.isArray(bindings.count_initial) ? bindings.count_initial : [];
  const discountIds = Array.isArray(bindings.probability) ? bindings.probability : [];
  const totalId = Array.isArray(bindings.total) ? bindings.total[0] : null;
  const prices = priceIds.slice(0, 2).map((id) => Number(world?.values?.[id]?.value));
  const discounts = discountIds.slice(0, 3).map((id) => Number(world?.values?.[id]?.value));
  const paidTotal = Number(world?.values?.[totalId]?.value);
  if (
    prices.length !== 2
    || discounts.length !== 3
    || ![...prices, ...discounts, paidTotal].every(Number.isFinite)
    || prices.some((value) => value <= 0)
    || discounts.some((value) => value < 0 || value >= 100)
    || paidTotal <= 0
  ) return null;

  const paidFirst = prices[0] * (1 - discounts[0] / 100);
  const paidSecond = prices[1] * (1 - discounts[1] / 100);
  const knownPaid = paidFirst + paidSecond;
  const paidThird = paidTotal - knownPaid;
  const thirdPaidPercent = 100 - discounts[2];
  const originalThird = paidThird / (thirdPaidPercent / 100);
  if (paidThird <= 0 || !Number.isFinite(originalThird) || originalThird <= 0) return null;

  return {
    originalFirst: prices[0],
    originalSecond: prices[1],
    discountFirst: discounts[0],
    discountSecond: discounts[1],
    discountThird: discounts[2],
    paidFirst,
    paidSecond,
    knownPaid,
    paidTotal,
    paidThird,
    thirdPaidPercent,
    originalThird,
  };
}

export function derivePolynomialModel(world, bindings = {}, problemType = "") {
  const coefficientIds = Array.isArray(bindings.coefficient) ? bindings.coefficient : [];
  const exponentIds = Array.isArray(bindings.exponent) ? bindings.exponent : [];
  const coefficients = coefficientIds.map((id) => Number(world?.values?.[id]?.value));
  const exponents = exponentIds.map((id) => Number(world?.values?.[id]?.value));
  if (!coefficients.length || coefficients.length !== exponents.length || ![...coefficients, ...exponents].every(Number.isFinite)) return null;
  const splitId = Array.isArray(bindings.count) ? bindings.count[0] : null;
  const split = Number(world?.values?.[splitId]?.value);
  const subtract = /subtract/i.test(problemType);
  const firstCount = Number.isInteger(split) && split > 0 && split < coefficients.length ? split : coefficients.length;
  const first = coefficients.slice(0, firstCount).map((coefficient, index) => ({ coefficient, exponent: exponents[index] }));
  const second = coefficients.slice(firstCount).map((coefficient, index) => ({ coefficient, exponent: exponents[firstCount + index] }));
  const combined = new Map();
  for (const term of first) combined.set(term.exponent, (combined.get(term.exponent) || 0) + term.coefficient);
  for (const term of second) combined.set(term.exponent, (combined.get(term.exponent) || 0) + (subtract ? -term.coefficient : term.coefficient));
  const result = [...combined].map(([exponent, coefficient]) => ({ exponent, coefficient })).filter((item) => item.coefficient !== 0).sort((a, b) => b.exponent - a.exponent);
  const xId = Array.isArray(bindings.x_value) ? bindings.x_value[0] : null;
  const x = Number(world?.values?.[xId]?.value);
  const evaluated = Number.isFinite(x) ? result.reduce((sum, term) => sum + term.coefficient * x ** term.exponent, 0) : null;
  return { first, second, result, operation: second.length ? (subtract ? "subtract" : "add") : "reorder", x: Number.isFinite(x) ? x : null, evaluated };
}

export function derivePartWhole(world, bindings = {}) {
  const initialId = Array.isArray(bindings.count_initial) ? bindings.count_initial[0] : null;
  const changeId = Array.isArray(bindings.count_change) ? bindings.count_change[0] : null;
  const totalId = Array.isArray(bindings.total) ? bindings.total[0] : null;
  let first = Number(world?.values?.[initialId]?.value);
  let second = Number(world?.values?.[changeId]?.value);
  let total = Number(world?.values?.[totalId]?.value);
  const missing = Array.isArray(bindings.unknown_count_initial) ? "first" : Array.isArray(bindings.unknown_count_change) ? "second" : "total";
  if (missing === "first" && Number.isFinite(total) && Number.isFinite(second)) first = total - second;
  else if (missing === "second" && Number.isFinite(total) && Number.isFinite(first)) second = total - first;
  else if (missing === "total" && Number.isFinite(first) && Number.isFinite(second)) total = first + second;
  if (![first, second, total].every(Number.isFinite) || first < 0 || second < 0 || Math.abs(first + second - total) > 1e-9) return null;
  return { first, second, total, missing };
}
