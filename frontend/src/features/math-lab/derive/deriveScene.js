/**
 * The maths behind a scene, derived from one number.
 *
 * A scene arrives from Master carrying the quantities the problem gave —
 * distance, speed, a start time. It does not carry where Lan is right now,
 * because that is not a fact of the problem, it is a position along it.
 *
 * So playback owns exactly one value, `progress` in [0, 1], and every
 * representation computes its own reading from it. That is what keeps the
 * path, the clock and the timeline from ever disagreeing: there is nothing
 * for them to disagree about. A renderer that kept its own timer would drift
 * the moment anyone paused, stepped or dragged.
 *
 * Nothing here is hard-coded to a particular problem. The arrival time is
 * computed from distance and speed; it is never written down.
 */

/** Canonical value of a world entry, falling back to the given one. */
export function canonical(world, id) {
  const entry = world?.values?.[id];
  if (!entry) return null;
  const value = entry.canonical_value != null ? entry.canonical_value : entry.value;
  const unit = entry.canonical_unit || entry.unit || "one";
  return Number.isFinite(Number(value)) ? { value: Number(value), unit } : null;
}

export function rawValue(world, id) {
  const entry = world?.values?.[id];
  return entry && Number.isFinite(Number(entry.value)) ? Number(entry.value) : null;
}

export function boundId(bindings, role, fallbackIds = []) {
  const candidates = bindings?.[role];
  if (Array.isArray(candidates) && candidates.length) return candidates[0];
  return fallbackIds[0] || null;
}

function canonicalRole(world, bindings, role, fallbackIds) {
  const bound = boundId(bindings, role, []);
  if (bound) return canonical(world, bound);
  for (const id of fallbackIds) {
    const value = canonical(world, id);
    if (value) return value;
  }
  return null;
}

function rawRole(world, bindings, role, fallbackIds) {
  const bound = boundId(bindings, role, []);
  if (bound) return rawValue(world, bound);
  for (const id of fallbackIds) {
    const value = rawValue(world, id);
    if (value != null) return value;
  }
  return null;
}

/** "06:45" → minutes since midnight. Returns null for anything else. */
export function parseClock(text) {
  if (typeof text !== "string") return null;
  const match = /^(\d{1,2}):(\d{2})$/.exec(text.trim());
  if (!match) return null;
  const hours = Number(match[1]);
  const minutes = Number(match[2]);
  if (hours > 23 || minutes > 59) return null;
  return hours * 60 + minutes;
}

