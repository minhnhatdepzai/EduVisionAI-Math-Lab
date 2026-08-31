import { derivePlaceValue } from "../derive/deriveCurriculum.js";
import styles from "./renderers.module.css";

const format = (value) => new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 3 }).format(value);

export default function PlaceValueRenderer({ world, progress, visualization }) {
  const model = derivePlaceValue(world, visualization?.bindings);
  if (!model) return <p className={styles.unavailable}>Cần một số nhỏ hơn một triệu để dựng bảng giá trị hàng.</p>;
  const phase = progress >= 1 ? 3 : Math.min(2, Math.floor(Math.max(0, progress) * 3));
  return (
    <figure className={`${styles.panel} ${styles.curriculumWide}`}>
      <figcaption className={styles.panelTitle}>Giá trị hàng · từ khối cơ số 10 đến dạng số</figcaption>
      <p className={styles.teachingStep}>{[
        "Bước 1 · Đặt từng chữ số vào đúng cột",
        "Bước 2 · Mỗi chữ số nhận giá trị theo vị trí",
        "Bước 3 · Đổi mỗi cột thành nhóm khối cơ số 10",
        "Bước 4 · Ghép các giá trị hàng để đọc lại số",
      ][phase]}</p>
      <div className={styles.placeTable} role="table" aria-label={`Bảng giá trị hàng của ${format(model.value)}`}>
        {model.columns.map((column) => (
          <div key={column.power} className={styles.placeColumn} role="cell">
            <small>{column.label}</small>
            <b>{column.digit}</b>
            <span>{phase >= 1 ? format(column.placeValue) : "?"}</span>
            <div className={styles.baseTenBlocks} aria-hidden="true">
              {phase >= 2 ? Array.from({ length: column.digit }, (_, index) => <i key={index} />) : null}
            </div>
          </div>
        ))}
      </div>
      <p className={styles.visualEquation}>
        {phase >= 3 ? `${model.expanded.map(format).join(" + ")} = ${format(model.value)}` : "Giá trị số = tổng giá trị của các hàng"}
      </p>
    </figure>
  );
}
