import { deriveMotion } from "../derive/deriveScene.js";
import styles from "./renderers.module.css";

/**
 * Why the answer is the answer.
 *
 * Every number below is computed from the world — including the arrival time,
 * which is `start + s / v` and is never written down anywhere. Change the
 * distance and this panel changes with it; that is the difference between
 * showing a formula and showing that the formula holds.
 */
export default function FormulaPanel({ world, progress, visualization }) {
  const motion = deriveMotion(world, progress, visualization?.bindings);
  if (!motion) return null;

  const hours = motion.totalMinutes / 60;
  const distanceKm = motion.totalDistance / 1000;
  const speedKmh = (motion.speed * 3600) / 1000;

  return (
    <figure className={styles.panel}>
      <figcaption className={styles.panelTitle}>Công thức</figcaption>
      <div className={styles.formula}>
        <p className={styles.formulaLine}><b>s</b> = <b>v</b> × <b>t</b></p>
        <p className={styles.formulaLine}><b>t</b> = s ÷ v</p>
        <p className={styles.formulaWork}>
          t = {round(distanceKm)} ÷ {round(speedKmh)} = {round(hours, 2)} giờ
          = {Math.round(motion.totalMinutes)} phút
        </p>
        {motion.startLabel ? (
          <p className={styles.formulaAnswer}>
            {motion.startLabel} + {Math.round(motion.totalMinutes)} phút = <b>{motion.arrivalLabel}</b>
          </p>
        ) : null}
      </div>
    </figure>
  );
}

function round(value, places = 1) {
  const factor = 10 ** places;
  return String(Math.round(value * factor) / factor).replace(".", ",");
}
