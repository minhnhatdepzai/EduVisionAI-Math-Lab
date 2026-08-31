import { deriveCoordinateGraph, deriveLinearSystem } from "../derive/deriveScene.js";
import { deriveCubicGraph, deriveQuadraticGraph } from "../derive/deriveCurriculum.js";
import styles from "./renderers.module.css";
import { normalizeProblemType } from "../schemas/mathLabSchema.js";

const SIZE = 300;
const PAD = 28;

export default function CoordinateGraphRenderer({ world, progress, visualization, scene }) {
  const problemType = normalizeProblemType(scene?.metadata?.problem_type);
  if (problemType === "cubic_equation") {
    return <CubicGraph world={world} progress={progress} visualization={visualization} />;
  }
  if (/^quadratic_(function_graph|equation(?:_vieta)?)$/.test(problemType)) {
    return <QuadraticGraph world={world} progress={progress} visualization={visualization} vieta={/vieta/.test(problemType)} />;
  }
  if (/linear_system_two_variables/.test(problemType)) {
    const system = deriveLinearSystem(world, visualization?.bindings);
    return system
      ? <LinearSystemGraph system={system} progress={progress} />
      : <p className={styles.unavailable}>Cần đủ hệ số của cả hai phương trình để dựng hai đường thẳng.</p>;
  }
  const graph = deriveCoordinateGraph(world, visualization?.bindings);
  if (!graph) {
    return <p className={styles.unavailable}>Cần hàm số hoặc ít nhất hai điểm để dựng đồ thị.</p>;
  }
  const phase = progress >= 1 ? 3 : Math.min(3, Math.floor(Math.max(0, progress) * 4));
  const scale = (SIZE - PAD * 2) / (graph.range * 2);
  const toX = (x) => SIZE / 2 + x * scale;
  const toY = (y) => SIZE / 2 - y * scale;
  const ticks = Array.from({ length: graph.range * 2 + 1 }, (_, index) => index - graph.range);
  if (graph.kind === "points") {
    const point = graph.points[0];
    return (
      <figure className={`${styles.panel} ${styles.coordinatePanel}`}>
        <figcaption className={styles.panelTitle}>Biểu diễn điểm trên mặt phẳng tọa độ</figcaption>
        <p className={styles.teachingStep}>{progress < 0.34 ? "Bước 1 · Dựng hai trục cùng tỉ lệ" : progress < 0.67 ? `Bước 2 · Đi theo hoành độ x = ${point.x}` : `Bước 3 · Đi theo tung độ y = ${point.y} và đặt điểm`}</p>
        <svg viewBox={`0 0 ${SIZE} ${SIZE}`} className={styles.coordinateGraph} role="img" aria-label={`Điểm có tọa độ ${point.x}, ${point.y}`}>
          {ticks.map((value) => <g key={value}><line className={styles.graphGrid} x1={toX(value)} y1={PAD} x2={toX(value)} y2={SIZE - PAD} /><line className={styles.graphGrid} x1={PAD} y1={toY(value)} x2={SIZE - PAD} y2={toY(value)} /></g>)}
          <line className={styles.graphAxis} x1={PAD} y1={toY(0)} x2={SIZE - PAD} y2={toY(0)} />
          <line className={styles.graphAxis} x1={toX(0)} y1={SIZE - PAD} x2={toX(0)} y2={PAD} />
          {progress >= 0.34 ? <line className={styles.slopeTriangle} x1={toX(point.x)} y1={toY(0)} x2={toX(point.x)} y2={progress >= 0.67 ? toY(point.y) : toY(0)} strokeDasharray="5 4" /> : null}
          {progress >= 0.67 ? <><circle className={styles.graphPointAccent} cx={toX(point.x)} cy={toY(point.y)} r="6" /><text className={styles.graphPointLabel} x={toX(point.x) + 8} y={toY(point.y) - 8}>A({point.x}; {point.y})</text></> : null}
        </svg>
      </figure>
    );
  }
  const lineStart = { x: -graph.range, y: graph.slope * -graph.range + graph.intercept };
  const lineEnd = { x: graph.range, y: graph.slope * graph.range + graph.intercept };
  const secondPoint = { x: 1, y: graph.slope + graph.intercept };
  return (
    <figure className={`${styles.panel} ${styles.coordinatePanel}`}>
      <figcaption className={styles.panelTitle}>Đồ thị tọa độ</figcaption>
      <p className={styles.teachingStep}>{[
        "Bước 1 · Dựng hai trục x, y và cùng một tỉ lệ",
        `Bước 2 · Đặt tung độ gốc A(0; ${graph.intercept})`,
        `Bước 3 · Đi sang 1, đi lên ${graph.slope}: B(1; ${secondPoint.y})`,
        "Bước 4 · Nối các điểm để được toàn bộ hàm số",
      ][phase]}</p>
      <svg viewBox={`0 0 ${SIZE} ${SIZE}`} className={styles.coordinateGraph} role="img"
        aria-label={`Đồ thị y bằng ${graph.slope}x cộng ${graph.intercept}`}>
        <defs>
          <marker id="axis-arrow" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M0,0 L8,4 L0,8 Z" className={styles.axisArrow} />
          </marker>
          <clipPath id="coordinate-clip"><rect x={PAD} y={PAD} width={SIZE - PAD * 2} height={SIZE - PAD * 2} /></clipPath>
        </defs>
        {ticks.map((value) => (
          <g key={value}>
            <line className={styles.graphGrid} x1={toX(value)} y1={PAD} x2={toX(value)} y2={SIZE - PAD} />
            <line className={styles.graphGrid} x1={PAD} y1={toY(value)} x2={SIZE - PAD} y2={toY(value)} />
            {value !== 0 ? <text className={styles.graphTickLabel} x={toX(value)} y={toY(0) + 13}>{value}</text> : null}
            {value !== 0 ? <text className={styles.graphTickLabel} x={toX(0) - 8} y={toY(value) + 3}>{value}</text> : null}
          </g>
        ))}
        <line className={styles.graphAxis} x1={PAD} y1={toY(0)} x2={SIZE - PAD + 5} y2={toY(0)} markerEnd="url(#axis-arrow)" />
        <line className={styles.graphAxis} x1={toX(0)} y1={SIZE - PAD} x2={toX(0)} y2={PAD - 5} markerEnd="url(#axis-arrow)" />
        <text className={styles.axisName} x={SIZE - PAD + 8} y={toY(0) + 4}>x</text>
        <text className={styles.axisName} x={toX(0) + 7} y={PAD - 7}>y</text>
        {phase >= 1 ? <circle className={styles.graphPoint} cx={toX(0)} cy={toY(graph.intercept)} r="5" /> : null}
        {phase >= 1 ? <text className={styles.graphPointLabel} x={toX(0) + 7} y={toY(graph.intercept) - 7}>A(0; {graph.intercept})</text> : null}
        {phase >= 2 ? (
          <g>
            <polyline className={styles.slopeTriangle} points={`${toX(0)},${toY(graph.intercept)} ${toX(1)},${toY(graph.intercept)} ${toX(1)},${toY(secondPoint.y)}`} />
            <circle className={styles.graphPointAccent} cx={toX(1)} cy={toY(secondPoint.y)} r="5" />
            <text className={styles.graphPointLabel} x={toX(1) + 7} y={toY(secondPoint.y) - 7}>B(1; {secondPoint.y})</text>
          </g>
        ) : null}
        <line clipPath="url(#coordinate-clip)"
          className={`${styles.functionLine} ${phase < 3 ? styles.graphCurvePreview : ""}`}
          x1={toX(lineStart.x)} y1={toY(lineStart.y)} x2={toX(lineEnd.x)} y2={toY(lineEnd.y)} />
      </svg>
      <div className={styles.coordinateDetails}>
        <div><small>Công thức</small><strong>y = {graph.slope}x {graph.intercept >= 0 ? "+" : "−"} {Math.abs(graph.intercept)}</strong></div>
        <div><small>Hệ số góc</small><strong>Δy / Δx = {graph.slope} / 1</strong></div>
        <div className={styles.pointTable}>
          {graph.table.map((point) => <span key={point.x}>({point.x}; {point.y})</span>)}
        </div>
      </div>
      {/linear_equation_two_variables/.test(problemType) ? (
        <div className={styles.visualConclusion}>
          <span>Tập nghiệm</span>
          <strong>Cả đường thẳng là đáp án</strong>
          <small>Mỗi điểm (x; y) nằm trên đường đều thỏa phương trình, nên có vô số nghiệm.</small>
        </div>
      ) : null}
    </figure>
  );
}

