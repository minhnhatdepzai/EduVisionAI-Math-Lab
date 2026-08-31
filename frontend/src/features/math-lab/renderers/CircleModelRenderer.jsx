import { deriveCircleArea, deriveCircleProof } from "../derive/deriveCoverage.js";
import styles from "./renderers.module.css";

const CENTRE = { x: 150, y: 140 };
const DRAWN_RADIUS = 92;

function format(value) {
  return new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 2 }).format(value);
}

function polar(angleDegrees, radius, centre = CENTRE) {
  const radians = (angleDegrees * Math.PI) / 180;
  return { x: centre.x + radius * Math.cos(radians), y: centre.y - radius * Math.sin(radians) };
}

function sectorPath(startDegrees, sweepDegrees, radius, centre = CENTRE) {
  const start = polar(startDegrees, radius, centre);
  const end = polar(startDegrees + sweepDegrees, radius, centre);
  const largeArc = sweepDegrees > 180 ? 1 : 0;
  return `M${centre.x} ${centre.y} L${start.x.toFixed(2)} ${start.y.toFixed(2)} `
    + `A${radius} ${radius} 0 ${largeArc} 0 ${end.x.toFixed(2)} ${end.y.toFixed(2)} Z`;
}

export default function CircleModelRenderer({ world, progress, visualization, scene }) {
  const problemType = String(scene?.metadata?.problem_type || "");
  if (/circle_tangent_cyclic/i.test(problemType)) {
    const proof = deriveCircleProof(world, visualization?.bindings);
    return proof
      ? <CircleProofModel proof={proof} progress={progress} />
      : <p className={styles.unavailable}>Cần bán kính và số đo góc ở tâm để dựng đường tròn.</p>;
  }
  const circle = deriveCircleArea(world, visualization?.bindings);
  if (!circle) {
    return <p className={styles.unavailable}>Cần bán kính hoặc đường kính để dựng hình tròn.</p>;
  }
  return <CircleAreaModel circle={circle} progress={progress} />;
}

