import {
  deriveAveragePerPerson,
  deriveBinomialSquare,
  deriveDirectProportionDistanceTime,
  deriveRatioShare,
  deriveRatioTotal,
  deriveSequentialRemainderQuantity,
  deriveSequentialRemainderRatio,
  deriveVariablePeopleWorkRate,
} from "../derive/deriveScene.js";
import {
  deriveArithmeticMean,
  deriveMultiStepArithmetic,
  deriveProportionalDifference,
} from "../derive/deriveCoverage.js";
import styles from "./renderers.module.css";

const PHASE_TITLES = [
  "Bắt đầu · Xác định 3 mốc thời gian",
  "Mốc 1 · Sản lượng tháng thứ nhất",
  "Mốc 2 · Cộng thêm tháng thứ hai",
  "Mốc 3 · Cộng thêm tháng thứ ba",
  "Bước 4 · Chia tổng thành 25 phần bằng nhau",
  "Bước 5 · Đọc trung bình của mỗi công nhân",
];

function phaseAt(progress) {
  if (progress >= 1) return 5;
  return Math.min(4, Math.floor(Math.max(0, progress) * 5));
}

function format(value) {
  return new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 2 }).format(value);
}

function ratioPhaseAt(progress) {
  if (progress >= 1) return 4;
  return Math.min(3, Math.floor(Math.max(0, progress) * 4));
}

function sequentialPhaseAt(progress) {
  if (progress >= 1) return 4;
  return Math.min(3, Math.floor(Math.max(0, progress) * 5));
}

function People({ count }) {
  if (!Number.isInteger(count) || count < 1 || count > 5) return <b>{format(count)}</b>;
  return (
    <span className={styles.peopleInPart} aria-label={`${count} học sinh`}>
      {Array.from({ length: count }, (_, index) => <i key={index} />)}
    </span>
  );
}

function RatioRow({ label, parts, value, onePart, visible, target = false }) {
  return (
    <div className={styles.ratioShareRow}>
      <div className={styles.ratioShareLabel}>
        <b>{label}</b>
        <span>{visible ? `${format(value)} học sinh` : "? học sinh"}</span>
      </div>
      <div className={styles.equalParts} style={{ gridTemplateColumns: `repeat(${parts}, minmax(32px, 1fr))` }}>
        {Array.from({ length: parts }, (_, index) => (
          <div
            key={index}
            className={visible ? (target && index === parts - 1 ? styles.equalPartExtra : styles.equalPartFilled) : styles.equalPart}
          >
            {visible ? <People count={onePart} /> : <span>1 phần</span>}
          </div>
        ))}
      </div>
      <small>{parts} phần bằng nhau{visible ? ` × ${format(onePart)} học sinh` : ""}</small>
    </div>
  );
}

function RatioShareModel({ ratio, progress }) {
  const phase = ratioPhaseAt(progress);
  const titles = [
    `Bắt đầu · Nữ bằng ${ratio.numerator}/${ratio.denominator} số học sinh nam`,
    `Bước 1 · ${ratio.denominator} phần nam ứng với ${format(ratio.known)} học sinh`,
    `Bước 2 · Một phần có ${format(ratio.known)} ÷ ${ratio.denominator} = ${format(ratio.onePart)} học sinh`,
    `Bước 3 · Dựng ${ratio.numerator} phần học sinh nữ`,
    `Bước 4 · ${ratio.numerator} × ${format(ratio.onePart)} = ${format(ratio.target)} học sinh nữ`,
  ];
  return (
    <figure className={`${styles.panel} ${styles.averagePanel}`}>
      <figcaption className={styles.panelTitle}>Sơ đồ phần bằng nhau</figcaption>
      <p className={styles.teachingStep}>{titles[phase]}</p>
      <div className={styles.ratioStatement}>
        <span>Nữ</span><b>{ratio.numerator}</b><i>/</i><b>{ratio.denominator}</b><span>Nam</span>
      </div>
      <RatioRow
        label="Học sinh nam"
        parts={ratio.denominator}
        value={ratio.known}
        onePart={ratio.onePart}
        visible={phase >= 1}
      />
      <div className={phase >= 2 ? styles.onePartRule : styles.onePartRulePending}>
        <span>Mỗi ô là một phần bằng nhau</span>
        <strong>{format(ratio.known)} ÷ {ratio.denominator} = {phase >= 2 ? format(ratio.onePart) : "?"} học sinh/phần</strong>
      </div>
      <RatioRow
        label="Học sinh nữ"
        parts={ratio.numerator}
        value={ratio.target}
        onePart={ratio.onePart}
        visible={phase >= 3}
        target
      />
      {phase >= 4 ? (
        <div className={styles.averageAnswer}>
          <small>Lấy 9 phần, mỗi phần 2 học sinh</small>
          <strong>{ratio.numerator} × {format(ratio.onePart)} = {format(ratio.target)}</strong>
          <b>Lớp 4A có {format(ratio.target)} học sinh nữ.</b>
        </div>
      ) : (
        <p className={styles.fractionHint}>Nhấn “Chạy” hoặc “Bước sau” để mở từng lớp ý nghĩa.</p>
      )}
    </figure>
  );
}

