import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import MathSceneRenderer from "./renderers/MathSceneRenderer.jsx";
import MathLabInspector from "./components/MathLabInspector.jsx";
import { visualizationRegistry } from "./visualizations/registry.js";
import { MATH_LAB_PRESETS, presetById } from "./fixtures/presets.js";
import { planLocally } from "./fixtures/localPlan.js";
import { createMathWorldState, mathWorldReducer } from "./state/mathWorldState.js";
import {
  deriveFraction,
  deriveFractionComparison,
  deriveFractionOperation,
  deriveFractionPower,
  deriveAveragePerPerson,
  deriveBinomialSquare,
  deriveCoordinateGraph,
  deriveDirectProportionDistanceTime,
  deriveGeometry3d,
  derivePlane3d,
  deriveLinearSystem,
  deriveLinearSystem3d,
  planeSamplePoints,
  deriveGrouping,
  deriveParenthesizedMultiplication,
  deriveLinearEquation,
  deriveRatioShare,
  deriveSequentialRemainderQuantity,
  deriveSequentialRemainderRatio,
  deriveVariablePeopleWorkRate,
  deriveGeometry2d,
  deriveMotion,
  deriveNumberLine,
  deriveObjectGroup,
  formatClock,
  parseClock,
} from "./derive/deriveScene.js";
import {
  deriveArithmeticMean,
  deriveCalendarDuration,
  deriveCentroidProof,
  deriveCircleArea,
  deriveCircleProof,
  deriveFactorLattice,
  deriveMapScale,
  deriveDecimalScaling,
  deriveExpressionTree,
  deriveFactorial,
  deriveLongDivision,
  deriveLongMultiplication,
  deriveExpressionModel,
  deriveMultiStepArithmetic,
  derivePercentWaterfall,
  deriveRectangleEquation,
  deriveTriangleSimilarity,
  deriveProportionalDifference,
  deriveQuadraticSurface,
  deriveRightTriangle,
  deriveSegmentedMotion,
  deriveSolutionSet,
  deriveTrigonometricGeometry,
  deriveTwoItemDiscountSystem,
} from "./derive/deriveCoverage.js";
import {
  deriveColumnAlgorithm,
  deriveCubicGraph,
  deriveDataChart,
  derivePlaceValue,
  deriveQuadraticGraph,
  deriveNumberComparison,
  deriveProbabilityExperiment,
  derivePercentModel,
  deriveReverseDiscountModel,
  deriveSolidRevolution,
  derivePartWhole,
  deriveUnitScale,
} from "./derive/deriveCurriculum.js";

function sceneFor(id) {
  return planLocally(presetById(id));
}

describe("visualization registry", () => {
  it("resolves a renderer for every visualization the backend can select", () => {
    for (const id of [
      "unsupported", "object_group", "number_line", "grouping", "bar_model", "fraction", "power_model", "clock",
      "timeline", "motion_path", "balance", "geometry_2d", "coordinate_graph", "geometry_3d",
      "place_value", "column_algorithm", "unit_scale", "data_chart",
      "number_compare",
      "probability_simulator",
      "percent_grid",
      "algebra_tiles", "part_whole",
      "shape_pattern",
      "circle_model", "factor_lattice", "expression_tree", "calendar", "solution_set",
    ]) {
      expect(visualizationRegistry.get(id)?.renderer, id).toBeTruthy();
      expect(visualizationRegistry.get(id)?.ready, id).toBe(true);
    }
  });
});

describe("curriculum exact renderers", () => {
  it("solves and visualizes the two-book discount system without trusting the printed claim", () => {
    const world = { values: {
      list: { value: 270000, unit: "one", label: "Tổng giá niêm yết (đồng)" },
      paid: { value: 228000, unit: "one", label: "Tổng tiền đã trả (đồng)" },
      mathDiscount: { value: 10, unit: "one", label: "Giảm giá sách Toán (%)" },
      literatureDiscount: { value: 20, unit: "one", label: "Giảm giá sách Ngữ Văn (%)" },
      x: { value: null, unit: "one", label: "Giá sách Toán (x)" },
      y: { value: null, unit: "one", label: "Giá sách Ngữ Văn (y)" },
    } };
    const bindings = {
      total: ["list", "paid"],
      probability: ["mathDiscount", "literatureDiscount"],
      variable: ["x", "y"],
    };
    const relations = [{
      type: "two_item_discount_system",
      parameters: {
        first_label: "Sách Toán",
        second_label: "Sách Ngữ Văn",
        first_symbol: "x",
        second_symbol: "y",
        claimed_first: 150000,
        claimed_second: 120000,
      },
    }];
    const model = deriveTwoItemDiscountSystem(world, bindings, relations);

    expect(model).toMatchObject({
      firstPrice: 120000,
      secondPrice: 150000,
      paidFirst: 108000,
      paidSecond: 120000,
      claimCorrect: false,
    });

    const scene = {
      id: "two-book-discount",
      grade: 9,
      kind: "algebra",
      metadata: { problem_type: "two_item_discount_system", relations },
      world,
      visualizations: [{ id: "discount", type: "percent_grid", bindings, options: {} }],
    };
    const html = renderToStaticMarkup(
      <MathSceneRenderer scene={scene} world={world} progress={1} />,
    );

    expect(html).toContain("Hai quyển sách");
    expect(html).toContain("0,9x + 0,8y = 228.000");
    expect(html).toContain("Sách Toán: 120.000đ");
    expect(html).toContain("Sách Ngữ Văn: 150.000đ");
    expect(html).toContain("108.000đ + 120.000đ = 228.000đ");
    expect(html).toContain("Khẳng định d) sai");
  });

  it("decomposes a decimal into visible place values", () => {
    const world = { values: { number: { value: 305.07, unit: "one", label: "Số đã cho" } } };
    const model = derivePlaceValue(world, { quantities: ["number"] });
    expect(model.columns.map((item) => item.digit)).toEqual([3, 0, 5, 0, 7]);
    expect(model.expanded).toEqual([300, 5, 0.07]);
  });

  it("keeps carries and borrows attached to their columns", () => {
    const addition = deriveColumnAlgorithm(
      { values: { left: { value: 278 }, right: { value: 145 } } },
      { quantities: ["left", "right"] },
      "column_arithmetic_regrouping_addition",
    );
    expect(addition.result).toBe(423);
    expect(addition.steps.some((item) => item.regroup === 1)).toBe(true);
    const subtraction = deriveColumnAlgorithm(
      { values: { left: { value: 402 }, right: { value: 187 } } },
      { quantities: ["left", "right"] },
      "column_arithmetic_regrouping_subtraction",
    );
    expect(subtraction.result).toBe(215);
    expect(subtraction.steps.filter((item) => item.regroup === 1).length).toBeGreaterThanOrEqual(2);
  });

  it("converts units through one shared base quantity", () => {
    const world = { values: {
      source: { value: 1.25, unit: "m" },
      target: { value: null, unit: "cm" },
    } };
    expect(deriveUnitScale(world, { quantities: ["source"], unknowns: ["target"] }))
      .toMatchObject({ factor: 100, result: 125, sourceUnit: "m", targetUnit: "cm" });
  });

  it("derives chart totals and quadratic invariants without model arithmetic", () => {
    const chart = deriveDataChart(
      { values: { a: { value: 3, label: "Đỏ" }, b: { value: 5, label: "Xanh" } } },
      { frequency: ["a", "b"] },
    );
    expect(chart).toMatchObject({ total: 8, winner: { label: "Xanh", value: 5 } });
    const quadratic = deriveQuadraticGraph(
      { values: { a: { value: 1 }, b: { value: -4 }, c: { value: 3 } } },
      { coefficient: ["a", "b"], constant: ["c"] },
    );
    expect(quadratic.vertexX).toBe(2);
    expect(quadratic.vertexY).toBe(-1);
    expect(quadratic.roots).toEqual([1, 3]);
  });

  it("solves a plain quadratic equation instead of showing unsupported", () => {
    const world = { values: {
      a: { value: 6, unit: "one", label: "Hệ số a của x²" },
      b: { value: -5, unit: "one", label: "Hệ số b của x" },
      c: { value: -1, unit: "one", label: "Hệ số tự do c" },
      roots: { value: null, unit: "one", label: "Nghiệm của x" },
    } };
    const scene = {
      id: "quadratic-equation-regression",
      metadata: { problem_type: "quadratic_equation" },
      world,
      visualizations: [{
        id: "quadratic",
        type: "coordinate_graph",
        bindings: { coefficient: ["a", "b"], constant: ["c"], unknown_result: ["roots"] },
        options: {},
      }],
    };
    const html = renderToStaticMarkup(
      <MathSceneRenderer scene={scene} world={world} progress={1} />,
    );

    expect(html).toContain("Parabol · bảng giá trị, đỉnh và nghiệm");
    expect(html).toContain("y = 6x² − 5x − 1");
    expect(html).toContain("= 49");
    expect(html).toContain("x₁ = −1/6; x₂ = 1");
    expect(html).toContain('text-anchor="end"');
    expect(html).toContain('text-anchor="start"');
    expect(html).toContain("x₁=−1/6");
    expect(html).toContain("x₂=1");
    expect(html).toContain("I(0.42; -2.04)");
    expect(html).not.toContain("unsupported");

    const irrationalWorld = { values: {
      ...world.values,
      a: { ...world.values.a, value: 1 },
      b: { ...world.values.b, value: 0 },
      c: { ...world.values.c, value: -2 },
    } };
    const irrationalHtml = renderToStaticMarkup(
      <MathSceneRenderer scene={{ ...scene, world: irrationalWorld }} world={irrationalWorld} progress={1} />,
    );
    expect(irrationalHtml).toContain("x₁ ≈ −1,41; x₂ ≈ 1,41");

    const scrubbedHtml = renderToStaticMarkup(
      <MathSceneRenderer scene={scene} world={world} progress={0.82} />,
    );
    expect(scrubbedHtml).toContain('clip-path="url(#quadratic-clip)"');
    expect(scrubbedHtml).toContain("Nghiệm = giao với Ox");
  });

  it("solves and visualizes every real root of a cubic equation", () => {
    const world = { values: {
      a: { value: 1, unit: "one", label: "Hệ số a của x³" },
      b: { value: -6, unit: "one", label: "Hệ số b của x²" },
      c: { value: 11, unit: "one", label: "Hệ số c của x" },
      d: { value: -6, unit: "one", label: "Hệ số tự do d" },
      roots: { value: null, unit: "one", label: "Các nghiệm thực của x" },
    } };
    const bindings = { coefficient: ["a", "b", "c"], constant: ["d"], unknown_result: ["roots"] };
    const cubic = deriveCubicGraph(world, bindings);
    cubic.roots.forEach((root, index) => expect(root).toBeCloseTo(index + 1, 10));
    cubic.roots.forEach((root) => expect(cubic.evaluate(root)).toBeCloseTo(0, 10));

    const scene = {
      id: "cubic-equation-regression",
      metadata: { problem_type: "cubic_equation" },
      world,
      visualizations: [{ id: "cubic", type: "coordinate_graph", bindings, options: {} }],
    };
    const html = renderToStaticMarkup(
      <MathSceneRenderer scene={scene} world={world} progress={0.82} />,
    );
    expect(html).toContain("Phương trình bậc ba · nghiệm là giao điểm với trục Ox");
    expect(html).toContain("x³ − 6x² + 11x − 6 = 0");
    expect(html).toContain("x₁ = 1; x₂ = 2; x₃ = 3");
    expect(html).toContain('clip-path="url(#cubic-clip)"');
    expect(html).toContain("P(1) = 0; P(2) = 0; P(3) = 0");
    expect(html).not.toContain("unsupported");
  });

  it("never routes a spaced cubic provider label to the straight-line renderer", () => {
    const world = { values: {
      a: { value: 6, unit: "one", label: "Hệ số a của x³" },
      b: { value: 4, unit: "one", label: "Hệ số b của x²" },
      c: { value: -5, unit: "one", label: "Hệ số c của x" },
      d: { value: -1, unit: "one", label: "Hệ số tự do d" },
      roots: { value: null, unit: "one", label: "Các nghiệm thực của x" },
    } };
    const bindings = { coefficient: ["a", "b", "c"], constant: ["d"], unknown_result: ["roots"] };
    const scene = {
      id: "typed-cubic-spacing-regression",
      metadata: { problem_type: "cubic equation" },
      world,
      visualizations: [{ id: "cubic", type: "coordinate_graph", bindings, options: {} }],
    };
    const graph = deriveCubicGraph(world, bindings);
    expect(graph.roots).toHaveLength(3);
    expect(graph.roots[0]).toBeCloseTo(-1.23292464, 7);
    expect(graph.roots[1]).toBeCloseTo(-0.18092053, 7);
    expect(graph.roots[2]).toBeCloseTo(0.7471785, 7);

    const html = renderToStaticMarkup(
      <MathSceneRenderer scene={scene} world={world} progress={1} />,
    );
    expect(html).toContain("6x³ + 4x² − 5x − 1 = 0");
    expect(html).toContain("Cách đọc để dựng hình · không thay đổi đề gốc");
    expect(html).toContain("y = 6x³ + 4x² − 5x − 1");
    expect(html).toContain("Xấp xỉ:");
    expect(html).toContain("P(x₁) ≈ 0 với x₁ ≈ −1,23");
    expect(html).not.toContain("P(−1,23) = 0");
    expect(html).toContain('clip-path="url(#cubic-clip)"');
    expect(html).not.toContain("y = 6x − 1");
    expect(html).not.toContain("Hệ số góc");
  });

  it("places many numbers and rounds by visible distance", () => {
    const ordering = deriveNumberComparison(
      { values: { a: { value: 42 }, b: { value: 17 }, c: { value: 31 } } },
      { quantities: ["a", "b", "c"] },
      "number_ordering_rounding_ordering",
    );
    expect(ordering.sorted.map((item) => item.value)).toEqual([17, 31, 42]);
    const rounding = deriveNumberComparison(
      { values: { value: { value: 167 }, scale: { value: 10 } } },
      { quantities: ["value", "scale"], constant: ["scale"] },
      "number_ordering_rounding_rounding",
    );
    expect(rounding).toMatchObject({ lower: 160, midpoint: 165, upper: 170, result: 170 });
  });

  it("replays an experimental probability with the exact frequency invariant", () => {
    const experiment = deriveProbabilityExperiment(
      { values: { success: { value: 7 }, total: { value: 20 } } },
      { frequency: ["success"], count: ["total"] },
    );
    expect(experiment.outcomes).toHaveLength(20);
    expect(experiment.outcomes.filter(Boolean)).toHaveLength(7);
    expect(experiment.probability).toBe(0.35);
  });

  it("keeps percent and solids derived from one deterministic world", () => {
    expect(derivePercentModel(
      { values: { part: { value: 30 }, whole: { value: 120 } } },
      { count_change: ["part"], count_initial: ["whole"] },
    )).toMatchObject({ part: 30, whole: 120, percent: 25, filledCells: 25 });
    expect(deriveSolidRevolution(
      { values: { radius: { value: 3, unit: "cm" }, height: { value: 5, unit: "cm" } } },
      { radius: ["radius"], height: ["height"] },
      "cylinder_volume",
    ).volume).toBeCloseTo(45 * Math.PI);
  });

  it("derives every checkout amount before reversing the third discount", () => {
    const model = deriveReverseDiscountModel(
      { values: {
        price1: { value: 125000 },
        price2: { value: 300000 },
        discount1: { value: 30 },
        discount2: { value: 15 },
        discount3: { value: 12.5 },
        total: { value: 692500 },
      } },
      {
        count_initial: ["price1", "price2"],
        probability: ["discount1", "discount2", "discount3"],
        total: ["total"],
      },
    );
    expect(model).toMatchObject({
      paidFirst: 87500,
      paidSecond: 255000,
      knownPaid: 342500,
      paidThird: 350000,
      thirdPaidPercent: 87.5,
      originalThird: 400000,
    });
  });

  it("renders the reverse-discount receipt and the visible 87.5 percent bar", () => {
    const base = sceneFor("grade2_subtraction");
    const world = { values: {
      price1: { value: 125000 }, price2: { value: 300000 },
      discount1: { value: 30 }, discount2: { value: 15 }, discount3: { value: 12.5 },
      total: { value: 692500 }, result: { value: null },
    } };
    const scene = {
      ...base,
      grade: 7,
      kind: "ratio",
      world,
      metadata: { problem_type: "multi_item_reverse_discount" },
      visualizations: [{
        id: "visual_percent_grid",
        type: "percent_grid",
        bindings: {
          count_initial: ["price1", "price2"],
          probability: ["discount1", "discount2", "discount3"],
          total: ["total"],
          unknown_result: ["result"],
        },
        options: {},
      }],
    };
    const html = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={1} />);
    expect(html).toContain("Hóa đơn giảm giá");
    expect(html).toContain("87,5%");
    expect(html).toContain("350.000đ");
    expect(html).toContain("400.000đ");
  });

  it("derives a missing part without leaking it into known quantities", () => {
    expect(derivePartWhole(
      { values: { first: { value: 7 }, total: { value: 12 }, missing: { value: null } } },
      { count_initial: ["first"], total: ["total"], unknown_count_change: ["missing"] },
    )).toMatchObject({ first: 7, second: 5, total: 12, missing: "second" });
  });

  it("renders an honest unsupported card and all new visual layers", () => {
    const base = sceneFor("grade2_subtraction");
    const unsupported = { ...base, metadata: { problem_type: "circle_tangent_cyclic_proof" }, visualizations: [{ id: "visual_unsupported", type: "unsupported", options: { reason: "No exact renderer" }, bindings: {} }] };
    const unsupportedMarkup = renderToStaticMarkup(<MathSceneRenderer scene={unsupported} world={base.world} progress={1} />);
    expect(unsupportedMarkup).toContain("Chưa đủ dữ kiện để dựng hình cho đề này");
    // The abstention card reaches a teacher, so it must stay free of engine
    // vocabulary and must not print the internal family slug.
    for (const internal of ["renderer", "schema", "semantic", "payload", "backend", "circle_tangent_cyclic_proof"]) {
      expect(unsupportedMarkup.toLowerCase()).not.toContain(internal);
    }

    const cases = [
      ["place_value", { values: { number: { value: 305, unit: "one" } } }, { quantities: ["number"] }, "Giá trị hàng"],
      ["column_algorithm", { values: { a: { value: 278 }, b: { value: 145 } } }, { quantities: ["a", "b"] }, "Đặt tính"],
      ["unit_scale", { values: { a: { value: 1.25, unit: "m" }, result: { value: null, unit: "cm" } } }, { quantities: ["a"], unknowns: ["result"] }, "Thang đổi"],
      ["data_chart", { values: { a: { value: 3, label: "Đỏ" }, b: { value: 5, label: "Xanh" } } }, { frequency: ["a", "b"] }, "Biểu đồ"],
    ];
    for (const [type, world, bindings, expected] of cases) {
      const scene = { ...base, world, metadata: { problem_type: type }, visualizations: [{ id: `visual_${type}`, type, bindings, options: {} }] };
      expect(renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={1} />)).toContain(expected);
    }
  });
});

