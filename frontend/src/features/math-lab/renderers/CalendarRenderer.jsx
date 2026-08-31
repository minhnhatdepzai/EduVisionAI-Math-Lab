import { deriveCalendarDuration } from "../derive/deriveCoverage.js";
import styles from "./renderers.module.css";

/**
 * A month grid with the span actually shaded.
 *
 * Elapsed-day questions were previously routed through a clock, which can only
 * show a time of day. Counting on the grid is what makes a month boundary
 * visible instead of arithmetic the learner has to trust.
 */
export default function CalendarRenderer({ world, progress, visualization, scene }) {
  const model = deriveCalendarDuration(
    world,
    visualization?.bindings,
    scene?.metadata?.relations,
  );
  if (!model) {
    return <p className={styles.unavailable}>Cần ngày bắt đầu, số ngày và tháng để dựng lịch.</p>;
  }
  const phase = progress >= 1 ? 3 : Math.min(2, Math.floor(Math.max(0, progress) * 3));
  const revealedUntil = phase === 0
    ? model.startDay
    : phase === 1
      ? model.startDay + Math.floor(model.duration / 2)
      : model.startDay + model.duration;
  return (
    <figure className={`${styles.panel} ${styles.curriculumWide}`}>
      <figcaption className={styles.panelTitle}>Lịch tháng {model.month} · đếm khoảng thời gian</figcaption>
      <p className={styles.teachingStep}>{[
        `Bước 1 · Đánh dấu ngày bắt đầu ${model.startDay}/${model.month}${model.startWeekday ? ` (${model.startWeekday})` : ""}`,
        `Bước 2 · Đếm tới ${model.duration} ngày trên lịch, không cộng nhẩm`,
        model.rolledOver
          ? `Bước 3 · Tháng ${model.month} chỉ có ${model.daysInMonth} ngày nên phải sang tháng ${model.endMonth}`
          : `Bước 3 · Vẫn nằm trong tháng ${model.month}`,
        `Bước 4 · Ngày kết thúc là ${model.endDay}/${model.endMonth}${model.endWeekday ? ` (${model.endWeekday})` : ""}`,
      ][phase]}</p>
      <ol className={styles.calendarGrid} aria-label={`Lịch tháng ${model.month}`}>
        {model.cells.map((cell) => {
          const classes = [styles.calendarCell];
          if (cell.day >= model.startDay && cell.day <= revealedUntil) classes.push(styles.calendarInSpan);
          if (cell.isStart) classes.push(styles.calendarStart);
          if (cell.isEnd && phase >= 3) classes.push(styles.calendarEnd);
          return <li key={cell.day} className={classes.join(" ")}>{cell.day}</li>;
        })}
      </ol>
      <div className={styles.segmentReadout}>
        <span>Bắt đầu <b>{model.startDay}/{model.month}</b></span>
        <span>Kéo dài <b>{model.duration} ngày</b></span>
        <span>Kết thúc <b>{phase >= 3 ? `${model.endDay}/${model.endMonth}` : "?"}</b></span>
      </div>
      <p className={styles.visualEquation}>
        {phase >= 3
          ? model.rolledOver
            ? `${model.startDay} + ${model.duration} = ${model.startDay + model.duration} > ${model.daysInMonth} ngày của tháng ${model.month} → ${model.endDay}/${model.endMonth}`
            : `${model.startDay} + ${model.duration} = ${model.endDay} (ngày ${model.endDay}/${model.endMonth})`
          : "Mỗi ô là một ngày; đếm trên lịch để không quên số ngày của tháng"}
      </p>
    </figure>
  );
}