function RatioTotalModel({ ratio, progress }) {
  const phase = ratioPhaseAt(progress);
  const Bar = ({ parts, value, accent = false }) => <div className={styles.ratioTotalRow}><span>{parts} phần</span><div style={{ gridTemplateColumns: `repeat(${parts}, minmax(30px, 1fr))` }}>{Array.from({ length: parts }, (_, index) => <i key={index} className={accent ? styles.ratioTotalPartAccent : styles.ratioTotalPart}>{phase >= 2 ? format(ratio.onePart) : "1 phần"}</i>)}</div><b>{phase >= 3 ? format(value) : "?"}</b></div>;
  return (
    <figure className={`${styles.panel} ${styles.averagePanel}`}>
      <figcaption className={styles.panelTitle}>Tìm hai số khi biết tổng và tỉ số</figcaption>
      <p className={styles.teachingStep}>{[
        `Bước 1 · Tỉ số gồm ${ratio.firstParts} phần và ${ratio.secondParts} phần`,
        `Bước 2 · Toàn bộ ${format(ratio.total)} ứng với ${ratio.allParts} phần`,
        `Bước 3 · Một phần = ${format(ratio.total)} ÷ ${ratio.allParts} = ${format(ratio.onePart)}`,
        "Bước 4 · Nhân giá trị một phần với số phần của mỗi đại lượng",
        `Kết luận · Hai số là ${format(ratio.first)} và ${format(ratio.second)}`,
      ][phase]}</p>
      <div className={styles.ratioTotalBrace}>Tổng {format(ratio.total)} = {ratio.allParts} phần bằng nhau</div>
      <Bar parts={ratio.firstParts} value={ratio.first} />
      <Bar parts={ratio.secondParts} value={ratio.second} accent />
      <p className={styles.visualEquation}>{phase >= 4 ? `${ratio.firstParts} × ${format(ratio.onePart)} = ${format(ratio.first)}; ${ratio.secondParts} × ${format(ratio.onePart)} = ${format(ratio.second)}` : phase >= 2 ? `${format(ratio.total)} ÷ ${ratio.allParts} = ${format(ratio.onePart)}` : "Gộp số phần trước khi chia tổng"}</p>
    </figure>
  );
}

function SequentialRemainderRatioModel({ model, progress }) {
  const phase = sequentialPhaseAt(progress);
  const unit = model.unit;
  const firstTitles = [
    `Bước 1 · Coi toàn bộ ${format(model.total)} ${unit} là ${model.firstDenominator} phần bằng nhau`,
    `Bước 2 · Ngày 1 lấy ${model.firstNumerator}/${model.firstDenominator}: ${format(model.total)} × ${model.firstNumerator}/${model.firstDenominator} = ${format(model.firstDay)} ${unit}`,
    `Bước 3 · Còn ${format(model.remainingAfterFirst)} ${unit}; chia phần còn lại thành ${model.secondDenominator} phần bằng nhau`,
    `Bước 4 · Ngày 2 lấy ${model.secondNumerator}/${model.secondDenominator} phần còn lại; ngày 3 nhận phần còn lại cuối cùng`,
    `Bước 5 · So sánh ngày 3 với ngày 1 và rút gọn tỉ số`,
  ];
  const comparisonMaximum = Math.max(model.firstDay, model.thirdDay);

  return (
    <figure className={`${styles.panel} ${styles.sequentialRatioPanel}`}>
      <figcaption className={styles.panelTitle}>Mô phỏng bán gạo theo phần còn lại</figcaption>
      <p className={styles.teachingStep}>{firstTitles[phase]}</p>

      <section className={styles.riceStage} aria-label={`Tổng số gạo ban đầu ${model.total} ${unit}`}>
        <div className={styles.riceStageHeader}>
          <b>Ban đầu</b>
          <strong>{format(model.total)} {unit}</strong>
          <span>{model.firstDenominator} phần bằng nhau</span>
        </div>
        <div
          className={styles.riceCells}
          style={{ gridTemplateColumns: `repeat(${model.firstDenominator}, minmax(42px, 1fr))` }}
        >
          {Array.from({ length: model.firstDenominator }, (_, index) => {
            const isFirstDay = index < model.firstNumerator;
            const revealed = phase >= 1;
            return (
              <div
                key={index}
                className={revealed
                  ? (isFirstDay ? styles.riceCellDayOne : styles.riceCellRemaining)
                  : styles.riceCellBase}
              >
                <span>{revealed ? format(model.firstUnit) : "1 phần"}</span>
                {revealed ? <small>{isFirstDay ? "Ngày 1" : "Còn lại"}</small> : null}
              </div>
            );
          })}
        </div>
        <p className={styles.riceEquation}>
          {phase >= 1
            ? <><b>Ngày 1:</b> {format(model.total)} × {model.firstNumerator}/{model.firstDenominator} = <strong>{format(model.firstDay)} {unit}</strong> · Còn lại <strong>{format(model.remainingAfterFirst)} {unit}</strong></>
            : <>Mỗi ô biểu diễn {format(model.total)} ÷ {model.firstDenominator} = <strong>{format(model.firstUnit)} {unit}</strong></>}
        </p>
      </section>

      {phase >= 2 ? (
        <section className={styles.riceStage} aria-label={`Phần gạo còn lại ${model.remainingAfterFirst} ${unit}`}>
          <div className={styles.riceStageHeader}>
            <b>Sau ngày 1</b>
            <strong>{format(model.remainingAfterFirst)} {unit}</strong>
            <span>Chia lại thành {model.secondDenominator} phần</span>
          </div>
          <div
            className={styles.riceCells}
            style={{ gridTemplateColumns: `repeat(${model.secondDenominator}, minmax(58px, 1fr))` }}
          >
            {Array.from({ length: model.secondDenominator }, (_, index) => {
              const isSecondDay = index < model.secondNumerator;
              return (
                <div
                  key={index}
                  className={phase >= 3
                    ? (isSecondDay ? styles.riceCellDayTwo : styles.riceCellDayThree)
                    : styles.riceCellRepartition}
                >
                  <span>{format(model.secondUnit)} {unit}</span>
                  <small>{phase >= 3 ? (isSecondDay ? "Ngày 2" : "Ngày 3") : `${index + 1}/${model.secondDenominator}`}</small>
                </div>
              );
            })}
          </div>
          <p className={styles.riceEquation}>
            {phase >= 3 ? (
              <><b>Ngày 2:</b> {format(model.remainingAfterFirst)} × {model.secondNumerator}/{model.secondDenominator} = <strong>{format(model.secondDay)} {unit}</strong> · <b>Ngày 3:</b> {format(model.remainingAfterFirst)} − {format(model.secondDay)} = <strong>{format(model.thirdDay)} {unit}</strong></>
            ) : (
              <>Mỗi phần mới: {format(model.remainingAfterFirst)} ÷ {model.secondDenominator} = <strong>{format(model.secondUnit)} {unit}</strong></>
            )}
          </p>
        </section>
      ) : (
        <p className={styles.fractionHint}>Tiếp tục để chia lại đúng phần gạo còn sau ngày thứ nhất.</p>
      )}

      {phase >= 4 ? (
        <section className={styles.riceComparison} aria-label="So sánh số gạo ngày ba và ngày một">
          <div className={styles.riceCompareRow}>
            <span>Ngày 3</span>
            <i style={{ width: `${model.thirdDay / comparisonMaximum * 100}%` }} />
            <b>{format(model.thirdDay)} {unit}</b>
          </div>
          <div className={styles.riceCompareRow}>
            <span>Ngày 1</span>
            <i style={{ width: `${model.firstDay / comparisonMaximum * 100}%` }} />
            <b>{format(model.firstDay)} {unit}</b>
          </div>
          <div className={styles.riceRatioConclusion}>
            <small>Cùng chia hai số cho {format(model.divisor)}</small>
            <strong>{format(model.thirdDay)} : {format(model.firstDay)} = {format(model.ratioNumerator)} : {format(model.ratioDenominator)}</strong>
            <b>Tỉ số ngày 3 và ngày 1 là {format(model.ratioNumerator)}/{format(model.ratioDenominator)}.</b>
          </div>
        </section>
      ) : null}
    </figure>
  );
}

