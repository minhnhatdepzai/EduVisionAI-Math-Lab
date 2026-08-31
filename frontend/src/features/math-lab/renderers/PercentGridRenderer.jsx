import { derivePercentModel, deriveReverseDiscountModel } from "../derive/deriveCurriculum.js";
import { derivePercentWaterfall, deriveTwoItemDiscountSystem } from "../derive/deriveCoverage.js";
import styles from "./renderers.module.css";

const format = (value) => new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 2 }).format(value);

/**
 * Each price state kept on screen next to the one it came from.
 *
 * A single part-whole grid cannot show a discount followed by a tax: the tax
 * is a percentage of the discounted price, not of the list price, and that
 * is exactly the step learners get wrong.
 */
function PercentWaterfallModel({ model, progress }) {
  const total = model.stages.length;
  const revealed = progress >= 1 ? total : Math.min(total - 1, Math.floor(Math.max(0, progress) * total)) + 1;
  return (
    <figure className={`${styles.panel} ${styles.curriculumWide}`}>
      <figcaption className={styles.panelTitle}>Chuỗi giá · giảm giá rồi thuế</figcaption>
      <p className={styles.teachingStep}>{[
        `Bước 1 · Giá niêm yết là ${format(model.original)} đồng`,
        `Bước 2 · Giảm ${format(model.discount)}% của giá niêm yết: −${format(model.discountAmount)} đồng`,
        model.hasTax
          ? `Bước 3 · Thuế ${format(model.tax)}% tính trên giá đã giảm ${format(model.afterDiscount)} đồng: +${format(model.taxAmount)} đồng`
          : `Bước 3 · Giá phải trả là ${format(model.final)} đồng`,
      ][Math.min(2, revealed - 1)]}</p>
      <ol className={styles.waterfall}>
        {model.stages.map((stage, index) => (
          <li key={stage.id} className={index < revealed ? styles.partialVisible : styles.partialPending}>
            <span>{stage.label}</span>
            <div className={styles.waterfallTrack}>
              <div className={stage.delta < 0 ? styles.waterfallBarDown : styles.waterfallBar}
                style={{ width: index < revealed ? `${stage.percent}%` : "0%" }} />
            </div>
            <b>{index < revealed ? format(stage.value) : "?"}</b>
            {stage.delta ? (
              <em className={stage.delta < 0 ? styles.meanGive : styles.meanGain}>
                {stage.delta < 0 ? "−" : "+"}{format(Math.abs(stage.delta))}
              </em>
            ) : <em />}
          </li>
        ))}
      </ol>
      {revealed >= total ? (
        <div className={styles.visualConclusion}>
          <span>Số tiền phải trả</span>
          <strong>{format(model.final)} đồng</strong>
          <small>
            {format(model.original)} − {format(model.discountAmount)}
            {model.hasTax ? ` + ${format(model.taxAmount)}` : ""} = {format(model.final)}
          </small>
        </div>
      ) : <p className={styles.fractionHint}>Mỗi phần trăm được tính trên giá ở ngay bước trước, không phải trên giá gốc.</p>}
    </figure>
  );
}