describe("MathSceneRenderer", () => {
  it("draws every visualization a valid scene asks for", () => {
    const scene = sceneFor("grade5_motion");
    const state = createMathWorldState(scene);
    const html = renderToStaticMarkup(
      <MathSceneRenderer scene={scene} world={state.world} progress={0} />,
    );
    expect(html).toContain("Hành trình");
    expect(html).toContain("Đồng hồ");
    expect(html).toContain("Dòng thời gian");
  });

  it("says which visualization is unsupported instead of going blank", () => {
    const scene = { ...sceneFor("grade3_fraction") };
    scene.visualizations = [{ id: "visual_future", type: "future_visual", bindings: {}, options: {} }];
    const html = renderToStaticMarkup(
      <MathSceneRenderer scene={scene} world={{ values: {} }} progress={0} />,
    );
    expect(html).toContain("Chưa hỗ trợ hình biểu diễn");
  });

  it("reports a missing scene rather than throwing", () => {
    expect(renderToStaticMarkup(<MathSceneRenderer scene={null} world={null} progress={0} />))
      .toContain("Chưa có cảnh");
  });

  it("lets a teacher hide a visualization the system suggested", () => {
    const scene = sceneFor("grade5_motion");
    const state = createMathWorldState(scene);
    const html = renderToStaticMarkup(
      <MathSceneRenderer scene={scene} world={state.world} progress={0} hidden={["timeline"]} />,
    );
    expect(html).toContain("Hành trình");
    expect(html).not.toContain("Dòng thời gian");
  });
});

describe("MathLabInspector", () => {
  it("shows the mathematical domain and problem type instead of an internal model id", () => {
    const scene = sceneFor("grade5_motion");
    const state = createMathWorldState(scene);
    const html = renderToStaticMarkup(
      <MathLabInspector
        scene={scene}
        world={state.world}
        progress={0}
        hidden={[]}
        onToggle={() => {}}
      />,
    );
    expect(html).toContain("Chuyển động");
    expect(html).toContain("Quãng đường – vận tốc – thời gian");
    expect(html).not.toContain("lan_to_school");
  });
});

describe("every preset plans into a valid scene", () => {
  it.each(MATH_LAB_PRESETS.map((preset) => [preset.id]))("%s", (id) => {
    const scene = sceneFor(id);
    expect(scene.visualizations.length).toBeGreaterThan(0);
    expect(() => createMathWorldState(scene)).not.toThrow();
  });
});

describe("motion", () => {
  const world = createMathWorldState(sceneFor("grade5_motion")).world;

  it("computes the journey from distance and speed, never from a written answer", () => {
    // 1.2 km at 4 km/h is 18 minutes, and 06:45 + 18 is 07:03.
    const start = deriveMotion(world, 0);
    expect(Math.round(start.totalMinutes)).toBe(18);
    expect(start.startLabel).toBe("06:45");
    expect(start.arrivalLabel).toBe("07:03");
  });

  it("moves the walker and the clock off the same progress", () => {
    const third = deriveMotion(world, 1 / 3);
    expect(Math.round(third.distanceTravelled)).toBe(400);
    expect(Math.round(third.elapsedMinutes)).toBe(6);
    expect(third.currentLabel).toBe("06:51");

    const twoThirds = deriveMotion(world, 2 / 3);
    expect(twoThirds.currentLabel).toBe("06:57");
    expect(deriveMotion(world, 1).currentLabel).toBe("07:03");
  });

  it("clamps a progress outside the journey", () => {
    expect(deriveMotion(world, -5).distanceTravelled).toBe(0);
    expect(deriveMotion(world, 9).progress).toBe(1);
  });

  it("returns nothing rather than dividing by a zero speed", () => {
    expect(deriveMotion({ values: { distance: { value: 1 } } }, 0.5)).toBeNull();
  });
});

describe("clock arithmetic", () => {
  it("reads and writes a wall clock", () => {
    expect(parseClock("06:45")).toBe(405);
    expect(formatClock(423)).toBe("07:03");
  });

  it("refuses nonsense instead of guessing", () => {
    expect(parseClock("25:00")).toBeNull();
    expect(parseClock("6h45")).toBeNull();
    expect(parseClock(null)).toBeNull();
  });

  it("wraps past midnight", () => {
    expect(formatClock(1445)).toBe("00:05");
  });
});

describe("geometry", () => {
  it("uses semantic length/width bindings to represent a rectangle", () => {
    const world = {
      values: {
        q1: { value: 12, unit: "m" },
        q2: { value: 7, unit: "m" },
      },
    };
    const rectangle = deriveGeometry2d(world, { length: ["q1"], width: ["q2"] });

    expect(rectangle).toMatchObject({ kind: "rectangle", a: 12, b: 7, unit: "m" });
  });

  it("splits an explicit angle into two equal visible angles", () => {
    const world = { values: {
      wholeAngle: { value: 80, unit: "degree", label: "Góc xOy" },
      result: { value: null, unit: "degree", label: "Góc xOt" },
    } };
    const shape = deriveGeometry2d(world, { angle: ["wholeAngle"], unknown_result: ["result"] }, "angle_bisector");
    expect(shape).toMatchObject({ kind: "angle_bisector", totalAngle: 80, halfAngle: 40, unit: "degree" });

    const base = sceneFor("grade6_triangle");
    const scene = {
      ...base,
      metadata: { ...base.metadata, problem_type: "angle_bisector" },
      visualizations: [{ id: "visual_angle", type: "geometry_2d", bindings: { angle: ["wholeAngle"], unknown_result: ["result"] }, options: {} }],
    };
    const html = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={1} />);
    expect(html).toContain("Tia phân giác");
    expect(html).toContain("∠xOt = ∠tOy = 80° ÷ 2 = 40°");
  });
});