function SequentialRemainderQuantityModel({ model, progress }) {
  const phase = sequentialPhaseAt(progress);
  const unit = model.unit === "m2" ? "m²" : model.unit === "cm2" ? "cm²" : model.unit;
  const titles = [
    "Bước 1 · Đổi các thành phần về cùng đơn vị rồi ghép thành toàn bộ",
    `Bước 2 · Lấy ${model.firstNumerator}/${model.firstDenominator} của toàn bộ lần thứ nhất`,
    `Bước 3 · Coi ${format(model.remainingAfterFirst)} ${unit} còn lại là một toàn bộ mới`,
    `Bước 4 · Lấy ${model.secondNumerator}/${model.secondDenominator} của phần còn lại, không lấy của tổng ban đầu`,
    `Bước 5 · Phần cuối cùng còn ${format(model.finalRemainder)} ${unit}`,
  ];

  return (
    <figure className={`${styles.panel} ${styles.sequentialRatioPanel}`}>
      <figcaption className={styles.panelTitle}>Mô phỏng hai lần lấy phân số trên phần còn lại</figcaption>
      <p className={styles.teachingStep}>{titles[phase]}</p>

      <section className={styles.riceStage} aria-label={`Toàn bộ ban đầu ${model.total} ${unit}`}>
        <div className={styles.riceStageHeader}>
          <b>Đổi và cộng diện tích</b>
          <strong>{format(model.total)} {unit}</strong>
          <span>{model.components.map((item) => item.label).join(" + ")}</span>
        </div>
        <div
          className={styles.riceCells}
          style={{ gridTemplateColumns: `repeat(${model.firstDenominator}, minmax(42px, 1fr))` }}
        >
          {Array.from({ length: model.firstDenominator }, (_, index) => {
            const usedFirst = index < model.firstNumerator;
            return (
              <div
                key={index}
                className={phase >= 1
                  ? (usedFirst ? styles.riceCellDayOne : styles.riceCellRemaining)
                  : styles.riceCellBase}
              >
                <span>{phase >= 1 ? `${format(model.firstUnit)} ${unit}` : "1 phần"}</span>
                {phase >= 1 ? <small>{usedFirst ? "Dùng lần 1" : "Còn lại"}</small> : null}
              </div>
            );
          })}
        </div>
        <p className={styles.riceEquation}>
          {phase >= 1 ? (
            <><b>Lần 1:</b> {format(model.total)} × {model.firstNumerator}/{model.firstDenominator} = <strong>{format(model.firstAllocation)} {unit}</strong> · Còn <strong>{format(model.remainingAfterFirst)} {unit}</strong></>
          ) : (
            <>{model.components.map((item) => item.label).join(" + ")} = <strong>{format(model.total)} {unit}</strong>; mỗi phần là {format(model.total)} ÷ {model.firstDenominator} = <strong>{format(model.firstUnit)} {unit}</strong></>
          )}
        </p>
      </section>

      {phase >= 2 ? (
        <section className={styles.riceStage} aria-label={`Phần còn lại ${model.remainingAfterFirst} ${unit}`}>
          <div className={styles.riceStageHeader}>
            <b>Toàn bộ mới</b>
            <strong>{format(model.remainingAfterFirst)} {unit}</strong>
            <span>Chia lại thành {model.secondDenominator} phần bằng nhau</span>
          </div>
          <div
            className={styles.riceCells}
            style={{ gridTemplateColumns: `repeat(${model.secondDenominator}, minmax(58px, 1fr))` }}
          >
            {Array.from({ length: model.secondDenominator }, (_, index) => {
              const usedSecond = index < model.secondNumerator;
              return (
                <div
                  key={index}
                  className={phase >= 3
                    ? (usedSecond ? styles.riceCellDayTwo : styles.riceCellDayThree)
                    : styles.riceCellRepartition}
                >
                  <span>{format(model.secondUnit)} {unit}</span>
                  <small>{phase >= 3 ? (usedSecond ? "Dùng lần 2" : "Phần cuối") : `${index + 1}/${model.secondDenominator}`}</small>
                </div>
              );
            })}
          </div>
          <p className={styles.riceEquation}>
            {phase >= 3 ? (
              <><b>Lần 2:</b> {format(model.remainingAfterFirst)} × {model.secondNumerator}/{model.secondDenominator} = <strong>{format(model.secondAllocation)} {unit}</strong> · <b>Phần cuối:</b> {format(model.remainingAfterFirst)} − {format(model.secondAllocation)} = <strong>{format(model.finalRemainder)} {unit}</strong></>
            ) : (
              <>Mỗi phần mới: {format(model.remainingAfterFirst)} ÷ {model.secondDenominator} = <strong>{format(model.secondUnit)} {unit}</strong></>
            )}
          </p>
        </section>
      ) : (
        <p className={styles.fractionHint}>Phần còn lại sẽ được coi là một toàn bộ mới ở bước tiếp theo.</p>
      )}

      {phase >= 4 ? (
        <section className={styles.riceRatioConclusion} aria-label="Kết luận phần đại lượng còn lại cuối cùng">
          <small>Kiểm tra ba phần ghép lại đúng toàn bộ ban đầu</small>
          <strong>{format(model.total)} − {format(model.firstAllocation)} − {format(model.secondAllocation)} = {format(model.finalRemainder)} {unit}</strong>
          <b>{format(model.firstAllocation)} + {format(model.secondAllocation)} + {format(model.finalRemainder)} = {format(model.total)} {unit}</b>
        </section>
      ) : null}
    </figure>
  );
}

