import { deriveGeometry3d, deriveLinearSystem3d, derivePlane3d } from "../derive/deriveScene.js";
import { deriveSolidRevolution } from "../derive/deriveCurriculum.js";
import { deriveQuadraticSurface } from "../derive/deriveCoverage.js";
import styles from "./renderers.module.css";

function format(value) {
  return new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 2 }).format(value);
}

export default function Geometry3DRenderer({ world, progress, visualization, scene }) {
  if (/linear_system_three_variables/i.test(scene?.metadata?.problem_type || "")) {
    const system = deriveLinearSystem3d(
      world,
      visualization?.bindings,
      scene?.metadata?.relations,
    );
    return system
      ? <LinearSystem3DModel system={system} progress={progress} />
      : <p className={styles.unavailable}>Cần toàn bộ hệ số của từng phương trình để dựng hệ mặt phẳng.</p>;
  }
  if (/quadratic_surface/i.test(scene?.metadata?.problem_type || "")) {
    const surface = deriveQuadraticSurface(world, visualization?.bindings, scene?.metadata?.relations);
    return surface
      ? <QuadraticSurfaceModel surface={surface} progress={progress} />
      : <p className={styles.unavailable}>Cần một hạng tử bình phương và đủ hệ số tuyến tính để dựng mặt cong.</p>;
  }
  if (/linear_equation_three_variables/i.test(scene?.metadata?.problem_type || "")) {
    const plane = derivePlane3d(world, visualization?.bindings);
    return plane
      ? <PlaneEquationModel plane={plane} progress={progress} />
      : <p className={styles.unavailable}>Cần đủ hệ số của x, y, z và vế phải để dựng mặt phẳng.</p>;
  }
  const revolution = deriveSolidRevolution(world, visualization?.bindings, scene?.metadata?.problem_type);
  if (revolution) return <SolidRevolutionModel solid={revolution} progress={progress} />;
  const solid = deriveGeometry3d(world, visualization?.bindings);
  if (!solid) {
    return <p className={styles.unavailable}>Cần chiều dài, rộng và cao để dựng hình không gian.</p>;
  }
  const phase = progress >= 1 ? 3 : Math.min(2, Math.floor(Math.max(0, progress) * 3));
  const maxDimension = Math.max(solid.length, solid.width, solid.height);
  const scale = 86 / maxDimension;
  const yaw = -0.75 + Math.max(0, Math.min(1, progress)) * 0.55;
  const project = ([x, y, z]) => ({
    x: 130 + (x * Math.cos(yaw) - y * Math.sin(yaw)) * scale,
    y: 145 + (x * Math.sin(yaw) + y * Math.cos(yaw)) * scale * 0.42 - z * scale,
  });
  const vertices = [
    [0, 0, 0], [solid.length, 0, 0], [solid.length, solid.width, 0], [0, solid.width, 0],
    [0, 0, solid.height], [solid.length, 0, solid.height],
    [solid.length, solid.width, solid.height], [0, solid.width, solid.height],
  ].map(project);
  const points = (indices) => indices.map((index) => `${vertices[index].x},${vertices[index].y}`).join(" ");
  const origin = vertices[0];
  return (
    <figure className={`${styles.panel} ${styles.geometry3dPanel}`}>
      <figcaption className={styles.panelTitle}>Mô hình không gian trên trục x–y–z</figcaption>
      <p className={styles.teachingStep}>{[
        "Bước 1 · Dựng đáy trên mặt phẳng x–y",
        `Bước 2 · Đáy có diện tích ${format(solid.length)} × ${format(solid.width)} = ${format(solid.baseArea)} ${solid.unit}²`,
        `Bước 3 · Nâng đáy theo trục z một đoạn ${format(solid.height)} ${solid.unit}`,
        "Bước 4 · Ghép các lớp bằng nhau để đọc thể tích",
      ][phase]}</p>
      <svg viewBox="0 0 280 230" className={styles.geometry3d} role="img"
        aria-label={`Hình hộp dài ${solid.length}, rộng ${solid.width}, cao ${solid.height} ${solid.unit}`}>
        <defs>
          <marker id="axis-3d-arrow" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="6" markerHeight="6" orient="auto">
            <path d="M0,0 L8,4 L0,8 Z" className={styles.axisArrow} />
          </marker>
        </defs>
        <line className={styles.axis3dX} x1={origin.x} y1={origin.y} x2="255" y2={origin.y + 40} markerEnd="url(#axis-3d-arrow)" />
        <line className={styles.axis3dY} x1={origin.x} y1={origin.y} x2="35" y2={origin.y + 30} markerEnd="url(#axis-3d-arrow)" />
        <line className={styles.axis3dZ} x1={origin.x} y1={origin.y} x2={origin.x} y2="20" markerEnd="url(#axis-3d-arrow)" />
        <text className={styles.axis3dLabel} x="258" y={origin.y + 44}>x · dài</text>
        <text className={styles.axis3dLabel} x="15" y={origin.y + 35}>y · rộng</text>
        <text className={styles.axis3dLabel} x={origin.x + 6} y="18">z · cao</text>
        <polygon className={styles.solidBase} points={points([0, 1, 2, 3])} />
        {phase >= 2 ? (
          <>
            <polygon className={styles.solidFront} points={points([0, 1, 5, 4])} />
            <polygon className={styles.solidSide} points={points([1, 2, 6, 5])} />
            <polygon className={styles.solidTop} points={points([4, 5, 6, 7])} />
            {[0, 1, 2, 3].map((index) => (
              <line key={index} className={styles.solidEdge} x1={vertices[index].x} y1={vertices[index].y} x2={vertices[index + 4].x} y2={vertices[index + 4].y} />
            ))}
          </>
        ) : null}
        <polyline className={styles.solidEdge} points={`${points([0, 1, 2, 3])} ${vertices[0].x},${vertices[0].y}`} />
        {phase >= 2 ? <polyline className={styles.solidEdge} points={`${points([4, 5, 6, 7])} ${vertices[4].x},${vertices[4].y}`} /> : null}
      </svg>
      <div className={styles.dimensionFormula}>
        <span><b>x</b> = {format(solid.length)} {solid.unit}</span>
        <span><b>y</b> = {format(solid.width)} {solid.unit}</span>
        <span><b>z</b> = {format(solid.height)} {solid.unit}</span>
      </div>
      {phase >= 3 ? (
        <div className={styles.visualConclusion}>
          <span>V = dài × rộng × cao</span>
          <strong>{format(solid.length)} × {format(solid.width)} × {format(solid.height)} = {format(solid.volume)} {solid.unit}³</strong>
        </div>
      ) : <p className={styles.fractionHint}>Kéo thanh tiến độ để xoay nhẹ và dựng chiều cao.</p>}
    </figure>
  );
}

