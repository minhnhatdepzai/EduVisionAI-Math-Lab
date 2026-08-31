import { Badge, Icon } from "../../../components/ui/index.js";
import { visualizationRegistry } from "../visualizations/registry.js";
import { deriveMotion } from "../derive/deriveScene.js";
import styles from "./mathLab.module.css";
import { normalizeProblemType } from "../schemas/mathLabSchema.js";

/**
 * What the system believes, and where each belief came from.
 *
 * Two jobs. It lets a teacher watch the world change while the scene plays,
 * which is how a wrong renderer gets caught. And it separates what the problem
 * stated from what was inferred — a vision model's guess must never arrive
 * looking like a given.
 */
const SOURCE_LABELS = {
  explicit: { label: "Đề bài cho", tone: "success" },
  inferred: { label: "Suy ra", tone: "info" },
  uncertain: { label: "Chưa chắc", tone: "warning" },
};

const DOMAIN_LABELS = {
  arithmetic: "Số học",
  number: "Số và phép tính",
  fraction: "Phân số",
  ratio: "Tỉ số",
  measurement: "Đo lường",
  time: "Thời gian",
  motion: "Chuyển động",
  algebra: "Đại số",
  geometry_2d: "Hình học phẳng",
  coordinate: "Hệ trục tọa độ",
  geometry_3d: "Hình học không gian",
  probability: "Xác suất",
  statistics: "Thống kê",
  unknown: "Chưa phân loại",
};

const PROBLEM_TYPE_LABELS = {
  addition: "Phép cộng",
  addition_basic: "Phép cộng – gộp hai phần",
  subtraction: "Phép trừ",
  subtraction_basic: "Phép trừ – tìm phần còn lại",
  multiplication_basic: "Phép nhân – các nhóm bằng nhau",
  division_basic: "Phép chia đều",
  factorial: "Giai thừa",
  part_whole: "Phần và toàn thể",
  distance_speed_time: "Quãng đường – vận tốc – thời gian",
  distance_time_direct_proportion: "Quãng đường và thời gian tỉ lệ thuận",
  two_item_discount_system: "Hệ giá niêm yết và giảm giá",
  parenthesized_addition_multiplication: "Tính trong ngoặc rồi nhân",
  parenthesized_subtraction_multiplication: "Tính trong ngoặc rồi nhân",
  right_triangle: "Tam giác vuông",
  linear_equation: "Phương trình bậc nhất",
  fractional_linear_equation: "Phương trình bậc nhất có phân số",
  absolute_value_equation: "Phương trình giá trị tuyệt đối",
  biquadratic_equation: "Phương trình trùng phương",
  radical_equation: "Phương trình chứa căn",
  rational_equation: "Phương trình hữu tỉ có ẩn ở mẫu",
  linear_equation_two_variables_graph: "Phương trình hai biến trên Oxy",
  linear_equation_three_variables_plane: "Mặt phẳng phương trình trên Oxyz",
  linear_system_two_variables_graph: "Hệ hai phương trình hai ẩn",
  linear_system_three_variables_planes: "Hệ phương trình ba ẩn trên Oxyz",
  quadratic_equation: "Phương trình bậc hai",
  quadratic_equation_vieta: "Phương trình bậc hai – hệ thức Viète",
  quadratic_function_graph: "Hàm số bậc hai và parabol",
  cubic_equation: "Phương trình bậc ba",
  quadratic_surface_three_variables: "Phương trình ba ẩn có mặt cong",
  polynomial_evaluate_reorder: "Biểu thức đại số bằng tile",
  linear_function: "Hàm số bậc nhất",
  fraction_power: "Lũy thừa phân số",
  expansion: "Khai triển biểu thức",
  volume: "Thể tích",
};

const UNIT_LABELS = {
  second: "giây",
  minute: "phút",
  hour: "giờ",
  day: "ngày",
  degree: "độ",
  liter: "lít",
  ml: "ml",
  cm2: "cm²",
  m2: "m²",
  cm3: "cm³",
  m3: "m³",
};