export default function PercentGridRenderer({ scene, world, progress, visualization }) {
  if (scene?.metadata?.problem_type === "two_item_discount_system") {
    return (
      <TwoItemDiscountSystemRenderer
        scene={scene}
        world={world}
        progress={progress}
        visualization={visualization}
      />
    );
  }
  if (scene?.metadata?.problem_type === "multi_item_reverse_discount") {
    return <ReverseDiscountRenderer world={world} progress={progress} visualization={visualization} />;
  }
  if (/discount_tax_percentage/i.test(String(scene?.metadata?.problem_type || ""))) {
    const waterfall = derivePercentWaterfall(world, visualization?.bindings);
    return waterfall
      ? <PercentWaterfallModel model={waterfall} progress={progress} />
      : <p className={styles.unavailable}>Cần giá gốc và mức phần trăm để dựng chuỗi giá.</p>;
  }
  const model = derivePercentModel(world, visualization?.bindings);
  if (!model) return <p className={styles.unavailable}>Cần biết hai trong ba đại lượng: phần, toàn bộ và phần trăm.</p>;
  const phase = progress >= 1 ? 3 : Math.min(2, Math.floor(Math.max(0, progress) * 3));
  const visible = phase >= 2 ? model.filledCells : phase >= 1 ? Math.round(model.filledCells / 2) : 0;
  return (
    <figure className={`${styles.panel} ${styles.curriculumWide}`}>
      <figcaption className={styles.panelTitle}>Lưới 100 ô · phần, toàn bộ và phần trăm</figcaption>
      <p className={styles.teachingStep}>{[
        `Bước 1 · Coi toàn bộ ${format(model.whole)} là 100 ô`,
        `Bước 2 · Đặt phần ${format(model.part)} vào vùng tương ứng`,
        "Bước 3 · Quy cùng tỉ lệ để đọc số ô trên 100",
        "Bước 4 · Nối lưới với phân số và số thập phân",
      ][phase]}</p>
      <div className={styles.percentLayout}>
        <div className={styles.hundredGrid} role="img" aria-label={`${model.filledCells} trên 100 ô được tô`}>
          {Array.from({ length: 100 }, (_, index) => <i key={index} className={index < visible ? styles.percentCellFilled : styles.percentCell} />)}
        </div>
        <div className={styles.percentBar}><span style={{ width: `${phase >= 2 ? model.percent : 0}%` }} /><b>{phase >= 2 ? `${format(model.percent)}%` : "?%"}</b></div>
      </div>
      <p className={styles.visualEquation}>{phase >= 3 ? `${format(model.part)}/${format(model.whole)} = ${format(model.decimal)} = ${format(model.percent)}%` : "100 ô giúp nhìn phần trăm như một phần của toàn bộ"}</p>
    </figure>
  );
}

const money = (value) => `${new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 0 }).format(value)}đ`;

