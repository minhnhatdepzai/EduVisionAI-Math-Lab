import { deriveUnitScale } from "../derive/deriveCurriculum.js";
import { deriveMapScale } from "../derive/deriveCoverage.js";
import styles from "./renderers.module.css";

const format = (value) => new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 6 }).format(value);

/**
 * Two rulers that read the same distance.
 *
 * A scale is only believable when both measurements are visible at once: the
 * printed map length above, the real distance below, and the tick marks lining
 * up so the learner can check any intermediate point, not only the answer.
 */
function MapScaleModel({ model, progress }) {
  const phase = progress >= 1 ? 3 : Math.min(2, Math.floor(Math.max(0, progress) * 3));
  return (
    <figure className={`${styles.panel} ${styles.curriculumWide}`}>
      <figcaption className={styles.panelTitle}>Tỉ lệ bản đồ 1 : {format(model.denominator)}</figcaption>
      <p className={styles.teachingStep}>{[
        `Bước 1 · Đo trên bản đồ được ${format(model.mapLength)} ${model.mapUnit}`,
        `Bước 2 · Tỉ lệ 1 : ${format(model.denominator)} nghĩa là 1 ${model.mapUnit} trên bản đồ ứng với ${format(model.denominator)} ${model.mapUnit} thật`,
        `Bước 3 · Nhân: ${format(model.mapLength)} × ${format(model.denominator)} = ${format(model.realInMapUnit)} ${model.mapUnit}`,
        `Bước 4 · Đổi về đơn vị dễ đọc: ${format(model.realLength)} ${model.realUnit}`,
      ][phase]}</p>
      <div className={styles.scaleRulers}>
        <div className={styles.scaleRuler} data-role="map">
          <b>Trên bản đồ ({model.mapUnit})</b>
          <ol>{model.ticks.map((tick) => <li key={`map-${tick.map}`}><i /><span>{format(tick.map)}</span></li>)}</ol>
        </div>
        <div className={styles.scaleRuler} data-role="real">
          <b>Thực tế ({model.realUnit})</b>
          <ol>{model.ticks.map((tick) => (
            <li key={`real-${tick.real}`}><i /><span>{phase >= 2 ? format(tick.real) : "?"}</span></li>
          ))}</ol>
        </div>
      </div>
      <p className={styles.visualEquation}>
        {phase >= 3
          ? `${format(model.mapLength)} ${model.mapUnit} × ${format(model.denominator)} = ${format(model.realLength)} ${model.realUnit}`
          : "Hai thước đo cùng một quãng đường, chỉ khác đơn vị"}
      </p>
    </figure>
  );
}

export default function UnitScaleRenderer({ world, progress, visualization, scene }) {
  if (/map_scale|ti_le_ban_do/i.test(String(scene?.metadata?.problem_type || ""))) {
    const mapScale = deriveMapScale(world, visualization?.bindings);
    return mapScale
      ? <MapScaleModel model={mapScale} progress={progress} />
      : <p className={styles.unavailable}>Cần độ dài đo trên bản đồ và mẫu số của tỉ lệ để dựng hai thước.</p>;
  }
  const model = deriveUnitScale(world, visualization?.bindings);
  if (!model) return <p className={styles.unavailable}>Cần số đo và đơn vị đích cùng loại để đổi đơn vị.</p>;
  const phase = progress >= 1 ? 3 : Math.min(2, Math.floor(Math.max(0, progress) * 3));
  const direction = model.targetIndex > model.sourceIndex ? "sang phải" : "sang trái";
  return (
    <figure className={`${styles.panel} ${styles.curriculumWide}`}>
      <figcaption className={styles.panelTitle}>Thang đổi đơn vị</figcaption>
      <p className={styles.teachingStep}>{[
        `Bước 1 · Đặt ${format(model.sourceValue)} ${model.sourceUnit} lên thang`,
        `Bước 2 · Tìm đơn vị đích ${model.targetUnit}`,
        `Bước 3 · Di chuyển ${direction} và áp dụng hệ số × ${format(model.factor)}`,
        "Bước 4 · Hai cách viết biểu diễn cùng một đại lượng",
      ][phase]}</p>
      <div className={styles.unitLadder}>
        {model.units.map((unit, index) => (
          <div key={unit} className={index === model.sourceIndex ? styles.unitSource : index === model.targetIndex ? styles.unitTarget : styles.unitStep}>
            <b>{unit}</b>
            <span>{index === model.sourceIndex ? format(model.sourceValue) : index === model.targetIndex && phase >= 3 ? format(model.result) : ""}</span>
          </div>
        ))}
      </div>
      <div className={styles.unitArrow} aria-hidden="true">{model.sourceUnit} <span>⟶</span> {model.targetUnit}</div>
      <p className={styles.visualEquation}>{phase >= 2 ? `${format(model.sourceValue)} × ${format(model.factor)} = ${phase >= 3 ? format(model.result) : "?"} ${model.targetUnit}` : "Đếm bậc trước khi dịch dấu thập phân"}</p>
    </figure>
  );
}
