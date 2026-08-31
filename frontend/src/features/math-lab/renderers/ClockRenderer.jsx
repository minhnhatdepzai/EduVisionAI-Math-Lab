import { deriveMotion } from "../derive/deriveScene.js";
import styles from "./renderers.module.css";

/**
 * An analogue clock with no clock in it.
 *
 * It holds no `Date`, no interval and no time of its own: the hands are an
 * angle computed from the same progress the walker uses. That is why the two
 * can never drift apart, and why pausing stops both.
 */
export default function ClockRenderer({ world, progress, visualization }) {
  const motion = deriveMotion(world, progress, visualization?.bindings);
  if (!motion || motion.currentMinutes == null) {
    return <p className={styles.unavailable}>Cần giờ bắt đầu để hiển thị đồng hồ.</p>;
  }

  const minutes = ((motion.currentMinutes % 720) + 720) % 720;
  const minuteAngle = (minutes % 60) * 6;
  // The hour hand creeps between numbers rather than jumping, the way a real
  // one does — at 06:51 it is most of the way from 6 to 7.
  const hourAngle = (minutes / 60) * 30;

  return (
    <figure className={styles.panel}>
      <figcaption className={styles.panelTitle}>Đồng hồ</figcaption>

      <div className={styles.clockRow}>
        <svg viewBox="0 0 120 120" className={styles.clock} role="img" aria-label={`Đồng hồ chỉ ${motion.currentLabel}`}>
          <circle className={styles.clockFace} cx="60" cy="60" r="54" />
          {Array.from({ length: 12 }, (_, index) => {
            const angle = (index * 30 * Math.PI) / 180;
            const outer = 48;
            const inner = index % 3 === 0 ? 40 : 44;
            return (
              <line
                key={index}
                className={index % 3 === 0 ? styles.clockTickMajor : styles.clockTick}
                x1={60 + Math.sin(angle) * inner}
                y1={60 - Math.cos(angle) * inner}
                x2={60 + Math.sin(angle) * outer}
                y2={60 - Math.cos(angle) * outer}
              />
            );
          })}
          <line
            className={styles.hourHand}
            x1="60" y1="60"
            x2={60 + Math.sin((hourAngle * Math.PI) / 180) * 28}
            y2={60 - Math.cos((hourAngle * Math.PI) / 180) * 28}
          />
          <line
            className={styles.minuteHand}
            x1="60" y1="60"
            x2={60 + Math.sin((minuteAngle * Math.PI) / 180) * 42}
            y2={60 - Math.cos((minuteAngle * Math.PI) / 180) * 42}
          />
          <circle className={styles.clockPin} cx="60" cy="60" r="3" />
        </svg>

        <dl className={styles.readout}>
          <div>
            <dt>Bắt đầu</dt>
            <dd>{motion.startLabel}</dd>
          </div>
          <div>
            <dt>Bây giờ</dt>
            <dd className={styles.strong}>{motion.currentLabel}</dd>
          </div>
          <div>
            <dt>Đến nơi</dt>
            <dd>{motion.arrivalLabel}</dd>
          </div>
        </dl>
      </div>
    </figure>
  );
}
