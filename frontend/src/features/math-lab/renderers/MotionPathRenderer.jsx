import { boundId, deriveMotion } from "../derive/deriveScene.js";
import { deriveSegmentedMotion } from "../derive/deriveCoverage.js";
import styles from "./renderers.module.css";

const legFormat = (value) => new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 2 }).format(value);

/**
 * A route made of legs, each with its own speed and its own duration.
 *
 * One speed across the whole journey is the wrong model here: the average
 * speed of two equal-distance legs is not the average of the two speeds, and
 * only separate legs make that visible.
 */
function SegmentedMotionModel({ model, progress }) {
  const clamped = Math.max(0, Math.min(1, progress));
  const elapsed = clamped * model.totalDuration;
  const travelled = model.legs.reduce((sum, leg) => {
    if (elapsed >= leg.endTime) return sum + leg.distance;
    if (elapsed <= leg.startTime) return sum;
    return sum + (elapsed - leg.startTime) * leg.speed;
  }, 0);
  const activeIndex = model.legs.findIndex((leg) => elapsed < leg.endTime);
  const active = activeIndex === -1 ? model.legs.length - 1 : activeIndex;
  return (
    <figure className={`${styles.panel} ${styles.curriculumWide}`}>
      <figcaption className={styles.panelTitle}>Hành trình nhiều chặng</figcaption>
      <p className={styles.teachingStep}>
        {clamped >= 1
          ? `Bước ${model.legs.length + 1} · Tổng ${legFormat(model.totalDistance)} ${model.distanceUnit} trong ${legFormat(model.totalDuration)} giờ, vận tốc trung bình ${legFormat(model.averageSpeed)} ${model.distanceUnit}/giờ`
          : `Chặng ${active + 1} · ${legFormat(model.legs[active].distance)} ${model.distanceUnit} với vận tốc ${legFormat(model.legs[active].speed)} ${model.distanceUnit}/giờ mất ${legFormat(model.legs[active].duration)} giờ`}
      </p>
      <div className={styles.segmentRoute}>
        {model.legs.map((leg, index) => (
          <div key={leg.index} className={styles.segmentLeg}
            style={{ flexGrow: leg.distance }}
            data-state={elapsed >= leg.endTime ? "done" : index === active ? "active" : "pending"}>
            <span>{legFormat(leg.distance)} {model.distanceUnit}</span>
            <b>{legFormat(leg.speed)} {model.distanceUnit}/giờ</b>
            <small>{legFormat(leg.duration)} giờ</small>
          </div>
        ))}
      </div>
      <div className={styles.segmentReadout}>
        <span>Đã đi <b>{legFormat(travelled)} {model.distanceUnit}</b></span>
        <span>Đã mất <b>{legFormat(elapsed)} giờ</b></span>
        <span>Trung bình <b>{clamped >= 1 ? `${legFormat(model.averageSpeed)} ${model.distanceUnit}/giờ` : "?"}</b></span>
      </div>
      <p className={styles.visualEquation}>
        {clamped >= 1
          ? `${model.legs.map((leg) => `${legFormat(leg.distance)} ÷ ${legFormat(leg.speed)}`).join(" + ")} = ${legFormat(model.totalDuration)} giờ`
          : "Mỗi chặng có thời gian riêng; cộng lại mới ra tổng thời gian"}
      </p>
    </figure>
  );
}

/**
 * The journey, drawn to scale.
 *
 * The walker's position is `distanceTravelled / totalDistance`. Nothing here
 * animates on its own and no pixel offset is written by hand — move the
 * progress and the figure moves, because that ratio is what a position along
 * a route means.
 */
export default function MotionPathRenderer({ world, progress, scene, visualization }) {
  const bindings = visualization?.bindings;
  if (/multi_segment|multi_leg|segmented_motion/i.test(String(scene?.metadata?.problem_type || ""))) {
    const segmented = deriveSegmentedMotion(world, bindings);
    if (segmented) return <SegmentedMotionModel model={segmented} progress={progress} />;
    return <p className={styles.unavailable}>Cần quãng đường và vận tốc của từng chặng để dựng hành trình nhiều chặng.</p>;
  }
  const motion = deriveMotion(world, progress, bindings);
  if (!motion) {
    return <p className={styles.unavailable}>Cần quãng đường và vận tốc để dựng hành trình.</p>;
  }

  const objects = scene?.objects || [];
  const label = (semanticRef, fallback) =>
    objects.find((item) => item.semantic_ref === semanticRef)?.label || fallback;
  const origin = boundId(bindings, "origin", ["home"]);
  const destination = boundId(bindings, "destination", ["school"]);
  const movingEntity = boundId(bindings, "moving_entity", ["lan"]);

  const percent = motion.progress * 100;
  // Ticks every 300 m, which is what a Year 5 problem is usually read in.
  const step = motion.totalDistance > 2000 ? 500 : 300;
  const ticks = [];
  for (let metres = 0; metres <= motion.totalDistance + 1; metres += step) {
    ticks.push(Math.min(metres, motion.totalDistance));
  }
  if (ticks[ticks.length - 1] < motion.totalDistance) ticks.push(motion.totalDistance);

  return (
    <figure className={styles.panel}>
      <figcaption className={styles.panelTitle}>Hành trình</figcaption>

      <div className={styles.route}>
        <span className={styles.routeEnd}>
          <b>🏠</b>
          <small>{label(origin, "Xuất phát")}</small>
        </span>

        <span className={styles.routeTrack}>
          <span className={styles.routeDone} style={{ width: `${percent}%` }} />
          <span
            className={styles.walker}
            style={{ left: `${percent}%` }}
            aria-hidden="true"
          >
            <b>🚶</b>
            <small>{label(movingEntity, "Đang đi")}</small>
          </span>
          <span className={styles.ticks}>
            {ticks.map((metres) => (
              <i
                key={metres}
                style={{ left: `${(metres / motion.totalDistance) * 100}%` }}
                data-label={`${Math.round(metres)} m`}
              />
            ))}
          </span>
        </span>

        <span className={styles.routeEnd}>
          <b>🏫</b>
          <small>{label(destination, "Đích")}</small>
        </span>
      </div>

      <dl className={styles.readout}>
        <div>
          <dt>Đã đi</dt>
          <dd>{Math.round(motion.distanceTravelled)} m</dd>
        </div>
        <div>
          <dt>Còn lại</dt>
          <dd>{Math.round(motion.distanceRemaining)} m</dd>
        </div>
        <div>
          <dt>Tổng quãng đường</dt>
          <dd>{Math.round(motion.totalDistance)} m</dd>
        </div>
      </dl>
    </figure>
  );
}
