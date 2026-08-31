import { normalizeMathScene } from "../schemas/mathLabSchema.js";

/*
 * `progress` is the single number playback owns, in [0, 1].
 *
 * Every representation derives its own reading from it — where Lan is, what
 * the clock says, how far along the timeline sits — so they cannot disagree.
 * It is separate from `stepIndex`, which walks the discrete teaching steps the
 * pedagogy planner produced; a scene can have both.
 */

function clone(value) {
  return structuredClone(value);
}

function applyStep(world, step) {
  const changes = step?.changes?.values;
  if (!changes || typeof changes !== "object" || Array.isArray(changes)) return world;
  const values = { ...world.values };
  for (const [id, patch] of Object.entries(changes)) {
    if (!values[id] || !patch || typeof patch !== "object") continue;
    values[id] = { ...values[id], ...patch };
  }
  return { revision: world.revision + 1, values };
}

function replay(scene, stepIndex) {
  let world = clone(scene.world);
  for (let index = 0; index < stepIndex; index += 1) {
    world = applyStep(world, scene.steps[index]);
  }
  return world;
}

export function createMathWorldState(sceneInput) {
  const scene = normalizeMathScene(sceneInput);
  return {
    scene,
    initialWorld: clone(scene.world),
    world: clone(scene.world),
    stepIndex: 0,
    progress: 0,
    playback: "paused",
  };
}

export function mathWorldReducer(state, action) {
  if (action.type === "clear") return null;
  if (action.type === "load") return createMathWorldState(action.scene);
  // Playback callbacks can finish one tick after a scene is cleared.  Ignore
  // those actions instead of dereferencing a stale/null world.
  if (!state) return state;

  switch (action.type) {
    case "play":
      // Starting from the end replays rather than sitting still.
      return {
        ...state,
        progress: state.progress >= 1 ? 0 : state.progress,
        playback: "playing",
      };
    case "pause":
      return { ...state, playback: "paused" };
    case "reset":
      return {
        ...state,
        world: clone(state.initialWorld),
        stepIndex: 0,
        progress: 0,
        playback: "paused",
      };

    case "set_progress": {
      const progress = Math.min(Math.max(Number(action.progress) || 0, 0), 1);
      // Reaching the end stops playback rather than looping: the journey
      // finished, and a learner should see it finished.
      const playback = progress >= 1 ? "paused" : state.playback;
      return { ...state, progress, playback };
    }

    case "scrub":
      // A hand on the scrubber takes over from playback.
      return {
        ...state,
        progress: Math.min(Math.max(Number(action.progress) || 0, 0), 1),
        playback: "paused",
      };
    case "set_value": {
      const current = state.world.values[action.id];
      if (!current || !current.editable) return state;
      const value = Number(action.value);
      if (!Number.isFinite(value)) return state;
      if (current.minimum != null && value < current.minimum) return state;
      if (current.maximum != null && value > current.maximum) return state;
      return {
        ...state,
        world: {
          revision: state.world.revision + 1,
          values: { ...state.world.values, [action.id]: { ...current, value } },
        },
      };
    }
    case "next": {
      if (state.stepIndex >= state.scene.steps.length) return { ...state, playback: "paused" };
      const stepIndex = state.stepIndex + 1;
      return {
        ...state,
        world: applyStep(state.world, state.scene.steps[state.stepIndex]),
        stepIndex,
        progress: stepIndex / state.scene.steps.length,
        playback: "paused",
      };
    }
    case "previous": {
      const stepIndex = Math.max(0, state.stepIndex - 1);
      const progress = state.scene.steps.length ? stepIndex / state.scene.steps.length : 0;
      return {
        ...state,
        world: replay(state.scene, stepIndex),
        stepIndex,
        progress,
        playback: "paused",
      };
    }
    default:
      return state;
  }
}