function distanceTimePhaseAt(progress) {
  if (progress >= 1) return 4;
  return Math.min(3, Math.floor(Math.max(0, progress) * 5));
}

function unitLabel(unit) {
  return {
    hour: "giờ",
    minute: "phút",
    km: "km",
    m: "m",
  }[unit] || unit;
}

function TimeDistanceRow({
  duration,
  distance,
  unitDistance,
  maximum,
  visible,
  segmented,
  durationUnit,
  distanceUnit,
  target = false,
}) {
  const parts = segmented ? duration : 1;
  return (
    <div className={styles.distanceTimeRow}>
      <div className={styles.distanceTimeLabel}>
        <b>{target ? "Thời gian mới" : "Dữ kiện đã biết"}</b>
        <span>{format(duration)} {durationUnit}</span>
      </div>
      <div
        className={target ? styles.distanceTimeTrackTarget : styles.distanceTimeTrack}
        style={{
          "--distance-time-width": `${Math.max(12, duration / maximum * 100)}%`,
          gridTemplateColumns: `repeat(${parts}, minmax(0, 1fr))`,
        }}
        role="img"
        aria-label={`${format(duration)} ${durationUnit} gồm ${parts} phần thời gian, quãng đường ${visible ? format(distance) : "chưa tính"}`}
      >
        {Array.from({ length: parts }, (_, index) => (
          <i key={index} className={visible ? styles.distanceTimeBlockVisible : styles.distanceTimeBlock}>
            <span>{segmented ? `1 ${durationUnit}` : `${format(duration)} ${durationUnit}`}</span>
            <small>{visible ? `${format(segmented ? unitDistance : distance)} ${distanceUnit}` : `? ${distanceUnit}`}</small>
          </i>
        ))}
      </div>
      <strong>{visible ? `${format(distance)} ${distanceUnit}` : `? ${distanceUnit}`}</strong>
    </div>
  );
}

function DirectProportionDistanceTimeModel({ model, progress }) {
  const phase = distanceTimePhaseAt(progress);
  const durationUnit = unitLabel(model.durationUnit);
  const distanceUnit = unitLabel(model.distanceUnit);
  const maximum = Math.max(model.knownDuration, model.targetDuration);
  const titles = [
    `Bước 1 · ${format(model.knownDuration)} ${durationUnit} ứng với ${format(model.knownDistance)} ${distanceUnit}`,
    `Bước 2 · Tìm quãng đường trong 1 ${durationUnit}: ${format(model.knownDistance)} ÷ ${format(model.knownDuration)}`,
    `Bước 3 · Dựng ${format(model.targetDuration)} phần thời gian bằng nhau`,
    `Bước 4 · Nhân quãng đường 1 ${durationUnit} với ${format(model.targetDuration)}`,
    "Bước 5 · Kiểm tra quãng đường trên mỗi giờ không đổi",
  ];
  return (
    <figure className={`${styles.panel} ${styles.distanceTimePanel}`}>
      <figcaption className={styles.panelTitle}>Sơ đồ quãng đường tỉ lệ thuận với thời gian</figcaption>
      <p className={styles.teachingStep}>{titles[phase]}</p>

      <div className={styles.distanceTimeInvariant}>
        <span>Cùng một ô tô · vận tốc không đổi</span>
        <strong>Mỗi phần thời gian đi được cùng một quãng đường</strong>
      </div>

      <TimeDistanceRow
        duration={model.knownDuration}
        distance={model.knownDistance}
        unitDistance={model.unitDistance}
        maximum={maximum}
        visible
        segmented={model.segmented}
        durationUnit={durationUnit}
        distanceUnit={distanceUnit}
      />

      <div className={phase >= 1 ? styles.distanceTimeUnitRule : styles.distanceTimeUnitRulePending}>
        <span>Quy về 1 {durationUnit}</span>
        <strong>
          {format(model.knownDistance)} ÷ {format(model.knownDuration)} = {phase >= 1 ? format(model.unitDistance) : "?"} {distanceUnit}/{durationUnit}
        </strong>
      </div>

      {phase >= 2 ? (
        <TimeDistanceRow
          duration={model.targetDuration}
          distance={model.targetDistance}
          unitDistance={model.unitDistance}
          maximum={maximum}
          visible={phase >= 3}
          segmented={model.segmented}
          durationUnit={durationUnit}
          distanceUnit={distanceUnit}
          target
        />
      ) : (
        <p className={styles.fractionHint}>Tiếp tục để xếp số phần thời gian mới bằng đúng kích thước mỗi giờ ở hàng trên.</p>
      )}

      {phase >= 3 ? (
        <div className={styles.distanceTimeAnswer}>
          <small>Giữ nguyên {format(model.unitDistance)} {distanceUnit} trong mỗi {durationUnit}</small>
          <strong>{format(model.unitDistance)} × {format(model.targetDuration)} = {format(model.targetDistance)} {distanceUnit}</strong>
          <b>Ô tô đi trong {format(model.targetDuration)} {durationUnit} được {format(model.targetDistance)} {distanceUnit}.</b>
          {phase >= 4 ? <em>Kiểm tra: {format(model.targetDistance)} ÷ {format(model.targetDuration)} = {format(model.unitDistance)} {distanceUnit}/{durationUnit}</em> : null}
        </div>
      ) : null}
    </figure>
  );
}

