import { deriveDataChart } from "../derive/deriveCurriculum.js";
import styles from "./renderers.module.css";

export default function DataChartRenderer({ world, progress, visualization, scene }) {
  const chart = deriveDataChart(world, visualization?.bindings);
  if (!chart) return <p className={styles.unavailable}>Cần ít nhất hai tần số có nhãn để dựng biểu đồ.</p>;
  const phase = progress >= 1 ? 3 : Math.min(2, Math.floor(Math.max(0, progress) * 3));
  const probability = /probability/i.test(scene?.metadata?.problem_type || "");
  const width = 420;
  const height = 250;
  const baseY = 205;
  const plotHeight = 150;
  const slot = 340 / chart.items.length;
  return (
    <figure className={`${styles.panel} ${styles.curriculumWide}`}>
      <figcaption className={styles.panelTitle}>Biểu đồ dữ liệu có chung bảng tần số</figcaption>
      <p className={styles.teachingStep}>{[
        "Bước 1 · Ghép từng nhãn với đúng tần số",
        "Bước 2 · Dựng trục từ 0 với cùng một tỉ lệ",
        "Bước 3 · Dựng chiều cao từng cột từ bảng dữ liệu",
        probability ? "Bước 4 · Tính xác suất từ phần thuận lợi trên tổng số" : "Bước 4 · So sánh và đọc kết luận từ các cột",
      ][phase]}</p>
      <svg viewBox={`0 0 ${width} ${height}`} className={styles.dataChart} role="img" aria-label="Biểu đồ cột theo bảng tần số">
        <line x1="48" y1="24" x2="48" y2={baseY} className={styles.chartAxis} />
        <line x1="48" y1={baseY} x2="402" y2={baseY} className={styles.chartAxis} />
        {chart.items.map((item, index) => {
          const barHeight = phase >= 2 ? (item.value / chart.maximum) * plotHeight : 0;
          const x = 58 + index * slot;
          return <g key={item.id}>
            <rect x={x} y={baseY - barHeight} width={Math.max(22, slot - 16)} height={barHeight} rx="5" className={styles.chartBar} />
            <text x={x + Math.max(22, slot - 16) / 2} y={baseY + 18} textAnchor="middle" className={styles.chartLabel}>{item.label.slice(0, 12)}</text>
            {phase >= 2 ? <text x={x + Math.max(22, slot - 16) / 2} y={baseY - barHeight - 7} textAnchor="middle" className={styles.chartValue}>{item.value}</text> : null}
          </g>;
        })}
        <text x="22" y="28" className={styles.chartLabel}>Số lượng</text>
      </svg>
      {phase >= 2 ? <div className={styles.pictograph} aria-label={`Biểu đồ tranh, mỗi chấm bằng ${chart.iconScale}`}>
        <small>Biểu đồ tranh · ● = {chart.iconScale}</small>
        {chart.items.map((item) => <div key={item.id}><b>{item.label}</b><span>{Array.from({ length: Math.ceil(item.value / chart.iconScale) }, (_, index) => <i key={index}>●</i>)}</span><em>{item.value}</em></div>)}
      </div> : null}
      <div className={styles.chartSummary}>
        <span>Tổng: <b>{phase >= 3 ? chart.total : "?"}</b></span>
        <span>Lớn nhất: <b>{phase >= 3 ? `${chart.winner.label} (${chart.winner.value})` : "?"}</b></span>
        {probability ? chart.items.map((item) => <span key={item.id}>P({item.label}) = <b>{phase >= 3 ? `${item.value}/${chart.total}` : "?"}</b></span>) : null}
      </div>
    </figure>
  );
}