/** Cut the disc into equal sectors and re-lay them as a near rectangle. */
function CircleAreaModel({ circle, progress }) {
  const phase = progress >= 1 ? 4 : Math.min(3, Math.floor(Math.max(0, progress) * 4));
  const sweep = 360 / circle.sectors;
  const sectors = Array.from({ length: circle.sectors }, (_, index) => index);
  const stripTop = 60;
  const stripLeft = 26;
  const stripWidth = 248;
  const sectorWidth = stripWidth / circle.sectors;
  const stripHeight = 74;
  return (
    <figure className={`${styles.panel} ${styles.circlePanel}`}>
      <figcaption className={styles.panelTitle}>Hình tròn và diện tích π × r²</figcaption>
      <p className={styles.teachingStep}>{[
        `Bước 1 · Đánh dấu tâm O và bán kính r = ${format(circle.radius)} ${circle.unit}`,
        `Bước 2 · Chia hình tròn thành ${circle.sectors} hình quạt bằng nhau`,
        "Bước 3 · Xếp xen kẽ các hình quạt thành hình gần chữ nhật",
        `Bước 4 · Chiều dài là nửa chu vi π × r = ${format(circle.halfCircumference)} ${circle.unit}, chiều rộng là r`,
        `Bước 5 · Diện tích = π × r × r = ${format(circle.area)} ${circle.unit}²`,
      ][phase]}</p>
      <svg viewBox="0 0 300 260" className={styles.circleDiagram} role="img"
        aria-label={`Hình tròn bán kính ${circle.radius} ${circle.unit} được cắt thành ${circle.sectors} hình quạt`}>
        {phase <= 1 ? (
          <g>
            <circle className={styles.circleBody} cx={CENTRE.x} cy={CENTRE.y} r={DRAWN_RADIUS} />
            {phase >= 1 ? sectors.map((index) => (
              <path key={index} className={index % 2 ? styles.circleSectorAlt : styles.circleSector}
                d={sectorPath(index * sweep, sweep, DRAWN_RADIUS)} />
            )) : null}
            <circle className={styles.circleCentre} cx={CENTRE.x} cy={CENTRE.y} r="3.5" />
            <line className={styles.circleRadius} x1={CENTRE.x} y1={CENTRE.y}
              x2={CENTRE.x + DRAWN_RADIUS} y2={CENTRE.y} />
            <text className={styles.geometryMeasure} x={CENTRE.x + DRAWN_RADIUS / 2 - 8} y={CENTRE.y - 8}>
              r = {format(circle.radius)} {circle.unit}
            </text>
            <text className={styles.geometryLabel} x={CENTRE.x - 14} y={CENTRE.y + 16}>O</text>
          </g>
        ) : (
          <g>
            {sectors.map((index) => {
              const pointingUp = index % 2 === 0;
              const x = stripLeft + index * sectorWidth;
              const baseY = pointingUp ? stripTop + stripHeight : stripTop;
              const apexY = pointingUp ? stripTop : stripTop + stripHeight;
              return (
                <path key={index} className={pointingUp ? styles.circleSector : styles.circleSectorAlt}
                  d={`M${x.toFixed(2)} ${baseY} L${(x + sectorWidth).toFixed(2)} ${baseY} `
                    + `L${(x + sectorWidth / 2).toFixed(2)} ${apexY} Z`} />
              );
            })}
            <rect className={styles.circleRectangleOutline} x={stripLeft} y={stripTop}
              width={stripWidth} height={stripHeight} />
            <line className={styles.circleRadius} x1={stripLeft - 8} y1={stripTop} x2={stripLeft - 8} y2={stripTop + stripHeight} />
            <text className={styles.geometryMeasure} x={stripLeft - 22} y={stripTop + stripHeight / 2} transform={`rotate(-90 ${stripLeft - 22} ${stripTop + stripHeight / 2})`}>
              r = {format(circle.radius)}
            </text>
            {phase >= 3 ? (
              <text className={styles.geometryMeasure} x={stripLeft + stripWidth / 2 - 44} y={stripTop + stripHeight + 22}>
                π × r = {format(circle.halfCircumference)} {circle.unit}
              </text>
            ) : null}
          </g>
        )}
      </svg>
      <div className={styles.dimensionFormula}>
        <span><b>r</b> = {format(circle.radius)} {circle.unit}</span>
        <span><b>d</b> = {format(circle.diameter)} {circle.unit}</span>
        <span><b>C</b> = 2π × r = {format(circle.circumference)} {circle.unit}</span>
      </div>
      {phase >= 4 ? (
        <div className={styles.visualConclusion}>
          <span>Diện tích hình tròn</span>
          <strong>S = π × {format(circle.radius)} × {format(circle.radius)} = {format(circle.area)} {circle.unit}²</strong>
        </div>
      ) : <p className={styles.fractionHint}>Kéo thanh tiến độ để cắt và xếp lại các hình quạt.</p>}
    </figure>
  );
}