function WorkTileMatrix({ workers, totalWork, active, label }) {
  return (
    <div className={styles.workMatrixWrap}>
      <div className={styles.workMatrixLabel}>
        <b>{label}</b>
        <span>{workers} cột người</span>
      </div>
      <div
        className={styles.workMatrix}
        style={{ gridTemplateColumns: `repeat(${workers}, minmax(22px, 1fr))` }}
        role="img"
        aria-label={`${totalWork} ô công-ngày xếp theo ${workers} người`}
      >
        {Array.from({ length: totalWork }, (_, index) => (
          <i key={index} className={active ? styles.workTileActive : styles.workTile}>
            <span>{(index % workers) + 1}</span>
          </i>
        ))}
      </div>
    </div>
  );
}

function VariablePeopleWorkRateModel({ model, progress }) {
  const phase = progress >= 1 ? 4 : Math.min(3, Math.floor(Math.max(0, progress) * 5));
  const changeSign = model.workerChange >= 0 ? "+" : "−";
  const changeMagnitude = Math.abs(model.workerChange);
  const titles = [
    `Bước 1 · Dựng ${model.initialWorkers} người làm trong ${model.plannedDays} ngày`,
    `Bước 2 · Toàn bộ công việc = ${model.initialWorkers} × ${model.plannedDays} = ${format(model.totalWork)} công-ngày`,
    `Bước 3 · Tổ mới có ${model.initialWorkers} ${changeSign} ${changeMagnitude} = ${model.newWorkers} người`,
    `Bước 4 · Xếp lại nguyên ${format(model.totalWork)} ô công-ngày cho ${model.newWorkers} người`,
    `Bước 5 · ${format(model.totalWork)} ÷ ${model.newWorkers} = ${format(model.newDays)} ngày`,
  ];

  return (
    <figure className={`${styles.panel} ${styles.workRatePanel}`}>
      <figcaption className={styles.panelTitle}>Mô phỏng công việc không đổi</figcaption>
      <p className={styles.teachingStep}>{titles[phase]}</p>

      <div className={styles.workInvariant}>
        <span>Mỗi ô = 1 người làm trong 1 ngày</span>
        <strong>Công việc giữ nguyên: người × ngày</strong>
      </div>

      <section className={styles.workStage}>
        <header>
          <div><small>Tổ ban đầu</small><b>{model.initialWorkers} người</b></div>
          <span>×</span>
          <div><small>Kế hoạch</small><b>{model.plannedDays} ngày</b></div>
          <span>=</span>
          <div><small>Khối lượng</small><b>{phase >= 1 ? `${format(model.totalWork)} công-ngày` : "? công-ngày"}</b></div>
        </header>
        <WorkTileMatrix
          workers={model.initialWorkers}
          totalWork={model.totalWork}
          active={phase >= 1}
          label={`${model.initialWorkers} người × ${model.plannedDays} ngày`}
        />
      </section>

      {phase >= 2 ? (
        <div className={styles.workRearrangeArrow}>
          <span>{model.initialWorkers} {changeSign} {changeMagnitude} = <b>{model.newWorkers} người</b></span>
          <strong>↓ Giữ nguyên {format(model.totalWork)} ô, chỉ xếp lại ↓</strong>
        </div>
      ) : null}

      {phase >= 2 ? (
        <section className={styles.workStage}>
          <header>
            <div><small>Tổ mới</small><b>{model.newWorkers} người</b></div>
            <span>×</span>
            <div><small>Thời gian mới</small><b>{phase >= 4 ? `${format(model.newDays)} ngày` : "? ngày"}</b></div>
            <span>=</span>
            <div><small>Cùng công việc</small><b>{format(model.totalWork)} công-ngày</b></div>
          </header>
          <WorkTileMatrix
            workers={model.newWorkers}
            totalWork={model.totalWork}
            active={phase >= 3}
            label={`${model.newWorkers} người × ? ngày`}
          />
        </section>
      ) : (
        <p className={styles.fractionHint}>Tiếp tục để bổ sung người nhưng giữ nguyên toàn bộ công việc.</p>
      )}

      {phase >= 4 ? (
        <div className={styles.workRateAnswer}>
          <small>Chia khối lượng công việc cho số người mới</small>
          <strong>{format(model.totalWork)} ÷ {model.newWorkers} = {format(model.newDays)} ngày</strong>
          <b>Kiểm tra: {model.newWorkers} × {format(model.newDays)} = {format(model.totalWork)} công-ngày</b>
        </div>
      ) : null}
    </figure>
  );
}

