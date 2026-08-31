import { deriveMotion, formatClock } from "../derive/deriveScene.js";
import styles from "./renderers.module.css";

/**
 * The same journey again, measured in minutes instead of metres.
 *
 * Showing one quantity two ways is the point: a learner who can see that
 * "half the distance" and "half the time" land together has understood that
 * the speed is constant. The pointer reads the same progress as the walker.
 */
export default function TimelineRenderer({ world, progress, visualization }) {
  const motion = deriveMotion(world, progress, visualization?.bindings);
  if (!motion) {
    return <p className={styles.unavailable}>Cần quãng đường và vận tốc để dựng dòng thời gian.</p>;
  }

  const total = motion.totalMinutes;
  const step = total > 60 ? 15 : total > 20 ? 6 : 3;
  const marks = [];
  for (let minute = 0; minute <= total + 0.001; minute += step) {
    marks.push(Math.min(minute, total));
  }
  if (marks[marks.length - 1] < total - 0.001) marks.push(total);

  return (
    <figure className={styles.panel}>
      <figcaption className={styles.panelTitle}>Dòng thời gian</figcaption>

      <div className={styles.timeline}>
        <span className={styles.timelineTrack}>
          <span className={styles.timelineDone} style={{ width: `${motion.progress * 100}%` }} />
          <span className={styles.timelinePointer} style={{ left: `${motion.progress * 100}%` }}>
            <b>{Math.round(motion.elapsedMinutes)}′</b>
          </span>
        </span>

        <span className={styles.timelineMarks}>
          {marks.map((minute) => (
            <i key={minute} style={{ left: `${(minute / total) * 100}%` }}>
              <em>{Math.round(minute)}′</em>
              {motion.startMinutes == null ? null : (
                <small>{formatClock(motion.startMinutes + minute)}</small>
              )}
            </i>
          ))}
        </span>
      </div>

      <dl className={styles.readout}>
        <div>
          <dt>Đã trôi qua</dt>
          <dd>{Math.round(motion.elapsedMinutes)} phút</dd>
        </div>
        <div>
          <dt>Tổng thời gian</dt>
          <dd className={styles.strong}>{Math.round(total)} phút</dd>
        </div>
      </dl>
    </figure>
  );
}
