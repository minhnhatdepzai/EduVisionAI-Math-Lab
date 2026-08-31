import { deriveGeometry2d } from "../derive/deriveScene.js";
import {
  deriveCentroidProof,
  deriveRightTriangle,
  deriveTrigonometricGeometry,
  deriveTriangleSimilarity,
} from "../derive/deriveCoverage.js";
import styles from "./renderers.module.css";

const measure = (value) => new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 2 }).format(value);

/** Both triangles, their marked corresponding sides and the single ratio. */
function SimilarityProofModel({ model, progress }) {
  const phase = progress >= 1 ? 3 : Math.min(2, Math.floor(Math.max(0, progress) * 3));
  const unit = model.unit;
  const scale = 150 / Math.max(model.large.a, model.large.b);
  const triangle = (side, other, originX) => {
    const width = side * scale;
    const height = other * scale;
    return `${originX},${180} ${originX + width},${180} ${originX},${180 - height}`;
  };
  return (
    <figure className={`${styles.panel} ${styles.geometryPanel}`}>
      <figcaption className={styles.panelTitle}>Hai tam giác đồng dạng · tỉ số và cạnh tương ứng</figcaption>
      <p className={styles.teachingStep}>{[
        `Bước 1 · Dựng tam giác nhỏ với cạnh ${measure(model.small.a)} ${unit} và ${measure(model.small.b)} ${unit}`,
        `Bước 2 · Dựng tam giác lớn có cạnh tương ứng ${measure(model.large.a)} ${unit}`,
        `Bước 3 · Tỉ số đồng dạng k = ${measure(model.large.a)} : ${measure(model.small.a)} = ${measure(model.scale)}`,
        `Bước 4 · Cạnh còn lại nhân cùng tỉ số: ${measure(model.small.b)} × ${measure(model.scale)} = ${measure(model.large.b)} ${unit}`,
      ][phase]}</p>
      <svg viewBox="0 0 400 210" className={styles.geometryDiagram} role="img"
        aria-label={`Hai tam giác đồng dạng tỉ số ${model.scale}`}>
        <polygon className={styles.shapeFill} points={triangle(model.small.a, model.small.b, 20)} />
        <polygon className={styles.shapeStroke} points={triangle(model.small.a, model.small.b, 20)} fill="none" />
        <text className={styles.geometryMeasure} x={20 + (model.small.a * scale) / 2} y="196">{measure(model.small.a)} {unit}</text>
        <text className={styles.geometryMeasure} x="12" y={180 - (model.small.b * scale) / 2}
          transform={`rotate(-90 12 ${180 - (model.small.b * scale) / 2})`}>{measure(model.small.b)} {unit}</text>
        {phase >= 1 ? (
          <>
            <polygon className={styles.shapeFillAccent} points={triangle(model.large.a, model.large.b, 210)} />
            <polygon className={styles.shapeStroke} points={triangle(model.large.a, model.large.b, 210)} fill="none" />
            <text className={styles.geometryMeasure} x={210 + (model.large.a * scale) / 2} y="196">{measure(model.large.a)} {unit}</text>
            <text className={styles.geometryMeasure} x="202" y={180 - (model.large.b * scale) / 2}
              transform={`rotate(-90 202 ${180 - (model.large.b * scale) / 2})`}>
              {phase >= 3 ? `${measure(model.large.b)} ${unit}` : "?"}
            </text>
          </>
        ) : null}
        {phase >= 2 ? <text className={styles.geometryMeasure} x="200" y="20">k = {measure(model.scale)}</text> : null}
      </svg>
      {phase >= 3 ? (
        <div className={styles.visualConclusion}>
          <span>Tỉ số các cạnh tương ứng bằng nhau</span>
          <strong>{model.ratioText}</strong>
        </div>
      ) : <p className={styles.fractionHint}>Đồng dạng nghĩa là mọi cặp cạnh tương ứng có cùng một tỉ số.</p>}
    </figure>
  );
}