const SYSTEM_STATE_TEXT = {
  intersecting: "Hai đường cắt nhau tại đúng một điểm: hệ có nghiệm duy nhất.",
  parallel: "Hai đường song song, không có điểm chung: hệ vô nghiệm.",
  coincident: "Hai đường trùng nhau: mọi điểm trên đường đều là nghiệm, hệ có vô số nghiệm.",
};

function readable(value) {
  return new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 2 }).format(value);
}

function gcdInteger(left, right) {
  let a = Math.abs(left);
  let b = Math.abs(right);
  while (b) [a, b] = [b, a % b];
  return a || 1;
}

function quadraticRootText(value) {
  if (!Number.isFinite(value)) return "?";
  if (Math.abs(value - Math.round(value)) <= 1e-9) return String(Math.round(value)).replace("-", "−");
  for (let denominator = 2; denominator <= 100; denominator += 1) {
    const numerator = Math.round(value * denominator);
    if (Math.abs(value - numerator / denominator) > 1e-9) continue;
    const divisor = gcdInteger(numerator, denominator);
    const reducedNumerator = numerator / divisor;
    const reducedDenominator = denominator / divisor;
    const sign = reducedNumerator < 0 ? "−" : "";
    return `${sign}${Math.abs(reducedNumerator)}/${reducedDenominator}`;
  }
  return `≈ ${readable(value).replace("-", "−")}`;
}

