import { deriveSolutionSet } from "../derive/deriveCoverage.js";
import styles from "./renderers.module.css";

const SIZE = { width: 460, height: 120 };
const PAD = 30;
const format = (value) => new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 3 }).format(value);

/**
 * One number line, three questions.
 *
 * An inequality, a product equation and a domain condition all describe a
 * subset of the reals, and drawing that subset is what turns "tập nghiệm" into
 * something a learner reads off instead of recites. Endpoints carry their own
 * meaning: a hollow circle is a value the set excludes, a solid one includes it.
 */
export default function SolutionSetRenderer({ world, progress, visualization, scene }) {
  const model = deriveSolutionSet(world, visualization?.bindings, scene?.metadata?.relations);
  if (!model) {
    return <p className={styles.unavailable}>Cần hệ số và hằng số của biểu thức để dựng tập nghiệm.</p>;
  }
  // Four teaching states; 82% is already the verification/conclusion state,
  // matching what the learner sees in the quadratic and cubic renderers.
  const phase = progress >= 1 ? 3 : Math.min(3, Math.floor(Math.max(0, progress) * 4));
  const { min, max } = model.range;
  const span = max - min || 1;
  const toX = (value) => PAD + ((value - min) / span) * (SIZE.width - PAD * 2);
  const axisY = 62;
  const ticks = [];
  const step = Math.max(1, Math.round(span / 10));
  for (let value = Math.ceil(min); value <= max; value += step) ticks.push(value);
  const markers = model.markers || (model.pairs || []).map((pair) => ({
    ...pair,
    excluded: Boolean(model.excluded),
    label: `${model.symbol} ${model.excluded ? "≠" : "="} ${format(pair.value)}`,
  }));
  const titles = {
    inequality: "Tập nghiệm của bất phương trình",
    excluded_values: "Điều kiện xác định trên trục số",
    product_roots: "Nghiệm của phương trình tích",
    absolute_value: "Hai nhánh của phương trình giá trị tuyệt đối",
    biquadratic: "Ẩn phụ t = x² và các nghiệm đối xứng",
    radical: "Nghiệm đúng và nghiệm ngoại lai",
    rational: "Nghiệm và các giá trị làm mẫu bằng 0",
  };
  const legacySteps = model.kind === "inequality" ? [
    `Bước 1 · Chuyển vế: ${format(model.coefficient)}${model.symbol} ${model.printedOperator} ${format(model.constant)}`,
    model.flipped
      ? `Bước 2 · Chia hai vế cho ${format(model.coefficient)} < 0 nên phải đổi chiều: ${model.printedOperator} thành ${model.operator}`
      : `Bước 2 · Chia hai vế cho ${format(model.coefficient)} > 0, chiều giữ nguyên`,
    `Bước 3 · Điểm biên ${format(model.boundary)} ${model.strict ? "không thuộc" : "thuộc"} tập nghiệm`,
    `Bước 4 · Tập nghiệm là ${model.statement}; thử ${model.symbol} = ${format(model.sample)} thấy thỏa mãn`,
  ] : model.excluded ? [
    "Bước 1 · Liệt kê các mẫu thức có chứa ẩn",
    "Bước 2 · Cho từng mẫu thức bằng 0",
    "Bước 3 · Loại các giá trị vừa tìm khỏi trục số",
    `Bước 4 · Điều kiện xác định: ${model.statement}`,
  ] : [
    "Bước 1 · Đọc hai thừa số của tích",
    "Bước 2 · Tích bằng 0 khi ít nhất một thừa số bằng 0",
    "Bước 3 · Giải từng thừa số bằng 0",
    `Bước 4 · Các nghiệm: ${model.statement}`,
  ];
  const teachingSteps = model.steps || legacySteps;
  const rows = model.rows || (model.pairs || []).map((pair, index) => ({
    label: model.excluded ? `Mẫu thức ${index + 1}` : `Thừa số ${index + 1}`,
    expression: `${pair.factor} = 0`,
    result: `${model.symbol} = ${format(pair.value)}`,
    excluded: Boolean(model.excluded),
  }));

  return (
    <figure className={`${styles.panel} ${styles.curriculumWide}`}>
      <figcaption className={styles.panelTitle}>{titles[model.kind] || "Tập nghiệm trên trục số"}</figcaption>
      <p className={styles.teachingStep}>{teachingSteps[phase] || teachingSteps.at(-1)}</p>
      {model.steps ? (
        <ol className={styles.equationStages}>
          {model.steps.map((item, index) => (
            <li key={item} className={index <= phase ? styles.equationStageVisible : styles.equationStagePending}>
              <small>Bước {index + 1}</small>
              <b>{index <= phase ? item.replace(/^Bước \d+ · /, "") : "…"}</b>
            </li>
          ))}
        </ol>
      ) : null}

      <svg viewBox={`0 0 ${SIZE.width} ${SIZE.height}`} className={styles.solutionAxis} role="img"
        aria-label={`Trục số biểu diễn ${model.statement}`}>
        <defs>
          <marker id="solution-arrow" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto">
            <path d="M0,0 L8,4 L0,8 Z" className={styles.axisArrow} />
          </marker>
        </defs>
        {model.kind === "inequality" && phase >= 3 ? (
          <line className={styles.solutionRay} y1={axisY} y2={axisY}
            x1={toX(model.boundary)}
            x2={model.direction === "right" ? SIZE.width - PAD : PAD} />
        ) : null}
        <line className={styles.graphAxis} x1={PAD - 8} y1={axisY} x2={SIZE.width - PAD + 8} y2={axisY}
          markerEnd="url(#solution-arrow)" />
        {ticks.map((value) => (
          <g key={value}>
            <line className={styles.graphGrid} x1={toX(value)} y1={axisY - 5} x2={toX(value)} y2={axisY + 5} />
            <text className={styles.graphTickLabel} x={toX(value)} y={axisY + 19}>{value}</text>
          </g>
        ))}

        {model.kind === "inequality" && phase >= 2 ? (
          <g>
            <circle cx={toX(model.boundary)} cy={axisY} r="6"
              className={model.strict ? styles.solutionOpenPoint : styles.solutionClosedPoint} />
            <text className={styles.graphPointLabel} x={toX(model.boundary) - 10} y={axisY - 14}>
              {format(model.boundary)}
            </text>
          </g>
        ) : null}

        {model.kind !== "inequality" && phase >= 2 ? markers.map((marker, index) => (
          <g key={`${marker.value}:${marker.label || index}`}>
            <circle cx={toX(marker.value)} cy={axisY} r="6"
              className={marker.excluded ? styles.solutionOpenPoint : styles.solutionClosedPoint} />
            <text className={styles.graphPointLabel} x={toX(marker.value) - 8} y={axisY - 14 - (index % 2) * 14}>
              {marker.label || `${model.symbol} ${marker.excluded ? "≠" : "="} ${format(marker.value)}`}
            </text>
            {marker.excluded ? (
              <text className={styles.solutionCross} x={toX(marker.value)} y={axisY + 5}>×</text>
            ) : null}
          </g>
        )) : null}
      </svg>

      {model.kind !== "inequality" && rows.length ? (
        <ol className={styles.expressionSteps}>
          {rows.map((row, index) => (
            <li key={`${row.label}:${index}`} className={index <= phase ? styles.partialVisible : styles.partialPending}>
              <small>{row.label}</small>
              <span>{row.expression}</span>
              <b>{index <= phase ? row.result : "?"}</b>
            </li>
          ))}
        </ol>
      ) : null}

      {phase >= 3 ? (
        <div className={styles.visualConclusion}>
          <span>{model.kind === "inequality" ? "Tập nghiệm" : model.kind === "excluded_values" ? "Điều kiện xác định" : "Kết luận"}</span>
          <strong>{model.statement}</strong>
          {model.kind === "product_roots" ? (
            <small>Tổng các nghiệm: {format(model.sum)}</small>
          ) : null}
          {model.kind === "excluded_values" ? (
            <small>Các giá trị này làm một mẫu thức bằng 0 nên phải loại.</small>
          ) : null}
          {model.kind === "radical" ? (
            <small>Chấm rỗng có dấu × là nghiệm ngoại lai sinh ra khi bình phương.</small>
          ) : null}
          {model.kind === "rational" ? (
            <small>Chấm rỗng có dấu × làm mẫu bằng 0; chấm đặc mới là nghiệm.</small>
          ) : null}
        </div>
      ) : <p className={styles.fractionHint}>Vòng tròn rỗng là giá trị bị loại, vòng tròn đặc là giá trị được nhận.</p>}
    </figure>
  );
}
