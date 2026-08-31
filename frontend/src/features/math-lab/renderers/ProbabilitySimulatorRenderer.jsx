import { deriveProbabilityExperiment } from "../derive/deriveCurriculum.js";
import styles from "./renderers.module.css";

export default function ProbabilitySimulatorRenderer({ world, progress, visualization }) {
  const model = deriveProbabilityExperiment(world, visualization?.bindings);
  if (!model) return <p className={styles.unavailable}>Cần tần số biến cố và tổng số phép thử hợp lệ.</p>;
  const visible = progress >= 1 ? model.total : Math.round(Math.max(0, progress) * model.total);
  const visibleSuccess = model.outcomes.slice(0, visible).filter(Boolean).length;
  const phase = progress >= 1 ? 3 : Math.min(2, Math.floor(Math.max(0, progress) * 3));
  return (
    <figure className={`${styles.panel} ${styles.curriculumWide}`}>
      <figcaption className={styles.panelTitle}>Xác suất thực nghiệm · phát lại từng phép thử</figcaption>
      <p className={styles.teachingStep}>{[
        `Bước 1 · Chuẩn bị ${model.total} phép thử`,
        "Bước 2 · Mở lần lượt từng kết quả",
        "Bước 3 · Cộng tần số biến cố sau mỗi lần thử",
        "Bước 4 · Lấy tần số chia tổng số phép thử",
      ][phase]}</p>
      <div className={styles.trialStrip} role="img" aria-label={`${visible} trên ${model.total} phép thử đã hiện`}>
        {model.outcomes.map((success, index) => <span key={index} className={index >= visible ? styles.trialPending : success ? styles.trialSuccess : styles.trialOther}>{index < visible ? (success ? "✓" : "·") : ""}</span>)}
      </div>
      <div className={styles.probabilityCounters}>
        <span>Đã thử <b>{visible}/{model.total}</b></span>
        <span>Biến cố xảy ra <b>{visibleSuccess}</b> lần</span>
        <span>P thực nghiệm <b>{visible ? `${visibleSuccess}/${visible}` : "0/0"}</b></span>
      </div>
      <p className={styles.visualEquation}>{phase >= 3 ? `P = ${model.success}/${model.total} = ${(model.probability * 100).toFixed(1).replace(".", ",")}%` : "Tần số được nối trực tiếp với từng ô kết quả"}</p>
    </figure>
  );
}