describe("fraction", () => {
  it("derives and renders (-2/5)^3 with an odd negative sign and choice C", () => {
    const world = {
      revision: 0,
      values: {
        numerator: { value: -2, unit: "one", label: "Tử số" },
        denominator: { value: 5, unit: "one", label: "Mẫu số" },
        exponent: { value: 3, unit: "one", label: "Số mũ" },
        result: { value: null, unit: "one", label: "Kết quả" },
      },
    };
    const bindings = {
      numerator: ["numerator"], denominator: ["denominator"], exponent: ["exponent"],
    };
    const choices = ["A. 8/125", "B. 4/25", "C. -8/125", "D. 8/15"];
    expect(deriveFractionPower(world, bindings, choices)).toMatchObject({
      sign: -1,
      numeratorMagnitude: 8,
      denominatorMagnitude: 125,
      resultNumerator: -8,
      resultDenominator: 125,
      choiceLabel: "C",
    });

    const scene = {
      schema_version: "1.0",
      id: "scene_fraction_power",
      kind: "algebra",
      grade: 7,
      semantic_model_id: "fraction_power",
      world,
      objects: [],
      visualizations: [{ id: "visual_power", type: "power_model", bindings }],
      constraints: [],
      steps: [],
      actions: [],
      metadata: { problem_type: "fraction_power", choices },
    };
    const html = renderToStaticMarkup(
      <MathSceneRenderer scene={scene} world={world} progress={1} />,
    );
    expect(html).toContain("Lũy thừa phân số");
    expect(html).toContain("5 nhân 5 nhân 5");
    expect(html).toContain("Chọn C");
  });

  it("keeps the shaded amount when the bar is recut", () => {
    // 1/2 rewritten as 2/4 is the same amount in smaller pieces.
    const world = createMathWorldState(sceneFor("grade4_fraction_add")).world;
    const before = deriveFraction(world, 0);
    const after = deriveFraction(world, 1);
    expect(before.parts).toBe(2);
    expect(before.shaded).toBe(1);
    expect(after.parts).toBe(4);
    expect(after.shaded).toBe(2);
    expect(after.shaded / after.parts).toBe(before.shaded / before.parts);
  });

  it("leaves a plain fraction alone", () => {
    const world = createMathWorldState(sceneFor("grade3_fraction")).world;
    const fraction = deriveFraction(world, 1);
    expect(fraction.rewriting).toBe(false);
    expect(fraction.parts).toBe(4);
    expect(fraction.shaded).toBe(3);
  });

  it("finds a common partition and carries both colours into the sum", () => {
    const world = {
      values: {
        n1: { value: 1 }, d1: { value: 2 }, n2: { value: 1 }, d2: { value: 3 },
      },
    };
    const bindings = {
      numerator: ["n1"], denominator: ["d1"],
      addend_numerator: ["n2"], addend_denominator: ["d2"],
    };
    const operation = deriveFractionOperation(world, bindings, "fraction_addition");
    expect(operation).toMatchObject({
      commonDenominator: 6,
      leftCommon: 3,
      rightCommon: 2,
      resultNumerator: 5,
      resultDenominator: 6,
    });
  });

  it("renders multiplication as the intersection of two fraction layers", () => {
    const scene = sceneFor("grade5_fraction_multiply");
    const html = renderToStaticMarkup(
      <MathSceneRenderer scene={scene} world={scene.world} progress={1} />,
    );
    expect(deriveFractionOperation(scene.world, scene.visualizations[0].bindings, "fraction_multiplication"))
      .toMatchObject({ resultNumerator: 6, resultDenominator: 12, reducedNumerator: 1, reducedDenominator: 2 });
    expect(html).toContain("Phần giao của hai lớp màu");
    expect(html).toContain("= 1/2");
  });

  it("reduces and compares two bound fractions without drawing 92 cells", () => {
    const world = {
      values: {
        n1: { value: 48, unit: "one" },
        d1: { value: 92, unit: "one" },
        n2: { value: 36, unit: "one" },
        d2: { value: 69, unit: "one" },
      },
    };
    const bindings = { numerator: ["n1", "n2"], denominator: ["d1", "d2"] };
    const result = deriveFractionComparison(world, bindings);

    expect(result.left).toMatchObject({ divisor: 4, reducedNumerator: 12, reducedDenominator: 23 });
    expect(result.right).toMatchObject({ divisor: 3, reducedNumerator: 12, reducedDenominator: 23 });
    expect(result.equal).toBe(true);

    const scene = {
      ...sceneFor("grade3_fraction"),
      metadata: { problem_type: "comparison of fractions" },
      world,
      visualizations: [{ id: "visual_fraction", type: "fraction", bindings, options: {} }],
    };
    const html = renderToStaticMarkup(
      <MathSceneRenderer scene={scene} world={world} progress={1} />,
    );
    expect(html).toContain("chia cả tử và mẫu cho");
    expect(html).toContain("Vậy hai phân số bằng nhau");
    expect(html.match(/ratioTrack/g) || []).toHaveLength(2);
  });
});

