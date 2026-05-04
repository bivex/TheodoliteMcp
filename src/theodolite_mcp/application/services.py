from ..domain.models import TraverseData, TraverseResult
from ..domain.logic import calculate_traverse

class SurveyService:
    def process_theodolite_traverse(self, data: TraverseData) -> TraverseResult:
        # Here we could add logging, authorization, etc.
        # But for now, it's a thin wrapper around domain logic.
        return calculate_traverse(data)
