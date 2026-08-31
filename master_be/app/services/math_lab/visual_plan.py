from __future__ import annotations

from app.schemas.math_lab import (
    MathSemanticModel,
    PedagogyPlan,
    VisualConcept,
    VisualConceptType,
    VisualizationDecision,
    VisualizationId,
    VisualPlan,
    VisualPlanStage,
    VisualPrimitive,
)


CONCEPT_BY_VISUALIZATION: dict[VisualizationId, VisualConceptType] = {
    VisualizationId.OBJECT_GROUP: VisualConceptType.PART_WHOLE,
    VisualizationId.PART_WHOLE: VisualConceptType.PART_WHOLE,
    VisualizationId.GROUPING: VisualConceptType.EQUAL_GROUPS,
    VisualizationId.NUMBER_LINE: VisualConceptType.OPERATION_ON_NUMBER_LINE,
    VisualizationId.BAR_MODEL: VisualConceptType.RATIO_PROPORTION,
    VisualizationId.FRACTION: VisualConceptType.FRACTION_PARTITION,
    VisualizationId.POWER_MODEL: VisualConceptType.FRACTION_PARTITION,
    VisualizationId.CLOCK: VisualConceptType.CHANGE_OVER_TIME,
    VisualizationId.TIMELINE: VisualConceptType.CHANGE_OVER_TIME,
    VisualizationId.MOTION_PATH: VisualConceptType.CHANGE_OVER_TIME,
    VisualizationId.UNIT_SCALE: VisualConceptType.MEASUREMENT,
    VisualizationId.PLACE_VALUE: VisualConceptType.MEASUREMENT,
    VisualizationId.COLUMN_ALGORITHM: VisualConceptType.ALGEBRA_TRANSFORM,
    VisualizationId.BALANCE: VisualConceptType.ALGEBRA_TRANSFORM,
    VisualizationId.ALGEBRA_TILES: VisualConceptType.ALGEBRA_TRANSFORM,
    VisualizationId.GEOMETRY_2D: VisualConceptType.GEOMETRY_CONSTRUCTION,
    VisualizationId.SHAPE_PATTERN: VisualConceptType.GEOMETRY_CONSTRUCTION,
    VisualizationId.COORDINATE_GRAPH: VisualConceptType.COORDINATE_RELATION,
    VisualizationId.DATA_CHART: VisualConceptType.STATISTICS_PROBABILITY,
    VisualizationId.PROBABILITY_SIMULATOR: VisualConceptType.STATISTICS_PROBABILITY,
    VisualizationId.GEOMETRY_3D: VisualConceptType.SPATIAL_3D,
    VisualizationId.PERCENT_GRID: VisualConceptType.RATIO_PROPORTION,
    VisualizationId.NUMBER_COMPARE: VisualConceptType.OPERATION_ON_NUMBER_LINE,
    VisualizationId.CIRCLE_MODEL: VisualConceptType.GEOMETRY_CONSTRUCTION,
    VisualizationId.FACTOR_LATTICE: VisualConceptType.EQUAL_GROUPS,
    VisualizationId.EXPRESSION_TREE: VisualConceptType.ALGEBRA_TRANSFORM,
    VisualizationId.CALENDAR: VisualConceptType.CHANGE_OVER_TIME,
    VisualizationId.SOLUTION_SET: VisualConceptType.OPERATION_ON_NUMBER_LINE,
    VisualizationId.UNSUPPORTED: VisualConceptType.UNSUPPORTED,
}

