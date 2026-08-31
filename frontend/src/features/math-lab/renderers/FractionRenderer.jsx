import {
  deriveFraction,
  deriveFractionComparison,
  deriveFractionOperation,
} from "../derive/deriveScene.js";
import styles from "./renderers.module.css";

/**
 * A fraction as a bar cut into equal parts.
 *
 * When the scene asks for a rewrite — 1/2 becoming 2/4 — the cuts double but
 * the shaded width does not move. Seeing the amount stay put while the pieces
 * get smaller is the whole idea of an equivalent fraction, and it is why this
 * is a bar rather than a picture of one.
 */
function FractionText({ numerator, denominator }) {
  return (
    <span className={styles.stackedFraction} aria-label={`${numerator} phần ${denominator}`}>
      <b>{numerator}</b>
      <i />
      <b>{denominator}</b>
    </span>
  );
}

function ComparisonCard({ fraction, reduced, accent = false }) {
  return (
    <div className={styles.comparisonCard}>
      <div className={styles.ratioTrack} aria-hidden="true">
        <span
          className={accent ? styles.ratioFillAccent : styles.ratioFill}
          style={{ width: `${Math.min(Math.max(fraction.ratio * 100, 0), 100)}%` }}
        />
      </div>
      <div className={styles.reductionLine}>
        <FractionText numerator={fraction.numerator} denominator={fraction.denominator} />
        {reduced ? (
          <>
            <span className={styles.reductionOperation}>
              chia cả tử và mẫu cho <b>{fraction.divisor}</b>
            </span>
            <span aria-hidden="true">→</span>
            <FractionText
              numerator={fraction.reducedNumerator}
              denominator={fraction.reducedDenominator}
            />
          </>
        ) : (
          <span className={styles.reductionOperation}>Chưa rút gọn</span>
        )}
      </div>
    </div>
  );
}

function FractionComparison({ comparison, progress }) {
  const phase = progress >= 0.82 ? 3 : progress >= 0.55 ? 2 : progress >= 0.25 ? 1 : 0;
  const titles = [
    "Bước 1 · Đọc hai phân số",
    "Bước 2 · Rút gọn phân số thứ nhất",
    "Bước 3 · Rút gọn phân số thứ hai",
    "Bước 4 · So sánh hai kết quả",
  ];
  return (
    <figure className={`${styles.panel} ${styles.fractionComparison}`}>
      <figcaption className={styles.panelTitle}>So sánh hai phân số</figcaption>
      <p className={styles.teachingStep}>{titles[phase]}</p>
      <div className={styles.comparisonGrid}>
        <ComparisonCard fraction={comparison.left} reduced={phase >= 1} />
        <span className={styles.comparisonSign} aria-label={phase >= 3 ? (comparison.equal ? "bằng" : "không bằng") : "cần so sánh"}>
          {phase >= 3 ? (comparison.equal ? "=" : "≠") : "?"}
        </span>
        <ComparisonCard fraction={comparison.right} reduced={phase >= 2} accent />
      </div>
      {phase >= 3 ? (
        <div className={comparison.equal ? styles.comparisonConclusion : styles.comparisonConclusionWarning}>
          <span>
            <FractionText
              numerator={comparison.left.reducedNumerator}
              denominator={comparison.left.reducedDenominator}
            />
            {comparison.equal ? " = " : " ≠ "}
            <FractionText
              numerator={comparison.right.reducedNumerator}
              denominator={comparison.right.reducedDenominator}
            />
          </span>
          <strong>
            {comparison.equal
              ? "Vậy hai phân số bằng nhau."
              : "Vậy hai phân số không bằng nhau."}
          </strong>
        </div>
      ) : (
        <p className={styles.fractionHint}>Nhấn “Chạy” hoặc “Bước sau” để quan sát từng bước.</p>
      )}
    </figure>
  );
}

function PartBar({ denominator, first = 0, second = 0, label }) {
  if (denominator > 48) {
    return (
      <div className={styles.compactFractionBar} role="img" aria-label={label}>
        <i style={{ width: `${Math.max(0, Math.min(100, (first / denominator) * 100))}%` }} />
        <b style={{ width: `${Math.max(0, Math.min(100, (second / denominator) * 100))}%` }} />
      </div>
    );
  }
  return (
    <div className={styles.fractionBar} role="img" aria-label={label}>
      {Array.from({ length: denominator }, (_, index) => (
        <span
          key={index}
          className={index < first
            ? styles.fractionPartFilled
            : index < first + second
              ? styles.fractionPartSecond
              : styles.fractionPart}
        />
      ))}
    </div>
  );
}