/** A median split by the centroid, with both parts drawn and measured. */
function CentroidProofModel({ model, progress }) {
  const phase = progress >= 1 ? 3 : Math.min(2, Math.floor(Math.max(0, progress) * 3));
  const { a, b, c } = model.vertices;
  const midpoint = [(b[0] + c[0]) / 2, (b[1] + c[1]) / 2];
  const centroid = [
    a[0] + ((midpoint[0] - a[0]) * 2) / 3,
    a[1] + ((midpoint[1] - a[1]) * 2) / 3,
  ];
  return (
    <figure className={`${styles.panel} ${styles.geometryPanel}`}>
      <figcaption className={styles.panelTitle}>Trung tuyến và trọng tâm · tỉ số 2 : 1</figcaption>
      <p className={styles.teachingStep}>{[
        "Bước 1 · Dựng tam giác ABC",
        "Bước 2 · Lấy M là trung điểm BC, hai đoạn BM và MC bằng nhau",
        `Bước 3 · Trọng tâm G chia trung tuyến AM thành ${measure(model.longPart)} và ${measure(model.shortPart)} ${model.unit}`,
        `Bước 4 · AG : GM = ${model.ratio}, tức AG = 2/3 AM`,
      ][phase]}</p>
      <svg viewBox="0 0 220 200" className={styles.geometryDiagram} role="img" aria-label="Tam giác với trung tuyến và trọng tâm">
        <polygon className={styles.shapeFill} points={`${a} ${b} ${c}`} />
        <polygon className={styles.shapeStroke} points={`${a} ${b} ${c}`} fill="none" />
        <text className={styles.geometryLabel} x={a[0] - 8} y={a[1] - 6}>A</text>
        <text className={styles.geometryLabel} x={b[0] - 12} y={b[1] + 14}>B</text>
        <text className={styles.geometryLabel} x={c[0] + 4} y={c[1] + 14}>C</text>
        {phase >= 1 ? (
          <>
            <line className={styles.geometryHyp} x1={a[0]} y1={a[1]} x2={midpoint[0]} y2={midpoint[1]} />
            <circle className={styles.graphPoint} cx={midpoint[0]} cy={midpoint[1]} r="4" />
            <text className={styles.geometryLabel} x={midpoint[0] + 5} y={midpoint[1] + 16}>M</text>
            <text className={styles.geometryMeasure} x={(b[0] + midpoint[0]) / 2} y={b[1] + 14}>=</text>
            <text className={styles.geometryMeasure} x={(midpoint[0] + c[0]) / 2} y={c[1] + 14}>=</text>
          </>
        ) : null}
        {phase >= 2 ? (
          <>
            <circle className={styles.graphPointAccent} cx={centroid[0]} cy={centroid[1]} r="5" />
            <text className={styles.geometryLabel} x={centroid[0] + 7} y={centroid[1]}>G</text>
            <text className={styles.geometryMeasure} x={(a[0] + centroid[0]) / 2 - 18} y={(a[1] + centroid[1]) / 2}>
              AG = {measure(model.longPart)}
            </text>
            <text className={styles.geometryMeasure} x={(centroid[0] + midpoint[0]) / 2 + 20} y={(centroid[1] + midpoint[1]) / 2}>
              GM = {measure(model.shortPart)}
            </text>
          </>
        ) : null}
      </svg>
      {phase >= 3 ? (
        <div className={styles.visualConclusion}>
          <span>Trọng tâm chia trung tuyến</span>
          <strong>AG : GM = {model.ratio}</strong>
          <small>AM = {measure(model.median)} {model.unit} = {measure(model.longPart)} + {measure(model.shortPart)}</small>
        </div>
      ) : <p className={styles.fractionHint}>Hai dấu bằng trên BC cho thấy M thật sự là trung điểm.</p>}
    </figure>
  );
}

/**
 * A triangle drawn from its measurements, to scale.
 *
 * The right-angle marker appears only when the scene carries an explicit
 * perpendicular constraint. A vision model that merely guessed the angle must
 * not have that guess drawn as a fact — the inspector shows where the claim
 * came from, and an inferred one stays unmarked.
 */