function TwoItemDiscountSystemRenderer({ scene, world, progress, visualization }) {
  const model = deriveTwoItemDiscountSystem(
    world,
    visualization?.bindings,
    scene?.metadata?.relations,
  );
  if (!model) {
    return <p className={styles.unavailable}>Cần tổng giá niêm yết, hai mức giảm và tổng tiền thực trả.</p>;
  }
  const phase = progress >= 1 ? 5 : Math.min(5, Math.floor(Math.max(0, progress) * 6));
  const steps = [
    `Đặt ${model.firstSymbol} là giá ${model.firstLabel}, ${model.secondSymbol} là giá ${model.secondLabel}`,
    "Ghép hai giá niêm yết thành phương trình tổng",
    "Tô phần còn lại sau giảm giá để lập phương trình tiền thực trả",
    `Dùng ${format(model.secondRate)}(${model.firstSymbol} + ${model.secondSymbol}) để khử ${model.secondSymbol}`,
    "Tìm giá thứ nhất rồi dùng tổng để tìm giá thứ hai",
    "Thay lại vào hóa đơn và kiểm tra các khẳng định",
  ];
  const showPrices = phase >= 4;

  return (
    <figure className={`${styles.panel} ${styles.curriculumWide}`}>
      <figcaption className={styles.panelTitle}>Hai quyển sách · hệ phương trình giảm giá</figcaption>
      <p className={styles.teachingStep}>Bước {phase + 1} · {steps[phase]}</p>

      <div className={styles.bookDiscountPair}>
        <DiscountBookCard
          label={model.firstLabel}
          symbol={model.firstSymbol}
          price={model.firstPrice}
          discount={model.firstDiscount}
          retained={model.firstRetainedPercent}
          paid={model.paidFirst}
          showDiscount={phase >= 2}
          showPrice={showPrices}
          showPaid={phase >= 5}
        />
        <span className={styles.bookPricePlus}>+</span>
        <DiscountBookCard
          label={model.secondLabel}
          symbol={model.secondSymbol}
          price={model.secondPrice}
          discount={model.secondDiscount}
          retained={model.secondRetainedPercent}
          paid={model.paidSecond}
          showDiscount={phase >= 2}
          showPrice={showPrices}
          showPaid={phase >= 5}
        />
      </div>

      <div className={styles.discountSystemEquations} aria-label="Hệ phương trình giá sách">
        <p className={phase >= 1 ? styles.partialVisible : styles.partialPending}>
          <b>{model.firstSymbol} + {model.secondSymbol} = {format(model.listTotal)}</b>
          <span>Tổng giá niêm yết</span>
        </p>
        <p className={phase >= 2 ? styles.partialVisible : styles.partialPending}>
          <b>{format(model.firstRate)}{model.firstSymbol} + {format(model.secondRate)}{model.secondSymbol} = {format(model.paidTotal)}</b>
          <span>Tổng tiền sau giảm</span>
        </p>
      </div>

      {phase >= 3 ? (
        <div className={styles.discountElimination}>
          <span>{format(model.secondRate)}({model.firstSymbol} + {model.secondSymbol}) = {format(model.scaledListTotal)}</span>
          <span>
            ({format(model.firstRate)}{model.firstSymbol} + {format(model.secondRate)}{model.secondSymbol})
            {" − "}({format(model.secondRate)}{model.firstSymbol} + {format(model.secondRate)}{model.secondSymbol})
            {" = "}{format(model.differencePaid)}
          </span>
          <strong>{format(model.coefficientDifference)}{model.firstSymbol} = {format(model.differencePaid)}</strong>
        </div>
      ) : null}

      {showPrices ? (
        <div className={styles.visualConclusion}>
          <span>Giá niêm yết đúng</span>
          <strong>{model.firstLabel}: {money(model.firstPrice)} · {model.secondLabel}: {money(model.secondPrice)}</strong>
          <small>
            {model.firstSymbol} = {format(model.differencePaid)} ÷ {format(model.coefficientDifference)};
            {" "}{model.secondSymbol} = {format(model.listTotal)} − {format(model.firstPrice)}
          </small>
        </div>
      ) : null}

      {phase >= 5 ? (
        <div className={styles.discountVerification}>
          <b>{money(model.paidFirst)} + {money(model.paidSecond)} = {money(model.paidTotal)} ✓</b>
          {model.claimCorrect === false ? (
            <strong>Khẳng định d) sai: hai giá trong ảnh đã bị đảo cho nhau.</strong>
          ) : model.claimCorrect === true ? (
            <strong>Khẳng định giá trong đề là đúng.</strong>
          ) : null}
        </div>
      ) : null}
    </figure>
  );
}

function DiscountBookCard({ label, symbol, price, discount, retained, paid, showDiscount, showPrice, showPaid }) {
  return (
    <article className={styles.bookDiscountCard}>
      <span>{label}</span>
      <strong>{showPrice ? money(price) : `${symbol} đồng`}</strong>
      <div className={styles.bookDiscountBar}>
        <i style={{ width: showDiscount ? `${retained}%` : "100%" }} />
        <em style={{ width: showDiscount ? `${discount}%` : "0%" }} />
      </div>
      <small>{showDiscount ? `Giữ ${format(retained)}% · giảm ${format(discount)}%` : "Giá niêm yết 100%"}</small>
      <b>{showPaid ? `Thực trả ${money(paid)}` : showDiscount ? `${format(retained / 100)}${symbol}` : `${symbol} > 0`}</b>
    </article>
  );
}

