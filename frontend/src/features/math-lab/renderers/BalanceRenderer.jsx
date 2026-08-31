import { deriveLinearEquation } from "../derive/deriveScene.js";
import styles from "./renderers.module.css";

const decimal = (value) => new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 3 }).format(value);

function exactFraction(value, maximumDenominator = 100) {
  if (!Number.isFinite(value)) return null;
  for (let denominator = 1; denominator <= maximumDenominator; denominator += 1) {
    const numerator = Math.round(value * denominator);
    if (Math.abs(value - numerator / denominator) <= 1e-10) {
      return { numerator, denominator };
    }
  }
  return null;
}

function solutionText(value) {
  const fraction = exactFraction(value);
  if (!fraction || fraction.denominator === 1) return decimal(value);
  return `${fraction.numerator}/${fraction.denominator} ≈ ${decimal(value)}`;
}

function XBlocks({ count }) {
  const wholeBlocks = Number.isInteger(count) && count > 0 && count <= 12;
  return (
    <span className={styles.xBlocks}>
      {wholeBlocks
        ? Array.from({ length: count }, (_, index) => <i key={index}>x</i>)
        : <i>{count}x</i>}
    </span>
  );
}

function Units({ value, muted = false }) {
  const canCount = Number.isInteger(value) && value >= 0 && value <= 12;
  return (
    <span className={muted ? styles.balanceUnitsMuted : styles.balanceUnits}>
      {canCount
        ? Array.from({ length: value }, (_, index) => <i key={index}>1</i>)
        : <b className={styles.balanceNumericToken}>{value}</b>}
    </span>
  );
}

/** Printed → expanded → collected, computed by the backend, shown in order.
 *
 * A bracketed equation is not solved in one move. Without these states the
 * scale would jump from the question straight to `ax = d`, hiding exactly the
 * step the grade-8 lesson is about.
 */
function TransformationStages({ stages, labels, revealed }) {
  if (!stages || stages.length < 2) return null;
  const captions = labels || ["Đề bài", "Phá ngoặc và thu gọn", "Chuyển vế, gộp hạng tử chứa x"];
  return (
    <ol className={styles.equationStages}>
      {stages.map((stage, index) => (
        <li key={stage} className={index <= revealed ? styles.equationStageVisible : styles.equationStagePending}>
          <small>{captions[index] || `Bước ${index + 1}`}</small>
          <b>{index <= revealed ? stage : "…"}</b>
        </li>
      ))}
    </ol>
  );
}

function equationStages(scene) {
  const relation = (scene?.metadata?.relations || [])
    .find((item) => item?.type === "linear_equation_stages");
  const stages = relation?.parameters?.stages;
  return Array.isArray(stages) ? {
    stages,
    labels: Array.isArray(relation?.parameters?.stage_labels)
      ? relation.parameters.stage_labels : null,
    denominators: Array.isArray(relation?.parameters?.denominators)
      ? relation.parameters.denominators : null,
  } : null;
}