function FractionAddition({ operation, progress }) {
  const phase = progress >= 1 ? 4 : Math.min(3, Math.floor(Math.max(0, progress) * 4));
  const symbol = operation.operation === "subtract" ? "−" : "+";
  const verb = operation.operation === "subtract" ? "trừ" : "cộng";
  const titles = [
    `Bước 1 · Hai phân số chưa cùng loại phần`,
    `Bước 2 · Chia lại cả hai thành ${operation.commonDenominator} phần bằng nhau`,
    `Bước 3 · Đổi thành ${operation.leftCommon}/${operation.commonDenominator} ${symbol} ${operation.rightCommon}/${operation.commonDenominator}`,
    `Bước 4 · ${operation.operation === "subtract" ? "Bớt" : "Ghép"} các phần cùng kích thước`,
    `Bước 5 · Rút gọn và kết luận`,
  ];
  const simplified = operation.divisor > 1;
  return (
    <figure className={`${styles.panel} ${styles.fractionOperation}`}>
      <figcaption className={styles.panelTitle}>Phép {verb} phân số · mô hình phần bằng nhau</figcaption>
      <p className={styles.teachingStep}>{titles[phase]}</p>

      <div className={styles.fractionEquation}>
        <FractionText {...operation.left} />
        <strong>{symbol}</strong>
        <FractionText {...operation.right} />
        <strong>=</strong>
        <span>{phase >= 3 ? <FractionText numerator={operation.resultNumerator} denominator={operation.resultDenominator} /> : "?"}</span>
      </div>

      <div className={styles.operationBars}>
        <section>
          <b>Số hạng 1</b>
          <PartBar
            denominator={phase >= 1 ? operation.commonDenominator : operation.left.denominator}
            first={phase >= 1 ? operation.leftCommon : operation.left.numerator}
            label={`Phân số thứ nhất ${operation.left.numerator} phần ${operation.left.denominator}`}
          />
          <span>{phase >= 1 ? `${operation.left.numerator}/${operation.left.denominator} = ${operation.leftCommon}/${operation.commonDenominator}` : `${operation.left.numerator}/${operation.left.denominator}`}</span>
        </section>
        <section>
          <b>Số hạng 2</b>
          <PartBar
            denominator={phase >= 1 ? operation.commonDenominator : operation.right.denominator}
            first={0}
            second={phase >= 1 ? operation.rightCommon : operation.right.numerator}
            label={`Phân số thứ hai ${operation.right.numerator} phần ${operation.right.denominator}`}
          />
          <span>{phase >= 1 ? `${operation.right.numerator}/${operation.right.denominator} = ${operation.rightCommon}/${operation.commonDenominator}` : `${operation.right.numerator}/${operation.right.denominator}`}</span>
        </section>
      </div>

      <div className={phase >= 3 ? styles.fractionMergeReady : styles.fractionMergePending}>
        <strong>Cùng một thanh đơn vị</strong>
        <PartBar
          denominator={operation.resultDenominator}
          first={phase >= 3 ? Math.max(0, operation.operation === "subtract" ? operation.resultNumerator : operation.leftCommon) : 0}
          second={phase >= 3 && operation.operation === "add" ? operation.rightCommon : 0}
          label={`Kết quả ${operation.resultNumerator} phần ${operation.resultDenominator}`}
        />
        <span>
          {phase >= 3
            ? `${operation.leftCommon} ${symbol} ${operation.rightCommon} = ${operation.resultNumerator} phần, giữ nguyên mẫu ${operation.resultDenominator}`
            : "Chỉ ghép hoặc bớt sau khi mọi phần đã có cùng kích thước."}
        </span>
      </div>

      {phase >= 4 ? (
        <div className={styles.visualConclusion}>
          <span>{operation.resultNumerator}/{operation.resultDenominator}</span>
          {simplified ? <span>÷ {operation.divisor} ở cả tử và mẫu</span> : <span>đã tối giản</span>}
          <strong>= {operation.reducedNumerator}/{operation.reducedDenominator}</strong>
        </div>
      ) : <p className={styles.fractionHint}>Nhấn “Bước sau” để thấy từng phép biến đổi.</p>}
    </figure>
  );
}