/** A right triangle drawn to scale, with the third side and both angles derived. */
function TrigonometricGeometryModel({ model, progress }) {
  const phase = progress >= 1 ? 3 : Math.min(3, Math.floor(Math.max(0, progress) * 4));

  if (model.kind === "angle_of_depression") {
    const towerX = 100;
    const topY = 48;
    const baseY = 220;
    const shipX = 445;
    return (
      <figure className={`${styles.panel} ${styles.geometryPanel}`}>
        <figcaption className={styles.panelTitle}>Góc nghiêng xuống · tam giác vuông nhìn thấy được</figcaption>
        <p className={styles.teachingStep}>{[
          `Bước 1 · Dựng điểm quan sát cao ${measure(model.height)} ${model.unit} và mặt biển nằm ngang`,
          `Bước 2 · Kẻ phương ngang qua đỉnh: góc nghiêng xuống ${measure(model.angle)}° bằng góc nâng từ tàu`,
          `Bước 3 · tan ${measure(model.angle)}° = ${measure(model.height)} / d`,
          `Bước 4 · d = ${measure(model.height)} ÷ tan ${measure(model.angle)}° ≈ ${measure(model.distance)} ${model.unit}`,
        ][phase]}</p>
        <svg viewBox="0 0 520 270" className={styles.geometryDiagram} role="img"
          aria-label={`Hải đăng cao ${model.height} ${model.unit}, góc nghiêng xuống ${model.angle} độ`}>
          <line className={styles.trigWater} x1="28" y1={baseY} x2="490" y2={baseY} />
          <polygon className={styles.trigTower} points={`${towerX - 22},${baseY} ${towerX + 22},${baseY} ${towerX + 10},${topY} ${towerX - 10},${topY}`} />
          <line className={styles.geometryEdge} x1={towerX} y1={topY} x2={towerX} y2={baseY} />
          <rect className={styles.rightAngleMark} x={towerX} y={baseY - 13} width="13" height="13" />
          <text className={styles.geometryMeasure} x="44" y="138">h = {measure(model.height)} {model.unit}</text>
          {phase >= 1 ? (
            <>
              <line className={styles.trigGuide} x1={towerX} y1={topY} x2={shipX} y2={topY} />
              <line className={styles.trigSight} x1={towerX} y1={topY} x2={shipX} y2={baseY} />
              <path className={styles.trigAngleArc} d={`M ${towerX + 55} ${topY} A 55 55 0 0 1 ${towerX + 49} ${topY + 25}`} />
              <text className={styles.geometryMeasure} x={towerX + 61} y={topY + 25}>{measure(model.angle)}°</text>
              <text className={styles.trigShip} x={shipX - 18} y={baseY - 5}>⛴</text>
            </>
          ) : null}
          {phase >= 2 ? (
            <>
              <line className={styles.trigDistance} x1={towerX} y1={baseY + 18} x2={shipX} y2={baseY + 18} />
              <text className={styles.geometryMeasure} x={(towerX + shipX) / 2 - 38} y={baseY + 40}>
                d {phase >= 3 ? `≈ ${measure(model.distance)} ${model.unit}` : "= ?"}
              </text>
            </>
          ) : null}
        </svg>
        {phase >= 3 ? (
          <div className={styles.visualConclusion}>
            <span>Khoảng cách ngang từ tàu đến chân hải đăng</span>
            <strong>{measure(model.distance)} {model.unit}</strong>
            <small>Kiểm tra: tan {measure(model.angle)}° × {measure(model.distance)} ≈ {measure(model.height)}</small>
          </div>
        ) : <p className={styles.fractionHint}>Đường ngang ở đỉnh và mặt biển song song nên hai góc so le trong bằng nhau.</p>}
      </figure>
    );
  }

  if (model.kind === "oblique_triangle_altitude") {
    const [leftVertex, rightVertex] = model.baseVertices;
    const left = model.baseSegments[leftVertex];
    const right = model.baseSegments[rightVertex];
    const scale = Math.min(330 / (left + right), 180 / model.height);
    const footX = 80 + left * scale;
    const baseY = 240;
    const apexY = baseY - model.height * scale;
    const leftX = 80;
    const rightX = footX + right * scale;
    return (
      <figure className={`${styles.panel} ${styles.geometryPanel}`}>
        <figcaption className={styles.panelTitle}>Một tam giác xiên · hai tam giác vuông dùng chung đường cao</figcaption>
        <p className={styles.teachingStep}>{[
          `Bước 1 · Hạ ${model.apex}${model.foot} = ${measure(model.height)} ${model.unit}, chia tam giác thành hai phần vuông`,
          `Bước 2 · ${model.apex}${leftVertex} = ${measure(model.height)} ÷ sin ${measure(model.angles[leftVertex])}° = ${measure(model.sideLengths[`${model.apex}${leftVertex}`.split("").sort().join("")])} ${model.unit}`,
          `Bước 3 · ${model.apex}${rightVertex} = ${measure(model.height)} ÷ sin ${measure(model.angles[rightVertex])}° = ${measure(model.sideLengths[`${model.apex}${rightVertex}`.split("").sort().join("")])} ${model.unit}`,
          `Bước 4 · ${model.baseName} = ${measure(left)} + ${measure(right)} = ${measure(model.sideLengths[model.baseName])} ${model.unit}`,
        ][phase]}</p>
        <svg viewBox="0 0 520 285" className={styles.geometryDiagram} role="img"
          aria-label={`Tam giác ${model.vertices} có đường cao ${model.apex}${model.foot}`}>
          <polygon className={styles.shapeFill} points={`${leftX},${baseY} ${footX},${apexY} ${rightX},${baseY}`} />
          <polygon className={styles.shapeStroke} points={`${leftX},${baseY} ${footX},${apexY} ${rightX},${baseY}`} fill="none" />
          <line className={styles.trigGuide} x1={footX} y1={apexY} x2={footX} y2={baseY} />
          <rect className={styles.rightAngleMark} x={footX} y={baseY - 13} width="13" height="13" />
          <text className={styles.geometryLabel} x={footX - 5} y={apexY - 9}>{model.apex}</text>
          <text className={styles.geometryLabel} x={leftX - 18} y={baseY + 18}>{leftVertex}</text>
          <text className={styles.geometryLabel} x={rightX + 7} y={baseY + 18}>{rightVertex}</text>
          <text className={styles.geometryLabel} x={footX - 6} y={baseY + 18}>{model.foot}</text>
          <text className={styles.geometryMeasure} x={footX + 8} y={(apexY + baseY) / 2}>
            {model.apex}{model.foot} = {measure(model.height)} {model.unit}
          </text>
          <text className={styles.geometryMeasure} x={leftX + 18} y={baseY - 12}>{leftVertex} = {measure(model.angles[leftVertex])}°</text>
          <text className={styles.geometryMeasure} x={rightX - 72} y={baseY - 12}>{rightVertex} = {measure(model.angles[rightVertex])}°</text>
          {phase >= 1 ? <text className={styles.geometryMeasure} x={(leftX + footX) / 2 - 35} y={baseY + 35}>{measure(left)} {model.unit}</text> : null}
          {phase >= 2 ? <text className={styles.geometryMeasure} x={(footX + rightX) / 2 - 35} y={baseY + 35}>{measure(right)} {model.unit}</text> : null}
        </svg>
        {phase >= 3 ? (
          <div className={styles.visualConclusion}>
            <span>Ba cạnh của tam giác {model.vertices}</span>
            <strong>{Object.entries(model.sideLengths).map(([name, value]) => `${name} ≈ ${measure(value)} ${model.unit}`).join("; ")}</strong>
            <small>Góc {model.apex} = 180° − {measure(model.angles[leftVertex])}° − {measure(model.angles[rightVertex])}° = {measure(model.apexAngle)}°</small>
          </div>
        ) : <p className={styles.fractionHint}>Hai tam giác vuông dùng chung đúng một đường cao, không phải hai chiều cao khác nhau.</p>}
      </figure>
    );
  }

  const sideScale = 90 / model.sideLength;
  const diagonalScale = 90 / (model.sideLength * Math.tan((model.angle * Math.PI) / 180));
  const commonScale = Math.min(sideScale, diagonalScale);
  const sidePx = model.sideLength * commonScale;
  const diagonalPx = model.diagonalLength * commonScale;
  const a = { x: 180, y: 145 };
  const d = { x: 180, y: 145 + sidePx };
  const c = { x: 180 + diagonalPx, y: 145 };
  const b = { x: c.x, y: c.y - sidePx };
  return (
    <figure className={`${styles.panel} ${styles.geometryPanel}`}>
      <figcaption className={styles.panelTitle}>Hình bình hành · đường chéo trở thành chiều cao</figcaption>
      <p className={styles.teachingStep}>{[
        `Bước 1 · Dựng ${model.vertices}, ${model.diagonal} ⟂ ${model.side}, ${model.side} = ${measure(model.sideLength)} ${model.unit}`,
        `Bước 2 · Tam giác vuông chứa góc ${model.angleVertex} = ${measure(model.angle)}°`,
        `Bước 3 · ${model.diagonal} = ${model.side} × tan ${measure(model.angle)}° ≈ ${measure(model.diagonalLength)} ${model.unit}`,
        `Bước 4 · S = ${model.side} × ${model.diagonal} ≈ ${measure(model.area)} ${model.areaUnit}`,
      ][phase]}</p>
      <svg viewBox="0 0 520 285" className={styles.geometryDiagram} role="img"
        aria-label={`Hình bình hành ${model.vertices} có ${model.diagonal} vuông góc ${model.side}`}>
        <polygon className={styles.shapeFillAccent} points={`${a.x},${a.y} ${b.x},${b.y} ${c.x},${c.y} ${d.x},${d.y}`} />
        <polygon className={styles.shapeStroke} points={`${a.x},${a.y} ${b.x},${b.y} ${c.x},${c.y} ${d.x},${d.y}`} fill="none" />
        <line className={styles.trigSight} x1={a.x} y1={a.y} x2={c.x} y2={c.y} />
        <rect className={styles.rightAngleMark} x={a.x} y={a.y} width="13" height="13" />
        {[a, b, c, d].map((point, index) => <text key={index} className={styles.geometryLabel} x={point.x - 13} y={point.y - 8}>{model.vertices[index]}</text>)}
        <text className={styles.geometryMeasure} x={a.x - 70} y={(a.y + d.y) / 2}>{model.side} = {measure(model.sideLength)} {model.unit}</text>
        {phase >= 1 ? <text className={styles.geometryMeasure} x={d.x + 12} y={d.y - 22}>∠{model.angleVertex} = {measure(model.angle)}°</text> : null}
        {phase >= 2 ? <text className={styles.geometryMeasure} x={(a.x + c.x) / 2 - 40} y={a.y - 12}>{model.diagonal} ≈ {measure(model.diagonalLength)} {model.unit}</text> : null}
      </svg>
      {phase >= 3 ? (
        <div className={styles.visualConclusion}>
          <span>Diện tích hình bình hành</span>
          <strong>{measure(model.area)} {model.areaUnit}</strong>
          <small>{measure(model.sideLength)} × {measure(model.diagonalLength)} = {measure(model.area)}</small>
        </div>
      ) : <p className={styles.fractionHint}>Vì đường chéo vuông góc với cạnh đáy, nó chính là chiều cao tương ứng.</p>}
    </figure>
  );
}