describe("advanced visual reasoning", () => {
  it("turns a three-variable equation into a visible plane on Oxyz", () => {
    const world = {
      values: {
        coefficient_x: { value: 3, unit: "one", label: "Hệ số x" },
        coefficient_y: { value: 1, unit: "one", label: "Hệ số y" },
        coefficient_z: { value: 1, unit: "one", label: "Hệ số z" },
        plane_right_side: { value: 6, unit: "one", label: "Vế phải" },
      },
    };
    const bindings = {
      coefficient: ["coefficient_x", "coefficient_y", "coefficient_z"],
      constant: ["plane_right_side"],
    };
    const plane = derivePlane3d(world, bindings);
    expect(plane).toMatchObject({ a: 3, b: 1, c: 1, rightSide: 6, intercepts: [2, 6, 6] });
    expect(plane.vertices).toHaveLength(4);

    const scene = {
      id: "three-variable-plane",
      metadata: { problem_type: "linear_equation_three_variables_plane" },
      world,
      visualizations: [{ id: "plane", type: "geometry_3d", bindings, options: {} }],
    };
    const html = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={1} />);
    expect(html).toContain("Mặt phẳng nghiệm trên hệ trục Oxyz");
    expect(html).toContain("3x + y + z = 6");
    expect(html).toContain("Ox");
    expect(html).toContain("Oy");
    expect(html).toContain("Oz");
  });

  it("keeps 3x + y = z on the origin instead of inventing three intercepts", () => {
    // 3x + y = z canonicalizes to 3x + y − z = 0. Every axis intercept is O,
    // so the scene must teach the normal vector and verified sample points.
    const world = {
      values: {
        plane_x_coefficient: { value: 3, unit: "one", label: "Hệ số x" },
        plane_y_coefficient: { value: 1, unit: "one", label: "Hệ số y" },
        plane_z_coefficient: { value: -1, unit: "one", label: "Hệ số z" },
        plane_right_side: { value: 0, unit: "one", label: "Vế phải" },
      },
    };
    const bindings = {
      coefficient: ["plane_x_coefficient", "plane_y_coefficient", "plane_z_coefficient"],
      constant: ["plane_right_side"],
    };
    const plane = derivePlane3d(world, bindings);
    expect(plane).toMatchObject({ a: 3, b: 1, c: -1, rightSide: 0, throughOrigin: true });
    expect(plane.samplePoints.length).toBeGreaterThanOrEqual(3);
    for (const [x, y, z] of plane.samplePoints) {
      expect(3 * x + 1 * y + -1 * z).toBeCloseTo(0, 9);
    }
    // The normal is (3, 1, −1) up to the unit length used for drawing.
    const scale = plane.normal[0] / 3;
    expect(plane.normal[1] / 1).toBeCloseTo(scale, 9);
    expect(plane.normal[2] / -1).toBeCloseTo(scale, 9);

    const scene = {
      id: "plane-through-origin",
      metadata: { problem_type: "linear_equation_three_variables_plane" },
      world,
      visualizations: [{ id: "plane", type: "geometry_3d", bindings, options: {} }],
    };
    const html = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={1} />);
    expect(html).toContain("Mặt phẳng nghiệm trên hệ trục Oxyz");
    expect(html).toContain("3x + y − z = 0");
    expect(html).toContain("O(0; 0; 0)");
    expect(html).toContain("Pháp tuyến");
    expect(html).toContain("Vô số bộ");
    expect(html).not.toContain("unsupported");
  });

  it("verifies every sample point it is willing to draw on a plane", () => {
    for (const [a, b, c, d] of [[3, 1, -1, 0], [1, 1, -1, 0], [3, 1, 1, 6], [-2, 4, -1, 8]]) {
      const points = planeSamplePoints(a, b, c, d);
      expect(points.length).toBeGreaterThan(0);
      for (const [x, y, z] of points) {
        expect(a * x + b * y + c * z).toBeCloseTo(d, 6);
      }
    }
    // A degenerate normal has no plane to sample.
    expect(planeSamplePoints(0, 0, 0, 5)).toHaveLength(0);
  });

  it("draws a system of two equations as two lines and their real state", () => {
    const worldFor = (values) => ({
      values: Object.fromEntries(values.map((value, index) => [`quantity_${index + 1}`, { value, unit: "one" }])),
    });
    const bindings = {
      coefficient: ["quantity_1", "quantity_2", "quantity_4", "quantity_5"],
      constant: ["quantity_3", "quantity_6"],
    };

    const meeting = deriveLinearSystem(worldFor([1, 1, 3, 1, -1, 1]), bindings);
    expect(meeting.state).toBe("intersecting");
    expect(meeting.intersection.x).toBeCloseTo(2, 9);
    expect(meeting.intersection.y).toBeCloseTo(1, 9);

    expect(deriveLinearSystem(worldFor([2, 1, 5, 4, 2, 10]), bindings).state).toBe("coincident");
    expect(deriveLinearSystem(worldFor([2, 1, 5, 4, 2, 3]), bindings).state).toBe("parallel");
    // A vertical line has no slope but is still a line the scene must draw.
    const vertical = deriveLinearSystem(worldFor([1, 0, 2, 0, 1, 3]), bindings);
    expect(vertical.state).toBe("intersecting");
    expect(vertical.intersection).toMatchObject({ x: 2, y: 3 });

    const world = worldFor([1, 1, 3, 1, -1, 1]);
    const scene = {
      id: "linear-system",
      metadata: { problem_type: "linear_system_two_variables_graph" },
      world,
      visualizations: [{ id: "system", type: "coordinate_graph", bindings, options: {} }],
    };
    const html = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={1} />);
    expect(html).toContain("Hệ hai phương trình bậc nhất trên cùng hệ trục Oxy");
    expect(html).toContain("M(2; 1)");
    expect(html).toContain("nghiệm duy nhất");
    expect(html.match(/functionLine/g) || []).not.toHaveLength(0);
  });

  it("solves and draws every plane of a three-variable linear system", () => {
    const relations = [{
      type: "linear_system",
      parameters: {
        coordinate_system: "Oxyz",
        symbols: ["x", "y", "z"],
        state: "unique",
        coefficient_rank: 3,
        augmented_rank: 3,
        equations: [
          [4, 5, 1, 0],
          [0, 6, 0, 9],
          [4, 0, 9, 0],
        ],
        canonical_forms: ["4x + 5y + z = 0", "6y = 9", "4x + 9z = 0"],
        solution: [-135 / 64, 3 / 2, 15 / 16],
        solution_exact: ["-135/64", "3/2", "15/16"],
        elimination_steps: [{
          operation: "Ma trận rút gọn",
          matrix: [["1", "0", "0", "-135/64"], ["0", "1", "0", "3/2"], ["0", "0", "1", "15/16"]],
        }],
      },
    }];
    const system = deriveLinearSystem3d({}, {}, relations);
    expect(system).not.toBeNull();
    expect(system.planes).toHaveLength(3);
    expect(system.solutionExact).toEqual(["-135/64", "3/2", "15/16"]);
    expect(system.checks.every((check) => Math.abs(check.left - check.right) < 1e-9)).toBe(true);

    const world = { values: {} };
    const scene = {
      id: "linear-system-three-variables",
      metadata: { problem_type: "linear_system_three_variables_planes", relations },
      world,
      visualizations: [{ id: "system3", type: "geometry_3d", bindings: {}, options: {} }],
    };
    const html = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={1} />);
    expect(html).toContain("Hệ phương trình ba ẩn");
    expect(html).toContain("4x + 5y + z = 0");
    expect(html).toContain("-135/64");
    expect(html).toContain("Hệ có nghiệm duy nhất");
    expect((html.match(/systemPlane/g) || []).length).toBeGreaterThanOrEqual(3);
    expect(html).toContain("Thay vào P3");
    expect(html).not.toContain("Cần toàn bộ hệ số");
  });

  it("counts a calendar span on the grid and notices the month boundary", () => {
    const world = { values: { d: { value: 25 }, n: { value: 10, unit: "day" } } };
    const bindings = { count_initial: ["d"], duration: ["n"] };
    const relations = [{ type: "calendar_span", parameters: { month: 4, start_weekday: 1 } }];
    const model = deriveCalendarDuration(world, bindings, relations);
    // April has 30 days: 25 + 10 rolls into May.
    expect(model).toMatchObject({ daysInMonth: 30, rolledOver: true, endDay: 5, endMonth: 5 });
    expect(model.startWeekday).toBe("Thứ hai");
    expect(model.endWeekday).toBe("Thứ năm");
    const inside = deriveCalendarDuration(
      { values: { d: { value: 3 }, n: { value: 10 } } },
      bindings,
      relations,
    );
    expect(inside).toMatchObject({ rolledOver: false, endDay: 13, endMonth: 4 });
    expect(deriveCalendarDuration(world, bindings, [])).toBeNull();

    const scene = {
      id: "calendar",
      metadata: { problem_type: "time_calendar_duration", relations },
      world,
      visualizations: [{ id: "cal", type: "calendar", bindings, options: {} }],
    };
    const html = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={1} />);
    expect(html).toContain("Lịch tháng 4");
    expect(html).toContain("5/5");
  });

  it("solves a right triangle from a leg and the hypotenuse", () => {
    const world = { values: { ab: { value: 5, unit: "cm" }, bc: { value: 13, unit: "cm" } } };
    const bindings = { length: ["ab"], height: ["bc"] };
    const relations = [{
      type: "right_triangle",
      parameters: {
        vertices: "ABC", right_vertex: "A", hypotenuse: "BC", legs: ["AB", "AC"],
        known_sides: { AB: 5, BC: 13 }, unit: "cm", solve_all: true, round_to_minute: true,
      },
    }];
    const model = deriveRightTriangle(world, bindings, relations);
    // A leg and the hypotenuse means a difference of squares, not a sum.
    expect(model.sides.AC).toBeCloseTo(12, 9);
    expect(model.missing).toBe("AC");
    expect(model.sides.AB ** 2 + model.sides.AC ** 2).toBeCloseTo(model.sides.BC ** 2, 6);
    // The angle at B is opposite AC, the angle at C is opposite AB.
    const angleB = model.angles.find((item) => item.vertex === "B");
    const angleC = model.angles.find((item) => item.vertex === "C");
    expect(angleB.degrees).toBeCloseTo((Math.asin(12 / 13) * 180) / Math.PI, 6);
    expect(angleC.degrees).toBeCloseTo((Math.asin(5 / 13) * 180) / Math.PI, 6);
    expect(model.angleSum).toBeCloseTo(90, 6);
    expect(angleB.minutes).toBeLessThan(60);

    // Two legs instead: the hypotenuse comes from a sum of squares.
    const legs = deriveRightTriangle(
      { values: { ab: { value: 3 }, ac: { value: 4 } } },
      { length: ["ab"], height: ["ac"] },
      [{ type: "right_triangle", parameters: {
        vertices: "ABC", right_vertex: "A", hypotenuse: "BC", legs: ["AB", "AC"],
        known_sides: { AB: 3, AC: 4 }, unit: "cm", solve_all: false, round_to_minute: false,
      } }],
    );
    expect(legs.sides.BC).toBeCloseTo(5, 9);

    // A leg longer than the hypotenuse is not a triangle; draw nothing.
    expect(deriveRightTriangle(world, bindings, [{ type: "right_triangle", parameters: {
      vertices: "ABC", right_vertex: "A", hypotenuse: "BC", legs: ["AB", "AC"],
      known_sides: { AB: 13, BC: 5 }, unit: "cm", solve_all: true,
    } }])).toBeNull();
    expect(deriveRightTriangle(world, bindings, [])).toBeNull();

    const scene = {
      id: "right-triangle",
      metadata: { problem_type: "right_triangle_solution", relations },
      world,
      visualizations: [{ id: "geo", type: "geometry_2d", bindings, options: {} }],
    };
    const html = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={1} />);
    expect(html).toContain("Giải tam giác ABC vuông tại A");
    expect(html).toContain("12");
    expect(html).toContain("67°23");
    expect(html).not.toContain("Chưa đủ dữ kiện");
  });

  it("solves a right triangle from one side and one acute angle", () => {
    const world = { values: { ab: { value: 5, unit: "cm" }, b: { value: 30, unit: "degree" } } };
    const bindings = { length: ["ab"], angle: ["b"] };
    const relations = [{
      type: "right_triangle",
      parameters: {
        vertices: "ABC", right_vertex: "A", hypotenuse: "BC", legs: ["AB", "AC"],
        known_sides: { AB: 5 }, known_angles: { B: 30 },
        unit: "cm", solve_all: true, round_to_minute: false,
      },
    }];
    const model = deriveRightTriangle(world, bindings, relations);
    expect(model.fromAngle).toBe(true);
    // AB contains B, so AB is adjacent to the angle at B and AC is opposite.
    expect(model.sides.BC).toBeCloseTo(5 / Math.cos(Math.PI / 6), 9);
    expect(model.sides.AC).toBeCloseTo(5 * Math.tan(Math.PI / 6), 9);
    // Whatever route produced them, the three sides must still satisfy
    // Pythagoras and the acute angles must still be complementary.
    expect(model.sides.AB ** 2 + model.sides.AC ** 2).toBeCloseTo(model.sides.BC ** 2, 6);
    expect(model.angleSum).toBeCloseTo(90, 6);
    expect(model.angles.find((item) => item.vertex === "B").degrees).toBeCloseTo(30, 6);

    // The hypotenuse as the given side takes the sine/cosine route instead.
    const fromHypotenuse = deriveRightTriangle(
      { values: {} },
      {},
      [{ type: "right_triangle", parameters: {
        vertices: "ABC", right_vertex: "A", hypotenuse: "BC", legs: ["AB", "AC"],
        known_sides: { BC: 10 }, known_angles: { C: 30 }, unit: "cm", solve_all: true,
      } }],
    );
    expect(fromHypotenuse.sides.AB).toBeCloseTo(10 * Math.sin(Math.PI / 6), 9);
    expect(fromHypotenuse.sides.AC).toBeCloseTo(10 * Math.cos(Math.PI / 6), 9);

    // A right or obtuse "acute" angle describes no right triangle.
    expect(deriveRightTriangle(world, bindings, [{ type: "right_triangle", parameters: {
      vertices: "ABC", right_vertex: "A", hypotenuse: "BC", legs: ["AB", "AC"],
      known_sides: { AB: 5 }, known_angles: { B: 90 }, unit: "cm", solve_all: true,
    } }])).toBeNull();

    const scene = {
      id: "right-triangle-angle",
      metadata: { problem_type: "right_triangle_solution", relations },
      world,
      visualizations: [{ id: "geo", type: "geometry_2d", bindings, options: {} }],
    };
    const html = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={1} />);
    expect(html).toContain("Giải tam giác ABC vuông tại A");
    expect(html).not.toContain("Chưa đủ dữ kiện");
  });

  it("derives a similar triangle's side from one shared ratio", () => {
    const world = {
      values: {
        ab: { value: 3, unit: "cm" },
        ac: { value: 4, unit: "cm" },
        a2b2: { value: 9, unit: "cm" },
      },
    };
    const bindings = { length: ["ab", "ac"], height: ["a2b2"] };
    const model = deriveTriangleSimilarity(world, bindings);
    expect(model.scale).toBeCloseTo(3, 9);
    expect(model.large.b).toBeCloseTo(12, 9);
    // The two corresponding ratios must agree; that equality is the proof.
    expect(model.large.a / model.small.a).toBeCloseTo(model.large.b / model.small.b, 9);
    expect(deriveTriangleSimilarity(world, { length: ["ab"] })).toBeNull();

    const scene = {
      id: "similar",
      metadata: { problem_type: "triangle_similarity_metric_relation" },
      world,
      visualizations: [{ id: "geo", type: "geometry_2d", bindings, options: {} }],
    };
    const html = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={1} />);
    expect(html).toContain("Hai tam giác đồng dạng");
    expect(html).toContain("12");
  });

  it("splits a median at the centroid in the ratio it claims", () => {
    const world = { values: { m: { value: 12, unit: "cm" } } };
    const model = deriveCentroidProof(world, { length: ["m"] });
    expect(model.longPart).toBeCloseTo(8, 9);
    expect(model.shortPart).toBeCloseTo(4, 9);
    expect(model.longPart + model.shortPart).toBeCloseTo(model.median, 9);
    expect(model.longPart / model.shortPart).toBeCloseTo(2, 9);

    const scene = {
      id: "centroid",
      metadata: { problem_type: "triangle_centroid_median_proof" },
      world,
      visualizations: [{ id: "geo", type: "geometry_2d", bindings: { length: ["m"] }, options: {} }],
    };
    const html = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={1} />);
    expect(html).toContain("trọng tâm");
    expect(html).toContain("2 : 1");
  });

  it("turns a rectangle word problem into an equation with a matching shape", () => {
    const world = { values: { p: { value: 58, unit: "m" }, d: { value: 7 } } };
    const bindings = { total: ["p"], count_change: ["d"] };
    const model = deriveRectangleEquation(world, bindings);
    expect(model.width).toBeCloseTo(11, 9);
    expect(model.length).toBeCloseTo(18, 9);
    expect(2 * (model.length + model.width)).toBeCloseTo(model.perimeter, 9);
    expect(model.equation).toContain("29");
    expect(deriveRectangleEquation({ values: {} }, {})).toBeNull();
  });

  it("maps each phrase of a worded quantity to exactly one term", () => {
    const world = { values: { c: { value: 3 }, k: { value: -5 } } };
    const bindings = { coefficient: ["c"], constant: ["k"] };
    const relations = [{
      type: "expression_model",
      parameters: { symbol: "x", subject: "số bút của An", result: "số bút của Bình" },
    }];
    const model = deriveExpressionModel(world, bindings, relations);
    expect(model.expression).toBe("3x − 5");
    expect(model.mapping).toHaveLength(2);
    for (const sample of model.samples) {
      expect(sample.evaluated).toBe(3 * sample.value - 5);
    }
    expect(deriveExpressionModel({ values: { c: { value: 3 } } }, { coefficient: ["c"] }, relations)).toBeNull();
  });

  it("reduces a mixed expression by precedence, not left to right", () => {
    const world = {
      values: {
        a: { value: 0.5 },
        b: { value: 0.25 },
        c: { value: 0.2 },
      },
    };
    const bindings = { count: ["a", "b", "c"] };
    const relations = [{
      type: "expression_tree",
      parameters: { operators: ["+", "×"], operand_labels: ["1/2", "1/4", "20%"] },
    }];
    const tree = deriveExpressionTree(world, bindings, relations);
    // Left to right would give (0.5 + 0.25) × 0.2 = 0.15; precedence gives 0.55.
    expect(tree.result).toBeCloseTo(0.55, 9);
    expect(tree.steps[0]).toMatchObject({ operator: "×", level: 2 });
    expect(tree.steps[1]).toMatchObject({ operator: "+", level: 1 });
    expect(deriveExpressionTree(world, bindings, [])).toBeNull();

    const scene = {
      id: "expr",
      metadata: { problem_type: "mixed_rational_expression", relations },
      world,
      visualizations: [{ id: "tree", type: "expression_tree", bindings, options: {} }],
    };
    const html = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={1} />);
    expect(html).toContain("Cây biểu thức");
    expect(html).toContain("Ưu tiên 1");
    expect(html).toContain("0,55");
  });

  it("applies tax to the discounted price, not to the list price", () => {
    const world = {
      values: { p: { value: 500000 }, d: { value: 20 }, t: { value: 10 } },
    };
    const bindings = { count_initial: ["p"], probability: ["d", "t"] };
    const model = derivePercentWaterfall(world, bindings);
    expect(model.afterDiscount).toBe(400000);
    // 10% of 400000, not of 500000.
    expect(model.taxAmount).toBe(40000);
    expect(model.final).toBe(440000);
    expect(model.stages).toHaveLength(3);
    const noTax = derivePercentWaterfall(
      { values: { p: { value: 500000 }, d: { value: 20 } } },
      { count_initial: ["p"], probability: ["d"] },
    );
    expect(noTax.stages).toHaveLength(2);
    expect(noTax.final).toBe(400000);

    const scene = {
      id: "waterfall",
      metadata: { problem_type: "discount_tax_percentage" },
      world,
      visualizations: [{ id: "pct", type: "percent_grid", bindings, options: {} }],
    };
    const html = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={1} />);
    expect(html).toContain("Chuỗi giá");
    expect(html).toContain("440.000");
  });

  it("gives each motion leg its own duration instead of one shared speed", () => {
    const world = {
      values: {
        d1: { value: 30, unit: "km" },
        d2: { value: 30, unit: "km" },
        s1: { value: 10, unit: "km/h" },
        s2: { value: 15, unit: "km/h" },
      },
    };
    const bindings = { distance: ["d1", "d2"], speed: ["s1", "s2"] };
    const model = deriveSegmentedMotion(world, bindings);
    expect(model.legs.map((leg) => leg.duration)).toEqual([3, 2]);
    expect(model.totalDuration).toBe(5);
    // The average speed of equal distances is not the average of the speeds.
    expect(model.averageSpeed).toBeCloseTo(12, 9);
    expect(model.averageSpeed).not.toBeCloseTo(12.5, 3);
    expect(deriveSegmentedMotion(world, { distance: ["d1"], speed: ["s1"] })).toBeNull();

    const scene = {
      id: "segments",
      metadata: { problem_type: "multi_segment_equal_distance_motion" },
      world,
      visualizations: [{ id: "motion", type: "motion_path", bindings, options: {} }],
    };
    const html = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={1} />);
    expect(html).toContain("Hành trình nhiều chặng");
    expect(html).toContain("12");
  });

  it("shows the bracket expansion a compound equation depends on", () => {
    const world = {
      values: {
        c: { value: 1, unit: "one" },
        k: { value: 0, unit: "one" },
        r: { value: 6, unit: "one" },
      },
    };
    const bindings = { coefficient: ["c"], constant: ["k"], result: ["r"] };
    const scene = {
      id: "compound",
      metadata: {
        problem_type: "compound_linear_equation",
        relations: [{
          type: "linear_equation_stages",
          participants: {},
          parameters: { stages: ["3(x+2)-5=2x+7", "3x+1 = 2x+7", "x = 6"] },
        }],
      },
      world,
      visualizations: [{ id: "balance", type: "balance", bindings, options: {} }],
    };
    const html = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={1} />);
    expect(html).toContain("3(x+2)-5=2x+7");
    expect(html).toContain("3x+1 = 2x+7");
    expect(html).toContain("Phá ngoặc và thu gọn");

    // A one-step equation has no expansion, so no stage list is drawn.
    const simple = { ...scene, metadata: { problem_type: "linear_equation", relations: [] } };
    const simpleHtml = renderToStaticMarkup(<MathSceneRenderer scene={simple} world={world} progress={1} />);
    expect(simpleHtml).not.toContain("Phá ngoặc và thu gọn");
  });

  it("shifts every partial product into its own place value", () => {
    const world = { values: { a: { value: 543 }, b: { value: 87 } } };
    const bindings = { count_initial: ["a"], count_change: ["b"] };
    const model = deriveLongMultiplication(world, bindings);
    expect(model.partials.map((item) => item.value)).toEqual([3801, 43440]);
    expect(model.partials.reduce((sum, item) => sum + item.value, 0)).toBe(model.result);
    expect(model.result).toBe(543 * 87);

    const scene = {
      id: "long-mult",
      metadata: { problem_type: "column_arithmetic_regrouping_multiplication" },
      world,
      visualizations: [{ id: "col", type: "column_algorithm", bindings, options: {} }],
    };
    const html = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={1} />);
    expect(html).toContain("Nhân nhiều chữ số theo cột");
    expect(html).toContain("47.241");
  });

  it("brings down one digit per long-division step and checks the product back", () => {
    const world = { values: { a: { value: 1918 }, b: { value: 7 } } };
    const bindings = { count_initial: ["a"], count_change: ["b"] };
    const model = deriveLongDivision(world, bindings);
    expect(model.quotient).toBe(274);
    expect(model.remainder).toBe(0);
    expect(model.steps).toHaveLength(4);
    for (const step of model.steps) {
      expect(step.current - step.product).toBe(step.remainder);
      expect(step.remainder).toBeLessThan(model.divisor);
    }
    const withRemainder = deriveLongDivision(
      { values: { a: { value: 1000 }, b: { value: 7 } } },
      bindings,
    );
    expect(withRemainder.divisor * withRemainder.quotient + withRemainder.remainder).toBe(1000);

    const scene = {
      id: "long-div",
      metadata: { problem_type: "column_arithmetic_regrouping_division" },
      world,
      visualizations: [{ id: "col", type: "column_algorithm", bindings, options: {} }],
    };
    const html = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={1} />);
    expect(html).toContain("Chia dài");
    expect(html).toContain("274");
  });

  it("uses compact exact algorithms for very large typed arithmetic", () => {
    const bindings = { count_initial: ["a"], count_change: ["b"] };
    const multiplicationWorld = { values: { a: { value: 38475 }, b: { value: 9374 } } };
    const multiplication = deriveLongMultiplication(multiplicationWorld, bindings);
    expect(multiplication.result).toBe(360664650);
    expect(multiplication.partials.map((item) => item.value)).toEqual([
      153900, 2693250, 11542500, 346275000,
    ]);
    const multiplicationHtml = renderToStaticMarkup(<MathSceneRenderer
      scene={{
        id: "large-multiply",
        metadata: { problem_type: "multiplication_basic", source_text: "38475*9374" },
        world: multiplicationWorld,
        visualizations: [{ id: "column", type: "column_algorithm", bindings, options: {} }],
      }}
      world={multiplicationWorld}
      progress={1}
    />);
    expect(multiplicationHtml).toContain("Nhân nhiều chữ số theo cột");
    expect(multiplicationHtml).toContain("360.664.650");

    const divisionWorld = { values: { a: { value: 993948 }, b: { value: 7 } } };
    const division = deriveLongDivision(divisionWorld, bindings);
    expect(division).toMatchObject({ quotient: 141992, remainder: 4, exact: false });
    expect(division.steps).toHaveLength(6);
    const divisionHtml = renderToStaticMarkup(<MathSceneRenderer
      scene={{
        id: "large-divide",
        metadata: { problem_type: "division_basic", source_text: "993948 chia 7" },
        world: divisionWorld,
        visualizations: [{ id: "column", type: "column_algorithm", bindings, options: {} }],
      }}
      world={divisionWorld}
      progress={1}
    />);
    expect(divisionHtml).toContain("141.992");
    expect(divisionHtml).toContain("dư 4");
    expect(divisionHtml).toContain("993.948");
  });

  it("computes 92 factorial exactly with BigInt checkpoints", () => {
    const world = { values: { n: { value: 92, unit: "one" } } };
    const bindings = { count_initial: ["n"] };
    const factorial = deriveFactorial(world, bindings);
    expect(factorial).toMatchObject({ input: 92, digits: 143, trailingZeros: 21 });
    expect(factorial.result).toBe("12438414054641307255475324325873553077577991715875414356840239582938137710983519518443046123837041347353107486982656753664000000000000000000000");
    const html = renderToStaticMarkup(<MathSceneRenderer
      scene={{
        id: "factorial-92",
        metadata: { problem_type: "factorial", source_text: "92!" },
        world,
        visualizations: [{ id: "factorial", type: "expression_tree", bindings, options: {} }],
      }}
      world={world}
      progress={1}
    />);
    expect(html).toContain("Giai thừa · tích giảm dần đến 1");
    expect(html).toContain("92 × 91 × 90 × 89 × 88 × … × 3 × 2 × 1");
    expect(html).toContain("143 chữ số · 21 số 0 tận cùng");
    expect(html).toContain("12.438.414.054.641.307");
  });

  it("explains a decimal product by the digits it counts, not by rounding", () => {
    const world = { values: { a: { value: 5.6 }, b: { value: 0.25 } } };
    const bindings = { count_initial: ["a"], count_change: ["b"] };
    const model = deriveDecimalScaling(world, bindings, "decimal_arithmetic_multiplication");
    expect(model).toMatchObject({ leftWhole: 56, rightWhole: 25, wholeResult: 1400, resultPlaces: 3 });
    expect(model.result).toBeCloseTo(1.4, 9);

    // Division scales both sides by the same power of ten, so the quotient is
    // unchanged -- that invariant is the lesson.
    const divide = deriveDecimalScaling(
      { values: { a: { value: 21.06 }, b: { value: 7.8 } } },
      bindings,
      "decimal_arithmetic_division",
    );
    expect(divide.scaledLeft / divide.scaledRight).toBeCloseTo(21.06 / 7.8, 9);

    const scene = {
      id: "decimal-mult",
      metadata: { problem_type: "decimal_arithmetic_multiplication" },
      world,
      visualizations: [{ id: "col", type: "column_algorithm", bindings, options: {} }],
    };
    const html = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={1} />);
    expect(html).toContain("Nhân số thập phân");
    expect(html).toContain("1,4");
  });

  it("levels any number of columns to their own mean", () => {
    const world = {
      values: {
        a: { value: 12, label: "Ngày 1" },
        b: { value: 20, label: "Ngày 2" },
        c: { value: 16, label: "Ngày 3" },
        d: { value: 24, label: "Ngày 4" },
      },
    };
    const bindings = { count_change: ["a", "b", "c", "d"] };
    const mean = deriveArithmeticMean(world, bindings);
    expect(mean).toMatchObject({ count: 4, total: 72, mean: 18 });
    // What each column gives up must be exactly what the others receive.
    expect(mean.transfers.reduce((sum, item) => sum + item.delta, 0)).toBeCloseTo(0, 9);
    expect(deriveArithmeticMean({ values: { a: { value: 5 } } }, { count_change: ["a"] })).toBeNull();

    const scene = {
      id: "mean",
      metadata: { problem_type: "arithmetic_mean" },
      world,
      visualizations: [{ id: "mean", type: "bar_model", bindings, options: {} }],
    };
    const html = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={1} />);
    expect(html).toContain("Trung bình cộng");
    expect(html).toContain("÷ 4 = 18");
  });

  it("reads a difference as a whole number of equal ratio parts", () => {
    const world = { values: { d: { value: 40 }, n: { value: 5 }, m: { value: 3 } } };
    const bindings = { count_change: ["d"], numerator: ["n"], denominator: ["m"] };
    const model = deriveProportionalDifference(world, bindings);
    expect(model).toMatchObject({ partGap: 2, onePart: 20, first: 100, second: 60, total: 160 });
    expect(model.first - model.second).toBe(model.difference);
    // A difference that is not a whole number of parts has no equal-part model.
    expect(deriveProportionalDifference(
      { values: { d: { value: 41 }, n: { value: 5 }, m: { value: 3 } } },
      bindings,
    )).toBeNull();

    const scene = {
      id: "proportional",
      metadata: { problem_type: "proportional_system_two_variables" },
      world,
      visualizations: [{ id: "prop", type: "bar_model", bindings, options: {} }],
    };
    const html = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={1} />);
    expect(html).toContain("biết hiệu và tỉ số");
    expect(html).toContain("100");
    expect(html).toContain("60");
  });

  it("carries one running total through two dependent operations", () => {
    const world = { values: { s: { value: 200 }, a: { value: 45 }, b: { value: 30 } } };
    const bindings = { count_initial: ["s"], count_change: ["a", "b"] };
    const model = deriveMultiStepArithmetic(world, bindings, "multi_step_arithmetic_subtract_then_add");
    expect(model.stages.map((stage) => stage.after)).toEqual([155, 185]);
    expect(model.result).toBe(185);
    // The intermediate value must be a visible state, not just the final one.
    expect(model.stages[0].before).toBe(200);
    expect(model.stages[1].before).toBe(155);
    expect(deriveMultiStepArithmetic(world, { count_initial: ["s"], count_change: ["a"] }, "")).toBeNull();

    const scene = {
      id: "multi-step",
      metadata: { problem_type: "multi_step_arithmetic_subtract_then_add" },
      world,
      visualizations: [{ id: "ms", type: "bar_model", bindings, options: {} }],
    };
    const html = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={1} />);
    expect(html).toContain("Bài toán nhiều bước");
    expect(html).toContain("155");
    expect(html).toContain("185");
  });

  it("keeps a map ruler and a real ruler reading the same distance", () => {
    const world = { values: { L: { value: 4, unit: "cm" }, k: { value: 100000 } } };
    const bindings = { length: ["L"], coefficient: ["k"] };
    const model = deriveMapScale(world, bindings);
    expect(model).toMatchObject({ mapLength: 4, denominator: 100000, realUnit: "km", realLength: 4 });
    expect(model.ticks).toHaveLength(5);
    for (const tick of model.ticks) {
      expect(tick.real).toBeCloseTo((tick.map * model.denominator) / 100000, 6);
    }
    expect(deriveMapScale({ values: { L: { value: 4, unit: "cm" } } }, { length: ["L"] })).toBeNull();

    const scene = {
      id: "map-scale",
      metadata: { problem_type: "map_scale" },
      world,
      visualizations: [{ id: "scale", type: "unit_scale", bindings, options: {} }],
    };
    const html = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={1} />);
    expect(html).toContain("Tỉ lệ bản đồ 1 :");
    expect(html).toContain("Thực tế (km)");
  });

  it("unrolls a circle into sectors that re-form pi*r*r", () => {
    const world = { values: { r: { value: 6, unit: "cm", label: "Bán kính" } } };
    const bindings = { radius: ["r"], quantities: ["r"] };
    const circle = deriveCircleArea(world, bindings);
    expect(circle).toMatchObject({ radius: 6, diameter: 12, unit: "cm" });
    expect(circle.area).toBeCloseTo(Math.PI * 36, 6);
    expect(circle.halfCircumference).toBeCloseTo(Math.PI * 6, 6);
    // A diameter alone still determines the radius; it must not be read as one.
    const fromDiameter = deriveCircleArea(
      { values: { d: { value: 12, unit: "cm" } } },
      { diameter: ["d"] },
    );
    expect(fromDiameter).toMatchObject({ radius: 6, fromDiameter: true });
    expect(deriveCircleArea({ values: {} }, {})).toBeNull();

    const scene = {
      id: "circle-area",
      metadata: { problem_type: "circle_area" },
      world,
      visualizations: [{ id: "circle", type: "circle_model", bindings, options: {} }],
    };
    const html = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={1} />);
    expect(html).toContain("Hình tròn và diện tích");
    expect(html).toContain("113,1");
    expect(html).not.toContain("Chưa hỗ trợ hình biểu diễn");
  });

  it("keeps the inscribed angle at half the central angle it shares an arc with", () => {
    const world = {
      values: {
        r: { value: 5, unit: "cm" },
        a: { value: 80, unit: "degree" },
      },
    };
    const bindings = { radius: ["r"], angle: ["a"] };
    const proof = deriveCircleProof(world, bindings);
    expect(proof).toMatchObject({ radius: 5, centralAngle: 80, inscribedAngle: 40, tangentAngle: 90 });
    // A missing or impossible central angle must not produce a drawn claim.
    expect(deriveCircleProof({ values: { r: { value: 5 } } }, { radius: ["r"] })).toBeNull();
    expect(deriveCircleProof(
      { values: { r: { value: 5 }, a: { value: 400 } } },
      { radius: ["r"], angle: ["a"] },
    )).toBeNull();

    const scene = {
      id: "circle-proof",
      metadata: { problem_type: "circle_tangent_cyclic_proof" },
      world,
      visualizations: [{ id: "proof", type: "circle_model", bindings, options: {} }],
    };
    const html = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={1} />);
    expect(html).toContain("tiếp tuyến và góc nội tiếp");
    expect(html).toContain("80");
    expect(html).toContain("40");
  });

  it("marks both multiple sets and the least common multiple on one lattice", () => {
    const world = { values: { a: { value: 4 }, b: { value: 6 } } };
    const bindings = { count_initial: ["a"], count_change: ["b"] };
    const lattice = deriveFactorLattice(world, bindings);
    expect(lattice).toMatchObject({ first: 4, second: 6, leastCommonMultiple: 12, greatestCommonDivisor: 2 });
    expect(lattice.commonMultiples.slice(0, 2)).toEqual([12, 24]);
    for (const value of lattice.commonMultiples) {
      expect(value % 4).toBe(0);
      expect(value % 6).toBe(0);
    }
    expect(deriveFactorLattice({ values: { a: { value: 0 }, b: { value: 6 } } }, bindings)).toBeNull();

    const scene = {
      id: "lattice",
      metadata: { problem_type: "divisibility_common_multiple" },
      world,
      visualizations: [{ id: "lattice", type: "factor_lattice", bindings, options: {} }],
    };
    const html = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={1} />);
    expect(html).toContain("Lưới bội của 4 và 6");
    expect(html).toContain("BCNN(4; 6) = 12");
  });

  it("renders 2x + 1 as two x tiles and one unit tile", () => {
    const world = {
      values: {
        coefficient_x: { value: 2, unit: "one" },
        coefficient_constant: { value: 1, unit: "one" },
        exponent_x: { value: 1, unit: "one" },
        exponent_constant: { value: 0, unit: "one" },
      },
    };
    const bindings = {
      coefficient: ["coefficient_x", "coefficient_constant"],
      exponent: ["exponent_x", "exponent_constant"],
    };
    const scene = {
      id: "linear-expression-tiles",
      metadata: { problem_type: "polynomial_evaluate_reorder" },
      world,
      visualizations: [{ id: "tiles", type: "algebra_tiles", bindings, options: {} }],
    };
    const html = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={1} />);
    expect(html).toContain("Tile đại số");
    expect(html).toContain("2x");
    expect(html).toContain("+ 1");
  });

  it("keeps both sides of 2x + 3 = 9 equivalent through isolation", () => {
    const scene = sceneFor("grade7_balance");
    const equation = deriveLinearEquation(scene.world, scene.visualizations[0].bindings);
    expect(equation).toMatchObject({ isolated: 6, solution: 3 });
    const html = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={scene.world} progress={1} />);
    expect(html).toContain("Mỗi khối x có giá trị 3");
    expect(html).toContain("= 3");
  });

  it("keeps negative and fractional linear coefficients visually truthful", () => {
    const scene = {
      id: "signed-linear-equation",
      metadata: { problem_type: "linear_equation", relations: [] },
      world: { values: {
        coefficient: { value: -2, unit: "one" },
        constant: { value: 3, unit: "one" },
        result: { value: 7, unit: "one" },
      } },
      visualizations: [{
        id: "balance",
        type: "balance",
        bindings: { coefficient: ["coefficient"], constant: ["constant"], result: ["result"] },
        options: {},
      }],
    };
    const signedHtml = renderToStaticMarkup(
      <MathSceneRenderer scene={scene} world={scene.world} progress={0.82} />,
    );
    expect(signedHtml).toContain("Nhân cả hai vế với −1 trước");
    expect(signedHtml).toContain("Mỗi khối x có giá trị -2");
    expect(signedHtml).toContain("= -2");

    const fractionalWorld = { values: {
      coefficient: { value: 0.5, unit: "one" },
      constant: { value: 1, unit: "one" },
      result: { value: 3, unit: "one" },
    } };
    const fractionalHtml = renderToStaticMarkup(
      <MathSceneRenderer scene={scene} world={fractionalWorld} progress={0} />,
    );
    expect(fractionalHtml).toContain("0.5x");
    expect(fractionalHtml).not.toContain(">x</i><i>x<");
  });

  it("keeps the exact fraction visible after clearing numeric denominators", () => {
    const scene = sceneFor("grade8_fractional_linear_equation");
    const html = renderToStaticMarkup(
      <MathSceneRenderer scene={scene} world={scene.world} progress={0.82} />,
    );
    expect(html).toContain("Mẫu số: 3, 5 · BCNN = 15");
    expect(html).toContain("10x − 5 = 3x + 6");
    expect(html).toContain("7x = 11");
    expect(html).toContain("11/7 ≈ 1,571");
  });

  it("derives a point table and draws slope on x-y axes", () => {
    const scene = sceneFor("grade8_linear_graph");
    const graph = deriveCoordinateGraph(scene.world, scene.visualizations[0].bindings);
    expect(graph).toMatchObject({ slope: 2, intercept: 1 });
    expect(graph.table.find((point) => point.x === 1)).toEqual({ x: 1, y: 3 });
    const html = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={scene.world} progress={1} />);
    expect(html).toContain("A(0; 1)");
    expect(html).toContain("B(1; 3)");
    expect(html).toContain("Δy / Δx = 2 / 1");
  });

  it("builds a cuboid on xyz and computes volume from its three dimensions", () => {
    const scene = sceneFor("grade9_cuboid");
    expect(deriveGeometry3d(scene.world, scene.visualizations[0].bindings))
      .toMatchObject({ baseArea: 12, volume: 24 });
    const html = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={scene.world} progress={1} />);
    expect(html).toContain("x–y–z");
    expect(html).toContain("4 × 3 × 2 = 24 cm³");
  });

  it("proves the binomial identity with four measured areas", () => {
    const scene = sceneFor("grade8_area_model");
    expect(deriveBinomialSquare(scene.world, scene.visualizations[0].bindings))
      .toMatchObject({ aSquare: 9, ab: 6, bSquare: 4, total: 25 });
    const html = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={scene.world} progress={1} />);
    expect(html).toContain("a² + ab + ab + b²");
    expect(html).toContain("= 25");
  });

  it("keeps a symbolic binomial visible when the analyzer has no numeric side lengths", () => {
    const model = deriveBinomialSquare(
      { values: {} },
      { quantities: [], unknowns: ["unknown_1"] },
      "Khai triển (x + 3)^2.",
    );
    expect(model).toMatchObject({ a: "x", b: "3", symbolic: true });
    expect(model.total).toBe("x² + 2·x·3 + 3²");

    const base = sceneFor("grade8_area_model");
    const scene = {
      ...base,
      world: { revision: 0, values: { unknown_1: { value: null, unit: "one" } } },
      metadata: { problem_type: "binomial_expansion", source_text: "Khai triển (x + 3)^2." },
      visualizations: [{ id: "visual_bar_model", type: "bar_model", bindings: { quantities: [], unknowns: ["unknown_1"] }, options: {} }],
    };
    const html = renderToStaticMarkup(
      <MathSceneRenderer scene={scene} world={scene.world} progress={1} />,
    );
    expect(html).toContain("x² + 2·x·3 + 3²");
    expect(html).not.toContain("không khả dụng");
  });

  it("shows multiplication as equal groups rather than answer-only text", () => {
    const scene = sceneFor("grade3_multiplication");
    expect(deriveGrouping(scene.world, scene.visualizations[0].bindings, "multiplication"))
      .toMatchObject({ groups: 3, perGroup: 4, total: 12 });
    const html = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={scene.world} progress={1} />);
    expect(html).toContain("3 hàng, mỗi hàng 4 đồ vật");
    expect(html).toContain("= 12");
  });

  it("compresses 4 × 98 into four base-ten groups instead of a blank renderer", () => {
    const base = sceneFor("grade3_multiplication");
    const world = {
      values: {
        groups: { value: 4, unit: "one", label: "Số nhóm" },
        perGroup: { value: 98, unit: "one", label: "Số phần tử mỗi nhóm" },
        result: { value: null, unit: "one", label: "Kết quả" },
      },
    };
    const bindings = {
      count_initial: ["groups"],
      count_change: ["perGroup"],
      unknown_result: ["result"],
    };
    const scene = {
      ...base,
      world,
      metadata: { problem_type: "multiplication_basic", source_text: "4x98" },
      visualizations: [{ id: "large-grouping", type: "grouping", bindings, options: {} }],
    };
    expect(deriveGrouping(world, bindings, "multiplication_basic")).toMatchObject({
      mode: "place_value",
      groups: 4,
      perGroup: 98,
      total: 392,
      parts: [
        { label: "chục", digit: 9, value: 90 },
        { label: "đơn vị", digit: 8, value: 8 },
      ],
      partials: [
        { expression: "4 × 90", value: 360 },
        { expression: "4 × 8", value: 32 },
      ],
    });

    const html = renderToStaticMarkup(
      <MathSceneRenderer scene={scene} world={world} progress={1} />,
    );
    expect(html).toContain("4 nhóm, mỗi nhóm 98");
    expect(html).toContain("98 = 90 + 8");
    expect(html).toContain("4 × 90");
    expect(html).toContain("= 360");
    expect(html).toContain("= 392");
    expect(html).not.toContain("Cần hai số nguyên dương");
  });
});

