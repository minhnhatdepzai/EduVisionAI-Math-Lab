from __future__ import annotations

from dataclasses import dataclass

from app.schemas.math_lab import MathDomain, MathSemanticModel, VisualizationId


@dataclass(frozen=True, slots=True)
class VisualizationDefinition:
    id: VisualizationId
    supported_domains: frozenset[MathDomain]
    min_grade: int = 1
    max_grade: int = 9
    required_features: frozenset[str] = frozenset()

    def supports(self, model: MathSemanticModel) -> bool:
        return (
            self.min_grade <= model.grade <= self.max_grade
            and (model.domain in self.supported_domains or MathDomain.UNKNOWN in self.supported_domains)
        )


class VisualizationRegistry:
    def __init__(self, definitions: tuple[VisualizationDefinition, ...]) -> None:
        self._definitions = {definition.id: definition for definition in definitions}
        if len(self._definitions) != len(definitions):
            raise ValueError("Visualization registry contains duplicate IDs")

    def get(self, visualization_id: VisualizationId) -> VisualizationDefinition:
        try:
            return self._definitions[visualization_id]
        except KeyError as exc:
            raise KeyError(f"Visualization is not registered: {visualization_id}") from exc

    def supports(self, visualization_id: VisualizationId, model: MathSemanticModel) -> bool:
        return self.get(visualization_id).supports(model)

    @property
    def ids(self) -> tuple[VisualizationId, ...]:
        return tuple(self._definitions)


DEFAULT_VISUALIZATION_REGISTRY = VisualizationRegistry(
    (
        VisualizationDefinition(VisualizationId.UNSUPPORTED, frozenset({MathDomain.UNKNOWN}), 1, 9),
        VisualizationDefinition(VisualizationId.OBJECT_GROUP, frozenset({MathDomain.ARITHMETIC, MathDomain.NUMBER, MathDomain.FRACTION, MathDomain.PROBABILITY, MathDomain.STATISTICS}), 1, 3),
        VisualizationDefinition(VisualizationId.NUMBER_LINE, frozenset({MathDomain.NUMBER, MathDomain.ARITHMETIC, MathDomain.ALGEBRA, MathDomain.COORDINATE, MathDomain.PROBABILITY, MathDomain.UNKNOWN}), 1, 9),
        VisualizationDefinition(VisualizationId.GROUPING, frozenset({MathDomain.ARITHMETIC, MathDomain.RATIO}), 1, 6),
        VisualizationDefinition(VisualizationId.BAR_MODEL, frozenset({MathDomain.ARITHMETIC, MathDomain.NUMBER, MathDomain.FRACTION, MathDomain.RATIO, MathDomain.MEASUREMENT, MathDomain.GEOMETRY_2D, MathDomain.STATISTICS, MathDomain.ALGEBRA}), 2, 9),
        VisualizationDefinition(VisualizationId.FRACTION, frozenset({MathDomain.FRACTION, MathDomain.RATIO}), 2, 9),
        VisualizationDefinition(VisualizationId.POWER_MODEL, frozenset({MathDomain.FRACTION, MathDomain.NUMBER, MathDomain.ARITHMETIC, MathDomain.ALGEBRA}), 4, 9),
        VisualizationDefinition(VisualizationId.CLOCK, frozenset({MathDomain.TIME, MathDomain.MOTION}), 1, 7),
        VisualizationDefinition(VisualizationId.TIMELINE, frozenset({MathDomain.TIME, MathDomain.MOTION}), 3, 9),
        VisualizationDefinition(VisualizationId.MOTION_PATH, frozenset({MathDomain.MOTION}), 3, 9),
        VisualizationDefinition(VisualizationId.BALANCE, frozenset({MathDomain.ALGEBRA}), 5, 9),
        VisualizationDefinition(VisualizationId.GEOMETRY_2D, frozenset({MathDomain.GEOMETRY_2D, MathDomain.MEASUREMENT}), 1, 9),
        VisualizationDefinition(VisualizationId.COORDINATE_GRAPH, frozenset({MathDomain.COORDINATE, MathDomain.ALGEBRA, MathDomain.MOTION}), 5, 9),
        VisualizationDefinition(VisualizationId.GEOMETRY_3D, frozenset({MathDomain.GEOMETRY_3D, MathDomain.MEASUREMENT}), 1, 9),
        VisualizationDefinition(VisualizationId.PLACE_VALUE, frozenset({MathDomain.NUMBER, MathDomain.ARITHMETIC}), 1, 6),
        VisualizationDefinition(VisualizationId.COLUMN_ALGORITHM, frozenset({MathDomain.NUMBER, MathDomain.ARITHMETIC}), 1, 9),
        VisualizationDefinition(VisualizationId.UNIT_SCALE, frozenset({MathDomain.MEASUREMENT}), 2, 7),
        VisualizationDefinition(VisualizationId.DATA_CHART, frozenset({MathDomain.STATISTICS, MathDomain.PROBABILITY}), 2, 9),
        VisualizationDefinition(VisualizationId.NUMBER_COMPARE, frozenset({MathDomain.NUMBER, MathDomain.ARITHMETIC}), 1, 9),
        VisualizationDefinition(VisualizationId.PROBABILITY_SIMULATOR, frozenset({MathDomain.PROBABILITY}), 5, 9),
        VisualizationDefinition(VisualizationId.PERCENT_GRID, frozenset({MathDomain.RATIO, MathDomain.FRACTION, MathDomain.ARITHMETIC, MathDomain.ALGEBRA}), 4, 9),
        VisualizationDefinition(VisualizationId.ALGEBRA_TILES, frozenset({MathDomain.ALGEBRA}), 6, 9),
        VisualizationDefinition(VisualizationId.PART_WHOLE, frozenset({MathDomain.ARITHMETIC, MathDomain.NUMBER}), 1, 3),
        VisualizationDefinition(VisualizationId.SHAPE_PATTERN, frozenset({MathDomain.GEOMETRY_2D}), 1, 3),
        VisualizationDefinition(VisualizationId.CIRCLE_MODEL, frozenset({MathDomain.GEOMETRY_2D, MathDomain.MEASUREMENT}), 3, 9),
        VisualizationDefinition(VisualizationId.FACTOR_LATTICE, frozenset({MathDomain.NUMBER, MathDomain.ARITHMETIC}), 4, 9),
        VisualizationDefinition(VisualizationId.EXPRESSION_TREE, frozenset({MathDomain.ARITHMETIC, MathDomain.NUMBER, MathDomain.FRACTION, MathDomain.ALGEBRA, MathDomain.RATIO}), 1, 9),
        VisualizationDefinition(VisualizationId.CALENDAR, frozenset({MathDomain.TIME, MathDomain.MEASUREMENT, MathDomain.NUMBER}), 1, 9),
        VisualizationDefinition(VisualizationId.SOLUTION_SET, frozenset({MathDomain.ALGEBRA, MathDomain.NUMBER}), 6, 9),
    )
)