function FractionMultiplication({ operation, progress }) {
  const phase = progress >= 1 ? 3 : Math.min(2, Math.floor(Math.max(0, progress) * 3));
  const rows = operation.right.denominator;
  const columns = operation.left.denominator;
  const cellCount = rows * columns;
  return (
    <figure className={`${styles.panel} ${styles.fractionOperation}`}>
      <figcaption className={styles.panelTitle}>Nhân phân số · phần của một phần</figcaption>
      <p className={styles.teachingStep}>{[
        `Bước 1 · Tô ${operation.left.numerator}/${operation.left.denominator} theo chiều ngang`,
        `Bước 2 · Lấy ${operation.right.numerator}/${operation.right.denominator} của phần đã tô theo chiều dọc`,
        `Bước 3 · Phần giao nhau là tích cần tìm`,
        `Bước 4 · Đếm ô giao và rút gọn`,
      ][phase]}</p>
      <div className={styles.fractionEquation}>
        <FractionText {...operation.left} /><strong>×</strong><FractionText {...operation.right} />
        <strong>=</strong><FractionText numerator={operation.resultNumerator} denominator={operation.resultDenominator} />
      </div>
      {cellCount <= 144 ? (
        <div
          className={styles.fractionAreaGrid}
          style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}
          role="img"
          aria-label={`${operation.resultNumerator} ô giao nhau trên ${operation.resultDenominator} ô`}
        >
          {Array.from({ length: cellCount }, (_, index) => {
            const column = index % columns;
            const row = Math.floor(index / columns);
            const horizontal = column < operation.left.numerator;
            const vertical = row < operation.right.numerator;
            const className = phase >= 2 && horizontal && vertical
              ? styles.areaIntersection
              : phase >= 1 && vertical
                ? styles.areaVertical
                : horizontal
                  ? styles.areaHorizontal
                  : styles.areaEmpty;
            return <i key={index} className={className} />;
          })}
        </div>
      ) : <p className={styles.unavailable}>Lưới quá lớn; dùng phép đếm ô theo công thức bên dưới.</p>}
      <p className={styles.areaExplanation}>
        {phase >= 2
          ? `Phần giao của hai lớp màu: ${operation.left.numerator} × ${operation.right.numerator} = ${operation.resultNumerator} ô giao; ${operation.left.denominator} × ${operation.right.denominator} = ${operation.resultDenominator} ô tất cả.`
          : "Hai lớp màu giúp nhìn thấy “một phần của một phần”."}
      </p>
      {phase >= 3 ? (
        <div className={styles.visualConclusion}>
          <span>{operation.resultNumerator}/{operation.resultDenominator}</span>
          <span>÷ {operation.divisor}</span>
          <strong>= {operation.reducedNumerator}/{operation.reducedDenominator}</strong>
        </div>
      ) : null}
    </figure>
  );
}