PRIMITIVE_BY_VISUALIZATION: dict[VisualizationId, VisualPrimitive] = {
    VisualizationId.OBJECT_GROUP: VisualPrimitive.OBJECT_ARRAY,
    VisualizationId.PART_WHOLE: VisualPrimitive.BAR_MODEL,
    VisualizationId.GROUPING: VisualPrimitive.OBJECT_ARRAY,
    VisualizationId.NUMBER_LINE: VisualPrimitive.NUMBER_LINE,
    VisualizationId.BAR_MODEL: VisualPrimitive.BAR_MODEL,
    VisualizationId.FRACTION: VisualPrimitive.FRACTION_STRIP,
    VisualizationId.POWER_MODEL: VisualPrimitive.AREA_VOLUME_MODEL,
    VisualizationId.CLOCK: VisualPrimitive.CLOCK_TIMELINE,
    VisualizationId.TIMELINE: VisualPrimitive.CLOCK_TIMELINE,
    VisualizationId.MOTION_PATH: VisualPrimitive.CLOCK_TIMELINE,
    VisualizationId.BALANCE: VisualPrimitive.BALANCE_SCALE,
    VisualizationId.GEOMETRY_2D: VisualPrimitive.GEOMETRY_CONSTRUCTION,
    VisualizationId.COORDINATE_GRAPH: VisualPrimitive.COORDINATE_PLANE,
    VisualizationId.GEOMETRY_3D: VisualPrimitive.AREA_VOLUME_MODEL,
    VisualizationId.PLACE_VALUE: VisualPrimitive.OBJECT_ARRAY,
    VisualizationId.COLUMN_ALGORITHM: VisualPrimitive.TEXT_OVERLAY,
    VisualizationId.UNIT_SCALE: VisualPrimitive.UNIT_LADDER,
    VisualizationId.DATA_CHART: VisualPrimitive.CHART,
    VisualizationId.NUMBER_COMPARE: VisualPrimitive.NUMBER_LINE,
    VisualizationId.PROBABILITY_SIMULATOR: VisualPrimitive.PROBABILITY_SIMULATION,
    VisualizationId.PERCENT_GRID: VisualPrimitive.FRACTION_STRIP,
    VisualizationId.ALGEBRA_TILES: VisualPrimitive.ALGEBRA_TILES,
    VisualizationId.SHAPE_PATTERN: VisualPrimitive.GEOMETRY_CONSTRUCTION,
    VisualizationId.CIRCLE_MODEL: VisualPrimitive.GEOMETRY_CONSTRUCTION,
    VisualizationId.FACTOR_LATTICE: VisualPrimitive.OBJECT_ARRAY,
    VisualizationId.EXPRESSION_TREE: VisualPrimitive.TEXT_OVERLAY,
    VisualizationId.CALENDAR: VisualPrimitive.CLOCK_TIMELINE,
    VisualizationId.SOLUTION_SET: VisualPrimitive.NUMBER_LINE,
    VisualizationId.UNSUPPORTED: VisualPrimitive.TEXT_OVERLAY,
}


class VisualPlanBuilder:
    """Compile semantics and pedagogy into a renderer-independent plan."""

    def build(
        self,
        model: MathSemanticModel,
        decisions: list[VisualizationDecision],
        pedagogy: PedagogyPlan,
    ) -> VisualPlan:
        primary = decisions[0].visualization
        primitive = PRIMITIVE_BY_VISUALIZATION[primary]
        bindings: dict[str, list[str]] = {
            "quantities": [item.id for item in model.quantities],
            "unknowns": [item.id for item in model.unknowns],
            "relationships": [item.id for item in model.relations],
        }
        stages = [
            VisualPlanStage(
                id=f"visual_stage_{index}",
                title=step.title,
                goal=step.goal,
                primitive=primitive,
                bindings=bindings,
                state_delta={
                    "reveal_index": index,
                    "reveal_fraction": index / max(1, len(pedagogy.reveal_steps)),
                },
                oracle_checks=[
                    "bindings_resolve",
                    "known_values_match_source",
                    "unknown_not_preloaded",
                    "stage_preserves_invariants",
                ],
            )
            for index, step in enumerate(pedagogy.reveal_steps, 1)
        ]
        if not stages:
            stages = [VisualPlanStage(
                id="visual_stage_1",
                title="Giữ nguyên dữ kiện",
                goal="Không dựng kết quả khi chưa có mô hình trực quan đã kiểm chứng.",
                primitive=primitive,
                bindings=bindings,
                state_delta={"reveal_index": 1, "reveal_fraction": 1.0},
                oracle_checks=["unknown_not_preloaded"],
            )]
        blocked = primary == VisualizationId.UNSUPPORTED
        return VisualPlan(
            semantic_model_id=model.id,
            concepts=[VisualConcept(
                id="visual_concept_primary",
                type=CONCEPT_BY_VISUALIZATION[primary],
                relationship_refs=[item.id for item in model.relations],
                quantity_refs=[item.id for item in model.quantities],
                unknown_refs=[item.id for item in model.unknowns],
                explanation=decisions[0].reason,
            )],
            stages=stages,
            primary_renderer=primary,
            fallback_renderers=[item.visualization for item in decisions[1:]],
            status="blocked" if blocked else "ready",
            verification_requirements=[
                "schema_valid",
                "semantic_fingerprint_recorded",
                "renderer_contract_ready",
                "numeric_or_symbolic_oracle_passed",
                "visual_regression_passed",
            ],
        )