/** Minutes since midnight → "07:03", wrapping past midnight. */
export function formatClock(totalMinutes) {
  const wrapped = ((Math.round(totalMinutes) % 1440) + 1440) % 1440;
  const hours = Math.floor(wrapped / 60);
  const minutes = wrapped % 60;
  return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}`;
}

/**
 * A journey, read off the world at a given progress.
 *
 * Distance is canonical metres and speed canonical metres per second, so the
 * duration falls out of `t = s / v` without any unit special-casing here —
 * `units.py` already did that work on the way in.
 */
export function deriveMotion(world, progress = 0, bindings = {}) {
  const distance = canonicalRole(world, bindings, "distance", ["distance"]);
  const speed = canonicalRole(world, bindings, "speed", ["speed"]);
  if (!distance || !speed || speed.value <= 0) return null;

  const totalSeconds = distance.value / speed.value;
  const totalMinutes = totalSeconds / 60;
  const clamped = Math.min(Math.max(Number(progress) || 0, 0), 1);

  const startId = boundId(bindings, "start_time", ["start_time"]);
  const startMinutes = parseClock(world?.values?.[startId]?.value);
  const elapsedMinutes = totalMinutes * clamped;

  return {
    totalDistance: distance.value,
    totalMinutes,
    speed: speed.value,
    progress: clamped,
    distanceTravelled: distance.value * clamped,
    distanceRemaining: distance.value * (1 - clamped),
    elapsedMinutes,
    startMinutes,
    currentMinutes: startMinutes == null ? null : startMinutes + elapsedMinutes,
    startLabel: startMinutes == null ? null : formatClock(startMinutes),
    arrivalLabel: startMinutes == null ? null : formatClock(startMinutes + totalMinutes),
    currentLabel: startMinutes == null ? null : formatClock(startMinutes + elapsedMinutes),
  };
}

/**
 * A fraction, and the equivalent one it is being rewritten as.
 *
 * `progress` walks the rewrite: at 0 the bar is cut into the original number
 * of parts, at 1 into the target number. The shaded amount never changes,
 * which is the whole point a learner is meant to see.
 */
export function deriveFraction(world, progress = 0, bindings = {}) {
  const numerator = rawRole(world, bindings, "numerator", ["numerator"]);
  const denominator = rawRole(world, bindings, "denominator", ["denominator"]);
  if (numerator == null || denominator == null || denominator <= 0) return null;

  const targetDenominator = rawRole(world, bindings, "target_denominator", ["target_denominator"]);
  const clamped = Math.min(Math.max(Number(progress) || 0, 0), 1);
  const rewriting = targetDenominator != null && targetDenominator !== denominator;
  // The rewrite happens as a step, not as a slow morph: a bar cut into 3.4
  // pieces would be a lie.
  const parts = rewriting && clamped >= 0.5 ? targetDenominator : denominator;
  const factor = parts / denominator;

  return {
    numerator,
    denominator,
    parts,
    shaded: numerator * factor,
    value: numerator / denominator,
    rewriting,
    rewritten: rewriting && clamped >= 0.5,
    addend: rawRole(world, bindings, "addend_numerator", ["addend_numerator"]),
    addendDenominator: rawRole(world, bindings, "addend_denominator", ["addend_denominator"]),
  };
}

function greatestCommonDivisor(left, right) {
  let a = Math.abs(Math.trunc(left));
  let b = Math.abs(Math.trunc(right));
  while (b) [a, b] = [b, a % b];
  return a || 1;
}

/** Two explicit fractions reduced independently before they are compared. */
export function deriveFractionComparison(world, bindings = {}) {
  const numeratorIds = bindings?.numerator;
  const denominatorIds = bindings?.denominator;
  if (!Array.isArray(numeratorIds) || !Array.isArray(denominatorIds)
    || numeratorIds.length < 2 || denominatorIds.length < 2) return null;

  const pair = (index) => {
    const numerator = rawValue(world, numeratorIds[index]);
    const denominator = rawValue(world, denominatorIds[index]);
    if (numerator == null || denominator == null || denominator <= 0
      || !Number.isInteger(numerator) || !Number.isInteger(denominator)) return null;
    const divisor = greatestCommonDivisor(numerator, denominator);
    return {
      numerator,
      denominator,
      divisor,
      reducedNumerator: numerator / divisor,
      reducedDenominator: denominator / divisor,
      ratio: numerator / denominator,
    };
  };

  const left = pair(0);
  const right = pair(1);
  if (!left || !right) return null;
  return {
    left,
    right,
    equal: left.numerator * right.denominator === right.numerator * left.denominator,
  };
}

/** Three time-bounded production amounts accumulated, then shared per worker. */
export function deriveAveragePerPerson(world, bindings = {}) {
  const workerId = bindings?.count_initial?.[0];
  const workers = rawValue(world, workerId);
  const changeIds = Array.isArray(bindings?.count_change) ? bindings.count_change : [];
  let monthIds = changeIds.filter((id) => {
    const label = String(world?.values?.[id]?.label || "").toLocaleLowerCase("vi");
    return label.includes("tháng") || label.includes("month");
  });
  if (monthIds.length < 3) monthIds = changeIds.slice(0, 3);
  const monthly = monthIds.slice(0, 3).map((id, index) => ({
    id,
    label: `Tháng ${index + 1}`,
    value: rawValue(world, id),
  }));
  if (!Number.isInteger(workers) || workers <= 0
    || monthly.length !== 3 || monthly.some((item) => item.value == null || item.value < 0)) {
    return null;
  }
  let cumulative = 0;
  const milestones = monthly.map((item) => {
    cumulative += item.value;
    return { ...item, cumulative };
  });
  return {
    workers,
    monthly,
    milestones,
    total: cumulative,
    perPerson: cumulative / workers,
    maximumMonth: Math.max(...monthly.map((item) => item.value), 1),
  };
}

/**
 * One fixed job redistributed after the team size changes.
 *
 * Every tile represents one worker-day. The renderer may rearrange the same
 * tile count from `initialWorkers × plannedDays` into `newWorkers × newDays`,
 * but it must never create or remove work while animating the explanation.
 */
export function deriveVariablePeopleWorkRate(world, bindings = {}) {
  const initialWorkers = rawValue(world, bindings?.count_initial?.[0]);
  const plannedDays = rawValue(world, bindings?.duration?.[0]);
  const workerChange = rawValue(world, bindings?.count_change?.[0]);
  const newWorkers = initialWorkers + workerChange;
  const totalWork = initialWorkers * plannedDays;
  const newDays = totalWork / newWorkers;

  if (![initialWorkers, plannedDays, workerChange, newWorkers, totalWork, newDays].every(Number.isFinite)
    || !Number.isInteger(initialWorkers) || !Number.isInteger(plannedDays)
    || !Number.isInteger(workerChange) || initialWorkers <= 0 || plannedDays <= 0
    || newWorkers <= 0 || initialWorkers > 30 || newWorkers > 30
    || totalWork > 240) return null;

  return {
    initialWorkers,
    plannedDays,
    workerChange,
    newWorkers,
    totalWork,
    newDays,
  };
}

/**
 * A constant-rate journey represented as equal time blocks.
 *
 * Only the known time, known distance and target time live in the world. The
 * per-unit distance and requested distance are derived here so an AI answer
 * can never be silently accepted as a supplied fact.
 */
export function deriveDirectProportionDistanceTime(world, bindings = {}) {
  const durationIds = Array.isArray(bindings?.duration) ? bindings.duration : [];
  const distanceId = bindings?.distance?.[0];
  if (durationIds.length < 2 || !distanceId) return null;
  const knownDuration = rawValue(world, durationIds[0]);
  const targetDuration = rawValue(world, durationIds[1]);
  const knownDistance = rawValue(world, distanceId);
  const unitDistance = knownDistance / knownDuration;
  const targetDistance = unitDistance * targetDuration;
  if (![knownDuration, targetDuration, knownDistance, unitDistance, targetDistance]
    .every(Number.isFinite)
    || knownDuration <= 0 || targetDuration <= 0 || knownDistance <= 0
    || knownDuration > 10_000 || targetDuration > 10_000 || knownDistance > 10_000_000) {
    return null;
  }
  const knownDurationUnit = world?.values?.[durationIds[0]]?.unit || "hour";
  const targetDurationUnit = world?.values?.[durationIds[1]]?.unit || knownDurationUnit;
  if (knownDurationUnit !== targetDurationUnit) return null;
  return {
    knownDuration,
    targetDuration,
    knownDistance,
    unitDistance,
    targetDistance,
    durationUnit: knownDurationUnit,
    distanceUnit: world?.values?.[distanceId]?.unit || "km",
    segmented: Number.isInteger(knownDuration)
      && Number.isInteger(targetDuration)
      && Math.max(knownDuration, targetDuration) <= 24,
  };
}

/** Known total corresponds to denominator parts; derive one part and numerator parts. */
export function deriveRatioShare(world, bindings = {}) {
  const knownId = bindings?.count_initial?.[0] || bindings?.count?.[0];
  const numeratorId = bindings?.numerator?.[0];
  const denominatorId = bindings?.denominator?.[0];
  const known = rawValue(world, knownId);
  const numerator = rawValue(world, numeratorId);
  const denominator = rawValue(world, denominatorId);
  if (known == null || known < 0 || !Number.isInteger(numerator)
    || !Number.isInteger(denominator) || numerator <= 0 || denominator <= 0
    || numerator > 40 || denominator > 40) return null;
  return {
    known,
    numerator,
    denominator,
    onePart: known / denominator,
    target: (known / denominator) * numerator,
  };
}

export function deriveRatioTotal(world, bindings = {}) {
  const totalId = bindings?.total?.[0] || bindings?.count?.[0];
  const numeratorId = bindings?.numerator?.[0];
  const denominatorId = bindings?.denominator?.[0];
  const total = rawValue(world, totalId);
  const firstParts = rawValue(world, numeratorId);
  const secondParts = rawValue(world, denominatorId);
  const allParts = firstParts + secondParts;
  if (!Number.isFinite(total) || total <= 0 || !Number.isInteger(firstParts) || !Number.isInteger(secondParts)
    || firstParts <= 0 || secondParts <= 0 || allParts > 40 || total % allParts !== 0) return null;
  const onePart = total / allParts;
  return { total, firstParts, secondParts, allParts, onePart, first: firstParts * onePart, second: secondParts * onePart };
}

/**
 * A total is spent over three days: day one is a fraction of the total, day
 * two is a fraction of what remains, and the question compares day three with
 * day one. No answer is stored in the semantic model; all values below are
 * deterministically derived from the four printed fraction operands.
 */
export function deriveSequentialRemainderRatio(world, bindings = {}) {
  const totalId = bindings?.mass?.[0]
    || bindings?.count_initial?.[0]
    || bindings?.total?.[0];
  const firstNumerator = rawValue(world, bindings?.numerator?.[0]);
  const firstDenominator = rawValue(world, bindings?.denominator?.[0]);
  const secondNumerator = rawValue(world, bindings?.addend_numerator?.[0]);
  const secondDenominator = rawValue(world, bindings?.addend_denominator?.[0]);
  const total = rawValue(world, totalId);
  if (!Number.isFinite(total) || total <= 0
    || ![firstNumerator, firstDenominator, secondNumerator, secondDenominator]
      .every((value) => Number.isInteger(value) && value > 0)
    || firstNumerator >= firstDenominator
    || secondNumerator >= secondDenominator
    || firstDenominator > 40
    || secondDenominator > 40) return null;

  const firstDay = total * firstNumerator / firstDenominator;
  const remainingAfterFirst = total - firstDay;
  const secondDay = remainingAfterFirst * secondNumerator / secondDenominator;
  const thirdDay = remainingAfterFirst - secondDay;
  if (![firstDay, remainingAfterFirst, secondDay, thirdDay]
    .every((value) => Number.isInteger(value) && value >= 0)
    || firstDay === 0 || thirdDay === 0) return null;
  const divisor = integerGcd(thirdDay, firstDay);
  return {
    total,
    unit: world?.values?.[totalId]?.unit || "kg",
    firstNumerator,
    firstDenominator,
    firstUnit: total / firstDenominator,
    firstDay,
    remainingAfterFirst,
    secondNumerator,
    secondDenominator,
    secondUnit: remainingAfterFirst / secondDenominator,
    secondDay,
    thirdDay,
    divisor,
    ratioNumerator: thirdDay / divisor,
    ratioDenominator: firstDay / divisor,
  };
}

/**
 * General quantity variant of the same changing-remainder operation. Multiple
 * total components (for example 10 dam² and 80 m²) are summed in their
 * canonical unit before either fraction is applied. The semantic model still
 * contains no requested answer.
 */
export function deriveSequentialRemainderQuantity(world, bindings = {}) {
  const totalIds = [
    ...(bindings?.area || []),
    ...(bindings?.mass || []),
    ...(bindings?.count_initial || []),
    ...(bindings?.total || []),
  ];
  const components = totalIds.map((id) => {
    const resolved = canonical(world, id);
    return resolved ? {
      id,
      value: resolved.value,
      unit: resolved.unit,
      label: world?.values?.[id]?.label || "Thành phần ban đầu",
    } : null;
  }).filter(Boolean);
  if (!components.length || new Set(components.map((item) => item.unit)).size !== 1) return null;

  const firstNumerator = rawValue(world, bindings?.numerator?.[0]);
  const firstDenominator = rawValue(world, bindings?.denominator?.[0]);
  const secondNumerator = rawValue(world, bindings?.addend_numerator?.[0]);
  const secondDenominator = rawValue(world, bindings?.addend_denominator?.[0]);
  const total = components.reduce((sum, item) => sum + item.value, 0);
  if (!Number.isFinite(total) || total <= 0
    || ![firstNumerator, firstDenominator, secondNumerator, secondDenominator]
      .every((value) => Number.isInteger(value) && value > 0)
    || firstNumerator >= firstDenominator
    || secondNumerator >= secondDenominator
    || firstDenominator > 40
    || secondDenominator > 40) return null;

  const firstAllocation = total * firstNumerator / firstDenominator;
  const remainingAfterFirst = total - firstAllocation;
  const secondAllocation = remainingAfterFirst * secondNumerator / secondDenominator;
  const finalRemainder = remainingAfterFirst - secondAllocation;
  if (![firstAllocation, remainingAfterFirst, secondAllocation, finalRemainder]
    .every((value) => Number.isFinite(value) && value >= 0)) return null;

  return {
    components,
    total,
    unit: components[0].unit,
    firstNumerator,
    firstDenominator,
    firstUnit: total / firstDenominator,
    firstAllocation,
    remainingAfterFirst,
    secondNumerator,
    secondDenominator,
    secondUnit: remainingAfterFirst / secondDenominator,
    secondAllocation,
    finalRemainder,
  };
}

/** Where a marker sits on a number line, and the jumps that got it there. */
export function deriveNumberLine(world, progress = 0, problemType = null, bindings = {}) {
  const start = rawRole(world, bindings, "count_initial", ["left", "start"]);
  const change = rawRole(world, bindings, "count_change", ["right", "change"]);
  if (start == null || change == null) return null;
  const subtract = world?.values?.operation?.value === "subtract"
    || /subtraction/i.test(String(problemType || ""));
  const operation = subtract ? -1 : 1;
  const clamped = Math.min(Math.max(Number(progress) || 0, 0), 1);
  const end = start + change * operation;

  const minimum = rawValue(world, "line_min") ?? Math.min(0, start, end);
  const maximum = rawValue(world, "line_max") ?? Math.max(10, start, end);
  const absoluteChange = Math.abs(change);
  const jumpSize = absoluteChange > 20 ? 10 : absoluteChange > 10 ? 5 : 1;
  const jumps = [];
  let covered = 0;
  while (covered < absoluteChange - 1e-9) {
    const amount = Math.min(jumpSize, absoluteChange - covered);
    jumps.push({
      from: start + operation * covered,
      to: start + operation * (covered + amount),
      done: clamped >= (covered + amount) / Math.max(absoluteChange, 1),
      amount,
    });
    covered += amount;
  }

  return {
    minimum,
    maximum,
    start,
    end,
    change,
    operation,
    current: start + change * operation * clamped,
    // Small changes move one unit at a time; larger two-digit changes expose
    // tens first so the line stays readable instead of drawing 38 tiny arcs.
    jumps,
  };
}

/** Two groups of counters that merge, or one group that loses some. */
export function deriveObjectGroup(world, progress = 0, problemType = null, bindings = {}) {
  const left = rawRole(world, bindings, "count_initial", ["left"]);
  const right = rawRole(world, bindings, "count_change", ["right"]);
  if (left == null || right == null) return null;
  const subtract = world?.values?.operation?.value === "subtract"
    || /subtraction/i.test(String(problemType || ""));
  const clamped = Math.min(Math.max(Number(progress) || 0, 0), 1);

  return {
    left,
    right,
    subtract,
    total: subtract ? left - right : left + right,
    // How many of the second group have moved across (or been taken away).
    moved: Math.round(right * clamped),
    merged: clamped >= 1,
  };
}

/** A right triangle or rectangle described by explicit side lengths. */
export function deriveGeometry2d(world, bindings = {}, problemType = "") {
  if (/angle_bisector/i.test(problemType)) {
    const angleId = boundId(bindings, "angle", ["angle"]);
    const totalAngle = rawValue(world, angleId);
    if (!Number.isFinite(totalAngle) || totalAngle <= 0 || totalAngle >= 180) return null;
    return {
      kind: "angle_bisector",
      totalAngle,
      halfAngle: totalAngle / 2,
      unit: world?.values?.[angleId]?.unit || "degree",
    };
  }
  if (/ray_segment_midpoint/i.test(problemType)) {
    const lengthId = boundId(bindings, "length", ["length"]);
    const length = rawValue(world, lengthId);
    if (!Number.isFinite(length) || length <= 0) return null;
    return { kind: "segment", length, half: length / 2, unit: world?.values?.[lengthId]?.unit || "cm" };
  }
  if (/circle_radius_diameter/i.test(problemType)) {
    const radiusId = boundId(bindings, "radius", ["radius"]);
    const diameterId = boundId(bindings, "diameter", ["diameter"]);
    const explicitRadius = rawValue(world, radiusId);
    const explicitDiameter = rawValue(world, diameterId);
    const radius = explicitRadius ?? (explicitDiameter != null ? explicitDiameter / 2 : null);
    if (!Number.isFinite(radius) || radius <= 0) return null;
    return {
      kind: "circle",
      radius,
      diameter: explicitDiameter ?? radius * 2,
      circumference: 2 * Math.PI * radius,
      area: Math.PI * radius ** 2,
      unit: world?.values?.[radiusId]?.unit || world?.values?.[diameterId]?.unit || "cm",
    };
  }
  if (/(rhombus|parallelogram)_area_properties/i.test(problemType)) {
    const baseId = boundId(bindings, "length", ["base"]);
    const heightId = boundId(bindings, "height", ["height"]);
    const sideId = boundId(bindings, "width", ["side"]);
    const base = rawValue(world, baseId);
    const height = rawValue(world, heightId);
    const side = rawValue(world, sideId) ?? base;
    if (![base, height, side].every((value) => Number.isFinite(value) && value > 0)) return null;
    return {
      kind: /rhombus/i.test(problemType) ? "rhombus" : "parallelogram",
      a: base,
      b: height,
      side,
      area: base * height,
      perimeter: 2 * (base + side),
      unit: world?.values?.[baseId]?.unit || "cm",
    };
  }
  const lengthId = boundId(bindings, "length", []);
  const widthId = boundId(bindings, "width", []);
  const rectangleLength = rawValue(world, lengthId);
  const rectangleWidth = rawValue(world, widthId);
  if (rectangleLength != null && rectangleWidth != null) {
    return {
      kind: "rectangle",
      a: rectangleLength,
      b: rectangleWidth,
      perimeter: 2 * (rectangleLength + rectangleWidth),
      area: rectangleLength * rectangleWidth,
      unit: world?.values?.[lengthId]?.unit || world?.values?.[widthId]?.unit || "cm",
    };
  }

  const aId = boundId(bindings, "length", ["side_ab"]);
  const heightId = boundId(bindings, "height", ["side_ac"]);
  const a = rawValue(world, aId);
  const b = rawValue(world, heightId);
  if (a == null || b == null) return null;
  if (/triangle_area/i.test(problemType)) {
    return {
      kind: "triangle_area",
      a,
      b,
      area: (a * b) / 2,
      unit: world?.values?.[aId]?.unit || "cm",
    };
  }
  const hypotenuse = Math.sqrt(a * a + b * b);
  return {
    kind: "triangle",
    a,
    b,
    hypotenuse,
    area: (a * b) / 2,
    unit: world?.values?.[aId]?.unit || "cm",
  };
}

function integerGcd(left, right) {
  let a = Math.abs(Math.trunc(left));
  let b = Math.abs(Math.trunc(right));
  while (b) [a, b] = [b, a % b];
  return a || 1;
}

function leastCommonMultiple(left, right) {
  return Math.abs(left * right) / integerGcd(left, right);
}

function firstWorldValue(world, bindings, roles, fallbackIds = [], labelHints = []) {
  for (const role of roles) {
    const value = rawRole(world, bindings, role, []);
    if (value != null) return value;
  }
  for (const id of fallbackIds) {
    const value = rawValue(world, id);
    if (value != null) return value;
  }
  const quantityIds = Array.isArray(bindings?.quantities)
    ? bindings.quantities
    : Object.keys(world?.values || {});
  const hintedId = quantityIds.find((id) => {
    const text = `${id} ${world?.values?.[id]?.label || ""}`.toLocaleLowerCase("vi");
    return labelHints.some((hint) => text.includes(hint));
  });
  return hintedId ? rawValue(world, hintedId) : null;
}

/** A complete operation on two fractions, including the common-part model. */
export function deriveFractionOperation(world, bindings = {}, problemType = "") {
  const numeratorIds = Array.isArray(bindings?.numerator) ? bindings.numerator : [];
  const denominatorIds = Array.isArray(bindings?.denominator) ? bindings.denominator : [];
  const leftNumerator = rawRole(world, bindings, "numerator", ["numerator"]);
  const leftDenominator = rawRole(world, bindings, "denominator", ["denominator"]);
  const rightNumerator = rawRole(world, bindings, "addend_numerator", ["addend_numerator"])
    ?? (numeratorIds.length > 1 ? rawValue(world, numeratorIds[1]) : null);
  const rightDenominator = rawRole(world, bindings, "addend_denominator", ["addend_denominator"])
    ?? (denominatorIds.length > 1 ? rawValue(world, denominatorIds[1]) : null);
  if (![leftNumerator, leftDenominator, rightNumerator, rightDenominator]
    .every((value) => Number.isInteger(value))
    || leftDenominator <= 0 || rightDenominator <= 0) return null;

  const normalizedType = String(problemType).toLocaleLowerCase("vi");
  const operation = /(division|divide|quotient|chia)/.test(normalizedType)
    ? "divide"
    : /(multiplication|multiply|product|nhân)/.test(normalizedType)
      ? "multiply"
    : /(subtraction|subtract|difference|trừ)/.test(normalizedType)
      ? "subtract"
      : "add";
  let commonDenominator;
  let leftCommon;
  let rightCommon;
  let resultNumerator;
  let resultDenominator;
  if (operation === "multiply" || operation === "divide") {
    commonDenominator = null;
    leftCommon = leftNumerator;
    rightCommon = rightNumerator;
    resultNumerator = operation === "divide"
      ? leftNumerator * rightDenominator
      : leftNumerator * rightNumerator;
    resultDenominator = operation === "divide"
      ? leftDenominator * rightNumerator
      : leftDenominator * rightDenominator;
  } else {
    const requestedCommon = rawRole(
      world,
      bindings,
      "target_denominator",
      ["target_denominator"],
    );
    commonDenominator = Number.isInteger(requestedCommon)
      && requestedCommon > 0
      && requestedCommon % leftDenominator === 0
      && requestedCommon % rightDenominator === 0
      ? requestedCommon
      : leastCommonMultiple(leftDenominator, rightDenominator);
    leftCommon = leftNumerator * (commonDenominator / leftDenominator);
    rightCommon = rightNumerator * (commonDenominator / rightDenominator);
    resultNumerator = operation === "subtract"
      ? leftCommon - rightCommon
      : leftCommon + rightCommon;
    resultDenominator = commonDenominator;
  }
  const divisor = integerGcd(resultNumerator, resultDenominator);
  const measurementDenominator = operation === "divide"
    ? leastCommonMultiple(leftDenominator, rightDenominator)
    : null;
  return {
    operation,
    left: { numerator: leftNumerator, denominator: leftDenominator },
    right: { numerator: rightNumerator, denominator: rightDenominator },
    commonDenominator,
    leftCommon,
    rightCommon,
    resultNumerator,
    resultDenominator,
    divisor,
    reducedNumerator: resultNumerator / divisor,
    reducedDenominator: resultDenominator / divisor,
    measurementDenominator,
    dividendParts: measurementDenominator ? leftNumerator * (measurementDenominator / leftDenominator) : null,
    divisorParts: measurementDenominator ? rightNumerator * (measurementDenominator / rightDenominator) : null,
  };
}

function parseChoiceFraction(choice) {
  const normalized = String(choice || "").replaceAll("−", "-");
  const match = /(?:^|[^\d])(-?\s*\d+)\s*\/\s*(\d+)(?:\D|$)/.exec(normalized);
  if (!match) return null;
  const numerator = Number(match[1].replaceAll(" ", ""));
  const denominator = Number(match[2]);
  if (!Number.isInteger(numerator) || !Number.isInteger(denominator) || denominator === 0) return null;
  return { numerator, denominator };
}

/** A fractional power split into sign, repeated factors and a 5×5×5 magnitude. */
export function deriveFractionPower(world, bindings = {}, choices = []) {
  const numerator = rawRole(world, bindings, "numerator", ["numerator"]);
  const denominator = rawRole(world, bindings, "denominator", ["denominator"]);
  const exponent = rawRole(world, bindings, "exponent", ["exponent"]);
  if (![numerator, denominator, exponent].every(Number.isInteger)
    || denominator === 0 || exponent < 1 || exponent > 8) return null;

  const sign = numerator < 0 && exponent % 2 === 1 ? -1 : 1;
  const numeratorMagnitude = Math.abs(numerator) ** exponent;
  const denominatorMagnitude = Math.abs(denominator) ** exponent;
  const resultNumerator = sign * numeratorMagnitude;
  const resultDenominator = denominatorMagnitude;
  const choiceIndex = choices.findIndex((choice) => {
    const parsed = parseChoiceFraction(choice);
    return parsed && parsed.numerator * resultDenominator === resultNumerator * parsed.denominator;
  });

  return {
    numerator,
    denominator,
    exponent,
    sign,
    numeratorMagnitude,
    denominatorMagnitude,
    resultNumerator,
    resultDenominator,
    factors: Array.from({ length: exponent }, () => ({ numerator, denominator })),
    choices,
    choiceIndex,
    choiceLabel: choiceIndex >= 0 ? String.fromCharCode(65 + choiceIndex) : null,
  };
}

/** Equal groups or a rectangular array for multiplication and division. */
export function deriveParenthesizedMultiplication(world, bindings = {}, problemType = "") {
  const innerLeft = rawRole(world, bindings, "count_initial", ["inner_left"]);
  const innerRight = rawRole(world, bindings, "count_change", ["inner_right"]);
  const multiplier = rawRole(world, bindings, "coefficient", ["outer_multiplier"]);
  const innerOperation = String(problemType).includes("subtraction") ? "subtract" : "add";
  const innerValue = innerOperation === "subtract"
    ? innerLeft - innerRight
    : innerLeft + innerRight;
  const total = innerValue * multiplier;
  if (![innerLeft, innerRight, multiplier, innerValue, total].every(Number.isInteger)
    || innerLeft < 0 || innerRight < 0 || multiplier <= 0 || innerValue <= 0
    || total > 144) return null;
  return {
    innerLeft,
    innerRight,
    innerOperation,
    innerSymbol: innerOperation === "subtract" ? "−" : "+",
    innerValue,
    multiplier,
    groups: innerValue,
    perGroup: multiplier,
    total,
  };
}

export function deriveGrouping(world, bindings = {}, problemType = "") {
  const first = rawRole(world, bindings, "count_initial", ["left", "total"]);
  const second = rawRole(world, bindings, "count_change", ["right", "group_size"]);
  if (!Number.isInteger(first) || !Number.isInteger(second)
    || first <= 0 || second <= 0) return null;
  const division = /(division|divide|quotient|chia)/i.test(String(problemType));
  if (division) {
    if (first % second !== 0 || first > 144) return null;
    return { operation: "divide", total: first, groups: first / second, perGroup: second };
  }
  const total = first * second;
  if (!Number.isSafeInteger(total)) return null;

  // Drawing one dot per item is useful only for small products. For a large
  // product such as 4 × 98, refusing the renderer leaves a blank scene even
  // though the arithmetic is completely known. Keep the equal-group meaning,
  // but represent each large group with base-ten blocks and the distributive
  // law. Multiplication is commutative, so put the smaller factor in the
  // visible group count when that avoids dozens of repeated cards.
  let groups = first;
  let perGroup = second;
  let swapped = false;
  if (groups > 12 && second <= 12) {
    groups = second;
    perGroup = first;
    swapped = true;
  }
  const compact = total > 144 || perGroup > 24 || groups > 12;
  if (!compact) {
    return { operation: "multiply", total, groups, perGroup, mode: "objects", swapped };
  }

  const highestPlace = 10 ** Math.floor(Math.log10(perGroup));
  const placeValues = [];
  for (let place = highestPlace; place >= 1; place /= 10) placeValues.push(place);
  const placeLabels = {
    10000: "chục nghìn",
    1000: "nghìn",
    100: "trăm",
    10: "chục",
    1: "đơn vị",
  };
  const parts = placeValues.map((place) => {
    const digit = Math.floor(perGroup / place) % 10;
    return {
      place,
      label: placeLabels[place] || `hàng ${new Intl.NumberFormat("vi-VN").format(place)}`,
      digit,
      value: digit * place,
    };
  }).filter((part) => part.digit > 0);
  const partials = parts.map((part) => ({
    ...part,
    value: groups * part.value,
    expression: `${groups} × ${part.value}`,
  }));
  return {
    operation: "multiply",
    mode: "place_value",
    originalLeft: first,
    originalRight: second,
    groups,
    perGroup,
    swapped,
    total,
    parts,
    partials,
    // Repeated cards are still readable up to twelve groups. For larger
    // factors the partial-product board remains exact without creating an
    // unbounded amount of DOM.
    showGroupCards: groups <= 12,
  };
}

/** The algebraic states that keep a linear equation balanced. */
export function deriveLinearEquation(world, bindings = {}) {
  const coefficient = firstWorldValue(
    world,
    bindings,
    ["coefficient"],
    ["coefficient", "slope"],
    ["hệ số"],
  );
  const constant = firstWorldValue(
    world,
    bindings,
    ["constant"],
    ["constant"],
    ["hằng số", "số hạng"],
  ) ?? 0;
  const result = firstWorldValue(
    world,
    bindings,
    ["result"],
    ["result", "right_side"],
    ["vế phải", "kết quả"],
  );
  if (![coefficient, constant, result].every(Number.isFinite) || coefficient === 0) return null;
  const isolated = result - constant;
  return { coefficient, constant, result, isolated, solution: isolated / coefficient };
}

/** A line/function and its point table in one coordinate world. */
export function deriveCoordinateGraph(world, bindings = {}) {
  const xIds = Array.isArray(bindings?.x_value) ? bindings.x_value : [];
  const yIds = Array.isArray(bindings?.y_value) ? bindings.y_value : [];
  const explicitPoints = xIds.slice(0, Math.min(xIds.length, yIds.length)).map((id, index) => ({
    x: rawValue(world, id),
    y: rawValue(world, yIds[index]),
  })).filter((point) => Number.isFinite(point.x) && Number.isFinite(point.y));
  const slope = firstWorldValue(
    world,
    bindings,
    ["coefficient"],
    ["slope", "coefficient"],
    ["hệ số góc", "slope"],
  );
  const intercept = firstWorldValue(
    world,
    bindings,
    ["constant"],
    ["intercept", "constant"],
    ["tung độ gốc", "intercept"],
  ) ?? 0;
  if (!Number.isFinite(slope) && explicitPoints.length === 1) {
    const extent = Math.max(5, Math.abs(explicitPoints[0].x), Math.abs(explicitPoints[0].y));
    return { kind: "points", points: explicitPoints, table: explicitPoints, range: Math.min(12, Math.ceil(extent + 1)) };
  }
  if (!Number.isFinite(slope) && explicitPoints.length < 2) return null;
  const resolvedSlope = Number.isFinite(slope)
    ? slope
    : (explicitPoints[1].y - explicitPoints[0].y) / (explicitPoints[1].x - explicitPoints[0].x);
  const resolvedIntercept = Number.isFinite(slope)
    ? intercept
    : explicitPoints[0].y - resolvedSlope * explicitPoints[0].x;
  if (!Number.isFinite(resolvedSlope) || !Number.isFinite(resolvedIntercept)) return null;
  const table = [-2, -1, 0, 1, 2].map((x) => ({ x, y: resolvedSlope * x + resolvedIntercept }));
  const coordinates = explicitPoints.length ? explicitPoints : table;
  const extent = Math.max(
    5,
    ...coordinates.flatMap((point) => [Math.abs(point.x), Math.abs(point.y)]),
    Math.abs(resolvedIntercept),
  );
  const range = Math.min(12, Math.ceil(extent + 1));
  return { kind: "line", slope: resolvedSlope, intercept: resolvedIntercept, points: coordinates, table, range };
}

/** Values behind a dimensioned cuboid on x/y/z axes. */
export function deriveGeometry3d(world, bindings = {}) {
  const lengthId = boundId(bindings, "length", ["length"]);
  const widthId = boundId(bindings, "width", ["width"]);
  const heightId = boundId(bindings, "height", ["height"]);
  const length = rawValue(world, lengthId);
  const width = rawValue(world, widthId);
  const height = rawValue(world, heightId);
  if (![length, width, height].every((value) => Number.isFinite(value) && value > 0)) return null;
  return {
    length,
    width,
    height,
    volume: length * width * height,
    baseArea: length * width,
    surfaceArea: 2 * (length * width + length * height + width * height),
    unit: world?.values?.[lengthId]?.unit || world?.values?.[widthId]?.unit || "cm",
  };
}

/** A three-variable linear equation represented as a plane on Oxyz axes.
 *
 * `3x + y = z` canonicalizes to `3x + y − z = 0`, whose plane passes through
 * the origin: all three axis intercepts collapse onto O. Reporting three
 * separate intercepts there would be a lie, so `throughOrigin` lets the
 * renderer teach the normal vector and verified sample points instead.
 */
export function derivePlane3d(world, bindings = {}) {
  const coefficientIds = Array.isArray(bindings?.coefficient) ? bindings.coefficient : [];
  const coefficients = coefficientIds.slice(0, 3).map((id) => rawValue(world, id));
  const rightSide = rawRole(world, bindings, "constant", ["plane_right_side", "constant"]);
  if (coefficients.length !== 3 || ![...coefficients, rightSide].every(Number.isFinite)) return null;
  const [a, b, c] = coefficients;
  return planeGeometry(a, b, c, rightSide);
}

/** Geometry shared by a single equation and every plane in a linear system. */
function planeGeometry(a, b, c, rightSide) {
  const normSquared = a * a + b * b + c * c;
  if (normSquared <= 1e-12) return null;
  const norm = Math.sqrt(normSquared);
  const normal = [a / norm, b / norm, c / norm];
  const center = [a * rightSide / normSquared, b * rightSide / normSquared, c * rightSide / normSquared];
  const reference = Math.abs(normal[2]) < 0.9 ? [0, 0, 1] : [0, 1, 0];
  const cross = (left, right) => [
    left[1] * right[2] - left[2] * right[1],
    left[2] * right[0] - left[0] * right[2],
    left[0] * right[1] - left[1] * right[0],
  ];
  const rawU = cross(normal, reference);
  const uLength = Math.hypot(...rawU);
  const u = rawU.map((value) => value / uLength);
  const v = cross(normal, u);
  const throughOrigin = Math.abs(rightSide) <= 1e-9;
  const intercepts = [a, b, c].map((value) => Math.abs(value) > 1e-12 ? rightSide / value : null);
  const finiteIntercepts = intercepts.filter((value) => Number.isFinite(value));
  const radius = throughOrigin
    ? 4
    : Math.max(2, ...finiteIntercepts.map((value) => Math.min(8, Math.abs(value))));
  const vertex = (uSign, vSign) => center.map((value, index) => value + uSign * radius * u[index] + vSign * radius * v[index]);
  return {
    a, b, c, rightSide, normal, center, intercepts, throughOrigin,
    normalTip: normal.map((value) => value * Math.max(2, radius * 0.7)),
    samplePoints: planeSamplePoints(a, b, c, rightSide),
    vertices: [vertex(-1, -1), vertex(1, -1), vertex(1, 1), vertex(-1, 1)],
  };
}

/** Two or three planes belonging to one fully parsed three-variable system. */
export function deriveLinearSystem3d(_world, _bindings = {}, relations = []) {
  const relation = (relations || []).find((item) => (
    item?.type === "linear_system"
    && Array.isArray(item?.parameters?.symbols)
    && item.parameters.symbols.length === 3
  ));
  const parameters = relation?.parameters;
  const equations = parameters?.equations;
  if (!Array.isArray(equations) || equations.length < 2 || equations.length > 3) return null;
  const normalized = equations.map((row) => Array.isArray(row) ? row.map(Number) : []);
  if (normalized.some((row) => row.length !== 4 || !row.every(Number.isFinite))) return null;
  const planes = normalized.map(([a, b, c, rightSide]) => planeGeometry(a, b, c, rightSide));
  if (planes.some((plane) => !plane)) return null;
  const solution = Array.isArray(parameters.solution) ? parameters.solution.map(Number) : null;
  const uniqueSolution = solution?.length === 3 && solution.every(Number.isFinite) ? solution : null;
  const checks = uniqueSolution
    ? normalized.map(([a, b, c, rightSide]) => ({
      left: a * uniqueSolution[0] + b * uniqueSolution[1] + c * uniqueSolution[2],
      right: rightSide,
    }))
    : [];
  if (checks.some((check) => Math.abs(check.left - check.right) > 1e-6)) return null;
  const eliminationSteps = Array.isArray(parameters.elimination_steps)
    ? parameters.elimination_steps.filter((step) => (
      typeof step?.operation === "string"
      && Array.isArray(step?.matrix)
      && step.matrix.every((row) => Array.isArray(row) && row.length === 4)
    ))
    : [];
  return {
    symbols: parameters.symbols.map(String),
    equations: normalized,
    canonicalForms: Array.isArray(parameters.canonical_forms)
      ? parameters.canonical_forms.map(String)
      : [],
    planes,
    state: String(parameters.state || ""),
    solution: uniqueSolution,
    solutionExact: Array.isArray(parameters.solution_exact)
      ? parameters.solution_exact.map(String)
      : null,
    coefficientRank: Number(parameters.coefficient_rank),
    augmentedRank: Number(parameters.augmented_rank),
    eliminationSteps,
    checks,
  };
}

/** Points that genuinely satisfy `ax + by + cz = d`, re-checked before use. */
export function planeSamplePoints(a, b, c, rightSide, count = 4) {
  const axes = [a, b, c];
  const solveIndex = axes.reduce(
    (best, value, index) => (Math.abs(value) > Math.abs(axes[best]) ? index : best),
    0,
  );
  if (Math.abs(axes[solveIndex]) <= 1e-12) return [];
  const freeIndexes = [0, 1, 2].filter((index) => index !== solveIndex);
  const seeds = [[0, 0], [1, 0], [0, 1], [1, 1], [2, -1], [-1, 2]];
  const points = [];
  for (const [firstValue, secondValue] of seeds) {
    const point = [0, 0, 0];
    point[freeIndexes[0]] = firstValue;
    point[freeIndexes[1]] = secondValue;
    const remainder = rightSide
      - axes[freeIndexes[0]] * firstValue
      - axes[freeIndexes[1]] * secondValue;
    point[solveIndex] = remainder / axes[solveIndex];
    if (!point.every(Number.isFinite)) continue;
    const check = a * point[0] + b * point[1] + c * point[2];
    if (Math.abs(check - rightSide) > 1e-6) continue;
    points.push(point);
    if (points.length >= count) break;
  }
  return points;
}

/** Two simultaneous lines `a·x + b·y = c` sharing one set of Oxy axes.
 *
 * The general form is kept instead of a slope so a vertical line such as
 * `x = 2` stays drawable rather than collapsing into an infinite slope.
 */
export function deriveLinearSystem(world, bindings = {}) {
  const coefficientIds = Array.isArray(bindings?.coefficient) ? bindings.coefficient : [];
  const constantIds = Array.isArray(bindings?.constant) ? bindings.constant : [];
  if (coefficientIds.length < 4 || constantIds.length < 2) return null;
  const numbers = coefficientIds.slice(0, 4).map((id) => rawValue(world, id));
  const rightSides = constantIds.slice(0, 2).map((id) => rawValue(world, id));
  if (![...numbers, ...rightSides].every(Number.isFinite)) return null;
  const lines = [
    { a: numbers[0], b: numbers[1], c: rightSides[0] },
    { a: numbers[2], b: numbers[3], c: rightSides[1] },
  ];
  if (lines.some((line) => Math.abs(line.a) < 1e-12 && Math.abs(line.b) < 1e-12)) return null;
  const [first, second] = lines;
  const determinant = first.a * second.b - second.a * first.b;
  let state = "parallel";
  let intersection = null;
  if (Math.abs(determinant) > 1e-9) {
    state = "intersecting";
    intersection = {
      x: (first.c * second.b - second.c * first.b) / determinant,
      y: (first.a * second.c - second.a * first.c) / determinant,
    };
  } else if (
    Math.abs(first.a * second.c - second.a * first.c) <= 1e-9
    && Math.abs(first.b * second.c - second.b * first.c) <= 1e-9
  ) {
    state = "coincident";
  }
  const range = Math.min(
    12,
    Math.max(5, Math.ceil(Math.abs(intersection?.x ?? 0) + 2), Math.ceil(Math.abs(intersection?.y ?? 0) + 2)),
  );
  return {
    lines: lines.map((line) => ({ ...line, points: lineSegment(line, range) })),
    state,
    intersection,
    range,
  };
}

/** Clip `a·x + b·y = c` to the drawable square, vertical lines included. */
export function lineSegment({ a, b, c }, range) {
  if (Math.abs(b) > 1e-12) {
    return [
      { x: -range, y: (c - a * -range) / b },
      { x: range, y: (c - a * range) / b },
    ];
  }
  const x = c / a;
  return [{ x, y: -range }, { x, y: range }];
}

function binomialLabels(sourceText) {
  const source = String(sourceText || "").replaceAll("−", "-");
  const match = /\(([^()]*)\)\s*(?:\^\s*\{?2\}?|²)/.exec(source);
  if (!match) return { a: "a", b: "b" };
  const terms = match[1].split("+").map((item) => item.trim()).filter(Boolean);
  return terms.length === 2 ? { a: terms[0], b: terms[1] } : { a: "a", b: "b" };
}

/** Four visible areas proving (a + b)^2, not just displaying the identity. */
export function deriveBinomialSquare(world, bindings = {}, sourceText = "") {
  const a = firstWorldValue(world, bindings, [], ["a"], ["đại lượng a", "cạnh a"]);
  const b = firstWorldValue(world, bindings, [], ["b"], ["đại lượng b", "cạnh b"]);
  if (![a, b].every((value) => Number.isFinite(value) && value > 0)) {
    const labels = binomialLabels(sourceText);
    return {
      a: labels.a,
      b: labels.b,
      side: `${labels.a} + ${labels.b}`,
      aSquare: `${labels.a}²`,
      ab: `${labels.a}·${labels.b}`,
      bSquare: `${labels.b}²`,
      total: `${labels.a}² + 2·${labels.a}·${labels.b} + ${labels.b}²`,
      splitPercent: 60,
      symbolic: true,
    };
  }
  return {
    a,
    b,
    side: a + b,
    aSquare: a * a,
    ab: a * b,
    bSquare: b * b,
    total: (a + b) ** 2,
    splitPercent: (a / (a + b)) * 100,
    symbolic: false,
  };
}