function quadraticRootEquation(name, value, compact = false) {
  const rendered = quadraticRootText(value);
  const approximate = rendered.startsWith("≈");
  if (compact) return `${name}${approximate ? "" : "="}${rendered}`;
  return `${name} ${approximate ? rendered : `= ${rendered}`}`;
}

const EXPONENT_TEXT = { 2: "²", 3: "³" };

function polynomialText(coefficients, symbol = "x") {
  const degree = coefficients.length - 1;
  const pieces = [];
  coefficients.forEach((value, index) => {
    if (!Number.isFinite(value) || Math.abs(value) <= 1e-10) return;
    const power = degree - index;
    const magnitude = Math.abs(value);
    const variable = power > 0 ? `${symbol}${EXPONENT_TEXT[power] || ""}` : "";
    const coefficient = variable && Math.abs(magnitude - 1) <= 1e-10 ? "" : readable(magnitude);
    const body = `${coefficient}${variable}` || "0";
    if (!pieces.length) pieces.push(`${value < 0 ? "−" : ""}${body}`);
    else pieces.push(`${value < 0 ? "−" : "+"} ${body}`);
  });
  return pieces.join(" ") || "0";
}

function factorFromRoot(root, symbol = "x") {
  const rendered = quadraticRootText(root).replace(/^≈\s*/, "");
  if (Math.abs(root) <= 1e-10) return symbol;
  return `(${symbol} ${root < 0 ? "+" : "−"} ${rendered.replace(/^−/, "")})`;
}

function integerTicks(minimum, maximum, target = 8) {
  const step = Math.max(1, Math.ceil((maximum - minimum) / target));
  const first = Math.ceil(minimum / step) * step;
  const values = [];
  for (let value = first; value <= maximum + 1e-9; value += step) values.push(value);
  return values;
}