describe("parenthesized addition followed by multiplication", () => {
  const world = {
    values: {
      innerLeft: { value: 1, unit: "one", label: "Số thứ nhất trong ngoặc" },
      innerRight: { value: 1, unit: "one", label: "Số thứ hai trong ngoặc" },
      multiplier: { value: 2, unit: "one", label: "Thừa số ngoài ngoặc" },
      result: { value: null, unit: "one", label: "Kết quả biểu thức" },
    },
  };
  const bindings = {
    count_initial: ["innerLeft"],
    count_change: ["innerRight"],
    coefficient: ["multiplier"],
    unknown_result: ["result"],
  };

  it("derives the parenthesis before the equal groups without preloading four", () => {
    expect(deriveParenthesizedMultiplication(
      world,
      bindings,
      "parenthesized_addition_multiplication",
    )).toEqual({
      innerLeft: 1,
      innerRight: 1,
      innerOperation: "add",
      innerSymbol: "+",
      innerValue: 2,
      multiplier: 2,
      groups: 2,
      perGroup: 2,
      total: 4,
    });
    expect(world.values.result.value).toBeNull();
  });

  it("shows the order of operations and then two groups of two", () => {
    const scene = {
      ...sceneFor("grade3_multiplication"),
      grade: 3,
      kind: "arithmetic",
      metadata: { problem_type: "parenthesized_addition_multiplication" },
      world,
      visualizations: [{ id: "visual_grouping", type: "grouping", bindings, options: {} }],
    };
    const before = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={0} />);
    const after = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={1} />);

    expect(before).toContain("Khoanh phép tính 1 + 1 trong ngoặc");
    expect(before).toContain("Phải hoàn thành phép tính trong ngoặc trước");
    expect(after).toContain("Tính trong ngoặc rồi dựng nhóm bằng nhau");
    expect(after).toContain("2 nhóm, mỗi nhóm 2 đồ vật");
    expect(after).toContain("(1 + 1) × 2");
    expect(after).toContain("= 4");
  });
});