function BinomialAreaModel({ model, progress }) {
  const phase = progress >= 1 ? 4 : Math.min(3, Math.floor(Math.max(0, progress) * 4));
  const split = `${model.splitPercent}%`;
  return (
    <figure className={`${styles.panel} ${styles.binomialPanel}`}>
      <figcaption className={styles.panelTitle}>Mô hình diện tích của (a + b)²</figcaption>
      <p className={styles.teachingStep}>{[
        `Bước 1 · Dựng hình vuông cạnh a + b = ${model.a} + ${model.b}`,
        `Bước 2 · Cắt mỗi cạnh tại a = ${model.a} và b = ${model.b}`,
        "Bước 3 · Nhận ra bốn miền diện tích",
        "Bước 4 · Ghép hai hình chữ nhật ab giống nhau",
        "Bước 5 · Cộng diện tích toàn hình vuông",
      ][phase]}</p>
      <div className={styles.binomialLayout} style={{ "--binomial-split": split }}>
        <div className={styles.binomialSideTop}><span>a = {model.a}</span><span>b = {model.b}</span></div>
        <div
          className={styles.binomialSquare}
          style={{ gridTemplateColumns: `${split} 1fr`, gridTemplateRows: `${split} 1fr` }}
          role="img"
          aria-label={`Hình vuông cạnh ${model.side} chia thành a bình, hai ab và b bình`}
        >
          <div className={styles.areaASquare}><b>a²</b><span>{model.a} × {model.a} = {model.aSquare}</span></div>
          <div className={phase >= 2 ? styles.areaABVisible : styles.areaAB}><b>ab</b><span>{model.a} × {model.b} = {model.ab}</span></div>
          <div className={phase >= 2 ? styles.areaABVisible : styles.areaAB}><b>ab</b><span>{model.b} × {model.a} = {model.ab}</span></div>
          <div className={phase >= 2 ? styles.areaBSquareVisible : styles.areaBSquare}><b>b²</b><span>{model.b} × {model.b} = {model.bSquare}</span></div>
        </div>
        <div className={styles.binomialSideLeft}><span>a = {model.a}</span><span>b = {model.b}</span></div>
      </div>
      {phase >= 3 ? (
        <p className={styles.cumulativeFormula}>
          a² + ab + ab + b² = <b>a² + 2ab + b²</b>
        </p>
      ) : null}
      {phase >= 4 ? (
        <div className={styles.visualConclusion}>
          <span>({model.a} + {model.b})²</span>
          <span>= {model.aSquare} + 2 × {model.ab} + {model.bSquare}</span>
          <strong>= {model.total}</strong>
        </div>
      ) : <p className={styles.fractionHint}>Công thức xuất hiện sau khi bốn miền đã rõ.</p>}
    </figure>
  );
}


/** Uneven columns levelled to their own mean, with the transfers shown. */
function ArithmeticMeanModel({ model, progress }) {
  const phase = progress >= 1 ? 3 : Math.min(2, Math.floor(Math.max(0, progress) * 3));
  const height = (value) => `${Math.max(4, (value / model.scaleMax) * 100)}%`;
  return (
    <figure className={`${styles.panel} ${styles.averagePanel}`}>
      <figcaption className={styles.panelTitle}>Trung bình cộng · san bằng các cột</figcaption>
      <p className={styles.teachingStep}>{[
        `Bước 1 · Dựng ${model.count} cột theo đúng số liệu đã cho`,
        `Bước 2 · Gộp toàn bộ thành tổng ${format(model.total)}`,
        `Bước 3 · Chia đều tổng cho ${model.count} phần bằng nhau`,
        `Bước 4 · Mọi cột cùng cao ${format(model.mean)}: đó là trung bình cộng`,
      ][phase]}</p>
      <div className={styles.meanChart} style={{ "--mean-columns": model.count }}>
        {model.transfers.map((item, index) => (
          <div key={item.id} className={styles.meanColumn}>
            <div className={styles.meanBarTrack}>
              <div className={phase >= 3 ? styles.meanBarLevelled : styles.meanBar}
                style={{ height: phase >= 3 ? height(model.mean) : height(item.value) }} />
              {phase >= 2 ? <span className={styles.meanLevelLine} style={{ bottom: height(model.mean) }} /> : null}
            </div>
            <b>{format(phase >= 3 ? model.mean : item.value)}</b>
            <small>{item.label || `Số ${index + 1}`}</small>
            {phase >= 2 && item.delta !== 0 ? (
              <em className={item.delta > 0 ? styles.meanGain : styles.meanGive}>
                {item.delta > 0 ? "+" : "−"}{format(Math.abs(item.delta))}
              </em>
            ) : null}
          </div>
        ))}
      </div>
      {phase >= 3 ? (
        <div className={styles.visualConclusion}>
          <span>Trung bình cộng</span>
          <strong>({model.values.map((item) => format(item.value)).join(" + ")}) ÷ {model.count} = {format(model.mean)}</strong>
          <small>Kiểm tra: {format(model.mean)} × {model.count} = {format(model.total)}</small>
        </div>
      ) : <p className={styles.fractionHint}>Kéo thanh tiến độ để gộp tổng rồi san bằng các cột.</p>}
    </figure>
  );
}