function RightTriangleSolutionModel({ model, progress }) {
  const phase = progress >= 1 ? 4 : Math.min(3, Math.floor(Math.max(0, progress) * 4));
  const { sides, legNames, hypotenuseName, unit } = model;
  const [firstLeg, secondLeg] = legNames;
  const box = 210;
  const pad = 34;
  const longest = Math.max(sides[firstLeg], sides[secondLeg]);
  const scale = (box - pad * 2) / longest;
  // The right angle sits at the origin corner, so the two legs are the axes.
  const corner = { x: pad, y: box - pad };
  const along = { x: pad + sides[firstLeg] * scale, y: box - pad };
  const up = { x: pad, y: box - pad - sides[secondLeg] * scale };
  const points = `${corner.x},${corner.y} ${along.x},${along.y} ${up.x},${up.y}`;
  const angleAt = (vertex) => model.angles.find((item) => item.vertex === vertex);
  const showAngle = (index) => phase >= 2 + index;
  const formatAngle = (item) => (
    model.roundToMinute
      ? `${item.wholeDegrees}°${String(item.minutes).padStart(2, "0")}'`
      : `${measure(item.degrees)}°`
  );
  return (
    <figure className={`${styles.panel} ${styles.geometryPanel}`}>
      <figcaption className={styles.panelTitle}>
        Giải tam giác {model.vertices} vuông tại {model.rightVertex}
      </figcaption>
      <p className={styles.teachingStep}>{[
        `Bước 1 · Dựng tam giác với ${Object.entries(model.known).map(([name, value]) => `${name} = ${measure(value)} ${unit}`).join(", ")}`,
        model.hasHypotenuse
          ? `Bước 2 · ${model.missing}² = ${hypotenuseName}² − ${Object.keys(model.known).find((n) => n !== hypotenuseName)}² → ${model.missing} = ${measure(sides[model.missing])} ${unit}`
          : `Bước 2 · ${hypotenuseName}² = ${firstLeg}² + ${secondLeg}² → ${hypotenuseName} = ${measure(sides[hypotenuseName])} ${unit}`,
        model.angles[0] ? `Bước 3 · sin ${model.angles[0].vertex} = cạnh đối / cạnh huyền → ${model.angles[0].vertex} ≈ ${formatAngle(model.angles[0])}` : "",
        model.angles[1] ? `Bước 4 · ${model.angles[1].vertex} = 90° − ${model.angles[0].vertex} ≈ ${formatAngle(model.angles[1])}` : "",
        `Bước 5 · Kiểm tra: hai góc nhọn cộng lại bằng ${measure(model.angleSum)}°`,
      ][phase]}</p>
      <svg viewBox={`0 0 ${box} ${box}`} className={styles.geometryDiagram} role="img"
        aria-label={`Tam giác ${model.vertices} vuông tại ${model.rightVertex}`}>
        <polygon className={styles.shapeFill} points={points} />
        <polygon className={styles.shapeStroke} points={points} fill="none" />
        <rect className={styles.rightAngleMark} x={corner.x} y={corner.y - 13} width="13" height="13" />
        <text className={styles.geometryLabel} x={corner.x - 12} y={corner.y + 14}>{model.rightVertex}</text>
        <text className={styles.geometryLabel} x={along.x + 4} y={along.y + 14}>{firstLeg.replace(model.rightVertex, "")}</text>
        <text className={styles.geometryLabel} x={up.x - 14} y={up.y - 4}>{secondLeg.replace(model.rightVertex, "")}</text>
        <text className={styles.geometryMeasure} x={(corner.x + along.x) / 2} y={corner.y + 16}>
          {firstLeg} = {firstLeg in model.known || phase >= 1 ? `${measure(sides[firstLeg])} ${unit}` : "?"}
        </text>
        <text className={styles.geometryMeasure} x={corner.x - 18} y={(corner.y + up.y) / 2}
          transform={`rotate(-90 ${corner.x - 18} ${(corner.y + up.y) / 2})`}>
          {secondLeg} = {secondLeg in model.known || phase >= 1 ? `${measure(sides[secondLeg])} ${unit}` : "?"}
        </text>
        <text className={styles.geometryMeasure} x={(along.x + up.x) / 2 + 16} y={(along.y + up.y) / 2}>
          {hypotenuseName} = {hypotenuseName in model.known || phase >= 1 ? `${measure(sides[hypotenuseName])} ${unit}` : "?"}
        </text>
        {model.angles.map((item, index) => {
          if (!showAngle(index)) return null;
          const at = item.vertex === firstLeg.replace(model.rightVertex, "") ? along : up;
          return (
            <text key={item.vertex} className={styles.geometryMeasure}
              x={at === along ? at.x - 26 : at.x + 20} y={at === along ? at.y - 10 : at.y + 20}>
              {item.vertex} ≈ {formatAngle(item)}
            </text>
          );
        })}
      </svg>
      <div className={styles.dimensionFormula}>
        {[firstLeg, secondLeg, hypotenuseName].map((name) => (
          <span key={name}>
            <b>{name}</b> = {name in model.known || phase >= 1 ? `${measure(sides[name])} ${unit}` : "?"}
          </span>
        ))}
      </div>
      {phase >= 4 ? (
        <div className={styles.visualConclusion}>
          <span>Kết quả giải tam giác</span>
          <strong>
            {model.missing} = {measure(sides[model.missing])} {unit}
            {model.angles.map((item) => `; ${item.vertex} ≈ ${formatAngle(item)}`).join("")}
          </strong>
          <small>
            Kiểm tra: {firstLeg}² + {secondLeg}² = {measure(sides[firstLeg] ** 2 + sides[secondLeg] ** 2)} = {hypotenuseName}²
            {" "}và {model.angles.map((item) => item.vertex).join(" + ")} = {measure(model.angleSum)}°
          </small>
        </div>
      ) : <p className={styles.fractionHint}>Cạnh còn lại tìm bằng Pythagoras, sau đó mới tính được các góc nhọn.</p>}
    </figure>
  );
}