export default function BalanceRenderer({ world, progress, visualization, scene }) {
  const equation = deriveLinearEquation(world, visualization?.bindings);
  if (!equation) {
    return <p className={styles.unavailable}>Cần hệ số, hằng số và vế phải để dựng cân phương trình.</p>;
  }
  const phase = progress >= 1 ? 3 : Math.min(3, Math.floor(Math.max(0, progress) * 4));
  const stageData = equationStages(scene);
  const stages = stageData?.stages;
  const tilt = phase === 0 ? 0 : 0;
  // A negative number of physical x-blocks would be misleading. Multiplying
  // both sides by -1 first gives an equivalent equation with positive x tiles.
  const multiplier = equation.coefficient < 0 ? -1 : 1;
  const visible = {
    coefficient: equation.coefficient * multiplier,
    constant: equation.constant * multiplier,
    result: equation.result * multiplier,
    isolated: equation.isolated * multiplier,
    solution: equation.solution,
  };
  const printedSolution = solutionText(visible.solution);
  const inverseOperation = visible.constant > 0
    ? `bớt ${visible.constant}`
    : visible.constant < 0
      ? `thêm ${Math.abs(visible.constant)}`
      : "giữ nguyên";
  const operationSymbol = visible.constant > 0
    ? `− ${visible.constant}`
    : visible.constant < 0
      ? `+ ${Math.abs(visible.constant)}`
      : "+ 0";
  const titles = [
    `Bước 1 · Hai vế đang cân bằng: ${visible.coefficient}x ${visible.constant < 0 ? "−" : "+"} ${Math.abs(visible.constant)} = ${visible.result}`,
    `Bước 2 · Cùng ${inverseOperation} ở cả hai vế`,
    `Bước 3 · Chia cả hai vế cho ${visible.coefficient}`,
    `Bước 4 · Mỗi khối x có giá trị ${printedSolution}`,
  ];
  return (
    <figure className={`${styles.panel} ${styles.balancePanel}`}>
      <figcaption className={styles.panelTitle}>Cân bằng phương trình</figcaption>
      <p className={styles.teachingStep}>{
        stages && stages.length > 2 && phase === 0
          ? `Bước 1 · ${stageData?.labels?.[1] || "Phá ngoặc và thu gọn"}: ${stages[0]} trở thành ${stages[1]}`
          : titles[phase]
      }</p>
      {multiplier === -1 ? <p className={styles.balanceNormalization}>Nhân cả hai vế với −1 trước: hệ số của x trở thành số dương để mô hình khối không sai dấu.</p> : null}
      {stageData?.denominators ? (
        <p className={styles.balanceNormalization}>
          Mẫu số: {stageData.denominators.join(", ")} · BCNN = {stageData.denominators.reduce(
            (result, value) => {
              const gcd = (left, right) => (right ? gcd(right, left % right) : left);
              return Math.abs(result * value) / gcd(result, value);
            }, 1,
          )}
        </p>
      ) : null}
      <TransformationStages stages={stages} labels={stageData?.labels} revealed={phase} />
      <div className={styles.balanceEquation}>
        <span>{phase >= 2 ? "x" : phase >= 1 ? `${visible.coefficient}x` : `${visible.coefficient}x ${visible.constant < 0 ? "−" : "+"} ${Math.abs(visible.constant)}`}</span>
        <b>=</b>
        <span>{phase >= 2 ? printedSolution : phase >= 1 ? visible.isolated : visible.result}</span>
      </div>
      <div className={styles.balanceScale} style={{ "--balance-tilt": `${tilt}deg` }}>
        <div className={styles.balanceBeam}>
          <span className={styles.balancePanLeft}>
            <XBlocks count={phase >= 2 ? 1 : visible.coefficient} />
            {phase === 0 && visible.constant !== 0 ? <Units value={visible.constant} /> : null}
          </span>
          <span className={styles.balancePivot}>▲</span>
          <span className={styles.balancePanRight}>
            {phase >= 2 ? <strong>{printedSolution}</strong> : <Units value={phase >= 1 ? visible.isolated : visible.result} />}
          </span>
        </div>
      </div>
      {phase >= 1 ? (
        <div className={styles.sameOperation}>
          {phase >= 2 ? (
            <><span>Vế trái ÷ {visible.coefficient}</span><b>vẫn cân bằng</b><span>Vế phải ÷ {visible.coefficient}</span></>
          ) : (
            <><span>Vế trái {operationSymbol}</span><b>giữ thăng bằng</b><span>Vế phải {operationSymbol}</span></>
          )}
        </div>
      ) : <p className={styles.fractionHint}>Mọi thao tác phải làm giống nhau ở hai vế.</p>}
      {phase >= 3 ? (
        <div className={styles.visualConclusion}><span>x</span><strong>= {printedSolution}</strong><small>Thay lại vào phương trình ban đầu để kiểm tra hai vế bằng nhau.</small></div>
      ) : null}
    </figure>
  );
}
