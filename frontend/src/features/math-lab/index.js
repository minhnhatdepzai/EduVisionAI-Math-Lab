export {
  MATH_DOMAINS,
  MATH_LAB_SCHEMA_VERSION,
  MATH_UNITS,
  hasSourceIntegrityMismatch,
  MathLabValidationError,
  VISUALIZATION_IDS,
  normalizeMathScene,
  normalizeProblemType,
  normalizeSemanticModel,
} from "./schemas/mathLabSchema.js";
export { createMathWorldState, mathWorldReducer } from "./state/mathWorldState.js";
export {
  validateVisualizationDescriptor,
  visualizationDefinition,
  visualizationRegistry,
  readyVisualizations,
} from "./visualizations/registry.js";
export { default as MathLabPage } from "./components/MathLabPage.jsx";
export { default as MathSceneRenderer } from "./renderers/MathSceneRenderer.jsx";
