export const MATH_LAB_SCHEMA_VERSION = "1.0";

export const MATH_DOMAINS = Object.freeze([
  "arithmetic", "number", "fraction", "ratio", "measurement", "time",
  "motion", "algebra", "geometry_2d", "coordinate", "geometry_3d",
  "probability", "statistics", "unknown",
]);

export const VISUALIZATION_IDS = Object.freeze([
  "unsupported", "object_group", "number_line", "grouping", "bar_model", "fraction",
  "power_model", "clock", "timeline", "motion_path", "balance", "geometry_2d",
  "coordinate_graph", "geometry_3d", "place_value", "column_algorithm", "unit_scale",
  "data_chart", "number_compare", "probability_simulator", "percent_grid", "algebra_tiles", "part_whole", "shape_pattern",
  "circle_model", "factor_lattice", "expression_tree", "calendar", "solution_set",
]);

export const MATH_UNITS = Object.freeze([
  "one", "mm", "cm", "dm", "m", "km", "g", "kg", "second", "minute",
  "hour", "day", "cm2", "m2", "cm3", "m3", "liter", "ml", "m/s", "km/h",
  "degree",
]);

export const MATH_QUANTITY_ROLES = Object.freeze([
  "count", "count_initial", "count_change", "total", "distance", "speed", "duration",
  "start_time", "end_time", "numerator", "denominator", "target_denominator",
  "addend_numerator", "addend_denominator", "exponent", "length", "width", "height",
  "radius", "diameter", "angle", "variable", "coefficient", "constant",
  "mass", "capacity", "area", "volume", "result", "x_value", "y_value", "category", "frequency", "probability",
]);

const ID_PATTERN = /^[A-Za-z][A-Za-z0-9_.-]{0,63}$/;

export class MathLabValidationError extends Error {
  constructor(message, path = "mathLab") {
    super(`${path}: ${message}`);
    this.name = "MathLabValidationError";
    this.path = path;
  }
}

function plainObject(value, path) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new MathLabValidationError("must be an object", path);
  }
  return value;
}

function array(value, path) {
  if (!Array.isArray(value)) throw new MathLabValidationError("must be an array", path);
  return value;
}

function identifier(value, path) {
  if (typeof value !== "string" || !ID_PATTERN.test(value)) {
    throw new MathLabValidationError("must be a stable identifier", path);
  }
  return value;
}

function uniqueIds(groups, path) {
  const ids = groups.flat().map((item, index) => identifier(item?.id, `${path}[${index}].id`));
  if (new Set(ids).size !== ids.length) throw new MathLabValidationError("IDs must be unique", path);
}

function clone(value) {
  return structuredClone(value);
}

export function normalizeProblemType(value) {
  return String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/đ/g, "d")
    .replace(/Đ/g, "D")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .replace(/_+/g, "_");
}

export function hasSourceIntegrityMismatch(modelSource, scene) {
  if (typeof modelSource !== "string" || !modelSource) return false;
  return scene?.metadata?.source_preserved !== true
    || scene?.metadata?.source_text !== modelSource;
}

/**
 * Renderer-independent semantic contract mirrored from Master Pydantic models.
 * The backend remains authoritative; this validator prevents malformed local
 * edits or cached data from reaching renderers.
 *
 * @typedef {Object} MathSemanticModel
 * @property {"1.0"} schema_version
 * @property {number} grade
 * @property {string} domain
 * @property {string} problem_type
 * @property {Array<Object>} entities
 * @property {Array<Object>} quantities
 * @property {Array<Object>} unknowns
 * @property {Array<Object>} relations
 * @property {Array<Object>} constraints
 */

