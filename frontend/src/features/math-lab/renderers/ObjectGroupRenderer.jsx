import { deriveObjectGroup } from "../derive/deriveScene.js";
import styles from "./renderers.module.css";

/**
 * Counters, for the years where a number is still a quantity of things.
 *
 * Addition moves the second group across one counter at a time; subtraction
 * lifts them away. The child sees the operation happen to objects, which is
 * the step before it means anything as a symbol.
 */
export default function ObjectGroupRenderer({ world, progress, scene, visualization }) {
  const group = deriveObjectGroup(
    world,
    progress,
    scene?.metadata?.problem_type,
    visualization?.bindings,
  );
  if (!group) {
    return <p className={styles.unavailable}>Cần hai nhóm để dựng mô hình đồ vật.</p>;
  }

  const first = Array.from({ length: group.left }, (_, index) => index);
  const second = Array.from({ length: group.right }, (_, index) => index);
  const glyph = objectGlyph(scene?.metadata?.source_text);

  return (
    <figure className={styles.panel}>
      <figcaption className={styles.panelTitle}>
        {group.subtract ? "Bớt đi" : "Gộp nhóm"}
      </figcaption>

      <div className={styles.groups}>
        <span className={styles.group}>
          {first.map((index) => (
            <i
              key={index}
              className={`${group.subtract && index >= group.left - group.moved
                ? styles.counterTaken
                : styles.counter} ${glyph ? styles.counterGlyph : ""}`}
              aria-hidden="true"
            >{glyph}</i>
          ))}
        </span>

        {group.subtract ? null : (
          <>
            <b className={styles.operator}>+</b>
            <span className={styles.group}>
              {second.map((index) => (
                <i
                  key={index}
                  className={`${index < group.moved ? styles.counterMoved : styles.counterSecond} ${glyph ? styles.counterGlyph : ""}`}
                  aria-hidden="true"
                >{glyph}</i>
              ))}
            </span>
          </>
        )}
      </div>

      <p className={styles.groupTotal}>
        {group.left} {group.subtract ? "−" : "+"} {group.right} ={" "}
        <b>{group.merged ? group.total : "?"}</b>
      </p>
    </figure>
  );
}

function objectGlyph(sourceText = "") {
  if (/xe\s+t(?:ả|a)i|xe\s+(?:rời|roi)\s+bãi/i.test(sourceText)) return "🚚";
  if (/quả\s+táo|qua\s+tao/i.test(sourceText)) return "🍎";
  if (/kẹo|keo/i.test(sourceText)) return "🍬";
  return "";
}