describe("average per person", () => {
  const world = {
    values: {
      workers: { value: 25, unit: "one", label: "Số công nhân" },
      month1: { value: 954, unit: "one", label: "Sản phẩm tháng thứ nhất" },
      month2: { value: 821, unit: "one", label: "Sản phẩm tháng thứ hai" },
      month3: { value: 1350, unit: "one", label: "Sản phẩm tháng thứ ba" },
    },
  };
  const bindings = { count_initial: ["workers"], count_change: ["month1", "month2", "month3"] };

  it("accumulates all three time milestones before dividing equally", () => {
    const average = deriveAveragePerPerson(world, bindings);
    expect(average.milestones.map((item) => item.cumulative)).toEqual([954, 1775, 3125]);
    expect(average.perPerson).toBe(125);
  });

  it("renders time milestones and reveals the division only at the final step", () => {
    const scene = {
      ...sceneFor("grade2_subtraction"),
      kind: "arithmetic",
      grade: 4,
      metadata: { problem_type: "average_per_person" },
      world,
      visualizations: [{ id: "visual_bar", type: "bar_model", bindings, options: {} }],
    };
    const before = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={0} />);
    const after = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={1} />);

    expect(before).toContain("Xác định 3 mốc thời gian");
    expect(after).toContain("Cộng dồn: 3.125");
    expect(after).toContain("3.125 ÷ 25 = 125");
    expect(after).toContain("125 sản phẩm/người");
  });
});

