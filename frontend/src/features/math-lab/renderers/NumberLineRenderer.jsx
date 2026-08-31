import { deriveNumberLine } from "../derive/deriveScene.js";
import styles from "./renderers.module.css";

/**
 * Arithmetic as movement along a line.
 *
 * The marker does not merely slide to the answer: small changes take one jump
 * per unit, while larger changes split into tens and a final remainder. A
 * learner watching 8 − 3 sees three unit steps; 58 − 38 sees 10 + 10 + 10 + 8.
 */
export default function NumberLineRenderer({ world, progress, scene, visualization }) {
  const line = deriveNumberLine(
    world,
    progress,
    scene?.metadata?.problem_type,
    visualization?.bindings,
  );
  if (!line) {
    return <p className={styles.unavailable}>Tia số cần đủ số bắt đầu và số thay đổi.</p>;
  }
  const span = line.maximum - line.minimum;
  if (span <= 0) {
    return <p className={styles.unavailable}>Tia số cần khoảng giá trị hợp lệ.</p>;
  }

  const position = (value) => ((value - line.minimum) / span) * 100;
  const tickStep = span > 30 ? 10 : span > 15 ? 5 : 1;
  const ticks = new Set([line.minimum, line.maximum, line.start, line.end]);
  const firstTick = Math.ceil(line.minimum / tickStep) * tickStep;
  for (let value = firstTick; value <= line.maximum + 0.001; value += tickStep) {
    ticks.add(Math.round(value));
  }
  const orderedTicks = [...ticks].sort((left, right) => left - right);

  return (
    <figure className={styles.panel}>
      <figcaption className={styles.panelTitle}>Tia số</figcaption>

      <div className={styles.numberLine}>
        <span className={styles.numberLineTrack} />
        {line.jumps.map((jump, index) => (
          <span
            key={index}
            className={jump.done ? styles.jumpDone : styles.jump}
            style={{
              left: `${position(Math.min(jump.from, jump.to))}%`,
              width: `${Math.abs(position(jump.to) - position(jump.from))}%`,
            }}
          />
        ))}
        <span className={styles.numberLineMarker} style={{ left: `${position(line.current)}%` }}>
          <b>{round(line.current)}</b>
        </span>
        <span className={styles.numberLineTicks}>
          {orderedTicks.map((value) => (
            <i key={value} style={{ left: `${position(value)}%` }} data-label={value} />
          ))}
        </span>
      </div>

      <dl className={styles.readout}>
        <div><dt>Bắt đầu</dt><dd>{line.start}</dd></div>
        <div>
          <dt>{line.operation < 0 ? "Bớt" : "Thêm"}</dt>
          <dd>{Math.abs(line.change)}</dd>
        </div>
        <div><dt>Kết quả</dt><dd className={styles.strong}>{line.end}</dd></div>
      </dl>
    </figure>
  );
}

function round(value) {
  return Math.round(value * 10) / 10;
}
