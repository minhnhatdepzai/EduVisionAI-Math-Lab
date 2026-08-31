import { deriveColumnAlgorithm } from "../derive/deriveCurriculum.js";
import {
  deriveDecimalScaling,
  deriveLongDivision,
  deriveLongMultiplication,
} from "../derive/deriveCoverage.js";
import styles from "./renderers.module.css";

const format = (value) => new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 6 }).format(value);

/** One partial product per multiplier digit, each shifted into its place. */
function LongMultiplicationModel({ model, progress }) {
  const total = model.partials.length + (model.needsSum ? 1 : 0);
  const revealed = progress >= 1 ? total : Math.min(total - 1, Math.floor(Math.max(0, progress) * total));
  return (
    <figure className={`${styles.panel} ${styles.curriculumWide}`}>
      <figcaption className={styles.panelTitle}>Nhân nhiều chữ số theo cột</figcaption>
      <p className={styles.teachingStep}>
        {revealed === 0
          ? `Bước 1 · Viết ${format(model.left)} trên, ${format(model.right)} dưới và căn thẳng hàng đơn vị`
          : revealed <= model.partials.length
            ? `Bước ${revealed + 1} · Nhân với chữ số hàng ${["đơn vị", "chục", "trăm", "nghìn", "chục nghìn", "trăm nghìn"][model.partials[revealed - 1].position] || `10^${model.partials[revealed - 1].position}`}: ${format(model.left)} × ${model.partials[revealed - 1].digit} = ${format(model.partials[revealed - 1].raw)}`
            : `Bước ${total + 1} · Cộng các tích riêng đã dịch đúng hàng để được ${format(model.result)}`}
      </p>
      {model.swapped ? (
        <p className={styles.groupingCommutative}>
          Đổi thứ tự để đặt tính gọn hơn: {format(model.originalLeft)} × {format(model.originalRight)} = {format(model.left)} × {format(model.right)}.
        </p>
      ) : null}
      <ol className={styles.partialProducts}>
        {model.partials.map((partial, index) => (
          <li key={partial.position} className={index < revealed ? styles.partialVisible : styles.partialPending}>
            <span>{format(model.left)} × {partial.digit}{partial.position ? ` × ${10 ** partial.position}` : ""}</span>
            <b>{index < revealed ? format(partial.value) : "?"}</b>
          </li>
        ))}
      </ol>
      <p className={styles.visualEquation}>
        {revealed >= total
          ? `${format(model.originalLeft)} × ${format(model.originalRight)} = ${model.partials.map((item) => format(item.value)).join(" + ")} = ${format(model.result)}`
          : "Mỗi tích riêng phải lùi sang trái đúng bằng hàng của chữ số nhân"}
      </p>
    </figure>
  );
}

/** Long division, one brought-down digit and one quotient digit per step. */
function LongDivisionModel({ model, progress }) {
  const total = model.steps.length;
  const revealed = progress >= 1 ? total : Math.min(total - 1, Math.floor(Math.max(0, progress) * total));
  const step = model.steps[Math.max(0, Math.min(total - 1, revealed - 1))];
  return (
    <figure className={`${styles.panel} ${styles.curriculumWide}`}>
      <figcaption className={styles.panelTitle}>Chia dài · hạ từng chữ số</figcaption>
      <p className={styles.teachingStep}>
        {revealed === 0
          ? `Bước 1 · Đặt ${format(model.dividend)} chia ${format(model.divisor)} và lấy chữ số đầu tiên`
          : `Bước ${revealed + 1} · Hạ ${step.broughtDown}: ${step.current} ÷ ${model.divisor} được ${step.quotientDigit}, trừ ${step.product} còn ${step.remainder}`}
      </p>
      <ol className={styles.divisionSteps}>
        {model.steps.map((item, index) => (
          <li key={item.index} className={index < revealed ? styles.partialVisible : styles.partialPending}>
            <span>Hạ {item.broughtDown} → {item.current}</span>
            <b>{index < revealed ? `${item.quotientDigit} dư ${item.remainder}` : "?"}</b>
          </li>
        ))}
      </ol>
      <p className={styles.visualEquation}>
        {revealed >= total
          ? `${format(model.dividend)} ÷ ${format(model.divisor)} = ${format(model.quotient)}${model.exact ? "" : ` (dư ${format(model.remainder)})`} · kiểm tra ${format(model.divisor)} × ${format(model.quotient)} + ${format(model.remainder)} = ${format(model.dividend)}`
          : "Mỗi lần hạ một chữ số, thương lớn thêm đúng một chữ số"}
      </p>
    </figure>
  );
}

