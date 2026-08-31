import { deriveExpressionTree, deriveFactorial } from "../derive/deriveCoverage.js";
import styles from "./renderers.module.css";

const format = (value) => new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 4 }).format(value);

const formatIntegerString = (value) => String(value).replace(/\B(?=(\d{3})+(?!\d))/g, ".");

function FactorialModel({ model, progress }) {
  const phase = progress >= 1 ? 3 : Math.min(2, Math.floor(Math.max(0, progress) * 4));
  const visibleCheckpoints = phase >= 2
    ? model.checkpoints
    : model.checkpoints.slice(0, Math.max(1, Math.ceil(model.checkpoints.length / 4)));
  return (
    <figure className={`${styles.panel} ${styles.curriculumWide} ${styles.factorialPanel}`}>
      <figcaption className={styles.panelTitle}>Giai thừa · tích giảm dần đến 1</figcaption>
      <p className={styles.teachingStep}>{[
        `Bước 1 · ${model.input}! không phải ${model.input} × ${model.input}; ký hiệu này là tích từ ${model.input} giảm dần đến 1`,
        `Bước 2 · Khai triển: ${model.input}! = ${model.expression}`,
        "Bước 3 · Nhân tuần tự và đối chiếu các mốc 10!, 20!, ... để không mất thừa số",
        `Bước 4 · Kết quả có ${model.digits} chữ số và ${model.trailingZeros} số 0 tận cùng`,
      ][phase]}</p>
      <div className={styles.factorialDefinition}>
        <strong>{model.input}!</strong>
        <span>=</span>
        <b>{model.expression}</b>
      </div>
      <ol className={styles.factorialCheckpoints} aria-label="Các mốc tích giai thừa">
        {visibleCheckpoints.map((checkpoint) => (
          <li key={checkpoint.factor}>
            <b>{checkpoint.factor}!</b>
            <span>{formatIntegerString(checkpoint.value)}</span>
          </li>
        ))}
      </ol>
      {phase >= 3 ? (
        <div className={styles.factorialConclusion}>
          <span>Kết quả chính xác của {model.input}!</span>
          <strong>{formatIntegerString(model.result)}</strong>
          <small>{model.digits} chữ số · {model.trailingZeros} số 0 tận cùng</small>
        </div>
      ) : <p className={styles.fractionHint}>Mỗi mốc bằng mốc trước nhân tiếp các số tự nhiên còn thiếu.</p>}
    </figure>
  );
}

/**
 * A mixed expression reduced in the order its precedence requires.
 *
 * Left-to-right is the mistake this scene exists to prevent, so each
 * reduction is a separate visible state: the operands it consumed stay on
 * screen next to the value that replaced them.
 */
export default function ExpressionTreeRenderer({ world, progress, visualization, scene }) {
  if (/factorial/i.test(String(scene?.metadata?.problem_type || ""))) {
    const factorial = deriveFactorial(world, visualization?.bindings);
    return factorial
      ? <FactorialModel model={factorial} progress={progress} />
      : <p className={styles.unavailable}>Cần số nguyên từ 0 đến 500 để tính giai thừa.</p>;
  }
  const tree = deriveExpressionTree(
    world,
    visualization?.bindings,
    scene?.metadata?.relations,
  );
  if (!tree) {
    return <p className={styles.unavailable}>Cần các số hạng và thứ tự phép tính của biểu thức.</p>;
  }
  const total = tree.steps.length;
  const revealed = progress >= 1 ? total : Math.min(total - 1, Math.floor(Math.max(0, progress) * total));
  const current = tree.steps[Math.max(0, Math.min(total - 1, revealed - 1))];
  return (
    <figure className={`${styles.panel} ${styles.curriculumWide}`}>
      <figcaption className={styles.panelTitle}>Cây biểu thức · thứ tự thực hiện phép tính</figcaption>
      <p className={styles.teachingStep}>
        {revealed === 0
          ? `Bước 1 · Đọc biểu thức ${tree.expression} và tìm phép tính ưu tiên`
          : `Bước ${revealed + 1} · ${current.level === 2 ? "Nhân chia trước" : "Cộng trừ sau"}: ${current.left} ${current.operator} ${current.right} = ${format(current.value)}`}
      </p>
      <div className={styles.expressionRow}>
        {tree.operands.map((operand, index) => (
          <span key={`${operand.label}-${index}`}>
            {index ? <i className={styles.expressionOperator}>{tree.operators[index - 1]}</i> : null}
            <b>{operand.label}</b>
          </span>
        ))}
      </div>
      <ol className={styles.expressionSteps}>
        {tree.steps.map((step, index) => (
          <li key={`${step.left}-${step.operator}-${step.right}`}
            className={index < revealed ? styles.partialVisible : styles.partialPending}>
            <small>{step.level === 2 ? "Ưu tiên 1 · nhân chia" : "Ưu tiên 2 · cộng trừ"}</small>
            <span>{step.left} {step.operator} {step.right}</span>
            <b>{index < revealed ? format(step.value) : "?"}</b>
          </li>
        ))}
      </ol>
      {revealed >= total ? (
        <div className={styles.visualConclusion}>
          <span>Giá trị biểu thức</span>
          <strong>{tree.expression} = {format(tree.result)}</strong>
        </div>
      ) : <p className={styles.fractionHint}>Phép nhân và chia được rút gọn trước, rồi mới đến cộng và trừ.</p>}
    </figure>
  );
}