describe("direct proportion distance and time", () => {
  const world = {
    values: {
      knownDuration: { value: 5, unit: "hour", label: "Thời gian đã biết" },
      knownDistance: { value: 225, unit: "km", label: "Quãng đường đã biết" },
      targetDuration: { value: 8, unit: "hour", label: "Thời gian mới" },
      targetDistance: { value: null, unit: "km", label: "Quãng đường cần tìm" },
    },
  };
  const bindings = {
    duration: ["knownDuration", "targetDuration"],
    distance: ["knownDistance"],
    unknown_result: ["targetDistance"],
  };

  it("derives one-hour distance and target distance without storing the answer", () => {
    expect(deriveDirectProportionDistanceTime(world, bindings)).toMatchObject({
      knownDuration: 5,
      knownDistance: 225,
      targetDuration: 8,
      unitDistance: 45,
      targetDistance: 360,
      segmented: true,
    });
    expect(world.values.targetDistance.value).toBeNull();
  });

  it("renders equal hour blocks, unit rate, result and invariant check", () => {
    const scene = {
      ...sceneFor("grade2_subtraction"),
      kind: "ratio",
      grade: 5,
      metadata: { problem_type: "distance_time_direct_proportion" },
      world,
      visualizations: [{ id: "visual_bar", type: "bar_model", bindings, options: {} }],
    };
    const before = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={0} />);
    const after = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={1} />);

    expect(before).toContain("5 giờ ứng với 225 km");
    expect(before).toContain("Sơ đồ quãng đường tỉ lệ thuận với thời gian");
    expect(after).toContain("225 ÷ 5 = 45 km/giờ");
    expect(after).toContain("45 × 8 = 360 km");
    expect(after).toContain("Ô tô đi trong 8 giờ được 360 km");
    expect(after).toContain("Kiểm tra: 360 ÷ 8 = 45 km/giờ");
    expect(after).not.toContain("Chưa có mô hình");
  });
});

describe("variable people work rate", () => {
  const world = {
    values: {
      initialWorkers: { value: 8, unit: "one", label: "Số người ban đầu" },
      plannedDays: { value: 6, unit: "one", label: "Số ngày dự định" },
      addedWorkers: { value: 4, unit: "one", label: "Số người bổ sung" },
      newDays: { value: null, unit: "one", label: "Số ngày mới" },
    },
  };
  const bindings = {
    count_initial: ["initialWorkers"],
    duration: ["plannedDays"],
    count_change: ["addedWorkers"],
    unknown_result: ["newDays"],
  };

  it("keeps all 48 worker-day tiles while changing from 8 to 12 workers", () => {
    expect(deriveVariablePeopleWorkRate(world, bindings)).toEqual({
      initialWorkers: 8,
      plannedDays: 6,
      workerChange: 4,
      newWorkers: 12,
      totalWork: 48,
      newDays: 4,
    });
  });

  it("renders both tile arrangements and the inverse-proportion check", () => {
    const scene = {
      ...sceneFor("grade2_subtraction"),
      kind: "ratio",
      grade: 5,
      metadata: { problem_type: "work_rate_with_variable_people" },
      world,
      visualizations: [{ id: "visual_bar", type: "bar_model", bindings, options: {} }],
    };
    const before = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={0} />);
    const after = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={1} />);

    expect(before).toContain("8 người làm trong 6 ngày");
    expect(before).toContain("8 người × 6 ngày");
    expect(after).toContain("48 ÷ 12 = 4 ngày");
    expect(after).toContain("Kiểm tra: 12 × 4 = 48 công-ngày");
    expect(after).toContain("48 ô công-ngày xếp theo 12 người");
    expect(after).not.toContain("Chưa có mô hình");
  });
});

describe("find value from ratio", () => {
  const world = {
    values: {
      boys: { value: 16, unit: "one", label: "Số học sinh nam" },
      numerator: { value: 9, unit: "one", label: "Tử số" },
      denominator: { value: 8, unit: "one", label: "Mẫu số" },
    },
  };
  const bindings = {
    count_initial: ["boys"],
    numerator: ["numerator"],
    denominator: ["denominator"],
  };

  it("maps 16 boys onto 8 parts before building 9 girl parts", () => {
    expect(deriveRatioShare(world, bindings)).toMatchObject({
      known: 16,
      denominator: 8,
      numerator: 9,
      onePart: 2,
      target: 18,
    });
  });

  it("renders the equal-part reasoning and conclusion at the final step", () => {
    const scene = {
      ...sceneFor("grade2_subtraction"),
      kind: "arithmetic",
      grade: 4,
      metadata: { problem_type: "find value from ratio" },
      world,
      visualizations: [{ id: "visual_bar", type: "bar_model", bindings, options: {} }],
    };
    const before = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={0} />);
    const after = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={1} />);

    expect(before).toContain("Nữ bằng 9/8 số học sinh nam");
    expect(after).toContain("16 ÷ 8 = 2 học sinh/phần");
    expect(after).toContain("9 × 2 = 18");
    expect(after).toContain("Lớp 4A có 18 học sinh nữ");
  });
});

describe("sequential fraction of the remainder", () => {
  const world = {
    values: {
      riceTotal: { value: 160, unit: "kg", label: "Tổng số gạo ban đầu" },
      firstNumerator: { value: 3, unit: "one" },
      firstDenominator: { value: 8, unit: "one" },
      secondNumerator: { value: 1, unit: "one" },
      secondDenominator: { value: 4, unit: "one" },
    },
  };
  const bindings = {
    mass: ["riceTotal"],
    numerator: ["firstNumerator"],
    denominator: ["firstDenominator"],
    addend_numerator: ["secondNumerator"],
    addend_denominator: ["secondDenominator"],
  };

  it("derives each day only from the printed total and fractions", () => {
    expect(deriveSequentialRemainderRatio(world, bindings)).toMatchObject({
      total: 160,
      firstDay: 60,
      remainingAfterFirst: 100,
      secondDay: 25,
      thirdDay: 75,
      divisor: 15,
      ratioNumerator: 5,
      ratioDenominator: 4,
    });
  });

  it("shows both repartitions and the reduced final comparison", () => {
    const scene = {
      ...sceneFor("grade2_subtraction"),
      kind: "ratio",
      grade: 7,
      metadata: { problem_type: "sequential_fraction_remainder_ratio" },
      world,
      visualizations: [{ id: "visual_bar", type: "bar_model", bindings, options: {} }],
    };
    const before = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={0} />);
    const after = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={1} />);

    expect(before).toContain("160 kg");
    expect(before).toContain("160 ÷ 8 =");
    expect(after).toContain("160 × 3/8 =");
    expect(after).toContain("60 kg");
    expect(after).toContain("100 × 1/4 =");
    expect(after).toContain("25 kg");
    expect(after).toContain("75 kg");
    expect(after).toContain("75 : 60 = 5 : 4");
  });
});

describe("generic sequential fraction remainder quantity", () => {
  const world = {
    values: {
      largeArea: { value: 1000, unit: "m2", canonical_value: 1000, canonical_unit: "m2", label: "10 dam² = 1000 m²" },
      extraArea: { value: 80, unit: "m2", canonical_value: 80, canonical_unit: "m2", label: "80 m²" },
      firstNumerator: { value: 2, unit: "one" },
      firstDenominator: { value: 5, unit: "one" },
      secondNumerator: { value: 1, unit: "one" },
      secondDenominator: { value: 3, unit: "one" },
      result: { value: null, unit: "m2", label: "Diện tích phần đất cuối cùng" },
    },
  };
  const bindings = {
    area: ["largeArea", "extraArea"],
    numerator: ["firstNumerator"],
    denominator: ["firstDenominator"],
    addend_numerator: ["secondNumerator"],
    addend_denominator: ["secondDenominator"],
    unknown_result: ["result"],
  };

  it("combines mixed-area components before applying both fractions", () => {
    expect(deriveSequentialRemainderQuantity(world, bindings)).toMatchObject({
      total: 1080,
      firstAllocation: 432,
      remainingAfterFirst: 648,
      secondAllocation: 216,
      finalRemainder: 432,
      unit: "m2",
    });
  });

  it("shows unit conversion, changing whole and final area instead of a rice ratio", () => {
    const scene = {
      ...sceneFor("grade2_subtraction"),
      kind: "ratio",
      grade: 6,
      metadata: { problem_type: "sequential_fraction_remainder_quantity" },
      world,
      visualizations: [{ id: "visual_bar", type: "bar_model", bindings, options: {} }],
    };
    const before = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={0} />);
    const after = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={1} />);

    expect(before).toContain("10 dam² = 1000 m² + 80 m²");
    expect(before).toContain("1.080 m²");
    expect(after).toContain("1.080 − 432 − 216 = 432 m²");
    expect(after).toContain("432 + 216 + 432 = 1.080 m²");
    expect(after).not.toContain("bán gạo");
    expect(after).not.toContain("Chưa có mô hình");
  });
});

describe("number line", () => {
  it("does not invent zero operands when arithmetic bindings are missing", () => {
    expect(deriveNumberLine({ values: {} }, 1, "addition_basic", {})).toBeNull();
  });

  it("counts back one unit at a time for a subtraction", () => {
    const scene = sceneFor("grade2_subtraction");
    const world = createMathWorldState(scene).world;
    const line = deriveNumberLine(world, 1, scene.metadata.problem_type);
    expect(line.start).toBe(8);
    expect(line.end).toBe(5);
    expect(line.jumps).toHaveLength(3);
    expect(line.jumps.every((jump) => jump.done)).toBe(true);
  });

  it("treats the production family subtraction_basic as counting backwards", () => {
    const world = {
      values: {
        left_operand: { value: 58 },
        right_operand: { value: 38 },
      },
    };
    const bindings = {
      count_initial: ["left_operand"],
      count_change: ["right_operand"],
    };
    const line = deriveNumberLine(world, 1, "subtraction_basic", bindings);
    expect(line).toMatchObject({ start: 58, change: 38, end: 20, operation: -1 });
    expect(line.jumps.map((jump) => Math.abs(jump.to - jump.from))).toEqual([10, 10, 10, 8]);
  });

  it("stays inside its bounds", () => {
    const scene = sceneFor("grade2_subtraction");
    const world = createMathWorldState(scene).world;
    const line = deriveNumberLine(world, 0.5, scene.metadata.problem_type);
    expect(line.current).toBeGreaterThanOrEqual(line.minimum);
    expect(line.current).toBeLessThanOrEqual(line.maximum);
  });
});

describe("object group", () => {
  it("moves the second group across as progress runs", () => {
    const world = createMathWorldState(sceneFor("grade1_addition")).world;
    expect(deriveObjectGroup(world, 0).moved).toBe(0);
    expect(deriveObjectGroup(world, 1).moved).toBe(2);
    expect(deriveObjectGroup(world, 1).total).toBe(5);
  });

  it("takes counters away instead of creating a second group for subtraction", () => {
    const scene = sceneFor("grade2_subtraction");
    const world = createMathWorldState(scene).world;
    const group = deriveObjectGroup(world, 1, scene.metadata.problem_type);
    expect(group.subtract).toBe(true);
    expect(group.moved).toBe(3);
    expect(group.total).toBe(5);
  });

  it("shows trucks leaving the parking lot for the exact reported regression", () => {
    const world = {
      values: {
        left_operand: { value: 58 },
        right_operand: { value: 38 },
        arithmetic_result: { value: null },
      },
    };
    const bindings = {
      count_initial: ["left_operand"],
      count_change: ["right_operand"],
      unknown_result: ["arithmetic_result"],
    };
    const scene = {
      id: "parking-lot-subtraction",
      grade: 1,
      kind: "arithmetic",
      metadata: {
        problem_type: "subtraction_basic",
        source_text: "Trong bãi có 58 chiếc xe tải. Có 38 chiếc xe rời bãi.",
      },
      world,
      visualizations: [{ id: "trucks", type: "object_group", bindings, options: {} }],
    };
    const group = deriveObjectGroup(world, 1, scene.metadata.problem_type, bindings);
    expect(group).toMatchObject({ subtract: true, moved: 38, total: 20 });
    const html = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={1} />);
    expect(html.match(/🚚/gu)).toHaveLength(58);
    expect(html).toContain("58 − 38 =");
    expect(html).toContain(">20<");
  });
});