/** Tangent right angle plus the inscribed/central angle pair on one arc. */
function CircleProofModel({ proof, progress }) {
  const phase = progress >= 1 ? 4 : Math.min(3, Math.floor(Math.max(0, progress) * 4));
  const arcStart = 20;
  const arcEnd = arcStart + proof.centralAngle;
  const pointA = polar(arcStart, DRAWN_RADIUS);
  const pointB = polar(arcEnd, DRAWN_RADIUS);
  // The inscribed vertex sits on the major arc, so it subtends the same arc AB.
  const inscribedAt = arcEnd + (360 - proof.centralAngle) / 2;
  const pointM = polar(inscribedAt, DRAWN_RADIUS);
  const tangentDirection = polar(arcStart + 90, 62);
  const tangentOpposite = polar(arcStart - 90, 62);
  const tangentStart = { x: pointA.x + (tangentDirection.x - CENTRE.x), y: pointA.y + (tangentDirection.y - CENTRE.y) };
  const tangentEnd = { x: pointA.x + (tangentOpposite.x - CENTRE.x), y: pointA.y + (tangentOpposite.y - CENTRE.y) };
  const arcPath = `M${pointA.x.toFixed(2)} ${pointA.y.toFixed(2)} `
    + `A${DRAWN_RADIUS} ${DRAWN_RADIUS} 0 ${proof.centralAngle > 180 ? 1 : 0} 0 ${pointB.x.toFixed(2)} ${pointB.y.toFixed(2)}`;
  return (
    <figure className={`${styles.panel} ${styles.circlePanel}`}>
      <figcaption className={styles.panelTitle}>Đường tròn · tiếp tuyến và góc nội tiếp</figcaption>
      <p className={styles.teachingStep}>{[
        `Bước 1 · Dựng đường tròn tâm O, bán kính r = ${format(proof.radius)} ${proof.unit}`,
        "Bước 2 · Tiếp tuyến tại A vuông góc với bán kính OA",
        `Bước 3 · Góc ở tâm ∠AOB = ${format(proof.centralAngle)}° chắn cung AB`,
        `Bước 4 · Góc nội tiếp ∠AMB cùng chắn cung AB`,
        `Bước 5 · ∠AMB = ∠AOB ÷ 2 = ${format(proof.inscribedAngle)}°`,
      ][phase]}</p>
      <svg viewBox="0 0 300 280" className={styles.circleDiagram} role="img"
        aria-label={`Đường tròn với tiếp tuyến tại A và góc nội tiếp bằng ${proof.inscribedAngle} độ`}>
        <circle className={styles.circleBody} cx={CENTRE.x} cy={CENTRE.y} r={DRAWN_RADIUS} />
        <circle className={styles.circleCentre} cx={CENTRE.x} cy={CENTRE.y} r="3.5" />
        <text className={styles.geometryLabel} x={CENTRE.x - 14} y={CENTRE.y + 14}>O</text>
        <line className={styles.circleRadius} x1={CENTRE.x} y1={CENTRE.y} x2={pointA.x} y2={pointA.y} />
        <text className={styles.geometryLabel} x={pointA.x + 6} y={pointA.y + 4}>A</text>
        {phase >= 1 ? (
          <g>
            <line className={styles.circleTangent} x1={tangentStart.x} y1={tangentStart.y} x2={tangentEnd.x} y2={tangentEnd.y} />
            <rect className={styles.rightAngleMark} x={pointA.x - 12} y={pointA.y - 12} width="10" height="10"
              transform={`rotate(${-arcStart} ${pointA.x} ${pointA.y})`} />
            <text className={styles.geometryMeasure} x={tangentStart.x - 6} y={tangentStart.y - 6}>tiếp tuyến ⟂ OA = 90°</text>
          </g>
        ) : null}
        {phase >= 2 ? (
          <g>
            <line className={styles.circleRadius} x1={CENTRE.x} y1={CENTRE.y} x2={pointB.x} y2={pointB.y} />
            <text className={styles.geometryLabel} x={pointB.x + 6} y={pointB.y - 4}>B</text>
            <path className={styles.circleArcHighlight} d={arcPath} />
            <path className={styles.angleArc} d={sectorPath(arcStart, proof.centralAngle, 30)} />
            <text className={styles.geometryMeasure} x={CENTRE.x + 12} y={CENTRE.y - 34}>∠AOB = {format(proof.centralAngle)}°</text>
          </g>
        ) : null}
        {phase >= 3 ? (
          <g>
            <line className={styles.circleChord} x1={pointM.x} y1={pointM.y} x2={pointA.x} y2={pointA.y} />
            <line className={styles.circleChord} x1={pointM.x} y1={pointM.y} x2={pointB.x} y2={pointB.y} />
            <text className={styles.geometryLabel} x={pointM.x - 16} y={pointM.y + 14}>M</text>
          </g>
        ) : null}
        {phase >= 4 ? (
          <text className={styles.geometryMeasure} x={pointM.x - 30} y={pointM.y + 30}>∠AMB = {format(proof.inscribedAngle)}°</text>
        ) : null}
      </svg>
      <div className={styles.dimensionFormula}>
        <span><b>r</b> = {format(proof.radius)} {proof.unit}</span>
        <span><b>∠OAt</b> = {format(proof.tangentAngle)}°</span>
        <span><b>∠AOB</b> = {format(proof.centralAngle)}°</span>
      </div>
      {phase >= 4 ? (
        <div className={styles.visualConclusion}>
          <span>Góc nội tiếp cùng chắn cung AB</span>
          <strong>∠AMB = {format(proof.centralAngle)}° ÷ 2 = {format(proof.inscribedAngle)}°</strong>
        </div>
      ) : <p className={styles.fractionHint}>Kéo thanh tiến độ để dựng tiếp tuyến, góc ở tâm rồi góc nội tiếp.</p>}
    </figure>
  );
}
