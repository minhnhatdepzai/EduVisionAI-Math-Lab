import { deriveGrouping, deriveParenthesizedMultiplication } from "../derive/deriveScene.js";
import styles from "./renderers.module.css";

const format = (value) => new Intl.NumberFormat("vi-VN").format(value);

function ParenthesizedPile({ count, tone = "primary" }) {
  return (
    <span className={tone === "accent" ? styles.parenthesisPileAccent : styles.parenthesisPile}>
      {Array.from({ length: count }, (_, index) => <i key={index} />)}
    </span>
  );
}

function ParenthesizedGrouping({ model, progress }) {
  const phase = progress >= 1 ? 3 : Math.min(2, Math.floor(Math.max(0, progress) * 4));
  const titles = [
    `Bước 1 · Khoanh phép tính ${model.innerLeft} ${model.innerSymbol} ${model.innerRight} trong ngoặc`,
    `Bước 2 · Tính trong ngoặc trước: ${model.innerLeft} ${model.innerSymbol} ${model.innerRight} = ${model.innerValue}`,
    `Bước 3 · Dựng ${model.groups} nhóm, mỗi nhóm ${model.perGroup} đồ vật`,
    `Bước 4 · Đếm toàn bộ: ${model.innerValue} × ${model.multiplier} = ${model.total}`,
  ];
  return (
    <figure className={`${styles.panel} ${styles.groupingPanel}`}>
      <figcaption className={styles.panelTitle}>Tính trong ngoặc rồi dựng nhóm bằng nhau</figcaption>
      <p className={styles.teachingStep}>{titles[phase]}</p>

      <section className={styles.parenthesisStage} aria-label="Phép tính cần thực hiện trước trong ngoặc">
        <strong>(</strong>
        <div><ParenthesizedPile count={model.innerLeft} /><b>{model.innerLeft}</b></div>
        <em>{model.innerSymbol}</em>
        <div><ParenthesizedPile count={model.innerRight} tone="accent" /><b>{model.innerRight}</b></div>
        <strong>)</strong>
        <span>× {model.multiplier}</span>
        <i>=</i>
        <b>{phase >= 1 ? `${model.innerValue} × ${model.multiplier}` : `(? ) × ${model.multiplier}`}</b>
      </section>

      {phase >= 2 ? (
        <div className={styles.equalGroupGrid} aria-label={`${model.groups} nhóm, mỗi nhóm ${model.perGroup} đồ vật`}>
          {Array.from({ length: model.groups }, (_, groupIndex) => (
            <div key={groupIndex} className={styles.equalGroupActive}>
              <b>Nhóm {groupIndex + 1}</b>
              <span>{Array.from({ length: model.perGroup }, (_, itemIndex) => <i key={itemIndex} />)}</span>
              <small>{model.perGroup} đồ vật</small>
            </div>
          ))}
        </div>
      ) : (
        <p className={styles.fractionHint}>Phải hoàn thành phép tính trong ngoặc trước khi tạo các nhóm nhân.</p>
      )}

      {phase >= 3 ? (
        <div className={styles.visualConclusion}>
          <span>({model.innerLeft} {model.innerSymbol} {model.innerRight}) × {model.multiplier}</span>
          <span>= {model.innerValue} × {model.multiplier}</span>
          <strong>= {model.total}</strong>
        </div>
      ) : null}
    </figure>
  );
}

function PlaceValuePart({ part }) {
  return (
    <span className={styles.groupPlacePart}>
      <span className={part.place === 1 ? styles.groupUnitMarks : styles.groupPlaceMarks} aria-hidden="true">
        {Array.from({ length: part.digit }, (_, index) => <i key={index} />)}
      </span>
      <b>{part.digit} {part.label}</b>
      <small>= {format(part.value)}</small>
    </span>
  );
}