/** Decimal x/÷ taught as a whole-number operation plus a point shift. */
function DecimalScalingModel({ model, progress }) {
  const phase = progress >= 1 ? 3 : Math.min(2, Math.floor(Math.max(0, progress) * 3));
  const multiply = model.operation === "multiply";
  return (
    <figure className={`${styles.panel} ${styles.curriculumWide}`}>
      <figcaption className={styles.panelTitle}>
        {multiply ? "Nhân số thập phân" : "Chia số thập phân"}
      </figcaption>
      <p className={styles.teachingStep}>{multiply ? [
        `Bước 1 · Bỏ dấu phẩy: ${format(model.leftWhole)} và ${format(model.rightWhole)}`,
        `Bước 2 · Nhân như số tự nhiên: ${format(model.leftWhole)} × ${format(model.rightWhole)} = ${format(model.wholeResult)}`,
        `Bước 3 · Đếm tổng chữ số thập phân: ${model.leftPlaces} + ${model.rightPlaces} = ${model.resultPlaces}`,
        `Bước 4 · Đặt lại dấu phẩy: ${format(model.result)}`,
      ][phase] : [
        `Bước 1 · Nhân cả số bị chia và số chia với 10^${model.shift}`,
        `Bước 2 · Phép chia trở thành ${format(model.scaledLeft)} ÷ ${format(model.scaledRight)}`,
        "Bước 3 · Thương không đổi vì cả hai vế cùng nhân một số",
        `Bước 4 · Kết quả là ${format(model.result)}`,
      ][phase]}</p>
      <div className={styles.decimalShift}>
        <span><b>{format(model.left)}</b> {multiply ? "×" : "÷"} <b>{format(model.right)}</b></span>
        <span aria-hidden="true">⟶</span>
        <span>
          <b>{multiply ? format(model.leftWhole) : format(model.scaledLeft)}</b>
          {multiply ? " × " : " ÷ "}
          <b>{multiply ? format(model.rightWhole) : format(model.scaledRight)}</b>
        </span>
      </div>
      <p className={styles.visualEquation}>
        {phase >= 3
          ? `${format(model.left)} ${multiply ? "×" : "÷"} ${format(model.right)} = ${format(model.result)}`
          : multiply
            ? "Tích giữ nguyên chữ số, chỉ dấu phẩy phải đặt lại"
            : "Nhân cả hai vế cùng một lũy thừa của 10 không làm đổi thương"}
      </p>
    </figure>
  );
}

export default function ColumnAlgorithmRenderer({ world, progress, visualization, scene }) {
  const problemType = String(scene?.metadata?.problem_type || "");
  if (/decimal_arithmetic_(multiplication|division)/i.test(problemType)) {
    const decimal = deriveDecimalScaling(world, visualization?.bindings, problemType);
    return decimal
      ? <DecimalScalingModel model={decimal} progress={progress} />
      : <p className={styles.unavailable}>Cần đúng hai số thập phân để đặt tính.</p>;
  }
  if (/multiplication/i.test(problemType)) {
    const multiplication = deriveLongMultiplication(world, visualization?.bindings);
    return multiplication
      ? <LongMultiplicationModel model={multiplication} progress={progress} />
      : <p className={styles.unavailable}>Cần hai số tự nhiên để nhân theo cột.</p>;
  }
  if (/division/i.test(problemType)) {
    const division = deriveLongDivision(world, visualization?.bindings);
    return division
      ? <LongDivisionModel model={division} progress={progress} />
      : <p className={styles.unavailable}>Cần số bị chia và số chia để đặt phép chia dài.</p>;
  }
  const model = deriveColumnAlgorithm(world, visualization?.bindings, scene?.metadata?.problem_type);
  if (!model) return <p className={styles.unavailable}>Cần đúng hai số để đặt tính theo cột.</p>;
  const phase = progress >= 1 ? 3 : Math.min(2, Math.floor(Math.max(0, progress) * 3));
  const visibleSteps = phase === 0 ? 0 : phase === 1 ? 1 : phase === 2 ? Math.max(2, Math.ceil(model.steps.length / 2)) : model.steps.length;
  const visibleIndexes = new Set(model.steps.slice(0, visibleSteps).map((item) => item.index));
  const displayRow = (digits, className) => (
    <div className={className} style={{ gridTemplateColumns: `repeat(${model.width}, minmax(36px, 1fr))` }}>
      {digits.map((digit, index) => <b key={index}>{digit}</b>)}
    </div>
  );
  return (
    <figure className={`${styles.panel} ${styles.curriculumWide}`}>
      <figcaption className={styles.panelTitle}>Đặt tính theo giá trị hàng</figcaption>
      <p className={styles.teachingStep}>{[
        "Bước 1 · Căn thẳng hàng các chữ số và dấu thập phân",
        "Bước 2 · Tính cột nhỏ nhất ở bên phải",
        `Bước 3 · ${model.subtract ? "Mượn 1 hàng lớn = 10 hàng liền sau" : "Đổi 10 đơn vị thành 1 đơn vị ở hàng liền trước"}`,
        "Bước 4 · Đọc kết quả theo đúng vị trí từng cột",
      ][phase]}</p>
      <div className={styles.columnWork}>
        <div className={styles.regroupRow} style={{ gridTemplateColumns: `repeat(${model.width}, minmax(36px, 1fr))` }}>
          {model.topDigits.map((_, index) => {
            const step = model.steps.find((item) => item.index === index);
            return <span key={index}>{phase >= 2 && step?.regroup ? (model.subtract ? "mượn 1" : `nhớ ${step.regroup}`) : ""}</span>;
          })}
        </div>
        {displayRow(model.topDigits, styles.columnDigits)}
        <span className={styles.columnOperator}>{model.subtract ? "−" : "+"}</span>
        {displayRow(model.bottomDigits, styles.columnDigits)}
        <div className={styles.columnRule} />
        <div className={styles.columnDigits} style={{ gridTemplateColumns: `repeat(${model.width}, minmax(36px, 1fr))` }}>
          {model.resultDigits.map((digit, index) => <b key={index} className={visibleIndexes.has(index) ? styles.columnDigitReady : styles.columnDigitPending}>{visibleIndexes.has(index) ? digit : "?"}</b>)}
        </div>
      </div>
      <div className={styles.columnSteps}>
        {model.steps.slice(0, visibleSteps).map((step) => (
          <span key={step.index}><b>{step.place}</b>: {step.top}{step.incoming ? ` − ${step.incoming} đã ${model.subtract ? "mượn" : "nhớ"}` : ""} {model.subtract ? "−" : "+"} {step.bottom} → {step.result}</span>
        ))}
      </div>
      <p className={styles.visualEquation}>{phase >= 3 ? `${format(model.left)} ${model.subtract ? "−" : "+"} ${format(model.right)} = ${format(model.result)}` : "Tính lần lượt từ phải sang trái"}</p>
    </figure>
  );
}