function generalEquation({ a, b, c }) {
  const first = `${Math.abs(a) === 1 ? "" : readable(Math.abs(a))}x`;
  const second = `${Math.abs(b) === 1 ? "" : readable(Math.abs(b))}y`;
  const head = a === 0 ? "" : `${a < 0 ? "−" : ""}${first}`;
  const tail = b === 0 ? "" : `${head ? (b < 0 ? " − " : " + ") : (b < 0 ? "−" : "")}${second}`;
  return `${head}${tail} = ${readable(c)}`;
}

/** Two lines, one shared pair of axes, and the state they actually describe. */
function LinearSystemGraph({ system, progress, }) {
  const phase = progress >= 1 ? 4 : Math.min(3, Math.floor(Math.max(0, progress) * 4));
  const scale = (SIZE - PAD * 2) / (system.range * 2);
  const toX = (x) => SIZE / 2 + x * scale;
  const toY = (y) => SIZE / 2 - y * scale;
  const ticks = Array.from({ length: system.range * 2 + 1 }, (_, index) => index - system.range);
  const lineClasses = [styles.functionLine, styles.functionLineSecondary];
  return (
    <figure className={`${styles.panel} ${styles.coordinatePanel}`}>
      <figcaption className={styles.panelTitle}>Hệ hai phương trình bậc nhất trên cùng hệ trục Oxy</figcaption>
      <p className={styles.teachingStep}>{[
        "Bước 1 · Dựng trục x, y cùng tỉ lệ và đánh dấu gốc O",
        `Bước 2 · Vẽ đường thứ nhất ${generalEquation(system.lines[0])}`,
        `Bước 3 · Vẽ đường thứ hai ${generalEquation(system.lines[1])} trên cùng hệ trục`,
        `Bước 4 · ${SYSTEM_STATE_TEXT[system.state]}`,
        system.intersection
          ? `Bước 5 · Thay (${readable(system.intersection.x)}; ${readable(system.intersection.y)}) vào cả hai phương trình để kiểm tra`
          : `Bước 5 · ${SYSTEM_STATE_TEXT[system.state]}`,
      ][phase]}</p>
      <svg viewBox={`0 0 ${SIZE} ${SIZE}`} className={styles.coordinateGraph} role="img"
        aria-label={`Hai đường thẳng ${generalEquation(system.lines[0])} và ${generalEquation(system.lines[1])}`}>
        <defs>
          <clipPath id="system-clip"><rect x={PAD} y={PAD} width={SIZE - PAD * 2} height={SIZE - PAD * 2} /></clipPath>
        </defs>
        {ticks.map((value) => (
          <g key={value}>
            <line className={styles.graphGrid} x1={toX(value)} y1={PAD} x2={toX(value)} y2={SIZE - PAD} />
            <line className={styles.graphGrid} x1={PAD} y1={toY(value)} x2={SIZE - PAD} y2={toY(value)} />
            {value !== 0 && value % 2 === 0 ? <text className={styles.graphTickLabel} x={toX(value)} y={toY(0) + 13}>{value}</text> : null}
            {value !== 0 && value % 2 === 0 ? <text className={styles.graphTickLabel} x={toX(0) - 9} y={toY(value) + 3}>{value}</text> : null}
          </g>
        ))}
        <line className={styles.graphAxis} x1={PAD} y1={toY(0)} x2={SIZE - PAD} y2={toY(0)} />
        <line className={styles.graphAxis} x1={toX(0)} y1={SIZE - PAD} x2={toX(0)} y2={PAD} />
        <text className={styles.axisName} x={SIZE - PAD + 4} y={toY(0) + 4}>x</text>
        <text className={styles.axisName} x={toX(0) + 7} y={PAD - 7}>y</text>
        {system.lines.map((line, index) => (
          phase >= index + 1 ? (
            <line key={`line-${index}`} clipPath="url(#system-clip)" className={lineClasses[index]}
              strokeDasharray={index === 1 ? "8 5" : undefined}
              x1={toX(line.points[0].x)} y1={toY(line.points[0].y)}
              x2={toX(line.points[1].x)} y2={toY(line.points[1].y)} />
          ) : null
        ))}
        {phase >= 3 && system.intersection ? (
          <g>
            <circle className={styles.graphPointAccent} cx={toX(system.intersection.x)} cy={toY(system.intersection.y)} r="6" />
            <text className={styles.graphPointLabel} x={toX(system.intersection.x) + 8} y={toY(system.intersection.y) - 8}>
              M({readable(system.intersection.x)}; {readable(system.intersection.y)})
            </text>
          </g>
        ) : null}
      </svg>
      <div className={styles.coordinateDetails}>
        <div><small>Phương trình 1</small><strong>{generalEquation(system.lines[0])}</strong></div>
        <div><small>Phương trình 2</small><strong>{generalEquation(system.lines[1])}</strong></div>
        <div><small>Vị trí hai đường</small><strong>{SYSTEM_STATE_TEXT[system.state]}</strong></div>
        {system.intersection ? (
          <div><small>Nghiệm của hệ</small><strong>x = {readable(system.intersection.x)}; y = {readable(system.intersection.y)}</strong></div>
        ) : null}
      </div>
    </figure>
  );
}