function FractionDivision({ operation, progress }) {
  const phase = progress >= 1 ? 3 : Math.min(2, Math.floor(Math.max(0, progress) * 3));
  const parts = Math.min(operation.dividendParts || 0, 72);
  return (
    <figure className={`${styles.panel} ${styles.fractionOperation}`}>
      <figcaption className={styles.panelTitle}>Chia phân số · đo xem số chia nằm được bao nhiêu lần</figcaption>
      <p className={styles.teachingStep}>{[
        `Bước 1 · Đọc ${operation.left.numerator}/${operation.left.denominator} và cỡ nhóm ${operation.right.numerator}/${operation.right.denominator}`,
        `Bước 2 · Chia cùng một đơn vị thành ${operation.measurementDenominator} phần bằng nhau`,
        `Bước 3 · Mỗi nhóm cần ${operation.divisorParts} phần; đếm nhóm trong ${operation.dividendParts} phần`,
        "Bước 4 · Nối phép đo với quy tắc nhân nghịch đảo và rút gọn",
      ][phase]}</p>
      <div className={styles.fractionEquation}>
        <FractionText {...operation.left} /><strong>÷</strong><FractionText {...operation.right} />
        <strong>=</strong>{phase >= 3 ? <FractionText numerator={operation.reducedNumerator} denominator={operation.reducedDenominator} /> : <span>?</span>}
      </div>
      <div className={styles.divisionMeasure} style={{ gridTemplateColumns: `repeat(${Math.min(parts, 18)}, minmax(12px, 1fr))` }}
        role="img" aria-label={`${operation.dividendParts} phần nhỏ, mỗi nhóm gồm ${operation.divisorParts} phần`}>
        {phase >= 1 ? Array.from({ length: parts }, (_, index) => (
          <i key={index} data-group={Math.floor(index / operation.divisorParts) + 1}
            className={phase >= 2 && Math.floor(index / operation.divisorParts) % 2 ? styles.divisionPartAccent : styles.divisionPart} />
        )) : null}
      </div>
      <p className={styles.areaExplanation}>{phase >= 2
        ? `${operation.dividendParts} phần ÷ ${operation.divisorParts} phần/nhóm = ${operation.dividendParts / operation.divisorParts} nhóm.`
        : "Quy đồng ở đây chỉ để mọi đoạn đo có cùng kích thước."}</p>
      {phase >= 3 ? <div className={styles.visualConclusion}>
        <span>{operation.left.numerator}/{operation.left.denominator} × {operation.right.denominator}/{operation.right.numerator}</span>
        <span>= {operation.resultNumerator}/{operation.resultDenominator}</span>
        <strong>= {operation.reducedNumerator}/{operation.reducedDenominator}</strong>
      </div> : null}
    </figure>
  );
}

export default function FractionRenderer({ world, progress, visualization, scene }) {
  const comparison = deriveFractionComparison(world, visualization?.bindings);
  if (comparison) return <FractionComparison comparison={comparison} progress={progress} />;

  const problemType = scene?.metadata?.problem_type || "";
  const operation = deriveFractionOperation(world, visualization?.bindings, problemType);
  if (operation) {
    if (operation.operation === "multiply") return <FractionMultiplication operation={operation} progress={progress} />;
    if (operation.operation === "divide") return <FractionDivision operation={operation} progress={progress} />;
    return <FractionAddition operation={operation} progress={progress} />;
  }

  const fraction = deriveFraction(world, progress, visualization?.bindings);
  if (!fraction) {
    return <p className={styles.unavailable}>Cần tử số và mẫu số để dựng mô hình phân số.</p>;
  }

  const parts = Array.from({ length: fraction.parts }, (_, index) => index);
  const shaded = fraction.shaded;

  return (
    <figure className={styles.panel}>
      <figcaption className={styles.panelTitle}>Mô hình phân số</figcaption>

      <div className={styles.fractionBar} role="img"
        aria-label={`${shaded} phần được chọn trên ${fraction.parts} phần bằng nhau`}>
        {parts.map((index) => (
          <span
            key={index}
            className={index < shaded ? styles.fractionPartFilled : styles.fractionPart}
          />
        ))}
      </div>

      <p className={styles.fractionValue}>
        <b>{shaded}</b>
        <i>/</i>
        <b>{fraction.parts}</b>
        {fraction.rewritten ? (
          <em>= {fraction.numerator}/{fraction.denominator}, cùng một lượng</em>
        ) : null}
      </p>

      {fraction.addend != null && fraction.addendDenominator != null ? (
        <>
          <div className={styles.fractionBar} aria-label="Số hạng thứ hai">
            {Array.from({ length: fraction.addendDenominator }, (_, index) => (
              <span
                key={index}
                className={index < fraction.addend ? styles.fractionPartSecond : styles.fractionPart}
              />
            ))}
          </div>
          <p className={styles.fractionValue}>
            <b>{fraction.addend}</b><i>/</i><b>{fraction.addendDenominator}</b>
          </p>
          {fraction.rewritten && fraction.parts === fraction.addendDenominator ? (
            <p className={styles.fractionTotal}>
              Tổng: <b>{shaded + fraction.addend}</b>/<b>{fraction.parts}</b>
            </p>
          ) : (
            <p className={styles.fractionHint}>
              Chạy để quy đồng về mẫu số {fraction.addendDenominator}.
            </p>
          )}
        </>
      ) : (
        <dl className={styles.readout}>
          <div><dt>Số phần được chọn</dt><dd>{shaded}</dd></div>
          <div><dt>Số phần bằng nhau</dt><dd>{fraction.parts}</dd></div>
        </dl>
      )}
    </figure>
  );
}