export default function Geometry2DRenderer({ world, scene, visualization, progress }) {
  const problemType = String(scene?.metadata?.problem_type || "");
  if (/angle_of_depression|oblique_triangle_altitude|parallelogram_perpendicular_diagonal/i.test(problemType)) {
    const model = deriveTrigonometricGeometry(world, visualization?.bindings, scene?.metadata?.relations);
    return model
      ? <TrigonometricGeometryModel model={model} progress={progress} />
      : <p className={styles.unavailable}>Cần đủ độ dài và góc đã in để dựng mô hình lượng giác.</p>;
  }
  if (/right_triangle_solution/i.test(problemType)) {
    const triangle = deriveRightTriangle(world, visualization?.bindings, scene?.metadata?.relations);
    return triangle
      ? <RightTriangleSolutionModel model={triangle} progress={progress} />
      : <p className={styles.unavailable}>Cần hai cạnh của tam giác vuông để giải tam giác.</p>;
  }
  if (/triangle_similarity/i.test(problemType)) {
    const similarity = deriveTriangleSimilarity(world, visualization?.bindings);
    return similarity
      ? <SimilarityProofModel model={similarity} progress={progress} />
      : <p className={styles.unavailable}>Cần hai cạnh của tam giác nhỏ và một cạnh tương ứng của tam giác lớn.</p>;
  }
  if (/centroid|trung_tuyen/i.test(problemType)) {
    const centroid = deriveCentroidProof(world, visualization?.bindings);
    return centroid
      ? <CentroidProofModel model={centroid} progress={progress} />
      : <p className={styles.unavailable}>Cần độ dài đường trung tuyến để dựng trọng tâm.</p>;
  }
  const shape = deriveGeometry2d(world, visualization?.bindings, scene?.metadata?.problem_type);
  if (!shape) {
    return <p className={styles.unavailable}>Cần hai cạnh để dựng hình.</p>;
  }
  if (shape.kind === "circle") return <CircleModel shape={shape} progress={progress} />;
  if (["rhombus", "parallelogram"].includes(shape.kind)) return <QuadrilateralModel shape={shape} progress={progress} />;
  if (shape.kind === "segment") return <SegmentModel shape={shape} progress={progress} />;
  if (shape.kind === "angle_bisector") return <AngleBisectorModel shape={shape} progress={progress} />;

  const rightAngle = (scene?.constraints || []).find(
    (constraint) => constraint.type === "perpendicular"
      && constraint.evidence?.status === "explicit",
  );

  // Fit the longer side to the box, so a 3–4 triangle looks like a 3–4
  // triangle rather than whatever the container happens to be.
  const box = 180;
  const pad = 28;
  const scale = (box - pad * 2) / Math.max(shape.a, shape.b);
  const ax = pad;
  const ay = box - pad;
  const bx = pad + shape.a * scale;
  const by = box - pad;
  const triangleArea = shape.kind === "triangle_area";
  const cx = triangleArea ? pad + (shape.a * scale) / 2 : pad;
  const cy = box - pad - shape.b * scale;
  const dx = bx;
  const dy = cy;
  const rectangle = shape.kind === "rectangle";
  const phase = progress >= 1 ? 3 : Math.min(2, Math.floor(Math.max(0, progress) * 3));

  return (
    <figure className={styles.panel}>
      <figcaption className={styles.panelTitle}>Hình học phẳng</figcaption>
      <p className={styles.teachingStep}>{rectangle ? [
        "Bước 1 · Dựng hình theo đúng tỉ lệ hai cạnh",
        "Bước 2 · Đọc chiều dài và chiều rộng trên hình",
        "Bước 3 · Phủ hình bằng các ô đơn vị để hiểu diện tích",
        "Bước 4 · Tính chu vi và diện tích từ kích thước",
      ][phase] : [
        "Bước 1 · Dựng hai cạnh góc vuông theo đúng tỉ lệ",
        "Bước 2 · Khép tam giác bằng cạnh huyền",
        "Bước 3 · Ghép hai tam giác thành một hình chữ nhật",
        "Bước 4 · Diện tích tam giác bằng một nửa hình chữ nhật",
      ][phase]}</p>

      <svg viewBox={`0 0 ${box} ${box}`} className={styles.geometry} role="img"
        aria-label={`${rectangle ? "Hình chữ nhật" : "Tam giác"} với hai cạnh ${shape.a} và ${shape.b} ${shape.unit}`}>
        <polygon
          className={styles.geometryFill}
          points={rectangle
            ? `${ax},${ay} ${bx},${by} ${dx},${dy} ${cx},${cy}`
            : `${ax},${ay} ${bx},${by} ${cx},${cy}`}
        />
        {!rectangle && !triangleArea && phase >= 2 ? (
          <polyline className={styles.geometryConstruction} points={`${bx},${by} ${dx},${dy} ${cx},${cy}`} />
        ) : null}
        {triangleArea ? <line className={styles.geometryConstruction} strokeDasharray="5 4" x1={cx} y1={cy} x2={cx} y2={ay} /> : null}
        <line className={styles.geometryEdge} x1={ax} y1={ay} x2={bx} y2={by} />
        <line className={styles.geometryEdge} x1={ax} y1={ay} x2={cx} y2={cy} />
        {rectangle ? (
          <>
            <line className={styles.geometryEdge} x1={bx} y1={by} x2={dx} y2={dy} />
            <line className={styles.geometryEdge} x1={cx} y1={cy} x2={dx} y2={dy} />
          </>
        ) : (
          <line className={styles.geometryHyp} x1={bx} y1={by} x2={cx} y2={cy} />
        )}

        {!rectangle && (rightAngle || triangleArea) ? (
          <polyline
            className={styles.rightAngle}
            points={triangleArea
              ? `${cx + 14},${ay} ${cx + 14},${ay - 14} ${cx},${ay - 14}`
              : `${ax + 14},${ay} ${ax + 14},${ay - 14} ${ax},${ay - 14}`}
          />
        ) : null}

        <text className={styles.geometryLabel} x={ax - 8} y={ay + 12}>A</text>
        <text className={styles.geometryLabel} x={bx + 2} y={by + 12}>B</text>
        <text className={styles.geometryLabel} x={cx - 8} y={cy - 4}>{rectangle ? "D" : "C"}</text>
        {rectangle ? <text className={styles.geometryLabel} x={dx + 2} y={dy - 4}>C</text> : null}
        <text className={styles.geometryMeasure} x={(ax + bx) / 2} y={ay + 16}>
          {shape.a} {shape.unit}
        </text>
        <text className={styles.geometryMeasure} x={triangleArea ? cx + 7 : ax - 22} y={(ay + cy) / 2}>
          {shape.b} {shape.unit}
        </text>
      </svg>

      {rectangle ? (
        <dl className={styles.readout}>
          <div><dt>Chiều dài</dt><dd>{round(shape.a)} {shape.unit}</dd></div>
          <div><dt>Chiều rộng</dt><dd>{round(shape.b)} {shape.unit}</dd></div>
          <div><dt>Chu vi</dt><dd>{phase >= 3 ? `2 × (${round(shape.a)} + ${round(shape.b)}) = ${round(shape.perimeter)} ${shape.unit}` : "2 × (dài + rộng)"}</dd></div>
          <div><dt>Diện tích</dt><dd>{phase >= 3 ? `${round(shape.a)} × ${round(shape.b)} = ${round(shape.area)} ${shape.unit}²` : "dài × rộng"}</dd></div>
        </dl>
      ) : (
        <dl className={styles.readout}>
          {triangleArea ? <div><dt>Đáy</dt><dd>{round(shape.a)} {shape.unit}</dd></div> : <div><dt>Cạnh huyền</dt><dd>{round(shape.hypotenuse)} {shape.unit}</dd></div>}
          <div><dt>Diện tích</dt><dd>{phase >= 3 ? `${round(shape.a)} × ${round(shape.b)} ÷ 2 = ${round(shape.area)} ${shape.unit}²` : "đáy × cao ÷ 2"}</dd></div>
          <div>
            <dt>Góc vuông</dt>
            <dd>{triangleArea ? "Đáy vuông góc đường cao" : rightAngle ? "Đề bài cho" : "Không được nêu"}</dd>
          </div>
        </dl>
      )}
    </figure>
  );
}