function CubicGraph({ world, progress, visualization }) {
  const graph = deriveCubicGraph(world, visualization?.bindings);
  if (!graph) return <p className={styles.unavailable}>Cần đủ hệ số a, b, c, d và a khác 0 để giải phương trình bậc ba.</p>;
  const phase = progress >= 1 ? 4 : Math.min(4, Math.floor(Math.max(0, progress) * 5));
  const yPadding = Math.max(1, (graph.yMax - graph.yMin) * 0.06);
  const yMin = graph.yMin - yPadding;
  const yMax = graph.yMax + yPadding;
  const toX = (x) => PAD + ((x - graph.xMin) / (graph.xMax - graph.xMin)) * (SIZE - PAD * 2);
  const toY = (y) => PAD + ((yMax - y) / (yMax - yMin)) * (SIZE - PAD * 2);
  const path = graph.points.map((point, index) => `${index ? "L" : "M"}${toX(point.x).toFixed(2)},${toY(point.y).toFixed(2)}`).join(" ");
  const xTicks = integerTicks(graph.xMin, graph.xMax);
  const yTicks = Array.from({ length: 5 }, (_, index) => yMin + (index / 4) * (yMax - yMin));
  const canonical = `${polynomialText([graph.a, graph.b, graph.c, graph.d])} = 0`;
  const rootsText = graph.roots.map((root, index) => quadraticRootEquation(`x${graph.roots.length > 1 ? ["₁", "₂", "₃"][index] : ""}`, root)).join("; ");
  const firstRootIsApproximate = quadraticRootText(graph.roots[0]).startsWith("≈");
  const quotientText = graph.quotient && Math.abs(graph.quotientRemainder) <= 1e-6
    ? `${firstRootIsApproximate ? "Xấp xỉ: " : ""}${factorFromRoot(graph.roots[0])} · (${polynomialText(graph.quotient)}) ${firstRootIsApproximate ? "≈" : "="} 0`
    : "Tìm giao điểm của đồ thị với trục Ox";
  const verification = graph.roots.map((root, index) => {
    const rendered = quadraticRootText(root);
    const name = `x${graph.roots.length > 1 ? ["₁", "₂", "₃"][index] : ""}`;
    if (rendered.startsWith("≈")) return `P(${name}) ≈ 0 với ${name} ${rendered}`;
    return `P(${rendered}) ${Math.abs(graph.evaluate(root)) <= 1e-7 ? "= 0" : `≈ ${readable(graph.evaluate(root))}`}`;
  }).join("; ");
  return (
    <figure className={`${styles.panel} ${styles.coordinatePanel} ${styles.polynomialPanel}`}>
      <figcaption className={styles.panelTitle}>Phương trình bậc ba · nghiệm là giao điểm với trục Ox</figcaption>
      <div className={styles.formulaExplanation}>
        <strong>Cách đọc để dựng hình · không thay đổi đề gốc</strong>
        <span>Từ phương trình <b>{canonical}</b>, đặt <b>y = {polynomialText([graph.a, graph.b, graph.c, graph.d])}</b>.</span>
        <span>Điểm nào có y = 0 sẽ nằm trên trục Ox; hoành độ của điểm đó chính là nghiệm.</span>
      </div>
      <div className={styles.equationJourney} aria-label="Các bước giải phương trình bậc ba">
        <span><small>Dạng chuẩn</small><b>{canonical}</b></span>
        <i>→</i>
        <span><small>Tách một nhân tử</small><b>{quotientText}</b></span>
        <i>→</i>
        <span className={styles.equationJourneyAnswer}><small>Kết luận trên ℝ</small><b>{rootsText}</b></span>
      </div>
      <p className={styles.teachingStep}>{[
        `Bước 1 · Đưa toàn bộ về một vế: ${canonical}`,
        `Bước 2 · Dấu a = ${readable(graph.a)} cho biết nhánh phải của đồ thị đi ${graph.a > 0 ? "lên" : "xuống"}`,
        "Bước 3 · Đánh dấu mọi điểm mà đường cong cắt hoặc tiếp xúc trục Ox",
        `Bước 4 · Tách nhân tử: ${quotientText}`,
        `Bước 5 · Thay lại kiểm tra: ${verification}`,
      ][phase]}</p>
      <svg viewBox={`0 0 ${SIZE} ${SIZE}`} className={`${styles.coordinateGraph} ${styles.polynomialGraph}`} role="img" aria-label={`Đồ thị ${canonical}; nghiệm thực ${rootsText}`}>
        <defs><clipPath id="cubic-clip"><rect x={PAD} y={PAD} width={SIZE - PAD * 2} height={SIZE - PAD * 2} /></clipPath></defs>
        {xTicks.map((value) => <g key={`x-${value}`}><line className={styles.graphGrid} x1={toX(value)} y1={PAD} x2={toX(value)} y2={SIZE - PAD} />{value !== 0 && yMin <= 0 && yMax >= 0 ? <text className={styles.graphTickLabel} x={toX(value)} y={toY(0) + 13}>{value}</text> : null}</g>)}
        {yTicks.map((value, index) => <line key={`y-${index}`} className={styles.graphGrid} x1={PAD} y1={toY(value)} x2={SIZE - PAD} y2={toY(value)} />)}
        {graph.xMin <= 0 && graph.xMax >= 0 ? <line className={styles.graphAxis} x1={toX(0)} y1={PAD} x2={toX(0)} y2={SIZE - PAD} /> : null}
        {yMin <= 0 && yMax >= 0 ? <line className={styles.graphAxis} x1={PAD} y1={toY(0)} x2={SIZE - PAD} y2={toY(0)} /> : null}
        <path d={path} clipPath="url(#cubic-clip)" className={`${styles.functionLine} ${phase < 1 ? styles.graphCurvePreview : ""}`} fill="none" />
        {phase >= 1 ? graph.turningPoints.map((point) => <circle key={`turn-${point}`} className={styles.graphTurningPoint} cx={toX(point)} cy={toY(graph.evaluate(point))} r="4" />) : null}
        {phase >= 2 ? graph.roots.map((root, index) => (
          <g key={`root-${root}`}>
            <circle className={styles.graphPointAccent} cx={toX(root)} cy={toY(0)} r="6" />
            <text className={styles.graphPointLabel} textAnchor={index % 2 ? "start" : "end"} x={toX(root) + (index % 2 ? 7 : -7)} y={toY(0) - 9 - (index % 2) * 13}>
              {quadraticRootEquation(`x${graph.roots.length > 1 ? ["₁", "₂", "₃"][index] : ""}`, root, true)}
            </text>
          </g>
        )) : null}
      </svg>
      <div className={styles.coordinateDetails}>
        <div><small>Đa thức cần giải</small><strong>P(x) = {polynomialText([graph.a, graph.b, graph.c, graph.d])}</strong></div>
        <div><small>Số nghiệm thực phân biệt</small><strong>{graph.roots.length} nghiệm trên ℝ</strong></div>
        <div><small>Tách nhân tử</small><strong>{quotientText}</strong></div>
        <div><small>Kiểm tra</small><strong>{verification}</strong></div>
      </div>
      <div className={styles.visualConclusion}>
        <span>Đọc ngay trên hình: mỗi chấm sáng trên Ox là một nghiệm</span>
        <strong>{rootsText}</strong>
        <small>{graph.roots.length === 1 ? "Phương trình bậc ba này có một nghiệm thực; hai nghiệm còn lại không thuộc ℝ." : "Đường cong gặp Ox tại các vị trí trên, nên đó là toàn bộ nghiệm thực."}</small>
      </div>
    </figure>
  );
}

