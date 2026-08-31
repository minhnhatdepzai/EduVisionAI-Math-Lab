import { deriveFractionPower } from "../derive/deriveScene.js";
import styles from "./renderers.module.css";

function FractionText({ numerator, denominator }) {
  return (
    <span className={styles.stackedFraction} aria-label={`${numerator} phần ${denominator}`}>
      <b>{numerator}</b><i /><b>{denominator}</b>
    </span>
  );
}

function MagnitudeCube({ power, visible }) {
  const total = power.denominatorMagnitude;
  const canUseFiveCube = power.denominator === 5 && power.exponent === 3;
  if (!canUseFiveCube) {
    return (
      <div className={styles.powerMagnitudeCompact}>
        <strong>{power.numeratorMagnitude}</strong>
        <span>phần được chọn trong</span>
        <strong>{total}</strong>
        <span>phần bằng nhau</span>
      </div>
    );
  }
  return (
    <div
      className={styles.powerCube}
      role="img"
      aria-label={`${power.numeratorMagnitude} ô được tô trong khối 5 nhân 5 nhân 5 gồm 125 ô`}
    >
      {Array.from({ length: 5 }, (_, layer) => (
        <div key={layer} className={styles.powerLayer}>
          <b>Lớp {layer + 1}</b>
          <span>
            {Array.from({ length: 25 }, (__, cell) => {
              const row = Math.floor(cell / 5);
              const column = cell % 5;
              const inTwoByTwoByTwoCube = layer < 2 && row < 2 && column < 2;
              return <i key={cell} className={visible && inTwoByTwoByTwoCube ? styles.powerCellFilled : styles.powerCell} />;
            })}
          </span>
        </div>
      ))}
    </div>
  );
}

export default function PowerModelRenderer({ world, progress, visualization, scene }) {
  const power = deriveFractionPower(
    world,
    visualization?.bindings,
    scene?.metadata?.choices || [],
  );
  if (!power) {
    return <p className={styles.unavailable}>Cần tử số, mẫu số và số mũ để dựng lũy thừa phân số.</p>;
  }
  const phase = progress >= 1 ? 5 : Math.min(5, Math.floor(Math.max(0, progress) * 6));
  const negativeFactors = power.numerator < 0 ? power.exponent : 0;
  const titles = [
    "Bước 1 · Đọc toàn bộ phân số là cơ số",
    `Bước 2 · Số mũ ${power.exponent} nghĩa là nhân ${power.exponent} thừa số giống nhau`,
    `Bước 3 · ${negativeFactors} dấu âm là ${negativeFactors % 2 ? "số lẻ" : "số chẵn"}`,
    `Bước 4 · Tính riêng ${Math.abs(power.numerator)}${toSuperscript(power.exponent)} và ${power.denominator}${toSuperscript(power.exponent)}`,
    `Bước 5 · Nhìn ${power.numeratorMagnitude} phần trong ${power.denominatorMagnitude} phần bằng nhau`,
    "Bước 6 · Ghép dấu với độ lớn và chọn đáp án",
  ];

  return (
    <figure className={`${styles.panel} ${styles.powerPanel}`}>
      <figcaption className={styles.panelTitle}>Lũy thừa phân số · dấu và độ lớn</figcaption>
      <p className={styles.teachingStep}>{titles[phase]}</p>

      <div className={styles.powerExpression}>
        <span>(</span><FractionText numerator={power.numerator} denominator={power.denominator} />
        <span>)<sup>{power.exponent}</sup></span>
        <span>=</span>
        <span className={phase >= 5 ? styles.powerResultVisible : styles.powerResultHidden}>
          <FractionText numerator={power.resultNumerator} denominator={power.resultDenominator} />
        </span>
      </div>

      <div className={styles.powerFactors} aria-label="Phép nhân lặp lại">
        {power.factors.map((factor, index) => (
          <span key={index} className={phase >= 1 ? styles.powerFactorVisible : styles.powerFactorHidden}>
            {index ? <em>×</em> : null}
            <span>(<FractionText {...factor} />)</span>
          </span>
        ))}
      </div>

      <div className={styles.powerReasoningGrid}>
        <section className={phase >= 2 ? styles.powerReasonActive : styles.powerReasonPending}>
          <small>Dấu của tích</small>
          <strong>{Array.from({ length: negativeFactors }, () => "−").join(" × ") || "+"}</strong>
          <span>{phase >= 2 ? `${negativeFactors} dấu âm → ${power.sign < 0 ? "dấu âm" : "dấu dương"}` : "Đếm số thừa số âm"}</span>
        </section>
        <section className={phase >= 3 ? styles.powerReasonActive : styles.powerReasonPending}>
          <small>Tử số</small>
          <strong>{Array.from({ length: power.exponent }, () => Math.abs(power.numerator)).join(" × ")} = {power.numeratorMagnitude}</strong>
          <span>{Math.abs(power.numerator)}{toSuperscript(power.exponent)} = {power.numeratorMagnitude}</span>
        </section>
        <section className={phase >= 3 ? styles.powerReasonActive : styles.powerReasonPending}>
          <small>Mẫu số</small>
          <strong>{Array.from({ length: power.exponent }, () => power.denominator).join(" × ")} = {power.denominatorMagnitude}</strong>
          <span>{power.denominator}{toSuperscript(power.exponent)} = {power.denominatorMagnitude}</span>
        </section>
      </div>

      <MagnitudeCube power={power} visible={phase >= 4} />

      {phase >= 5 ? (
        <div className={styles.powerConclusion}>
          <span>Dấu {power.sign < 0 ? "âm" : "dương"}</span>
          <strong><FractionText numerator={power.resultNumerator} denominator={power.resultDenominator} /></strong>
          {power.choiceLabel ? <b>Chọn {power.choiceLabel}</b> : null}
        </div>
      ) : <p className={styles.fractionHint}>Nhấn “Chạy” để quan sát phép biến đổi từng bước.</p>}
    </figure>
  );
}

function toSuperscript(value) {
  const digits = { 0: "⁰", 1: "¹", 2: "²", 3: "³", 4: "⁴", 5: "⁵", 6: "⁶", 7: "⁷", 8: "⁸", 9: "⁹" };
  return String(value).split("").map((digit) => digits[digit] || digit).join("");
}
