import styles from "./renderers.module.css";

const NAMES = { circle: "hình tròn", square: "hình vuông", triangle: "hình tam giác", rectangle: "hình chữ nhật" };

function periodOf(types) {
  for (let size = 1; size <= Math.floor(types.length / 2); size += 1) {
    if (types.every((type, index) => type === types[index % size])) return size;
  }
  return null;
}

export default function ShapePatternRenderer({ scene, progress }) {
  const shapes = (scene?.objects || []).filter((item) => NAMES[item.type]);
  if (!shapes.length) return <p className={styles.unavailable}>Cần danh sách hình đã nhận diện để dựng overlay.</p>;
  const phase = progress >= 1 ? 3 : Math.min(2, Math.floor(Math.max(0, progress) * 3));
  const types = shapes.map((item) => item.type);
  const period = periodOf(types);
  const counts = types.reduce((result, type) => ({ ...result, [type]: (result[type] || 0) + 1 }), {});
  const next = period ? types[types.length % period] : null;
  return (
    <figure className={`${styles.panel} ${styles.curriculumWide}`}>
      <figcaption className={styles.panelTitle}>Overlay nhận dạng · mỗi hình chỉ được đếm một lần</figcaption>
      <p className={styles.teachingStep}>{[
        "Bước 1 · Khoanh và đánh số từng hình",
        "Bước 2 · Nhóm các hình cùng loại",
        period ? `Bước 3 · Chu kỳ lặp gồm ${period} hình` : "Bước 3 · Kiểm tra số lượng từng loại",
        next ? `Bước 4 · Hình tiếp theo là ${NAMES[next]}` : "Bước 4 · Đọc kết quả đếm từ các nhóm",
      ][phase]}</p>
      <div className={styles.shapeSequence}>
        {shapes.map((shape, index) => <div key={shape.id} className={phase >= 2 && period && index < period ? styles.shapeCycle : styles.shapeOverlay}><span className={styles[`shape_${shape.type}`]} /><b>{phase >= 1 ? index + 1 : ""}</b><small>{NAMES[shape.type]}</small></div>)}
        {next && phase >= 3 ? <div className={styles.shapeNext}><span className={styles[`shape_${next}`]} /><b>?</b><small>tiếp theo</small></div> : null}
      </div>
      <div className={styles.shapeCounts}>{Object.entries(counts).map(([type, count]) => <span key={type}>{NAMES[type]}: <b>{phase >= 1 ? count : "?"}</b></span>)}</div>
      <p className={styles.visualEquation}>{phase >= 3 ? next ? `Chu kỳ ${types.slice(0, period).map((type) => NAMES[type]).join(" → ")} → ${NAMES[next]}` : `Tổng cộng ${shapes.length} hình đã được đánh số` : "Overlay giúp không bỏ sót hoặc đếm trùng"}</p>
    </figure>
  );
}
