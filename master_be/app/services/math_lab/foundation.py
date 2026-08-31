from __future__ import annotations

from app.schemas.math_lab import (
    MathLabPlanResponse,
    MathScene,
    MathSceneObject,
    MathSemanticModel,
    MathStep,
    MathWorldState,
    PedagogyPlan,
    SceneAction,
    SceneConstraint,
    VisualizationDecision,
    VisualizationDescriptor,
    VisualizationId,
    VisualPlan,
    WorldValue,
)
from app.services.math_lab.decision_engine import VisualDecisionEngine
from app.services.math_lab.pedagogy import PedagogyPlanner
from app.services.math_lab.registry import DEFAULT_VISUALIZATION_REGISTRY
from app.services.math_lab.units import UnitConversionError, canonicalize, normalize_unit
from app.services.math_lab.visual_plan import VisualPlanBuilder


class MathLabFoundationService:
    def __init__(
        self,
        decision_engine: VisualDecisionEngine | None = None,
        pedagogy_planner: PedagogyPlanner | None = None,
    ) -> None:
        self.decision_engine = decision_engine or VisualDecisionEngine()
        self.pedagogy_planner = pedagogy_planner or PedagogyPlanner()

    def plan(
        self,
        semantic_model: MathSemanticModel,
        requested_visualizations: list[VisualizationId] | None = None,
    ) -> MathLabPlanResponse:
        decisions = self.decision_engine.decide(semantic_model)
        warnings: list[str] = []
        if requested_visualizations is not None:
            decisions = self._teacher_selection(
                semantic_model,
                requested_visualizations,
                decisions,
                warnings,
            )
        pedagogy = self.pedagogy_planner.plan(semantic_model, decisions)
        visual_plan = VisualPlanBuilder().build(semantic_model, decisions, pedagogy)
        scene = self._create_scene(semantic_model, decisions, pedagogy, visual_plan, warnings)
        return MathLabPlanResponse(
            semantic_model=semantic_model,
            decisions=decisions,
            pedagogy=pedagogy,
            visual_plan=visual_plan,
            scene=scene,
            warnings=warnings,
        )

    @staticmethod
    def _teacher_selection(
        semantic_model: MathSemanticModel,
        requested: list[VisualizationId],
        defaults: list[VisualizationDecision],
        warnings: list[str],
    ) -> list[VisualizationDecision]:
        selected: list[VisualizationDecision] = []
        seen: set[VisualizationId] = set()
        for visualization in requested:
            if visualization in seen:
                continue
            if not DEFAULT_VISUALIZATION_REGISTRY.supports(visualization, semantic_model):
                warnings.append(
                    f"{visualization.value} does not support grade {semantic_model.grade} and domain {semantic_model.domain.value}"
                )
                continue
            selected.append(
                VisualizationDecision(
                    visualization=visualization,
                    score=1.0,
                    reason="Teacher selected a registered compatible visualization",
                    source="teacher",
                )
            )
            seen.add(visualization)
        return selected or defaults

    @staticmethod
    def _create_scene(
        model: MathSemanticModel,
        decisions: list[VisualizationDecision],
        pedagogy: PedagogyPlan,
        visual_plan: VisualPlan,
        warnings: list[str],
    ) -> MathScene:
        values: dict[str, WorldValue] = {}
        for quantity in model.quantities:
            try:
                unit = normalize_unit(quantity.unit)
                canonical_value, canonical_unit = canonicalize(quantity.value, unit)
            except UnitConversionError as exc:
                warnings.append(str(exc))
                unit = quantity.unit
                canonical_value = None
                canonical_unit = None
            values[quantity.id] = WorldValue(
                value=quantity.value,
                unit=unit,
                label=quantity.label,
                canonical_value=canonical_value,
                canonical_unit=canonical_unit,
                editable=quantity.editable,
            )
        for unknown in model.unknowns:
            values[unknown.id] = WorldValue(value=None, unit=unknown.unit or "one", label=unknown.label)
        if model.time and model.time.start:
            values["start_time"] = WorldValue(value=model.time.start, unit="clock", label="Thời gian bắt đầu")

        objects = [
            MathSceneObject(
                id=f"object_{entity.id}",
                type=entity.type,
                label=entity.label,
                semantic_ref=entity.id,
                properties={"attributes": entity.attributes},
            )
            for entity in model.entities
        ]
        semantic_bindings: dict[str, list[str]] = {
            "entities": [item.id for item in model.entities],
            "quantities": [item.id for item in model.quantities],
            "unknowns": [item.id for item in model.unknowns],
        }
        for entity in model.entities:
            if entity.role:
                # Entity labels and numeric quantities occasionally share a
                # semantic role in VLM output (for example an entity named
                # ``count_initial`` plus two actual prices). Keeping them in
                # one array makes renderers read the entity ID as a number and
                # turn an otherwise valid scene into NaN. Preserve both facts,
                # but namespace colliding entity roles so quantity bindings
                # remain numeric and deterministic.
                quantity_roles = {
                    item.role.value for item in model.quantities if item.role
                }
                binding_role = (
                    f"entity_{entity.role}"
                    if entity.role in quantity_roles
                    else entity.role
                )
                semantic_bindings.setdefault(binding_role, []).append(entity.id)
        for quantity in model.quantities:
            if quantity.role:
                semantic_bindings.setdefault(quantity.role.value, []).append(quantity.id)
        for unknown in model.unknowns:
            if unknown.role:
                semantic_bindings.setdefault(f"unknown_{unknown.role.value}", []).append(unknown.id)
        if model.time and model.time.start:
            semantic_bindings["start_time"] = ["start_time"]

        visualizations = [
            VisualizationDescriptor(
                id=f"visual_{decision.visualization.value}",
                type=decision.visualization,
                bindings=semantic_bindings,
                options={"score": decision.score, "reason": decision.reason},
            )
            for decision in decisions
        ]
        constraints = [
            SceneConstraint(
                id=f"scene_{constraint.id}",
                type=constraint.type,
                target_ids=constraint.target_ids,
                parameters=constraint.parameters,
                locked=constraint.locked,
                evidence=constraint.evidence,
            )
            for constraint in model.constraints
        ]
        steps = [
            MathStep(
                id=f"step_{index + 1}",
                action="show" if index == 0 else "highlight",
                target_ids=[f"visual_{item.value}" for item in reveal.visualization_ids],
                explanation=reveal.goal,
            )
            for index, reveal in enumerate(pedagogy.reveal_steps)
        ]
        actions = [
            SceneAction(id="action_play", type="play"),
            SceneAction(id="action_pause", type="pause"),
            SceneAction(id="action_reset", type="reset"),
            SceneAction(id="action_next", type="next"),
            SceneAction(id="action_previous", type="previous"),
        ]
        if "what_if" in pedagogy.interaction_strategy:
            actions.append(SceneAction(id="action_what_if", type="what_if"))
        if "why" in pedagogy.interaction_strategy:
            actions.append(SceneAction(id="action_why", type="why"))
        return MathScene(
            id=f"scene_{model.id}",
            kind=model.domain.value,
            grade=model.grade,
            semantic_model_id=model.id,
            world=MathWorldState(values=values),
            objects=objects,
            visualizations=visualizations,
            constraints=constraints,
            steps=steps,
            actions=actions,
            metadata={
                "problem_type": model.problem_type,
                # Renderer code stays deterministic, but symbolic visual models
                # may need the original expression labels (for example x+3).
                "source_text": model.source_text,
                "source_preserved": True,
                "choices": model.choices,
                # Some families are defined by structure rather than by numbers
                # alone -- an operator order, a proof relation. Renderers read
                # those parameters here instead of re-parsing the stem.
                "relations": [
                    {
                        "type": relation.type,
                        "participants": relation.participants,
                        "parameters": relation.parameters,
                    }
                    for relation in model.relations
                ],
                "visual_plan": visual_plan.model_dump(mode="json"),
            },
        )
