import { useEffect, useRef } from "react";

/**
 * One clock for the whole lab.
 *
 * It advances a single `progress` value and nothing else. Every renderer
 * derives its own reading from that, so pausing pauses everything and there is
 * no second timer anywhere to fall out of step.
 *
 * Speed changes how long the demonstration takes to watch, never what the
 * maths says. A journey of eighteen minutes is eighteen minutes at every
 * speed; only the seconds of screen time differ.
 */
const BASE_DURATION_MS = 8000;

export function usePlayback({ playing, progress, speed = 1, onProgress, onFinish }) {
  const frame = useRef(0);
  const previous = useRef(0);
  const latest = useRef({ progress, onProgress, onFinish, speed });
  latest.current = { progress, onProgress, onFinish, speed };

  useEffect(() => {
    if (!playing) {
      previous.current = 0;
      return undefined;
    }

    const step = (timestamp) => {
      const state = latest.current;
      if (!previous.current) previous.current = timestamp;
      const delta = timestamp - previous.current;
      previous.current = timestamp;

      const next = state.progress + (delta / BASE_DURATION_MS) * state.speed;
      if (next >= 1) {
        state.onProgress(1);
        state.onFinish?.();
        return;
      }
      state.onProgress(next);
      frame.current = window.requestAnimationFrame(step);
    };

    frame.current = window.requestAnimationFrame(step);
    return () => {
      window.cancelAnimationFrame(frame.current);
      previous.current = 0;
    };
  }, [playing]);

  useEffect(() => () => window.cancelAnimationFrame(frame.current), []);
}

export const PLAYBACK_SPEEDS = [0.5, 1, 1.5, 2];