export default function MathLabInspector({ scene, world, progress, hidden, onToggle }) {
  if (!scene) return null;

  const values = Object.entries(world?.values || {});
  const known = values.filter(([, entry]) => entry.value != null);
  const unknown = values.filter(([, entry]) => entry.value == null);
  const motionVisualization = scene.visualizations.find((item) => item.type === "motion_path");
  const motion = deriveMotion(world, progress, motionVisualization?.bindings);
  const problemType = normalizeProblemType(scene.metadata?.problem_type);

  return (
    <aside className={styles.inspector} aria-label="Thông tin bài toán">
      <section>
        <h3>Bài toán</h3>
        <dl className={styles.facts}>
          <div><dt>Lớp</dt><dd>{scene.grade}</dd></div>
          <div><dt>Mảng kiến thức</dt><dd>{DOMAIN_LABELS[scene.kind] || scene.kind}</dd></div>
          {problemType ? (
            <div>
              <dt>Dạng bài</dt>
              <dd>{PROBLEM_TYPE_LABELS[problemType] || problemType.replaceAll("_", " ")}</dd>
            </div>
          ) : null}
        </dl>
      </section>

      <section>
        <h3>Dữ kiện đã biết</h3>
        <ul className={styles.valueList}>
          {known.map(([id, entry]) => (
            <li key={id}>
              <span>{entry.label || id}</span>
              <b>{formatValue(entry)}</b>
            </li>
          ))}
        </ul>
      </section>

      {unknown.length ? (
        <section>
          <h3>Cần tìm</h3>
          <ul className={styles.valueList}>
            {unknown.map(([id, entry]) => (
              <li key={id}>
                <span>{entry.label || id}</span>
                <b className={styles.unknownValue}>?</b>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <details className={styles.advancedDetails}>
        <summary>Tùy chọn nâng cao</summary>
        <section>
          <h3>Hình biểu diễn</h3>
          <p className={styles.sectionHint}>Hệ thống đã tự chọn cách phù hợp; giáo viên có thể ẩn để kiểm tra.</p>
          <ul className={styles.toggleList}>
            {scene.visualizations.map((visualization) => {
              const definition = visualizationRegistry.get(visualization.type);
              const on = !hidden.includes(visualization.type);
              return (
                <li key={visualization.id}>
                  <label>
                    <input
                      type="checkbox"
                      checked={on}
                      onChange={() => onToggle(visualization.type)}
                    />
                    <span>{definition?.label || visualization.type}</span>
                  </label>
                  {definition?.ready ? null : <Badge tone="warning">Chưa dựng</Badge>}
                </li>
              );
            })}
          </ul>
        </section>
      </details>

      {scene.constraints?.length ? (
        <section>
          <h3>Ràng buộc</h3>
          <ul className={styles.valueList}>
            {scene.constraints.map((constraint) => {
              const status = constraint.evidence?.status || "inferred";
              const source = SOURCE_LABELS[status] || SOURCE_LABELS.inferred;
              return (
                <li key={constraint.id}>
                  <span>{constraint.type}</span>
                  <Badge tone={source.tone}>{source.label}</Badge>
                </li>
              );
            })}
          </ul>
        </section>
      ) : null}

      {motion ? (
        <section>
          <h3>Trạng thái đang chạy</h3>
          <ul className={styles.valueList}>
            <li><span>Đã đi</span><b>{Math.round(motion.distanceTravelled)} m</b></li>
            <li><span>Thời gian trôi</span><b>{Math.round(motion.elapsedMinutes)} phút</b></li>
            {motion.currentLabel ? (
              <li><span>Đồng hồ</span><b>{motion.currentLabel}</b></li>
            ) : null}
          </ul>
          <p className={styles.sectionHint}>
            <Icon name="check" size={13} /> Mọi hình biểu diễn đọc cùng các giá trị này.
          </p>
        </section>
      ) : null}
    </aside>
  );
}

function formatValue(entry) {
  const displayedUnit = UNIT_LABELS[entry.unit] || entry.unit;
  const unit = displayedUnit && displayedUnit !== "one" && displayedUnit !== "clock" ? ` ${displayedUnit}` : "";
  return `${entry.value}${unit}`;
}
