from ..domain.models import TraverseData, TraverseResult, PlotPlan
from ..domain.logic import calculate_traverse
from ..domain.rendering import render_plot_plan

class SurveyService:
    def process_theodolite_traverse(self, data: TraverseData) -> TraverseResult:
        return calculate_traverse(data)

    def render_plot(self, plan: PlotPlan) -> bytes:
        return render_plot_plan(plan)