/** Large products stay concrete without allocating one DOM dot per item. */
function PlaceValueGrouping({ model, progress }) {
  const phase = progress >= 1 ? 3 : Math.min(2, Math.floor(Math.max(0, progress) * 4));
  const expansion = model.parts.map((part) => format(part.value)).join(" + ");
  const partialSum = model.partials.map((part) => format(part.value)).join(" + ");
  const steps = [
    `Bước 1 · Tách ${format(model.perGroup)} theo hàng: ${format(model.perGroup)} = ${expansion}`,
    model.showGroupCards
      ? `Bước 2 · Dựng ${format(model.groups)} nhóm; mỗi nhóm đều có ${format(model.perGroup)}`
      : `Bước 2 · Dùng tính chất phân phối để không phải vẽ ${format(model.groups)} nhóm quá dày`,
    `Bước 3 · Nhân riêng từng giá trị hàng: ${model.partials.map((part) => `${part.expression} = ${format(part.value)}`).join("; ")}`,
    `Bước 4 · Gộp các tích riêng: ${partialSum} = ${format(model.total)}`,
  ];
  return (
    <figure className={`${styles.panel} ${styles.groupingPanel} ${styles.placeValueGrouping}`}>
      <figcaption className={styles.panelTitle}>Nhân bằng nhóm và khối giá trị hàng</figcaption>
      <p className={styles.teachingStep}>{steps[phase]}</p>
      {model.swapped ? (
        <p className={styles.groupingCommutative}>
          Đổi thứ tự để hình dễ nhìn: {format(model.originalLeft)} × {format(model.originalRight)} = {format(model.groups)} × {format(model.perGroup)}.
        </p>
      ) : null}
      <p className={styles.groupingExpansion}>
        <span>Tách một nhóm theo giá trị hàng</span>
        <strong>{format(model.perGroup)} = {expansion}</strong>
      </p>

      {model.showGroupCards ? (
        <div className={styles.placeValueGroupGrid} aria-label={`${model.groups} nhóm, mỗi nhóm ${model.perGroup}`}>
          {Array.from({ length: model.groups }, (_, groupIndex) => (
            <section key={groupIndex} className={phase >= 1 ? styles.placeValueGroupActive : styles.placeValueGroup}>
              <strong>Nhóm {groupIndex + 1}</strong>
              <div>{model.parts.map((part) => <PlaceValuePart key={part.place} part={part} />)}</div>
              <b>{format(model.perGroup)}</b>
            </section>
          ))}
        </div>
      ) : (
        <div className={styles.placeValueSingleGroup}>
          <strong>Một thừa số được tách theo giá trị hàng</strong>
          <div>{model.parts.map((part) => <PlaceValuePart key={part.place} part={part} />)}</div>
        </div>
      )}

      <div className={styles.groupPartialProducts} aria-label="Các tích riêng theo giá trị hàng">
        {model.partials.map((partial) => (
          <span key={partial.place} className={phase >= 2 ? styles.groupPartialReady : styles.groupPartialPending}>
            <small>{partial.digit} {partial.label}</small>
            <b>{partial.expression}</b>
            <strong>{phase >= 2 ? `= ${format(partial.value)}` : "= ?"}</strong>
          </span>
        ))}
      </div>

      <div className={styles.visualConclusion}>
        <span>{format(model.originalLeft)} × {format(model.originalRight)}</span>
        <span>{phase >= 2 ? `= ${partialSum}` : `= ${model.groups} nhóm × ${format(model.perGroup)}`}</span>
        <strong>{phase >= 3 ? `= ${format(model.total)}` : "= ?"}</strong>
      </div>
    </figure>
  );
}

export default function GroupingRenderer({ world, progress, visualization, scene }) {
  const problemType = String(scene?.metadata?.problem_type || "");
  if (problemType.includes("parenthesized_") && problemType.includes("_multiplication")) {
    const parenthesized = deriveParenthesizedMultiplication(
      world,
      visualization?.bindings,
      problemType,
    );
    if (parenthesized) return <ParenthesizedGrouping model={parenthesized} progress={progress} />;
    return <p className={styles.unavailable}>Cần đủ ba số in trong biểu thức để tính trong ngoặc rồi dựng phép nhân.</p>;
  }
  const grouping = deriveGrouping(
    world,
    visualization?.bindings,
    problemType,
  );
  if (!grouping) {
    return <p className={styles.unavailable}>Cần hai số nguyên dương để dựng nhóm bằng nhau.</p>;
  }
  if (grouping.mode === "place_value") {
    return <PlaceValueGrouping model={grouping} progress={progress} />;
  }
  const visibleGroups = progress >= 1
    ? grouping.groups
    : Math.max(1, Math.ceil(grouping.groups * Math.max(0, progress)));
  return (
    <figure className={`${styles.panel} ${styles.groupingPanel}`}>
      <figcaption className={styles.panelTitle}>
        {grouping.operation === "divide" ? "Chia thành các nhóm bằng nhau" : "Nhân bằng mảng hình chữ nhật"}
      </figcaption>
      <p className={styles.teachingStep}>
        {grouping.operation === "divide"
          ? `${grouping.total} đồ vật được tách thành ${grouping.groups} nhóm, mỗi nhóm ${grouping.perGroup}.`
          : `${grouping.groups} hàng, mỗi hàng ${grouping.perGroup} đồ vật.`}
      </p>
      <div className={styles.equalGroupGrid}>
        {Array.from({ length: grouping.groups }, (_, groupIndex) => (
          <div key={groupIndex} className={groupIndex < visibleGroups ? styles.equalGroupActive : styles.equalGroup}>
            <b>Nhóm {groupIndex + 1}</b>
            <span>
              {Array.from({ length: grouping.perGroup }, (_, itemIndex) => <i key={itemIndex} />)}
            </span>
          </div>
        ))}
      </div>
      <div className={styles.visualConclusion}>
        {grouping.operation === "divide" ? (
          <><span>{grouping.total} ÷ {grouping.perGroup}</span><strong>= {grouping.groups} nhóm</strong></>
        ) : (
          <><span>{grouping.groups} × {grouping.perGroup}</span><strong>= {grouping.total}</strong></>
        )}
      </div>
    </figure>
  );
}