/** @returns {MathSemanticModel} */
export function normalizeSemanticModel(input) {
  const source = plainObject(input, "semantic_model");
  const grade = Number(source.grade);
  if (!Number.isInteger(grade) || grade < 1 || grade > 9) {
    throw new MathLabValidationError("grade must be an integer from 1 to 9", "semantic_model.grade");
  }
  if (!MATH_DOMAINS.includes(source.domain)) {
    throw new MathLabValidationError("domain is not supported", "semantic_model.domain");
  }
  if (typeof source.problem_type !== "string" || !source.problem_type.trim()) {
    throw new MathLabValidationError("problem_type is required", "semantic_model.problem_type");
  }
  const entities = array(source.entities || [], "semantic_model.entities");
  const quantities = array(source.quantities || [], "semantic_model.quantities");
  const unknowns = array(source.unknowns || [], "semantic_model.unknowns");
  const relations = array(source.relations || [], "semantic_model.relations");
  const constraints = array(source.constraints || [], "semantic_model.constraints");
  uniqueIds([entities, quantities, unknowns, relations, constraints], "semantic_model");
  const references = new Set([...entities, ...quantities, ...unknowns].map((item) => item.id));
  quantities.forEach((quantity, index) => {
    if (!Number.isFinite(Number(quantity.value))) {
      throw new MathLabValidationError("quantity value must be finite", `semantic_model.quantities[${index}].value`);
    }
    if (!MATH_UNITS.includes(quantity.unit || "one")) {
      throw new MathLabValidationError("quantity unit is not supported", `semantic_model.quantities[${index}].unit`);
    }
  });
  relations.forEach((relation, index) => {
    const participants = plainObject(relation.participants, `semantic_model.relations[${index}].participants`);
    if (!Object.keys(participants).length) {
      throw new MathLabValidationError("participants cannot be empty", `semantic_model.relations[${index}].participants`);
    }
    Object.values(participants).forEach((reference) => {
      if (!references.has(reference)) {
        throw new MathLabValidationError(`unknown reference ${reference}`, `semantic_model.relations[${index}]`);
      }
    });
  });
  constraints.forEach((constraint, index) => {
    array(constraint.target_ids, `semantic_model.constraints[${index}].target_ids`).forEach((reference) => {
      if (!references.has(reference)) {
        throw new MathLabValidationError(`unknown reference ${reference}`, `semantic_model.constraints[${index}]`);
      }
    });
  });
  return {
    ...clone(source),
    schema_version: MATH_LAB_SCHEMA_VERSION,
    id: source.id || "semantic_model",
    grade,
    problem_type: normalizeProblemType(source.problem_type),
    entities: clone(entities),
    quantities: clone(quantities),
    unknowns: clone(unknowns),
    relations: clone(relations),
    constraints: clone(constraints),
    choices: clone(source.choices || []),
    tags: clone(source.tags || []),
  };
}

/**
 * @typedef {Object} MathScene
 * @property {"1.0"} schema_version
 * @property {Object} world
 * @property {Array<Object>} objects
 * @property {Array<Object>} visualizations
 * @property {Array<Object>} steps
 */

/** @returns {MathScene} */
export function normalizeMathScene(input) {
  const source = plainObject(input, "scene");
  if (source.schema_version !== MATH_LAB_SCHEMA_VERSION) {
    throw new MathLabValidationError("unsupported schema version", "scene.schema_version");
  }
  const grade = Number(source.grade);
  if (!Number.isInteger(grade) || grade < 1 || grade > 9) {
    throw new MathLabValidationError("grade must be an integer from 1 to 9", "scene.grade");
  }
  identifier(source.id, "scene.id");
  identifier(source.semantic_model_id, "scene.semantic_model_id");
  const world = plainObject(source.world, "scene.world");
  plainObject(world.values || {}, "scene.world.values");
  const objects = array(source.objects || [], "scene.objects");
  const visualizations = array(source.visualizations, "scene.visualizations");
  if (!visualizations.length) throw new MathLabValidationError("at least one visualization is required", "scene.visualizations");
  const constraints = array(source.constraints || [], "scene.constraints");
  const steps = array(source.steps || [], "scene.steps");
  const actions = array(source.actions || [], "scene.actions");
  uniqueIds([objects, visualizations, constraints, steps, actions], "scene");
  visualizations.forEach((visualization, index) => {
    if (!VISUALIZATION_IDS.includes(visualization.type)) {
      throw new MathLabValidationError(`unregistered visualization ${visualization.type}`, `scene.visualizations[${index}]`);
    }
  });
  return {
    ...clone(source),
    grade,
    world: { revision: Number(world.revision || 0), values: clone(world.values || {}) },
    objects: clone(objects),
    visualizations: clone(visualizations),
    constraints: clone(constraints),
    steps: clone(steps),
    actions: clone(actions),
    metadata: {
      ...clone(source.metadata || {}),
      ...(source.metadata?.problem_type
        ? { problem_type: normalizeProblemType(source.metadata.problem_type) }
        : {}),
    },
  };
}