function ReverseDiscountRenderer({ world, progress, visualization }) {
  const model = deriveReverseDiscountModel(world, visualization?.bindings);
  if (!model) {
    return <p className={styles.unavailable}>Cần đủ hai giá gốc, ba mức giảm giá và tổng tiền thanh toán.</p>;
  }
  const phase = progress >= 1 ? 5 : Math.min(5, Math.floor(Math.max(0, progress) * 6));
  const steps = [
    `Món 1: giữ lại ${format(100 - model.discountFirst)}% của giá gốc`,
    `Món 2: giữ lại ${format(100 - model.discountSecond)}% của giá gốc`,
    "Cộng hai số tiền đã biết trên cùng hóa đơn",
    "Lấy tổng thanh toán trừ hai khoản đã biết",
    `Món 3 giảm ${format(model.discountThird)}% nên số tiền trả là ${format(model.thirdPaidPercent)}%`,
    "Suy ngược từ 87,5% về toàn bộ 100%",
  ];

  return (
    <figure className={`${styles.panel} ${styles.curriculumWide}`}>
      <figcaption className={styles.panelTitle}>Hóa đơn giảm giá · tìm ngược giá gốc</figcaption>
      <p className={styles.teachingStep}>Bước {phase + 1} · {steps[phase]}</p>

      <div className={styles.discountReceipt}>
        <DiscountItem
          title="Món hàng 1"
          original={model.originalFirst}
          discount={model.discountFirst}
          paid={model.paidFirst}
          visible={phase >= 0}
        />
        <DiscountItem
          title="Món hàng 2"
          original={model.originalSecond}
          discount={model.discountSecond}
          paid={model.paidSecond}
          visible={phase >= 1}
        />
        <article className={phase >= 3 ? styles.discountCardActive : styles.discountCard}>
          <span>Món hàng 3</span>
          <strong>{phase >= 5 ? money(model.originalThird) : "? giá gốc"}</strong>
          <small>Giảm {format(model.discountThird)}%</small>
          <b>{phase >= 3 ? `Đã trả ${money(model.paidThird)}` : "Chưa biết tiền đã trả"}</b>
        </article>
      </div>

      <div className={styles.receiptEquation}>
        {phase < 2 ? (
          <span>Đưa từng món hàng vào hóa đơn</span>
        ) : phase === 2 ? (
          <strong>{money(model.paidFirst)} + {money(model.paidSecond)} = {money(model.knownPaid)}</strong>
        ) : (
          <strong>{money(model.paidTotal)} − {money(model.knownPaid)} = {money(model.paidThird)}</strong>
        )}
      </div>

      <div className={styles.reversePercentModel}>
        <div className={styles.reversePercentLabels}>
          <span>0%</span><b>Tiền đã trả: {format(model.thirdPaidPercent)}%</b><span>100%</span>
        </div>
        <div className={styles.reversePercentBar}>
          <span style={{ width: `${phase >= 4 ? model.thirdPaidPercent : 0}%` }} />
          <i style={{ width: `${phase >= 4 ? model.discountThird : 0}%` }} />
        </div>
        <div className={styles.reversePercentValues}>
          <b>{phase >= 4 ? money(model.paidThird) : "?"}</b>
          <span>{phase >= 4 ? `Giảm ${format(model.discountThird)}%` : ""}</span>
          <strong>{phase >= 5 ? money(model.originalThird) : "? giá gốc"}</strong>
        </div>
      </div>

      <p className={styles.visualEquation}>
        {phase >= 5
          ? `${money(model.paidThird)} ÷ ${format(model.thirdPaidPercent)} × 100 = ${money(model.originalThird)}`
          : `${money(model.paidThird)} ứng với ${format(model.thirdPaidPercent)}% giá gốc`}
      </p>
    </figure>
  );
}

function DiscountItem({ title, original, discount, paid, visible }) {
  return (
    <article className={visible ? styles.discountCardActive : styles.discountCard}>
      <span>{title}</span>
      <strong>{money(original)}</strong>
      <small>Giảm {format(discount)}%</small>
      <b>{visible ? `Trả ${money(paid)}` : "Chờ tính"}</b>
    </article>
  );
}