describe("grade 9 trigonometric geometry", () => {
  const sceneForTrig = (problemType, world, bindings, parameters) => ({
    id: `trig-${parameters.kind}`,
    grade: 9,
    metadata: {
      problem_type: problemType,
      relations: [{ type: "trigonometric_geometry", parameters }],
    },
    world,
    visualizations: [{ id: "geometry", type: "geometry_2d", bindings, options: {} }],
  });

  it("turns an angle of depression into a visible horizontal distance", () => {
    const world = { values: { h: { value: 149, unit: "m" }, a: { value: 27, unit: "degree" } } };
    const bindings = { height: ["h"], angle: ["a"] };
    const parameters = { kind: "angle_of_depression", height: 149, angle: 27, unit: "m", landmark: "dai_hai_dang" };
    const relations = [{ type: "trigonometric_geometry", parameters }];
    const model = deriveTrigonometricGeometry(world, bindings, relations);
    expect(model.distance).toBeCloseTo(149 / Math.tan((27 * Math.PI) / 180), 9);
    const scene = sceneForTrig("angle_of_depression_distance", world, bindings, parameters);
    const html = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={1} />);
    expect(html).toContain("Góc nghiêng xuống");
    expect(html).toContain("Khoảng cách ngang");
    expect(html).not.toContain("Cần đủ");
  });

  it("splits an oblique triangle into two right triangles", () => {
    const world = { values: {
      h: { value: 5, unit: "cm" },
      b: { value: 70, unit: "degree" },
      c: { value: 35, unit: "degree" },
    } };
    const bindings = { height: ["h"], angle: ["b", "c"] };
    const parameters = {
      kind: "oblique_triangle_altitude", vertices: "ABC", apex: "A", foot: "H",
      height: 5, angles: { B: 70, C: 35 }, unit: "cm",
    };
    const model = deriveTrigonometricGeometry(world, bindings, [{ type: "trigonometric_geometry", parameters }]);
    expect(model.sideLengths.AB).toBeCloseTo(5 / Math.sin((70 * Math.PI) / 180), 9);
    expect(model.sideLengths.AC).toBeCloseTo(5 / Math.sin((35 * Math.PI) / 180), 9);
    expect(model.sideLengths.BC).toBeCloseTo(
      5 / Math.tan((70 * Math.PI) / 180) + 5 / Math.tan((35 * Math.PI) / 180),
      9,
    );
    const scene = sceneForTrig("oblique_triangle_altitude_solution", world, bindings, parameters);
    const html = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={1} />);
    expect(html).toContain("hai tam giác vuông");
    expect(html).toContain("Ba cạnh của tam giác ABC");
  });

  it("uses a perpendicular diagonal as the parallelogram height", () => {
    const world = { values: { side: { value: 3.5, unit: "one" }, angle: { value: 50, unit: "degree" } } };
    const bindings = { count_initial: ["side"], angle: ["angle"] };
    const parameters = {
      kind: "parallelogram_perpendicular_diagonal", vertices: "ABCD", diagonal: "AC",
      side: "AD", side_length: 3.5, angle_vertex: "D", angle: 50, unit: "one",
    };
    const model = deriveTrigonometricGeometry(world, bindings, [{ type: "trigonometric_geometry", parameters }]);
    expect(model.diagonalLength).toBeCloseTo(3.5 * Math.tan((50 * Math.PI) / 180), 9);
    expect(model.area).toBeCloseTo(3.5 ** 2 * Math.tan((50 * Math.PI) / 180), 9);
    const scene = sceneForTrig("parallelogram_perpendicular_diagonal_area", world, bindings, parameters);
    const html = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={1} />);
    expect(html).toContain("Diện tích hình bình hành");
    expect(html).toContain("14,6");
  });
});

describe("quadratic surface on Oxyz", () => {
  it("bends x² + 5y - z = 0 into a surface instead of a plane", () => {
    const parameters = {
      squared_symbol: "x",
      squared_coefficient: 1,
      linear_coefficients: { y: 5, z: -1 },
      right_side: 0,
      output_symbol: "z",
      coordinate_system: "Oxyz",
    };
    const relations = [{ type: "quadratic_surface", parameters }];
    const surface = deriveQuadraticSurface({ values: {} }, {}, relations);
    expect(surface.squaredSymbol).toBe("x");
    expect(surface.outputSymbol).toBe("z");
    expect(surface.gridLines).toHaveLength(10);
    for (const [x, y, z] of surface.samplePoints) {
      expect(x ** 2 + 5 * y - z).toBeCloseTo(0, 9);
    }
    const world = { values: {
      q: { value: 1 }, y: { value: 5 }, z: { value: -1 }, d: { value: 0 },
    } };
    const scene = {
      id: "quadratic-surface",
      grade: 9,
      metadata: { problem_type: "quadratic_surface_three_variables", relations },
      world,
      visualizations: [{
        id: "surface",
        type: "geometry_3d",
        bindings: { coefficient: ["q", "y", "z"], constant: ["d"] },
        options: {},
      }],
    };
    const html = renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={1} />);
    expect(html).toContain("Mặt cong nghiệm trên hệ trục Oxyz");
    expect(html).toContain("x² + 5y − z = 0");
    expect(html).not.toContain("Mặt phẳng nghiệm");
  });
});

describe("solution set", () => {
  const render = (problemType, world, bindings, parameters, progress = 1) => {
    const relations = [{ type: "solution_set", parameters }];
    const scene = {
      id: `solution-${parameters.kind}`,
      grade: 9,
      metadata: { problem_type: problemType, relations },
      world,
      visualizations: [{ id: "set", type: "solution_set", bindings, options: {} }],
    };
    return {
      model: deriveSolutionSet(world, bindings, relations),
      html: renderToStaticMarkup(<MathSceneRenderer scene={scene} world={world} progress={progress} />),
    };
  };

  it("reverses an inequality only when dividing by a negative coefficient", () => {
    const { model, html } = render(
      "linear_inequality_one_variable",
      { values: { a: { value: -2 }, c: { value: -4 } } },
      { coefficient: ["a"], constant: ["c"] },
      { kind: "inequality", symbol: "x", operator: "≤", strict: false },
    );
    expect(model).toMatchObject({ boundary: 2, operator: "≥", direction: "right", flipped: true });
    expect(html).toContain("x ≥ 2");
    expect(html).toContain("solutionClosedPoint");
    const intermediate = render(
      "linear_inequality_one_variable",
      { values: { a: { value: -2 }, c: { value: -4 } } },
      { coefficient: ["a"], constant: ["c"] },
      { kind: "inequality", symbol: "x", operator: "≤", strict: false },
      0.4,
    );
    expect(intermediate.html).toContain("đổi chiều");
  });

  it("shows both roots of a product equation as included points", () => {
    const { model, html } = render(
      "product_equation_roots",
      { values: { a1: { value: 1 }, c1: { value: -3 }, a2: { value: 1 }, c2: { value: 8 } } },
      { coefficient: ["a1", "a2"], constant: ["c1", "c2"] },
      { kind: "product_roots", symbol: "x" },
    );
    expect(model.values).toEqual([3, -8]);
    expect(model.sum).toBe(-5);
    expect(html).toContain("x = 3");
    expect(html).toContain("x = -8");
    expect(html).toContain("Tổng các nghiệm: -5");
  });

  it("draws forbidden denominator roots as hollow crossed points", () => {
    const { model, html } = render(
      "rational_equation_domain",
      { values: { a1: { value: 1 }, c1: { value: -3 }, a2: { value: 1 }, c2: { value: 3 } } },
      { coefficient: ["a1", "a2"], constant: ["c1", "c2"] },
      { kind: "excluded_values", symbol: "x" },
    );
    expect(model.values).toEqual([3, -3]);
    expect(html).toContain("x ≠ 3");
    expect(html).toContain("x ≠ -3");
    expect(html).toContain("solutionOpenPoint");
    expect(html).toContain(">×<");
  });

  it("splits an absolute-value equation into two visible linear branches", () => {
    const { model, html } = render(
      "absolute_value_equation",
      { values: { a: { value: 2 }, b: { value: -3 }, r: { value: 5 } } },
      { coefficient: ["a"], constant: ["b", "r"] },
      { kind: "absolute_value", symbol: "x", coefficient: 2, constant: -3, right_side: 5 },
      0.82,
    );
    expect([...model.values].sort((a, b) => a - b)).toEqual([-1, 4]);
    expect(html).toContain("2x − 3 = 5");
    expect(html).toContain("2x − 3 = -5");
    expect(html).toContain("x = -1; x = 4");
    expect(html).toContain("solutionClosedPoint");
  });

  it("uses t = x² and maps every non-negative t back to symmetric roots", () => {
    const { model, html } = render(
      "biquadratic_equation",
      { values: { a: { value: 1 }, b: { value: -5 }, c: { value: 4 } } },
      { coefficient: ["a", "b"], constant: ["c"] },
      { kind: "biquadratic", symbol: "x", coefficients: [1, -5, 4] },
      0.82,
    );
    expect(model.values).toEqual([-2, -1, 1, 2]);
    expect(html).toContain("Đặt t = x²");
    expect(html).toContain("x = -2; x = -1; x = 1; x = 2");
  });

  it("crosses out the radical candidate that fails the original equation", () => {
    const { model, html } = render(
      "radical_equation",
      { values: { a: { value: 1 }, b: { value: 1 }, c: { value: 1 }, d: { value: -1 } } },
      { coefficient: ["a", "c"], constant: ["b", "d"] },
      { kind: "radical", symbol: "x", radicand: [1, 1], right: [1, -1] },
      0.82,
    );
    expect(model.values).toEqual([3]);
    expect(model.markers).toEqual(expect.arrayContaining([
      expect.objectContaining({ value: 0, excluded: true }),
      expect.objectContaining({ value: 3, excluded: false }),
    ]));
    expect(html).toContain("x = 3");
    expect(html).toContain("nghiệm ngoại lai");
    expect(html).toContain(">×<");
  });

  it("keeps rational roots separate from every denominator exclusion", () => {
    const { model, html } = render(
      "rational_equation",
      { values: { a: { value: -1 }, b: { value: 1 }, c: { value: 1 } } },
      { coefficient: ["a", "b"], constant: ["c"] },
      {
        kind: "rational",
        symbol: "x",
        numerator_coefficients: [-1, 1, 1],
        denominators: [[1, 0], [1, 1]],
      },
      0.82,
    );
    expect(model.values).toHaveLength(2);
    expect(model.markers).toEqual(expect.arrayContaining([
      expect.objectContaining({ value: 0, excluded: true }),
      expect.objectContaining({ value: -1, excluded: true }),
    ]));
    expect(html).toContain("x ≠ 0");
    expect(html).toContain("x ≠ -1");
    expect(html).toContain("chấm đặc mới là nghiệm");
  });
});

describe("world state", () => {
  it("resets progress and playback together", () => {
    const state = createMathWorldState(sceneFor("grade5_motion"));
    const playing = mathWorldReducer(state, { type: "play" });
    const moved = mathWorldReducer(playing, { type: "set_progress", progress: 0.7 });
    expect(moved.progress).toBeCloseTo(0.7);

    const reset = mathWorldReducer(moved, { type: "reset" });
    expect(reset.progress).toBe(0);
    expect(reset.playback).toBe("paused");
  });

  it("stops at the end rather than looping", () => {
    const state = mathWorldReducer(createMathWorldState(sceneFor("grade5_motion")), { type: "play" });
    const finished = mathWorldReducer(state, { type: "set_progress", progress: 1 });
    expect(finished.playback).toBe("paused");
  });

  it("replays from the start when play is pressed at the end", () => {
    let state = createMathWorldState(sceneFor("grade5_motion"));
    state = mathWorldReducer(state, { type: "set_progress", progress: 1 });
    state = mathWorldReducer(state, { type: "play" });
    expect(state.progress).toBe(0);
    expect(state.playback).toBe("playing");
  });

  it("hands control to whoever drags the scrubber", () => {
    let state = mathWorldReducer(createMathWorldState(sceneFor("grade5_motion")), { type: "play" });
    state = mathWorldReducer(state, { type: "scrub", progress: 0.25 });
    expect(state.playback).toBe("paused");
    expect(state.progress).toBe(0.25);
  });
});
