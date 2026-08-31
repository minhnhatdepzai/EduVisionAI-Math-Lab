import { derivePartWhole } from "../derive/deriveCurriculum.js";
import styles from "./renderers.module.css";

export default function PartWholeRenderer({ world, progress, visualization }) {
  const model = derivePartWhole(world, visualization?.bindings);
  if (!model) return <p className={styles.unavailable}>Cần hai giá trị đã biết trong sơ đồ phần–toàn bộ.</p>;
  const phase = progress >= 1 ? 3 : Math.min(2, Math.floor(Math.max(0, progress) * 3));
  const value = (role, resolved) => model.missing === role && phase < 3 ? "?" : resolved;
  return (
    <figure className={`${styles.panel} ${styles.curriculumWide}`}>
      <figcaption className={styles.panelTitle}>Ô trống trong sơ đồ phần–toàn bộ</figcaption>
      <p className={styles.teachingStep}>{[
        "Bước 1 · Xác định ô trống là phần hay toàn bộ",
        "Bước 2 · Đặt hai phần dưới cùng một thanh toàn bộ",
        "Bước 3 · Dùng phép cộng để ghép hoặc phép trừ để tách",
        "Bước 4 · Điền giá trị và kiểm tra phần 1 + phần 2 = toàn bộ",
      ][phase]}</p>
      <div className={styles.partWholeModel}>
        <div className={styles.wholeBar}><small>Toàn bộ</small><b>{value("total", model.total)}</b></div>
        <div className={styles.partsRow} style={{ gridTemplateColumns: `${Math.max(model.first, 1)}fr ${Math.max(model.second, 1)}fr` }}>
          <div><small>Phần 1</small><b>{value("first", model.first)}</b></div>
          <div><small>Phần 2</small><b>{value("second", model.second)}</b></div>
        </div>
      </div>
      <p className={styles.visualEquation}>{phase >= 3 ? `${model.first} + ${model.second} = ${model.total}` : model.missing === "total" ? `${model.first} + ${model.second} = ?` : `${model.total} − ${model.missing === "first" ? model.second : model.first} = ?`}</p>
    </figure>
  );
}