function round(value) {
  return String(Math.round(value * 100) / 100).replace(".", ",");
}

function AngleBisectorModel({ shape, progress }) {
  const phase = progress >= 1 ? 3 : Math.min(2, Math.floor(Math.max(0, progress) * 3));
  const origin = { x: 82, y: 224 };
  const rayLength = 172;
  const pointAt = (angle, radius = rayLength) => {
    const radians = (-angle * Math.PI) / 180;
    return {
      x: origin.x + Math.cos(radians) * radius,
      y: origin.y + Math.sin(radians) * radius,
    };
  };
  const xPoint = pointAt(0);
  const yPoint = pointAt(shape.totalAngle);
  const tPoint = pointAt(shape.halfAngle);
  const wholeStart = pointAt(0, 58);
  const wholeEnd = pointAt(shape.totalAngle, 58);
  const firstStart = pointAt(0, 78);
  const firstEnd = pointAt(shape.halfAngle, 78);
  const secondEnd = pointAt(shape.totalAngle, 94);
  const arc = (start, end, radius) => `M ${start.x} ${start.y} A ${radius} ${radius} 0 0 0 ${end.x} ${end.y}`;

  return (
    <figure className={`${styles.panel} ${styles.curriculumWide}`}>
      <figcaption className={styles.panelTitle}>Tia phân giác · chia một góc thành hai phần bằng nhau</figcaption>
      <p className={styles.teachingStep}>{[
        "Bước 1 · Dựng hai tia Ox và Oy tạo thành góc xOy",
        `Bước 2 · Đánh dấu số đo toàn góc xOy = ${round(shape.totalAngle)}°`,
        "Bước 3 · Dựng tia Ot nằm giữa Ox và Oy",
        `Bước 4 · Hai góc bằng nhau: xOt = tOy = ${round(shape.halfAngle)}°`,
      ][phase]}</p>

      <svg viewBox="0 0 390 270" className={styles.angleDiagram} role="img"
        aria-label={`Góc xOy ${shape.totalAngle} độ, tia Ot là phân giác, góc xOt bằng ${shape.halfAngle} độ`}>
        <path d={`M ${xPoint.x} ${xPoint.y} L ${origin.x} ${origin.y} L ${yPoint.x} ${yPoint.y}`} className={styles.angleRegion} />
        <line x1={origin.x} y1={origin.y} x2={xPoint.x} y2={xPoint.y} className={styles.angleRay} />
        <line x1={origin.x} y1={origin.y} x2={yPoint.x} y2={yPoint.y} className={styles.angleRay} />
        <circle cx={origin.x} cy={origin.y} r="5" className={styles.graphPoint} />
        <text x={origin.x - 18} y={origin.y + 8} className={styles.geometryLabel}>O</text>
        <text x={xPoint.x + 8} y={xPoint.y + 7} className={styles.geometryLabel}>x</text>
        <text x={yPoint.x - 3} y={yPoint.y - 10} className={styles.geometryLabel}>y</text>

        {phase >= 1 ? <>
          <path d={arc(wholeStart, wholeEnd, 58)} className={styles.angleArc} />
          <text x={pointAt(shape.totalAngle / 2, 43).x - 15} y={pointAt(shape.totalAngle / 2, 43).y - 4} className={styles.geometryMeasure}>{round(shape.totalAngle)}°</text>
        </> : null}

        {phase >= 2 ? <>
          <line x1={origin.x} y1={origin.y} x2={tPoint.x} y2={tPoint.y} className={styles.angleRayAccent} />
          <text x={tPoint.x + 5} y={tPoint.y - 7} className={styles.geometryLabel}>t</text>
        </> : null}

        {phase >= 3 ? <>
          <path d={arc(firstStart, firstEnd, 78)} className={styles.angleArcAccent} />
          <path d={arc(firstEnd, secondEnd, 94)} className={styles.angleArcAccent} />
          <text x={pointAt(shape.halfAngle / 2, 105).x - 8} y={pointAt(shape.halfAngle / 2, 105).y + 5} className={styles.angleHalfLabel}>{round(shape.halfAngle)}°</text>
          <text x={pointAt(shape.halfAngle * 1.5, 115).x - 9} y={pointAt(shape.halfAngle * 1.5, 115).y + 5} className={styles.angleHalfLabel}>{round(shape.halfAngle)}°</text>
        </> : null}
      </svg>

      <div className={styles.angleReasoning}>
        <span><b>Toàn góc</b><strong>{round(shape.totalAngle)}°</strong></span>
        <span aria-hidden="true">÷ 2</span>
        <span><b>Mỗi góc</b><strong>{phase >= 3 ? `${round(shape.halfAngle)}°` : "?"}</strong></span>
      </div>
      <p className={styles.visualEquation}>{phase >= 3
        ? `∠xOt = ∠tOy = ${round(shape.totalAngle)}° ÷ 2 = ${round(shape.halfAngle)}°`
        : "Tia phân giác chia góc xOy thành hai góc bằng nhau"}</p>
    </figure>
  );
}

