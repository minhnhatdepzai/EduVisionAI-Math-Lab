import { normalizeMathScene, normalizeSemanticModel } from "../schemas/mathLabSchema.js";

/**
 * A scene built in the browser, for when Master is not reachable.
 *
 * This exists so a renderer can be worked on and tested without the whole
 * stack running. It is deliberately thin — it lays the given quantities into
 * `world.values` and takes the visualizations the fixture declares — because
 * the moment it starts making pedagogical decisions it becomes a second,
 * silently diverging planner.
 *
 * Whatever calls this MUST show the viewer that the scene is local. A fixture
 * that quietly stands in for the backend is how a broken endpoint goes
 * unnoticed for a week.
 */
export function planLocally(preset) {
  const model = normalizeSemanticModel(preset.model);

  const values = {};
  for (const quantity of model.quantities) {
    values[quantity.id] = {
      value: quantity.value,
      unit: quantity.unit || "one",
      label: quantity.label || quantity.id,
      canonical_value: canonicalValue(quantity),
      canonical_unit: canonicalUnit(quantity.unit),
      editable: quantity.editable !== false,
    };
  }
  for (const unknown of model.unknowns || []) {
    values[unknown.id] = {
      value: null,
      unit: unknown.unit || "one",
      label: unknown.label || unknown.id,
    };
  }
  if (model.time?.start) {
    values.start_time = { value: model.time.start, unit: "clock", label: "Thời gian bắt đầu" };
  }
  for (const [id, patch] of Object.entries(preset.worldOverrides || {})) {
    values[id] = { ...(values[id] || { unit: "one", label: id }), ...patch };
  }

  const bindings = {
    entities: (model.entities || []).map((item) => item.id),
    quantities: model.quantities.map((item) => item.id),
    unknowns: (model.unknowns || []).map((item) => item.id),
  };
  for (const entity of model.entities || []) {
    if (entity.role) (bindings[entity.role] ||= []).push(entity.id);
  }
  for (const quantity of model.quantities) {
    if (quantity.role) (bindings[quantity.role] ||= []).push(quantity.id);
  }
  for (const unknown of model.unknowns || []) {
    if (unknown.role) (bindings[`unknown_${unknown.role}`] ||= []).push(unknown.id);
  }
  if (model.time?.start) bindings.start_time = ["start_time"];

  return normalizeMathScene({
    schema_version: "1.0",
    id: `local_${preset.id}`,
    kind: model.domain,
    semantic_model_id: model.id,
    grade: model.grade,
    world: { revision: 0, values },
    objects: (model.entities || []).map((entity) => ({
      id: `object_${entity.id}`,
      type: entity.type,
      label: entity.label,
      semantic_ref: entity.id,
    })),
    visualizations: preset.expects.map((type) => ({
      id: `visual_${type}`,
      type,
      bindings,
      options: {},
    })),
    constraints: (model.constraints || []).map((constraint) => ({
      id: `scene_${constraint.id}`,
      type: constraint.type,
      target_ids: constraint.target_ids,
      locked: constraint.locked === true,
      evidence: constraint.evidence || { status: "explicit", confidence: 1 },
    })),
    steps: [],
    actions: [
      { id: "action_play", type: "play" },
      { id: "action_pause", type: "pause" },
      { id: "action_reset", type: "reset" },
    ],
    metadata: {
      problem_type: model.problem_type,
      source_text: model.source_text,
      source_preserved: true,
      relations: model.relations || [],
    },
  });
}

/*
 * Only the conversions the renderers actually rely on. `units.py` on the
 * backend is the authority; this covers the fixture path so a locally planned
 * motion scene can still compute `t = s / v`.
 */
const TO_CANONICAL = {
  km: [1000, "m"],
  m: [1, "m"],
  cm: [0.01, "m"],
  mm: [0.001, "m"],
  "km/h": [1000 / 3600, "m/s"],
  "m/s": [1, "m/s"],
  hour: [3600, "second"],
  minute: [60, "second"],
  second: [1, "second"],
};

function canonicalValue(quantity) {
  const rule = TO_CANONICAL[quantity.unit];
  return rule ? Number(quantity.value) * rule[0] : null;
}

function canonicalUnit(unit) {
  const rule = TO_CANONICAL[unit];
  return rule ? rule[1] : null;
}
