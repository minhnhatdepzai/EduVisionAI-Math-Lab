import { describe, expect, it } from "vitest";
import { VISUALIZATION_IDS } from "./schemas/mathLabSchema.js";
import {
  MathLabValidationError,
  createMathWorldState,
  hasSourceIntegrityMismatch,
  mathWorldReducer,
  normalizeMathScene,
  normalizeProblemType,
  normalizeSemanticModel,
  validateVisualizationDescriptor,
  visualizationRegistry,
} from "./index.js";

const semantic = {
  grade: 5,
  domain: "motion",
  problem_type: "distance_speed_time",
  entities: [
    { id: "person", type: "person", label: "Bạn nhỏ" },
    { id: "home", type: "location", label: "Nhà" },
  ],
  quantities: [{ id: "distance", value: 1.2, unit: "km" }],
  unknowns: [],
  relations: [{ id: "movement", type: "motion", participants: { subject: "person", from: "home" } }],
};

const scene = {
  schema_version: "1.0",
  id: "scene_motion",
  kind: "motion",
  grade: 5,
  semantic_model_id: "semantic_model",
  world: {
    revision: 0,
    values: {
      distance: { value: 1.2, unit: "km", editable: true, minimum: 0, maximum: 10 },
    },
  },
  objects: [{ id: "object_person", type: "person", semantic_ref: "person" }],
  visualizations: [{ id: "visual_motion", type: "motion_path" }],
  constraints: [],
  steps: [
    { id: "step_1", action: "set", changes: { values: { distance: { value: 2.4 } } } },
  ],
  actions: [{ id: "action_reset", type: "reset" }],
};

describe("Math Lab Phase 1 contracts", () => {
  it("normalizes a semantic model without inventing facts", () => {
    const result = normalizeSemanticModel(semantic);
    expect(result.schema_version).toBe("1.0");
    expect(result.entities.map((item) => item.label)).toEqual(["Bạn nhỏ", "Nhà"]);
    expect(result).not.toHaveProperty("answer");
  });

  it("canonicalizes provider problem labels before renderer routing", () => {
    expect(normalizeProblemType(" Cubic equation ")).toBe("cubic_equation");
    expect(normalizeSemanticModel({ ...semantic, problem_type: "Cubic equation" }).problem_type)
      .toBe("cubic_equation");
    expect(normalizeMathScene({
      ...scene,
      metadata: { problem_type: "cubic equation" },
    }).metadata.problem_type).toBe("cubic_equation");
  });

  it("preserves typed source verbatim and blocks a scene that rewrites it", () => {
    const exact = "  6X mũ 3 + 4X mũ 2 - 5X - 1 bằng 0  ";
    const model = normalizeSemanticModel({ ...semantic, source_text: exact });
    expect(model.source_text).toBe(exact);
    expect(hasSourceIntegrityMismatch(exact, {
      metadata: { source_text: exact, source_preserved: true },
    })).toBe(false);
    expect(hasSourceIntegrityMismatch(exact, {
      metadata: { source_text: "6x³+4x²-5x-1=0", source_preserved: true },
    })).toBe(true);
    expect(hasSourceIntegrityMismatch(exact, {
      metadata: { source_text: exact },
    })).toBe(true);
  });

  it("rejects a relation pointing to missing semantic data", () => {
    expect(() => normalizeSemanticModel({
      ...semantic,
      relations: [{ id: "bad", type: "motion", participants: { to: "school" } }],
    })).toThrow(MathLabValidationError);
  });

  it("rejects an unsupported unit before rendering", () => {
    expect(() => normalizeSemanticModel({
      ...semantic,
      quantities: [{ id: "distance", value: 1, unit: "parsec" }],
    })).toThrow(/unit is not supported/);
  });

  it("rejects unregistered renderer descriptors", () => {
    expect(() => normalizeMathScene({
      ...scene,
      visualizations: [{ id: "unsafe", type: "provider_javascript" }],
    })).toThrow(/unregistered visualization/);
    expect(() => validateVisualizationDescriptor({ id: "unsafe", type: "provider_javascript" })).toThrow();
  });

  it("registers every production visualization ID", () => {
    // A hard-coded count only records how many renderers existed on the day
    // it was written. The contract that matters is that every declared id can
    // actually draw, so registering an id without a renderer fails here.
    expect(visualizationRegistry.size).toBe(VISUALIZATION_IDS.length);
    for (const id of VISUALIZATION_IDS) {
      expect(visualizationRegistry.get(id)?.ready).toBe(true);
    }
    expect(visualizationRegistry.get("power_model")?.ready).toBe(true);
    expect(validateVisualizationDescriptor(scene.visualizations[0]).type).toBe("motion_path");
  });

  it("keeps one deterministic world state for steps and reset", () => {
    const initial = createMathWorldState(scene);
    const next = mathWorldReducer(initial, { type: "next" });
    expect(next.world.values.distance.value).toBe(2.4);
    expect(next.world.revision).toBe(1);
    expect(next.progress).toBe(1);
    const previous = mathWorldReducer(next, { type: "previous" });
    expect(previous.world.values.distance.value).toBe(1.2);
    expect(previous.progress).toBe(0);
    const changed = mathWorldReducer(previous, { type: "set_value", id: "distance", value: 3.6 });
    expect(changed.world.values.distance.value).toBe(3.6);
    const reset = mathWorldReducer(changed, { type: "reset" });
    expect(reset.world.values.distance.value).toBe(1.2);
  });

  it("clears a previous scene and safely ignores a late playback tick", () => {
    const initial = createMathWorldState(scene);
    const cleared = mathWorldReducer(initial, { type: "clear" });
    expect(cleared).toBeNull();
    expect(mathWorldReducer(cleared, { type: "set_progress", progress: 0.5 })).toBeNull();
  });

  it("refuses out-of-range what-if values", () => {
    const initial = createMathWorldState(scene);
    expect(mathWorldReducer(initial, { type: "set_value", id: "distance", value: 99 })).toBe(initial);
  });
});
