import { derivePolynomialModel } from "../derive/deriveCurriculum.js";
import styles from "./renderers.module.css";

function termText({ coefficient, exponent }, first = false) {
  const magnitude = Math.abs(coefficient);
  const variable = exponent === 0 ? "" : exponent === 1 ? "x" : `x${"²³⁴⁵"[exponent - 2] || `^${exponent}`}`;
  const body = `${magnitude === 1 && variable ? "" : magnitude}${variable}`;
  if (first) return `${coefficient < 0 ? "−" : ""}${body}`;
  return `${coefficient < 0 ? "−" : "+"} ${body}`;
}

function Polynomial({ terms }) {
  return <span>{terms.map((term, index) => <b key={`${term.exponent}-${index}`}>{termText(term, index === 0)} </b>)}</span>;
}

export default function AlgebraTilesRenderer({ world, progress, visualization, scene }) {
  const model = derivePolynomialModel(world, visualization?.bindings, scene?.metadata?.problem_type);
  if (!model) return <p className={styles.unavailable}>Cần các cặp hệ số–số mũ để dựng tile đại số.</p>;
  const phase = progress >= 1 ? 3 : Math.min(2, Math.floor(Math.max(0, progress) * 3));
  const displayTerms = phase >= 2 ? model.result : [...model.first, ...model.second];
  const degrees = [...new Set(displayTerms.map((term) => term.exponent))].sort((left, right) => right - left);
  return (
    <figure className={`${styles.panel} ${styles.curriculumWide}`}>
      <figcaption className={styles.panelTitle}>Tile đại số · nhìn bậc, dấu và hạng tử đồng dạng</figcaption>
      <p className={styles.teachingStep}>{[
        "Bước 1 · Mỗi hạng tử trở thành tile đúng bậc và dấu",
        "Bước 2 · Xếp các tile theo cột x², x và đơn vị",
        "Bước 3 · Ghép tile dương, triệt tiêu cặp dương–âm cùng loại",
        "Bước 4 · Đọc đa thức đã thu gọn từ các nhóm còn lại",
      ][phase]}</p>
      <div className={styles.polynomialInput}><Polynomial terms={model.first} />{model.second.length ? <><em>{model.operation === "subtract" ? "−" : "+"}</em><Polynomial terms={model.second} /></> : null}</div>
      <div className={styles.tileBoard}>
        {degrees.map((degree) => <section key={degree}><b>{degree === 2 ? "x²" : degree === 1 ? "x" : degree === 0 ? "1" : `x^${degree}`}</b><div>{displayTerms.filter((term) => term.exponent === degree).flatMap((term) => Array.from({ length: Math.min(Math.abs(term.coefficient), 16) }, (_, index) => <i key={`${term.coefficient}-${index}`} className={`${degree === 2 ? styles.tileSquare : degree === 1 ? styles.tileBar : degree === 0 ? styles.tileUnit : styles.tilePower} ${term.coefficient < 0 ? styles.tileNegative : ""}`}>{degree > 2 ? `x^${degree}` : ""}</i>))}</div></section>)}
      </div>
      <p className={styles.visualEquation}>{phase >= 3 ? <><Polynomial terms={model.result} />{model.x != null ? `; tại x = ${model.x} → ${model.evaluated}` : ""}</> : "Chỉ các tile cùng hình mới là hạng tử đồng dạng"}</p>
    </figure>
  );
}