/** `3·1`, `− 1·3`: the coefficient times a substituted value, sign kept apart. */
function substitutionTerm(coefficient, value, first = false) {
  const body = `${format(Math.abs(coefficient))}·${format(Math.abs(value))}`;
  const negative = coefficient * value < 0;
  if (first) return `${negative ? "−" : ""}${body}`;
  return `${negative ? "−" : "+"} ${body}`;
}

function signedTerm(value, variable, first = false) {
  const magnitude = Math.abs(value);
  const body = `${magnitude === 1 ? "" : format(magnitude)}${variable}`;
  if (first) return `${value < 0 ? "−" : ""}${body}`;
  return `${value < 0 ? "−" : "+"} ${body}`;
}

function LinearSystem3DModel({ system, progress }) {
  const phase = progress >= 1 ? 5 : Math.min(5, Math.floor(Math.max(0, progress) * 6));
  const yaw = -0.72 + Math.max(0, Math.min(1, progress)) * 0.4;
  const allPoints = system.planes.flatMap((plane) => [...plane.vertices, plane.center]);
  if (system.solution) allPoints.push(system.solution);
  const extent = Math.max(3, ...allPoints.flatMap((point) => point.map(Math.abs)));
  const scale = 72 / extent;
  const project = ([x, y, z]) => ({
    x: 180 + (x * Math.cos(yaw) - y * Math.sin(yaw)) * scale,
    y: 150 + (x * Math.sin(yaw) + y * Math.cos(yaw)) * scale * 0.42 - z * scale,
  });
  const origin = project([0, 0, 0]);
  const axisSize = extent * 1.2;
  const axes = [project([axisSize, 0, 0]), project([0, axisSize, 0]), project([0, 0, axisSize])];
  const labels = ["Ox", "Oy", "Oz"];
  const eliminationIndex = system.eliminationSteps.length
    ? Math.min(system.eliminationSteps.length - 1, Math.floor(Math.max(0, progress) * system.eliminationSteps.length))
    : -1;
  const elimination = eliminationIndex >= 0 ? system.eliminationSteps[eliminationIndex] : null;
  const exact = system.solutionExact || system.solution?.map(format) || [];
  const stateText = system.state === "unique"
    ? "Hệ có nghiệm duy nhất"
    : system.state === "infinite"
      ? "Hệ có vô số nghiệm"
      : "Hệ vô nghiệm";
  const teachingSteps = [
    "Bước 1 · Giữ nguyên từng phương trình và điền 0 cho hạng tử không xuất hiện",
    "Bước 2 · Xếp hệ số x, y, z và vế phải thành ma trận mở rộng",
    "Bước 3 · Biến đổi hàng để khử lần lượt các ẩn",
    "Bước 4 · Dựng mỗi phương trình thành một mặt phẳng trên cùng hệ trục Oxyz",
    "Bước 5 · Điểm chung của các mặt phẳng là nghiệm của cả hệ",
    "Bước 6 · Thay nghiệm vào từng phương trình ban đầu để kiểm tra",
  ];

  return (
    <figure className={`${styles.panel} ${styles.geometry3dPanel}`}>
      <figcaption className={styles.panelTitle}>Hệ phương trình ba ẩn · khử Gauss và giao của các mặt phẳng</figcaption>
      <p className={styles.teachingStep}>{teachingSteps[phase]}</p>

      <ol className={styles.systemEquationList}>
        {system.canonicalForms.map((equation, index) => (
          <li key={equation}><span>P{index + 1}</span><b>{equation}</b></li>
        ))}
      </ol>

      {phase >= 1 && elimination ? (
        <section className={styles.eliminationPanel} aria-label="Các bước khử Gauss">
          <div className={styles.eliminationHeader}>
            <b>Phép biến đổi {eliminationIndex + 1}/{system.eliminationSteps.length}</b>
            <span>{elimination.operation}</span>
          </div>
          <table className={styles.augmentedMatrix}>
            <thead><tr>{[...system.symbols, "Vế phải"].map((symbol) => <th key={symbol}>{symbol}</th>)}</tr></thead>
            <tbody>
              {elimination.matrix.map((row, rowIndex) => (
                <tr key={`row-${rowIndex}`}>
                  {row.map((value, columnIndex) => (
                    <td key={`${rowIndex}-${columnIndex}`} className={columnIndex === 3 ? styles.matrixRightSide : undefined}>{value}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ) : null}

      <svg viewBox="0 0 360 290" className={styles.geometry3d} role="img" aria-label={`${stateText} trên hệ trục Oxyz`}>
        <defs>
          <marker id="system3-axis-arrow" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="6" markerHeight="6" orient="auto">
            <path d="M0,0 L8,4 L0,8 Z" className={styles.axisArrow} />
          </marker>
        </defs>
        {axes.map((point, index) => (
          <line key={labels[index]} className={[styles.axis3dX, styles.axis3dY, styles.axis3dZ][index]}
            x1={origin.x} y1={origin.y} x2={point.x} y2={point.y} markerEnd="url(#system3-axis-arrow)" />
        ))}
        {phase >= 3 ? system.planes.map((plane, index) => {
          const vertices = plane.vertices.map(project);
          const polygon = vertices.map((point) => `${point.x},${point.y}`).join(" ");
          const center = project(plane.center);
          return (
            <g key={`plane-${index}`}>
              <polygon className={`${styles.systemPlane} ${styles[`systemPlane${index + 1}`]}`} points={polygon} />
              <polyline className={styles.systemPlaneEdge} points={`${polygon} ${vertices[0].x},${vertices[0].y}`} />
              <text className={styles.systemPlaneLabel} x={center.x + 5} y={center.y - 5}>P{index + 1}</text>
            </g>
          );
        }) : null}
        {phase >= 4 && system.solution ? (() => {
          const point = project(system.solution);
          return <g>
            <circle className={styles.systemIntersection} cx={point.x} cy={point.y} r="6" />
            <text className={styles.systemIntersectionLabel} x={point.x + 8} y={point.y - 8}>M({exact.join("; ")})</text>
          </g>;
        })() : null}
        {axes.map((point, index) => <text key={`label-${labels[index]}`} className={styles.axis3dLabel} x={point.x + 4} y={point.y - 4}>{labels[index]}</text>)}
        <circle className={styles.planeOrigin} cx={origin.x} cy={origin.y} r="3.5" />
        <text className={styles.geometryLabel} x={origin.x + 5} y={origin.y + 15}>O</text>
      </svg>

      <div className={styles.rankSummary}>
        <span>hạng(A) = <b>{format(system.coefficientRank)}</b></span>
        <span>hạng(A|b) = <b>{format(system.augmentedRank)}</b></span>
        <strong>{stateText}</strong>
      </div>

      {system.state === "unique" ? (
        <div className={styles.visualConclusion}>
          <span>Nghiệm chính xác</span>
          <strong>{`S = {(${exact.join("; ")})}`}</strong>
          <small>{`x ≈ ${format(system.solution[0])}; y ≈ ${format(system.solution[1])}; z ≈ ${format(system.solution[2])}`}</small>
        </div>
      ) : (
        <div className={styles.visualConclusion}>
          <span>Kết luận từ hạng ma trận</span>
          <strong>{stateText}</strong>
        </div>
      )}

      {phase >= 5 && system.checks.length ? (
        <ul className={styles.systemChecks}>
          {system.checks.map((check, index) => (
            <li key={`system-check-${index}`}>
              <span>Thay vào P{index + 1}</span>
              <b>{format(check.left)} = {format(check.right)} ✓</b>
            </li>
          ))}
        </ul>
      ) : null}
    </figure>
  );
}

function QuadraticSurfaceModel({ surface, progress }) {
  const phase = progress >= 1 ? 4 : Math.min(4, Math.floor(Math.max(0, progress) * 5));
  const yaw = -0.72 + Math.max(0, Math.min(1, progress)) * 0.38;
  const zExtent = Math.max(2, ...surface.gridLines.flat().map((point) => Math.abs(point[2])));
  const project = ([x, y, z]) => ({
    x: 180 + (x * Math.cos(yaw) - y * Math.sin(yaw)) * 38,
    y: 164 + (x * Math.sin(yaw) + y * Math.cos(yaw)) * 16 - z * (92 / zExtent),
  });
  const origin = project([0, 0, 0]);
  const axes = [project([3, 0, 0]), project([0, 3, 0]), project([0, 0, zExtent * 1.15])];
  const labels = ["Ox", "Oy", "Oz"];
  const coefficientText = (value, symbol, squared = false, first = false) => {
    const magnitude = Math.abs(value);
    const body = `${magnitude === 1 ? "" : format(magnitude)}${symbol}${squared ? "²" : ""}`;
    if (first) return `${value < 0 ? "−" : ""}${body}`;
    return `${value < 0 ? "−" : "+"} ${body}`;
  };
  const equationTerms = [coefficientText(surface.squaredCoefficient, surface.squaredSymbol, true, true)];
  for (const symbol of ["x", "y", "z"]) {
    const value = Number(surface.linearCoefficients[symbol] || 0);
    if (value) equationTerms.push(coefficientText(value, symbol));
  }
  const equation = `${equationTerms.join(" ")} = ${format(surface.rightSide)}`;
  const outputCoefficient = Number(surface.linearCoefficients[surface.outputSymbol]);
  const outputFormula = `${surface.outputSymbol} = (${format(surface.rightSide)} − ${format(surface.squaredCoefficient)}${surface.squaredSymbol}²`
    + surface.inputSymbols.filter((symbol) => symbol !== surface.squaredSymbol).map((symbol) => {
      const value = Number(surface.linearCoefficients[symbol] || 0);
      return value ? ` − (${format(value)})${symbol}` : "";
    }).join("") + `) ÷ ${format(outputCoefficient)}`;
  return (
    <figure className={`${styles.panel} ${styles.geometry3dPanel}`}>
      <figcaption className={styles.panelTitle}>Mặt cong nghiệm trên hệ trục Oxyz</figcaption>
      <p className={styles.teachingStep}>{[
        `Bước 1 · ${surface.squaredSymbol}² xuất hiện nên đây là mặt cong, không phải mặt phẳng`,
        `Bước 2 · Tách ${surface.outputSymbol}: ${outputFormula}`,
        `Bước 3 · Giữ ${surface.ruledSymbol} cố định và dựng nhiều lát parabol theo ${surface.squaredSymbol}`,
        `Bước 4 · Nối các lát theo hướng ${surface.ruledSymbol} để tạo toàn bộ mặt nghiệm`,
        "Bước 5 · Thay các điểm đánh dấu vào phương trình để kiểm tra",
      ][phase]}</p>
      <svg viewBox="0 0 360 310" className={styles.geometry3d} role="img" aria-label={`Mặt cong ${equation} trên Oxyz`}>
        <defs>
          <marker id="surface-axis-arrow" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="6" markerHeight="6" orient="auto">
            <path d="M0,0 L8,4 L0,8 Z" className={styles.axisArrow} />
          </marker>
        </defs>
        {axes.map((point, index) => (
          <g key={labels[index]}>
            <line className={[styles.axis3dX, styles.axis3dY, styles.axis3dZ][index]}
              x1={origin.x} y1={origin.y} x2={point.x} y2={point.y} markerEnd="url(#surface-axis-arrow)" />
            <text className={styles.axis3dLabel} x={point.x + 5} y={point.y - 5}>{labels[index]}</text>
          </g>
        ))}
        {phase >= 2 ? surface.gridLines.map((line, index) => {
          const points = line.map(project).map((point) => `${point.x},${point.y}`).join(" ");
          return <polyline key={index} points={points}
            className={index < 5 ? styles.quadraticCurve : styles.quadraticRuling} />;
        }) : null}
        {phase >= 4 ? surface.samplePoints.map((point, index) => {
          const shown = project(point);
          return (
            <g key={index}>
              <circle className={styles.planeSamplePoint} cx={shown.x} cy={shown.y} r="4.5" />
              <text className={styles.geometryLabel} x={shown.x + 6} y={shown.y - 6}>
                ({point.map(format).join("; ")})
              </text>
            </g>
          );
        }) : null}
        <circle className={styles.planeOrigin} cx={origin.x} cy={origin.y} r="3.5" />
        <text className={styles.geometryLabel} x={origin.x + 5} y={origin.y + 15}>O</text>
      </svg>
      <div className={styles.dimensionFormula}>
        <span>Hướng cong: <b>{surface.squaredSymbol}²</b></span>
        <span>Hướng các đường sinh: <b>{surface.ruledSymbol}</b></span>
        <span>Trục đầu ra: <b>{surface.outputSymbol}</b></span>
      </div>
      <div className={styles.visualConclusion}>
        <span>Tập nghiệm là một mặt parabol có đường sinh thẳng</span>
        <strong>{equation}</strong>
        <small>Mỗi điểm trên lưới là một bộ (x; y; z) thỏa phương trình; hình dùng tỉ lệ trục thích nghi để mặt cong dễ nhìn.</small>
      </div>
    </figure>
  );
}

function PlaneEquationModel({ plane, progress }) {
  const phase = progress >= 1 ? 4 : Math.min(3, Math.floor(Math.max(0, progress) * 4));
  const yaw = -0.7 + Math.max(0, Math.min(1, progress)) * 0.45;
  const extent = Math.max(
    2,
    ...plane.vertices.flatMap((point) => point.map(Math.abs)),
    ...plane.samplePoints.flatMap((point) => point.map(Math.abs)),
  );
  const scale = 78 / extent;
  const project = ([x, y, z]) => ({
    x: 165 + (x * Math.cos(yaw) - y * Math.sin(yaw)) * scale,
    y: 150 + (x * Math.sin(yaw) + y * Math.cos(yaw)) * scale * 0.42 - z * scale,
  });
  const vertices = plane.vertices.map(project);
  const polygon = vertices.map((point) => `${point.x},${point.y}`).join(" ");
  const origin = project([0, 0, 0]);
  const axisSize = extent * 1.25;
  const xAxis = project([axisSize, 0, 0]);
  const yAxis = project([0, axisSize, 0]);
  const zAxis = project([0, 0, axisSize]);
  const normalTip = project(plane.normalTip);
  const equation = `${signedTerm(plane.a, "x", true)} ${signedTerm(plane.b, "y")} ${signedTerm(plane.c, "z")} = ${format(plane.rightSide)}`;
  const labels = ["Ox", "Oy", "Oz"];
  const locateStep = plane.throughOrigin
    ? "Bước 3 · Vế phải bằng 0 nên O(0; 0; 0) đã là nghiệm: mặt phẳng đi qua gốc"
    : "Bước 3 · Cho lần lượt hai biến bằng 0 để đọc giao điểm với từng trục";
  return (
    <figure className={`${styles.panel} ${styles.geometry3dPanel}`}>
      <figcaption className={styles.panelTitle}>Mặt phẳng nghiệm trên hệ trục Oxyz</figcaption>
      <p className={styles.teachingStep}>{[
        `Bước 1 · Chuyển mọi hạng tử chứa biến về một vế: ${equation}`,
        "Bước 2 · Dựng ba trục x, y, z vuông góc tại O với cùng tỉ lệ",
        locateStep,
        `Bước 4 · Dựng mặt phẳng vuông góc với vectơ pháp tuyến n(${format(plane.a)}; ${format(plane.b)}; ${format(plane.c)})`,
        "Bước 5 · Thay từng điểm mẫu vào phương trình: có vô số nghiệm, không có một bộ x, y, z duy nhất",
      ][phase]}</p>
      <svg viewBox="0 0 330 280" className={styles.geometry3d} role="img" aria-label={`Mặt phẳng ${equation} trên hệ trục Oxyz`}>
        <defs>
          <marker id="plane-axis-arrow" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="6" markerHeight="6" orient="auto">
            <path d="M0,0 L8,4 L0,8 Z" className={styles.axisArrow} />
          </marker>
          <marker id="plane-normal-arrow" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto">
            <path d="M0,0 L8,4 L0,8 Z" className={styles.normalArrowHead} />
          </marker>
        </defs>
        <line className={styles.axis3dX} x1={origin.x} y1={origin.y} x2={xAxis.x} y2={xAxis.y} markerEnd="url(#plane-axis-arrow)" />
        <line className={styles.axis3dY} x1={origin.x} y1={origin.y} x2={yAxis.x} y2={yAxis.y} markerEnd="url(#plane-axis-arrow)" />
        <line className={styles.axis3dZ} x1={origin.x} y1={origin.y} x2={zAxis.x} y2={zAxis.y} markerEnd="url(#plane-axis-arrow)" />
        {phase >= 3 ? <polygon className={styles.solutionPlane} points={polygon} /> : null}
        {phase >= 3 ? <polyline className={styles.solidEdge} points={`${polygon} ${vertices[0].x},${vertices[0].y}`} /> : null}
        {phase >= 3 ? (
          <line className={styles.normalVector} x1={origin.x} y1={origin.y} x2={normalTip.x} y2={normalTip.y}
            markerEnd="url(#plane-normal-arrow)" />
        ) : null}
        {phase >= 3 ? <text className={styles.normalLabel} x={normalTip.x + 5} y={normalTip.y - 5}>n</text> : null}
        {phase >= 4 ? plane.samplePoints.map((point, index) => {
          const projected = project(point);
          return (
            <g key={`sample-${index}`}>
              <circle className={styles.planeSamplePoint} cx={projected.x} cy={projected.y} r="4.5" />
              <text className={styles.geometryLabel} x={projected.x + 6} y={projected.y - 6}>
                ({format(point[0])}; {format(point[1])}; {format(point[2])})
              </text>
            </g>
          );
        }) : null}
        {[xAxis, yAxis, zAxis].map((point, index) => <text key={labels[index]} className={styles.axis3dLabel} x={point.x + 4} y={point.y - 4}>{labels[index]}</text>)}
        <circle className={styles.planeOrigin} cx={origin.x} cy={origin.y} r="3.5" />
        <text className={styles.geometryLabel} x={origin.x + 5} y={origin.y + 15}>O</text>
      </svg>
      <div className={styles.dimensionFormula}>
        {plane.throughOrigin
          ? <span>Cả ba trục cắt mặt phẳng tại <b>O(0; 0; 0)</b></span>
          : plane.intercepts.map((value, index) => (
            <span key={labels[index]}><b>{labels[index]}</b>: {Number.isFinite(value) ? format(value) : "song song"}</span>
          ))}
        <span>Pháp tuyến <b>n({format(plane.a)}; {format(plane.b)}; {format(plane.c)})</b></span>
      </div>
      {plane.samplePoints.length ? (
        <ul className={styles.planeSampleList}>
          {plane.samplePoints.map((point, index) => (
            <li key={`check-${index}`}>
              <span>({format(point[0])}; {format(point[1])}; {format(point[2])})</span>
              <span>{substitutionTerm(plane.a, point[0], true)} {substitutionTerm(plane.b, point[1])} {substitutionTerm(plane.c, point[2])} = {format(plane.rightSide)}</span>
            </li>
          ))}
        </ul>
      ) : null}
      <div className={styles.visualConclusion}>
        <span>Phương trình mặt phẳng</span>
        <strong>{equation}</strong>
        <small>Vô số bộ (x; y; z) thỏa mãn, nên không kết luận một giá trị duy nhất.</small>
      </div>
    </figure>
  );
}

function SolidRevolutionModel({ solid, progress }) {
  const phase = progress >= 1 ? 3 : Math.min(2, Math.floor(Math.max(0, progress) * 3));
  const round = (value) => String(Math.round(value * 100) / 100).replace(".", ",");
  const names = { cylinder: "Hình trụ", cone: "Hình nón", sphere: "Hình cầu" };
  const formula = solid.kind === "sphere" ? "4/3 × π × r³" : solid.kind === "cone" ? "1/3 × π × r² × h" : "π × r² × h";
  return (
    <figure className={`${styles.panel} ${styles.solidPanel}`}>
      <figcaption className={styles.panelTitle}>{names[solid.kind]} · mặt cắt và các lớp thể tích</figcaption>
      <p className={styles.teachingStep}>{[
        "Bước 1 · Dựng mặt cắt qua trục và bán kính r",
        "Bước 2 · Quay mặt cắt để tạo khối tròn xoay",
        solid.kind === "cone" ? "Bước 3 · Ba hình nón cùng đáy, cùng cao lấp đầy một hình trụ" : "Bước 3 · Ghép khối từ các lớp tròn song song",
        "Bước 4 · Thay kích thước vào công thức thể tích",
      ][phase]}</p>
      <svg viewBox="0 0 330 260" className={styles.solidDiagram} role="img" aria-label={`${names[solid.kind]} bán kính ${solid.radius}`}>
        {solid.kind === "cylinder" ? <>
          <ellipse cx="165" cy="55" rx="82" ry="25" className={styles.solidTop} />
          <path d="M83 55 V205 M247 55 V205" className={styles.solidEdge} />
          <ellipse cx="165" cy="205" rx="82" ry="25" className={styles.solidBase} />
          {phase >= 2 ? [90, 125, 160].map((y) => <ellipse key={y} cx="165" cy={y} rx="82" ry="25" className={styles.solidLayer} />) : null}
        </> : null}
        {solid.kind === "cone" ? <>
          <ellipse cx="165" cy="205" rx="92" ry="27" className={styles.solidBase} />
          <path d="M165 32 L73 205 M165 32 L257 205" className={styles.solidEdge} />
          {phase >= 2 ? [90, 135, 170].map((y) => { const ratio = (y - 32) / 173; return <ellipse key={y} cx="165" cy={y} rx={92 * ratio} ry={27 * ratio} className={styles.solidLayer} />; }) : null}
        </> : null}
        {solid.kind === "sphere" ? <>
          <circle cx="165" cy="130" r="94" className={styles.solidBase} />
          <ellipse cx="165" cy="130" rx="94" ry="30" className={styles.solidLayer} />
          {phase >= 2 ? [76, 184].map((y) => <ellipse key={y} cx="165" cy={y} rx="76" ry="20" className={styles.solidLayer} />) : null}
        </> : null}
        {phase >= 1 ? <><line x1="165" y1="130" x2="255" y2="130" className={styles.geometryHyp} /><text x="202" y="121" className={styles.geometryMeasure}>r={solid.radius}</text></> : null}
      </svg>
      <div className={styles.solidReadout}><span>r = <b>{round(solid.radius)} {solid.unit}</b></span>{solid.kind !== "sphere" ? <span>h = <b>{round(solid.height)} {solid.unit}</b></span> : null}<span>V = <b>{phase >= 3 ? `${round(solid.volume)} ${solid.unit}³` : formula}</b></span></div>
      <p className={styles.visualEquation}>{phase >= 3 ? `V = ${formula} = ${round(solid.volume)} ${solid.unit}³` : formula}</p>
    </figure>
  );
}
