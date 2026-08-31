import { deriveFactorLattice } from "../derive/deriveCoverage.js";
import styles from "./renderers.module.css";

/**
 * Two multiple strips over one lattice.
 *
 * A single division cannot show why a number is a common multiple. Marking
 * both sets on the same grid makes the intersection -- and the first cell in
 * it -- something the learner reads off rather than takes on trust. Colour is
 * always reinforced by a dot/ring marker so the sets stay separable without it.
 */
export default function FactorLatticeRenderer({ world, progress, visualization }) {
  const lattice = deriveFactorLattice(world, visualization?.bindings);
  if (!lattice) {
    return <p className={styles.unavailable}>Cần hai số nguyên dương để dựng lưới bội chung.</p>;
  }
  const phase = progress >= 1 ? 3 : Math.min(2, Math.floor(Math.max(0, progress) * 3));
  const showFirst = phase >= 0;
  const showSecond = phase >= 1;
  const showCommon = phase >= 2;
  const showLeast = phase >= 3;
  return (
    <figure className={`${styles.panel} ${styles.latticePanel}`}>
      <figcaption className={styles.panelTitle}>Lưới bội của {lattice.first} và {lattice.second}</figcaption>
      <p className={styles.teachingStep}>{[
        `Bước 1 · Tô các ô là bội của ${lattice.first}`,
        `Bước 2 · Đánh dấu vòng tròn các ô là bội của ${lattice.second}`,
        "Bước 3 · Ô vừa được tô vừa có vòng tròn là bội chung",
        `Bước 4 · Bội chung nhỏ nhất là ${lattice.leastCommonMultiple}`,
      ][phase]}</p>
      <ol className={styles.latticeGrid} style={{ "--lattice-columns": lattice.columns }}>
        {lattice.cells.map((cell) => {
          const isCommon = cell.firstMultiple && cell.secondMultiple;
          const classes = [styles.latticeCell];
          if (showFirst && cell.firstMultiple) classes.push(styles.latticeFirst);
          if (showSecond && cell.secondMultiple) classes.push(styles.latticeSecond);
          if (showCommon && isCommon) classes.push(styles.latticeCommon);
          if (showLeast && cell.value === lattice.leastCommonMultiple) classes.push(styles.latticeLeast);
          return (
            <li key={cell.value} className={classes.join(" ")}>
              <span>{cell.value}</span>
              {showFirst && cell.firstMultiple ? <i className={styles.latticeMarkFirst} aria-hidden="true">•</i> : null}
              {showSecond && cell.secondMultiple ? <i className={styles.latticeMarkSecond} aria-hidden="true">○</i> : null}
            </li>
          );
        })}
      </ol>
      <div className={styles.latticeLegend}>
        <span><i className={styles.latticeMarkFirst} aria-hidden="true">•</i> Bội của {lattice.first}</span>
        <span><i className={styles.latticeMarkSecond} aria-hidden="true">○</i> Bội của {lattice.second}</span>
        <span>Ước chung lớn nhất: <b>{lattice.greatestCommonDivisor}</b></span>
      </div>
      {showLeast ? (
        <div className={styles.visualConclusion}>
          <span>Bội chung của {lattice.first} và {lattice.second} trong lưới</span>
          <strong>{lattice.commonMultiples.join("; ")}</strong>
          <small>Bội chung nhỏ nhất: BCNN({lattice.first}; {lattice.second}) = {lattice.leastCommonMultiple}</small>
        </div>
      ) : <p className={styles.fractionHint}>Kéo thanh tiến độ để tô lần lượt hai tập bội rồi tìm phần giao.</p>}
    </figure>
  );
}