/** Two bars in ratio a:b whose extra parts carry the printed difference. */
function ProportionalDifferenceModel({ model, progress }) {
  const phase = progress >= 1 ? 3 : Math.min(2, Math.floor(Math.max(0, progress) * 3));
  const Bar = ({ parts, accent, value }) => (
    <div className={styles.ratioTotalRow}>
      <span>{parts} phần</span>
      <div style={{ gridTemplateColumns: `repeat(${parts}, minmax(24px, 1fr))` }}>
        {Array.from({ length: parts }, (_, index) => (
          <i key={index} className={
            phase >= 1 && index >= Math.min(model.firstParts, model.secondParts)
              ? styles.ratioTotalPartAccent
              : (accent ? styles.ratioTotalPartAccent : styles.ratioTotalPart)
          }>
            {phase >= 2 ? format(model.onePart) : "1 phần"}
          </i>
        ))}
      </div>
      <b>{phase >= 3 ? format(value) : "?"}</b>
    </div>
  );
  return (
    <figure className={`${styles.panel} ${styles.averagePanel}`}>
      <figcaption className={styles.panelTitle}>Hai đại lượng tỉ lệ · biết hiệu và tỉ số</figcaption>
      <p className={styles.teachingStep}>{[
        `Bước 1 · Vẽ hai thanh theo tỉ số ${model.firstParts} : ${model.secondParts}`,
        `Bước 2 · Phần chênh lệch là ${model.partGap} phần và bằng ${format(model.difference)}`,
        `Bước 3 · Một phần bằng ${format(model.difference)} ÷ ${model.partGap} = ${format(model.onePart)}`,
        `Bước 4 · Nhân lại: ${format(model.first)} và ${format(model.second)}`,
      ][phase]}</p>
      <div className={styles.ratioTotalStack}>
        <Bar parts={model.firstParts} accent={false} value={model.first} />
        <Bar parts={model.secondParts} accent value={model.second} />
      </div>
      {phase >= 3 ? (
        <div className={styles.visualConclusion}>
          <span>Hai đại lượng</span>
          <strong>{format(model.first)} và {format(model.second)}</strong>
          <small>Kiểm tra hiệu: {format(model.first)} − {format(model.second)} = {format(model.first - model.second)}</small>
        </div>
      ) : <p className={styles.fractionHint}>Kéo thanh tiến độ để đọc giá trị một phần rồi suy ra hai đại lượng.</p>}
    </figure>
  );
}

/** One running total carried through two dependent operations. */
function MultiStepArithmeticModel({ model, progress }) {
  const phase = progress >= 1 ? 3 : Math.min(2, Math.floor(Math.max(0, progress) * 3));
  const width = (value) => `${Math.max(6, (value / model.scaleMax) * 100)}%`;
  const rows = [
    { label: "Ban đầu", value: model.start, visible: true },
    ...model.stages.map((stage, index) => ({
      label: `Sau bước ${index + 1}: ${stage.symbol} ${format(stage.operand)}`,
      value: stage.after,
      visible: phase >= index + 1,
    })),
  ];
  return (
    <figure className={`${styles.panel} ${styles.averagePanel}`}>
      <figcaption className={styles.panelTitle}>Bài toán nhiều bước · một đại lượng thay đổi liên tiếp</figcaption>
      <p className={styles.teachingStep}>{[
        `Bước 1 · Bắt đầu với ${format(model.start)}`,
        `Bước 2 · ${model.stages[0].symbol} ${format(model.stages[0].operand)} còn ${format(model.stages[0].after)}`,
        `Bước 3 · ${model.stages[1].symbol} ${format(model.stages[1].operand)} còn ${format(model.stages[1].after)}`,
        `Bước 4 · Kết quả cuối cùng là ${format(model.result)}`,
      ][phase]}</p>
      <ol className={styles.multiStepStack}>
        {rows.map((row) => (
          <li key={row.label} className={row.visible ? styles.multiStepRow : styles.multiStepRowPending}>
            <span>{row.label}</span>
            <div className={styles.multiStepTrack}>
              <div className={styles.multiStepBar} style={{ width: row.visible ? width(row.value) : "0%" }} />
            </div>
            <b>{row.visible ? format(row.value) : "?"}</b>
          </li>
        ))}
      </ol>
      {phase >= 3 ? (
        <div className={styles.visualConclusion}>
          <span>Chuỗi phép tính</span>
          <strong>
            {format(model.start)} {model.stages.map((stage) => `${stage.symbol} ${format(stage.operand)}`).join(" ")} = {format(model.result)}
          </strong>
        </div>
      ) : <p className={styles.fractionHint}>Mỗi bước chỉ đổi một đại lượng; thanh trước vẫn giữ nguyên để so sánh.</p>}
    </figure>
  );
}