function CircleModel({ shape, progress }) {
  const phase = progress >= 1 ? 3 : Math.min(2, Math.floor(Math.max(0, progress) * 3));
  return (
    <figure className={styles.panel}>
      <figcaption className={styles.panelTitle}>Bán kính và đường kính trên cùng một đường tròn</figcaption>
      <p className={styles.teachingStep}>{[
        "Bước 1 · Xác định tâm O",
        `Bước 2 · Dựng bán kính r = ${round(shape.radius)} ${shape.unit}`,
        "Bước 3 · Ghép hai bán kính thẳng hàng thành đường kính",
        "Bước 4 · Đọc quan hệ d = 2 × r",
      ][phase]}</p>
      <svg viewBox="0 0 240 210" className={styles.geometry} role="img" aria-label={`Đường tròn bán kính ${shape.radius}, đường kính ${shape.diameter}`}>
        <circle cx="120" cy="102" r="76" className={styles.circleFill} />
        <circle cx="120" cy="102" r="4" className={styles.graphPoint} />
        <text x="126" y="98" className={styles.geometryLabel}>O</text>
        {phase >= 1 ? <><line x1="120" y1="102" x2="196" y2="102" className={styles.geometryEdge} /><text x="152" y="94" className={styles.geometryMeasure}>r = {round(shape.radius)}</text></> : null}
        {phase >= 2 ? <><line x1="44" y1="102" x2="196" y2="102" className={styles.geometryHyp} /><text x="95" y="122" className={styles.geometryMeasure}>d = {round(shape.diameter)}</text></> : null}
      </svg>
      <p className={styles.visualEquation}>{phase >= 3 ? `${round(shape.diameter)} = 2 × ${round(shape.radius)} ${shape.unit}` : "Đường kính đi qua tâm và gồm hai bán kính"}</p>
    </figure>
  );
}

