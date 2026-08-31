import { deriveNumberComparison } from "../derive/deriveCurriculum.js";
import styles from "./renderers.module.css";

const format = (value) => new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 4 }).format(value);

export default function NumberCompareRenderer({ world, progress, visualization, scene }) {
  const model = deriveNumberComparison(world, visualization?.bindings, scene?.metadata?.problem_type);
  if (!model) return <p className={styles.unavailable}>Cần ít nhất hai số để sắp xếp, hoặc một số và hàng cần làm tròn.</p>;
  const phase = progress >= 1 ? 3 : Math.min(2, Math.floor(Math.max(0, progress) * 3));
  const position = (value) => 6 + ((value - model.minimum) / (model.maximum - model.minimum)) * 88;
  const markers = model.mode === "rounding"
    ? [{ label: "Mốc dưới", value: model.lower }, { label: "Số đã cho", value: model.items[0].value }, { label: "Điểm giữa", value: model.midpoint }, { label: "Mốc trên", value: model.upper }]
    : model.items;
  return (
    <figure className={`${styles.panel} ${styles.curriculumWide}`}>
      <figcaption className={styles.panelTitle}>{model.mode === "rounding" ? "Làm tròn bằng khoảng cách đến hai mốc" : "So sánh nhiều số trên cùng một tia số"}</figcaption>
      <p className={styles.teachingStep}>{[
        "Bước 1 · Đọc đầy đủ các số cần xét",
        "Bước 2 · Đặt mỗi số vào đúng vị trí trên cùng thang đo",
        model.mode === "rounding" ? "Bước 3 · So khoảng cách tới mốc dưới và mốc trên" : "Bước 3 · Số ở bên trái nhỏ hơn số ở bên phải",
        "Bước 4 · Viết kết luận từ vị trí các mốc",
      ][phase]}</p>
      <div className={styles.multiNumberLine} role="img" aria-label="Các số được đặt trên cùng một tia số">
        <div className={styles.multiNumberTrack} />
        {phase >= 1 ? markers.map((item, index) => <div key={`${item.label || item.id}-${index}`} className={index === 1 && model.mode === "rounding" ? styles.multiMarkerAccent : styles.multiMarker} style={{ left: `${position(item.value)}%` }}><b>{format(item.value)}</b><span>{item.label}</span></div>) : null}
      </div>
      <p className={styles.visualEquation}>{phase >= 3
        ? model.mode === "rounding"
          ? `${format(model.items[0].value)} làm tròn đến ${format(model.scale)} → ${format(model.result)}`
          : model.sorted.map((item) => format(item.value)).join(" < ")
        : "Quan sát vị trí trước khi kết luận"}</p>
    </figure>
  );
}