export default function BarModelRenderer({ world, progress, visualization, scene }) {
  const problemType = String(scene?.metadata?.problem_type || "").toLowerCase();
  const binomial = deriveBinomialSquare(
    world,
    visualization?.bindings,
    scene?.metadata?.source_text,
  );
  if (binomial && /(expansion|binomial|identity|hằng đẳng thức)/.test(problemType)) {
    return <BinomialAreaModel model={binomial} progress={progress} />;
  }
  if (problemType.includes("distance_time_direct_proportion")) {
    const distanceTime = deriveDirectProportionDistanceTime(world, visualization?.bindings);
    if (distanceTime) return <DirectProportionDistanceTimeModel model={distanceTime} progress={progress} />;
    return <p className={styles.unavailable}>Đề cần một cặp thời gian–quãng đường đã biết và thời gian mới để mô phỏng chính xác.</p>;
  }
  if (problemType.includes("work_rate_with_variable_people")) {
    const workRate = deriveVariablePeopleWorkRate(world, visualization?.bindings);
    if (workRate) return <VariablePeopleWorkRateModel model={workRate} progress={progress} />;
    return <p className={styles.unavailable}>Đề cần số người ban đầu, số ngày dự định và số người thêm hoặc bớt để mô phỏng chính xác.</p>;
  }
  const sequentialQuantityFamily = problemType.includes("sequential_fraction_remainder_quantity")
    || (visualization?.bindings?.area?.length
      && visualization?.bindings?.addend_numerator?.length
      && visualization?.bindings?.addend_denominator?.length);
  if (sequentialQuantityFamily) {
    const sequentialQuantity = deriveSequentialRemainderQuantity(world, visualization?.bindings);
    if (sequentialQuantity) {
      return <SequentialRemainderQuantityModel model={sequentialQuantity} progress={progress} />;
    }
    return <p className={styles.unavailable}>Đề cần toàn bộ ban đầu và hai phân số liên tiếp của phần còn lại để mô phỏng chính xác.</p>;
  }
  if (problemType.includes("sequential_fraction_remainder_ratio")) {
    const sequentialRatio = deriveSequentialRemainderRatio(world, visualization?.bindings);
    if (sequentialRatio) {
      return <SequentialRemainderRatioModel model={sequentialRatio} progress={progress} />;
    }
    return <p className={styles.unavailable}>Đề cần tổng ban đầu và hai phân số “ngày 1 / ngày 2 của phần còn lại” để mô phỏng chính xác.</p>;
  }
  if (problemType.includes("arithmetic_mean")) {
    const mean = deriveArithmeticMean(world, visualization?.bindings);
    if (mean) return <ArithmeticMeanModel model={mean} progress={progress} />;
    return <p className={styles.unavailable}>Đề cần ít nhất hai số liệu để tìm trung bình cộng.</p>;
  }
  if (problemType.includes("proportional_system_two_variables")) {
    const proportional = deriveProportionalDifference(world, visualization?.bindings);
    if (proportional) return <ProportionalDifferenceModel model={proportional} progress={progress} />;
    return <p className={styles.unavailable}>Đề cần hiệu hai đại lượng và tỉ số giữa chúng.</p>;
  }
  if (problemType.includes("multi_step_arithmetic")) {
    const multiStep = deriveMultiStepArithmetic(world, visualization?.bindings, problemType);
    if (multiStep) return <MultiStepArithmeticModel model={multiStep} progress={progress} />;
    return <p className={styles.unavailable}>Đề cần số ban đầu và hai phép tính liên tiếp.</p>;
  }
  const ratioTotal = deriveRatioTotal(world, visualization?.bindings);
  if (ratioTotal && problemType.includes("ratio_total_parts")) return <RatioTotalModel ratio={ratioTotal} progress={progress} />;
  const ratio = deriveRatioShare(world, visualization?.bindings);
  if (ratio && problemType.includes("ratio")) {
    return <RatioShareModel ratio={ratio} progress={progress} />;
  }
  const average = deriveAveragePerPerson(world, visualization?.bindings);
  if (!average || !problemType.includes("average")) {
    return <p className={styles.unavailable}>Sơ đồ trung bình cần ba mốc sản lượng và số công nhân.</p>;
  }

  const phase = phaseAt(progress);
  const visibleMonths = Math.min(phase, 3);
  const cumulative = visibleMonths ? average.milestones[visibleMonths - 1].cumulative : 0;

  return (
    <figure className={`${styles.panel} ${styles.averagePanel}`}>
      <figcaption className={styles.panelTitle}>Dòng thời gian sản lượng và chia đều</figcaption>
      <p className={styles.teachingStep}>{PHASE_TITLES[phase]}</p>

      <ol className={styles.averageTimeline} aria-label="Các mốc giải bài toán">
        {average.milestones.map((milestone, index) => {
          const reached = phase >= index + 1;
          return (
            <li key={milestone.id} className={reached ? styles.milestoneReached : styles.milestone}>
              <span>{index + 1}</span>
              <b>{milestone.label}</b>
              <small>+{format(milestone.value)} sản phẩm</small>
              <em>{reached ? `Cộng dồn: ${format(milestone.cumulative)}` : "Chưa đến mốc"}</em>
            </li>
          );
        })}
        <li className={phase >= 4 ? styles.milestoneReached : styles.milestone}>
          <span>÷</span>
          <b>Chia đều</b>
          <small>{average.workers} công nhân</small>
          <em>{phase >= 4 ? `${format(average.total)} ÷ ${average.workers}` : "Sau khi cộng đủ 3 tháng"}</em>
        </li>
      </ol>

      <div className={styles.monthBars}>
        {average.monthly.map((month, index) => (
          <div key={month.id} className={phase >= index + 1 ? styles.monthRowReached : styles.monthRow}>
            <b>{month.label}</b>
            <span className={styles.monthTrack}>
              <i style={{ width: phase >= index + 1 ? `${(month.value / average.maximumMonth) * 100}%` : "0%" }} />
            </span>
            <strong>{phase >= index + 1 ? format(month.value) : "?"}</strong>
          </div>
        ))}
      </div>

      <p className={styles.cumulativeFormula}>
        {visibleMonths === 0 ? (
          "Ta cộng lần lượt sản lượng theo đúng thứ tự thời gian."
        ) : visibleMonths < 3 ? (
          <>{average.monthly.slice(0, visibleMonths).map((item) => format(item.value)).join(" + ")} = <b>{format(cumulative)}</b> sản phẩm</>
        ) : (
          <>{average.monthly.map((item) => format(item.value)).join(" + ")} = <b>{format(average.total)}</b> sản phẩm trong 3 tháng</>
        )}
      </p>

      {phase >= 4 ? (
        <div className={styles.equalShareArea}>
          <div className={styles.workerGrid} aria-label={`${average.workers} công nhân`}>
            {Array.from({ length: average.workers }, (_, index) => <i key={index} />)}
          </div>
          <span className={styles.shareArrow}>→</span>
          <div className={phase >= 5 ? styles.averageAnswer : styles.averagePending}>
            <small>Mỗi công nhân</small>
            {phase >= 5 ? (
              <strong>{format(average.total)} ÷ {average.workers} = {format(average.perPerson)}</strong>
            ) : (
              <strong>{format(average.total)} ÷ {average.workers} = ?</strong>
            )}
            <b>{phase >= 5 ? `${format(average.perPerson)} sản phẩm/người` : "Chia thành các phần bằng nhau"}</b>
          </div>
        </div>
      ) : (
        <p className={styles.fractionHint}>Nhấn “Chạy” hoặc “Bước sau” để đi qua từng tháng.</p>
      )}
    </figure>
  );
}