function QuadrilateralModel({ shape, progress }) {
  const phase = progress >= 1 ? 3 : Math.min(2, Math.floor(Math.max(0, progress) * 3));
  const offset = shape.kind === "rhombus" ? 55 : 36;
  return (
    <figure className={styles.panel}>
      <figcaption className={styles.panelTitle}>{shape.kind === "rhombus" ? "Hình thoi" : "Hình bình hành"} · cắt và ghép diện tích</figcaption>
      <p className={styles.teachingStep}>{[
        "Bước 1 · Dựng đáy và cạnh bên",
        "Bước 2 · Hạ đường cao vuông góc với đáy",
        "Bước 3 · Cắt tam giác bên trái và chuyển sang bên phải",
        "Bước 4 · Hình chữ nhật ghép được có diện tích đáy × cao",
      ][phase]}</p>
      <svg viewBox="0 0 260 190" className={styles.geometry} role="img" aria-label={`${shape.kind} đáy ${shape.a}, cao ${shape.b}`}>
        <polygon points={`${35 + offset},35 220,35 ${220 - offset},145 35,145`} className={styles.geometryFill} />
        <polyline points={`${35 + offset},35 220,35 ${220 - offset},145 35,145 ${35 + offset},35`} className={styles.geometryEdge} fill="none" />
        {phase >= 1 ? <>
          <line x1={35 + offset} y1="35" x2={220 - offset} y2="145" className={styles.quadrilateralDiagonal} />
          <line x1="220" y1="35" x2="35" y2="145" className={styles.quadrilateralDiagonal} />
          <text x="122" y="27" className={styles.geometryMeasure}>∥</text>
          <text x="122" y="160" className={styles.geometryMeasure}>∥</text>
        </> : null}
        {phase >= 1 ? <line x1={35 + offset} y1="35" x2={35 + offset} y2="145" className={styles.geometryConstruction} strokeDasharray="5 4" /> : null}
        {phase >= 2 ? <polygon points={`${35 + offset},35 ${35 + offset},145 35,145`} className={styles.geometryCutPiece} /> : null}
        <text x="112" y="165" className={styles.geometryMeasure}>đáy = {round(shape.a)} {shape.unit}</text>
        <text x={42 + offset} y="94" className={styles.geometryMeasure}>h = {round(shape.b)}</text>
      </svg>
      {phase >= 2 ? <p className={styles.areaExplanation}>{shape.kind === "rhombus" ? "Bốn cạnh bằng nhau; hai đường chéo cắt nhau tại trung điểm. Hai cạnh đối song song." : "Hai cặp cạnh đối song song và bằng nhau; đường chéo cắt nhau tại trung điểm."}</p> : null}
      <p className={styles.visualEquation}>{phase >= 3 ? `S = ${round(shape.a)} × ${round(shape.b)} = ${round(shape.area)} ${shape.unit}²` : "Diện tích không phụ thuộc độ nghiêng của cạnh bên"}</p>
    </figure>
  );
}

function SegmentModel({ shape, progress }) {
  const phase = progress >= 1 ? 3 : Math.min(2, Math.floor(Math.max(0, progress) * 3));
  return (
    <figure className={`${styles.panel} ${styles.curriculumWide}`}>
      <figcaption className={styles.panelTitle}>Điểm · đoạn thẳng · tia · trung điểm</figcaption>
      <p className={styles.teachingStep}>{[
        "Bước 1 · Đoạn AB bị chặn bởi hai đầu mút",
        "Bước 2 · Tia AB bắt đầu ở A và kéo dài qua B",
        "Bước 3 · Trung điểm M nằm trên AB và chia AB thành hai phần bằng nhau",
        "Bước 4 · Kiểm tra AM = MB = AB ÷ 2",
      ][phase]}</p>
      <svg viewBox="0 0 520 180" className={styles.segmentDiagram} role="img" aria-label={`Đoạn AB dài ${shape.length}, trung điểm M`}>
        <defs><marker id="segment-arrow" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L8,4 L0,8 Z" className={styles.axisArrow} /></marker></defs>
        <text x="20" y="32" className={styles.geometryLabel}>Đoạn thẳng AB</text>
        <line x1="65" y1="66" x2="455" y2="66" className={styles.geometryEdge} />
        <circle cx="65" cy="66" r="5" className={styles.graphPoint} /><circle cx="455" cy="66" r="5" className={styles.graphPoint} />
        <text x="55" y="55" className={styles.geometryLabel}>A</text><text x="460" y="55" className={styles.geometryLabel}>B</text>
        {phase >= 1 ? <><text x="20" y="112" className={styles.geometryLabel}>Tia AB</text><line x1="65" y1="138" x2="475" y2="138" className={styles.geometryHyp} markerEnd="url(#segment-arrow)" /><circle cx="65" cy="138" r="5" className={styles.graphPoint} /></> : null}
        {phase >= 2 ? <><circle cx="260" cy="66" r="6" className={styles.graphPointAccent} /><text x="252" y="52" className={styles.geometryLabel}>M</text><line x1="254" y1="58" x2="266" y2="74" className={styles.midpointMark} /></> : null}
      </svg>
      <p className={styles.visualEquation}>{phase >= 3 ? `AM = MB = ${round(shape.length)} ÷ 2 = ${round(shape.half)} ${shape.unit}` : `AB = ${round(shape.length)} ${shape.unit}`}</p>
    </figure>
  );
}