function QuadraticGraph({ world, progress, visualization, vieta = false }) {
  const graph = deriveQuadraticGraph(world, visualization?.bindings);
  if (!graph) return <p className={styles.unavailable}>Cần đủ hệ số a, b, c và a khác 0 để dựng parabol.</p>;
  const phase = progress >= 1 ? 3 : Math.min(3, Math.floor(Math.max(0, progress) * 4));
  const yPadding = Math.max(1, (graph.yMax - graph.yMin) * 0.08);
  const yMin = graph.yMin - yPadding;
  const yMax = graph.yMax + yPadding;
  const toX = (x) => PAD + ((x - graph.xMin) / (graph.xMax - graph.xMin)) * (SIZE - PAD * 2);
  const toY = (y) => PAD + ((yMax - y) / (yMax - yMin)) * (SIZE - PAD * 2);
  const path = graph.points.map((point, index) => `${index ? "L" : "M"}${toX(point.x).toFixed(2)},${toY(point.y).toFixed(2)}`).join(" ");
  const xTicks = integerTicks(graph.xMin, graph.xMax);
  const yTicks = Array.from({ length: 5 }, (_, index) => yMin + (index / 4) * (yMax - yMin));
  const sign = (value) => value >= 0 ? `+ ${value}` : `− ${Math.abs(value)}`;
  const round = (value) => Math.round(value * 100) / 100;
  const canonical = `${polynomialText([graph.a, graph.b, graph.c])} = 0`;
  const rootsText = graph.discriminant < 0
    ? "Δ < 0 nên phương trình không có nghiệm thực"
    : graph.roots.length === 1
      ? quadraticRootEquation("x", graph.roots[0])
      : `${quadraticRootEquation("x₁", graph.roots[0])}; ${quadraticRootEquation("x₂", graph.roots[1])}`;
  return (
    <figure className={`${styles.panel} ${styles.coordinatePanel} ${styles.polynomialPanel}`}>
      <figcaption className={styles.panelTitle}>Parabol · bảng giá trị, đỉnh và nghiệm</figcaption>
      <div className={styles.equationJourney} aria-label="Các bước giải phương trình bậc hai">
        <span><small>Dạng chuẩn</small><b>{canonical}</b></span>
        <i>→</i>
        <span><small>Biệt thức</small><b>Δ = {round(graph.discriminant)}</b></span>
        <i>→</i>
        <span className={styles.equationJourneyAnswer}><small>Nghiệm = giao với Ox</small><b>{rootsText}</b></span>
      </div>
      <p className={styles.teachingStep}>{[
        "Bước 1 · Dựng hệ trục và xác định chiều mở từ dấu của a",
        `Bước 2 · Đặt đỉnh I(${round(graph.vertexX)}; ${round(graph.vertexY)}) và trục đối xứng`,
        `Bước 3 · Đối chiếu Δ = ${round(graph.discriminant)} với giao điểm trục Ox`,
        "Bước 4 · Dựng parabol qua các điểm đối xứng",
      ][phase]}</p>
      <svg viewBox={`0 0 ${SIZE} ${SIZE}`} className={styles.coordinateGraph} role="img" aria-label={`Parabol y bằng ${graph.a} x bình phương cộng ${graph.b} x cộng ${graph.c}`}>
        <defs><clipPath id="quadratic-clip"><rect x={PAD} y={PAD} width={SIZE - PAD * 2} height={SIZE - PAD * 2} /></clipPath></defs>
        {xTicks.map((value) => <g key={`x-${value}`}><line className={styles.graphGrid} x1={toX(value)} y1={PAD} x2={toX(value)} y2={SIZE - PAD} />{value !== 0 && yMin <= 0 && yMax >= 0 ? <text className={styles.graphTickLabel} x={toX(value)} y={toY(0) + 13}>{value}</text> : null}</g>)}
        {yTicks.map((value, index) => <line key={`y-${index}`} className={styles.graphGrid} x1={PAD} y1={toY(value)} x2={SIZE - PAD} y2={toY(value)} />)}
        {graph.xMin <= 0 && graph.xMax >= 0 ? <line className={styles.graphAxis} x1={toX(0)} y1={PAD} x2={toX(0)} y2={SIZE - PAD} /> : null}
        {yMin <= 0 && yMax >= 0 ? <line className={styles.graphAxis} x1={PAD} y1={toY(0)} x2={SIZE - PAD} y2={toY(0)} /> : null}
        <line className={styles.graphGrid} x1={toX(graph.vertexX)} y1={PAD} x2={toX(graph.vertexX)} y2={SIZE - PAD} strokeDasharray="5 4" />
        <path d={path} clipPath="url(#quadratic-clip)" className={`${styles.functionLine} ${phase < 3 ? styles.graphCurvePreview : ""}`} fill="none" />
        {phase >= 1 ? <circle className={styles.graphPointAccent} cx={toX(graph.vertexX)} cy={toY(graph.vertexY)} r="5" /> : null}
        {phase >= 1 ? (
          <text className={styles.graphPointLabel} textAnchor="middle"
            x={toX(graph.vertexX)} y={toY(graph.vertexY) + 19}>
            I({round(graph.vertexX)}; {round(graph.vertexY)})
          </text>
        ) : null}
        {phase >= 2 ? graph.roots.map((root, index) => {
          const onLeft = root <= graph.vertexX;
          const rootName = graph.roots.length === 1 ? "x" : `x${index === 0 ? "₁" : "₂"}`;
          return (
            <g key={root}>
              <circle className={styles.graphPoint} cx={toX(root)} cy={toY(0)} r="5" />
              <text className={styles.graphPointLabel}
                textAnchor={onLeft ? "end" : "start"}
                x={toX(root) + (onLeft ? -7 : 7)}
                y={toY(0) - (index === 0 ? 8 : 23)}>
                {quadraticRootEquation(rootName, root, true)}
              </text>
            </g>
          );
        }) : null}
      </svg>
      <div className={styles.coordinateDetails}>
        <div><small>Công thức</small><strong>y = {graph.a}x² {sign(graph.b)}x {sign(graph.c)}</strong></div>
        <div><small>Đỉnh</small><strong>I({round(graph.vertexX)}; {round(graph.vertexY)})</strong></div>
        <div><small>Biệt thức</small><strong>Δ = ({graph.b})² − 4·{graph.a}·({graph.c}) = {round(graph.discriminant)}</strong></div>
        <div><small>Nghiệm</small><strong>{rootsText}</strong></div>
        {vieta && graph.roots.length === 2 ? <>
          <div><small>Tổng nghiệm</small><strong>x₁ + x₂ = {round(graph.roots[0] + graph.roots[1])} = −b/a</strong></div>
          <div><small>Tích nghiệm</small><strong>x₁·x₂ = {round(graph.roots[0] * graph.roots[1])} = c/a</strong></div>
        </> : null}
      </div>
      <div className={styles.visualConclusion}>
        <span>Đọc ngay trên hình: nghiệm chính là hoành độ giao điểm với Ox</span>
        <strong>{rootsText}</strong>
        <small>Thay từng giá trị này vào {polynomialText([graph.a, graph.b, graph.c])}; kết quả phải bằng 0.</small>
      </div>
    </figure>
  );
}
