import { MathLabValidationError, VISUALIZATION_IDS } from "../schemas/mathLabSchema.js";
import ClockRenderer from "../renderers/ClockRenderer.jsx";
import FractionRenderer from "../renderers/FractionRenderer.jsx";
import Geometry2DRenderer from "../renderers/Geometry2DRenderer.jsx";
import MotionPathRenderer from "../renderers/MotionPathRenderer.jsx";
import NumberLineRenderer from "../renderers/NumberLineRenderer.jsx";
import ObjectGroupRenderer from "../renderers/ObjectGroupRenderer.jsx";
import TimelineRenderer from "../renderers/TimelineRenderer.jsx";
import BarModelRenderer from "../renderers/BarModelRenderer.jsx";
import BalanceRenderer from "../renderers/BalanceRenderer.jsx";
import CoordinateGraphRenderer from "../renderers/CoordinateGraphRenderer.jsx";
import Geometry3DRenderer from "../renderers/Geometry3DRenderer.jsx";
import GroupingRenderer from "../renderers/GroupingRenderer.jsx";
import PowerModelRenderer from "../renderers/PowerModelRenderer.jsx";
import UnsupportedRenderer from "../renderers/UnsupportedRenderer.jsx";
import PlaceValueRenderer from "../renderers/PlaceValueRenderer.jsx";
import ColumnAlgorithmRenderer from "../renderers/ColumnAlgorithmRenderer.jsx";
import UnitScaleRenderer from "../renderers/UnitScaleRenderer.jsx";
import DataChartRenderer from "../renderers/DataChartRenderer.jsx";
import NumberCompareRenderer from "../renderers/NumberCompareRenderer.jsx";
import ProbabilitySimulatorRenderer from "../renderers/ProbabilitySimulatorRenderer.jsx";
import PercentGridRenderer from "../renderers/PercentGridRenderer.jsx";
import AlgebraTilesRenderer from "../renderers/AlgebraTilesRenderer.jsx";
import PartWholeRenderer from "../renderers/PartWholeRenderer.jsx";
import ShapePatternRenderer from "../renderers/ShapePatternRenderer.jsx";
import CircleModelRenderer from "../renderers/CircleModelRenderer.jsx";
import FactorLatticeRenderer from "../renderers/FactorLatticeRenderer.jsx";
import ExpressionTreeRenderer from "../renderers/ExpressionTreeRenderer.jsx";
import CalendarRenderer from "../renderers/CalendarRenderer.jsx";
import SolutionSetRenderer from "../renderers/SolutionSetRenderer.jsx";

/**
 * Which component draws which visualization.
 *
 * `MathSceneRenderer` looks up here and nowhere else, so a new visualization
 * arrives by registering it rather than by editing a switch. The scene
 * renderer still handles a missing future renderer explicitly, so a partial
 * registry change cannot make the lab go blank.
 */
const RENDERERS = {
  unsupported: UnsupportedRenderer,
  object_group: ObjectGroupRenderer,
  grouping: GroupingRenderer,
  bar_model: BarModelRenderer,
  number_line: NumberLineRenderer,
  fraction: FractionRenderer,
  power_model: PowerModelRenderer,
  clock: ClockRenderer,
  timeline: TimelineRenderer,
  motion_path: MotionPathRenderer,
  geometry_2d: Geometry2DRenderer,
  balance: BalanceRenderer,
  coordinate_graph: CoordinateGraphRenderer,
  geometry_3d: Geometry3DRenderer,
  place_value: PlaceValueRenderer,
  column_algorithm: ColumnAlgorithmRenderer,
  unit_scale: UnitScaleRenderer,
  data_chart: DataChartRenderer,
  number_compare: NumberCompareRenderer,
  probability_simulator: ProbabilitySimulatorRenderer,
  percent_grid: PercentGridRenderer,
  algebra_tiles: AlgebraTilesRenderer,
  part_whole: PartWholeRenderer,
  shape_pattern: ShapePatternRenderer,
  circle_model: CircleModelRenderer,
  factor_lattice: FactorLatticeRenderer,
  expression_tree: ExpressionTreeRenderer,
  calendar: CalendarRenderer,
  solution_set: SolutionSetRenderer,
};

/** Vietnamese names, for the inspector and the teacher's own overrides. */
const LABELS = {
  unsupported: "Chưa có mô hình chính xác",
  object_group: "Nhóm đồ vật",
  number_line: "Tia số",
  grouping: "Gộp nhóm",
  bar_model: "Sơ đồ đoạn thẳng",
  fraction: "Mô hình phân số",
  power_model: "Lũy thừa phân số",
  clock: "Đồng hồ",
  timeline: "Dòng thời gian",
  motion_path: "Hành trình",
  balance: "Cân bằng phương trình",
  geometry_2d: "Hình học phẳng",
  coordinate_graph: "Đồ thị toạ độ",
  geometry_3d: "Hình học không gian",
  place_value: "Giá trị hàng và khối cơ số 10",
  column_algorithm: "Đặt tính nhớ – mượn",
  unit_scale: "Thang đổi đơn vị",
  data_chart: "Biểu đồ dữ liệu",
  number_compare: "So sánh và làm tròn trên tia số",
  probability_simulator: "Mô phỏng xác suất thực nghiệm",
  percent_grid: "Lưới 100 ô phần trăm",
  algebra_tiles: "Tile đa thức",
  part_whole: "Sơ đồ phần–toàn bộ",
  shape_pattern: "Overlay đếm và quy luật hình",
  circle_model: "Hình tròn và diện tích",
  expression_tree: "Cây biểu thức",
  calendar: "Lịch và khoảng thời gian",
  factor_lattice: "Lưới bội và ước chung",
  solution_set: "Tập nghiệm trên trục số",
};

const definitions = VISUALIZATION_IDS.map((id) => Object.freeze({
  id,
  label: LABELS[id] || id,
  renderer: RENDERERS[id] || null,
  ready: Boolean(RENDERERS[id]),
  phase: 3,
}));

export const visualizationRegistry = new Map(definitions.map((definition) => [definition.id, definition]));

export function visualizationDefinition(id) {
  const definition = visualizationRegistry.get(id);
  if (!definition) throw new MathLabValidationError(`unregistered visualization ${id}`, "visualization");
  return definition;
}

/** The types that can actually draw something today. */
export function readyVisualizations() {
  return definitions.filter((definition) => definition.ready);
}

export function validateVisualizationDescriptor(descriptor) {
  if (!descriptor || typeof descriptor !== "object" || Array.isArray(descriptor)) {
    throw new MathLabValidationError("descriptor must be an object", "visualization");
  }
  visualizationDefinition(descriptor.type);
  if (typeof descriptor.id !== "string" || !descriptor.id) {
    throw new MathLabValidationError("descriptor id is required", "visualization.id");
  }
  return structuredClone(descriptor);
}
