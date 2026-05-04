from mcp.server.fastmcp import FastMCP
from ..domain.models import TraverseData, Point, Observation
from ..application.services import SurveyService
from ..domain.logic import dms_to_decimal, decimal_to_dms, normalize_angle, calculate_azimuth_from_points
import math

mcp = FastMCP("Theodolite Survey Processor")
service = SurveyService()

@mcp.tool()
def convert_dms_to_decimal(degrees: int, minutes: int, seconds: float) -> float:
    """Converts Degrees, Minutes, Seconds to decimal degrees."""
    return dms_to_decimal(degrees, minutes, seconds)

@mcp.tool()
def convert_decimal_to_dms(decimal: float) -> dict:
    """Converts decimal degrees to Degrees, Minutes, Seconds."""
    d, m, s = decimal_to_dms(decimal)
    return {"degrees": d, "minutes": m, "seconds": round(s, 2)}

@mcp.tool()
def calculate_azimuth(x1: float, y1: float, x2: float, y2: float) -> float:
    """Calculates the azimuth (bearing) from point 1 to point 2."""
    p1 = Point(name="P1", x=x1, y=y1)
    p2 = Point(name="P2", x=x2, y=y2)
    return calculate_azimuth_from_points(p1, p2)

@mcp.tool()
def process_traverse(
    start_x: float,
    start_y: float,
    start_name: str,
    start_azimuth: float,
    observations_json: list[dict],
    is_closed: bool = False,
    end_x: float = None,
    end_y: float = None,
    end_name: str = None
):
    """
    Processes a theodolite traverse and calculates coordinates with misclosure adjustment.
    
    :param start_x: Starting X coordinate
    :param start_y: Starting Y coordinate
    :param start_name: Name of the starting point
    :param start_azimuth: Starting azimuth in decimal degrees
    :param observations_json: List of observations, each with 'point_name', 'horizontal_angle', and 'distance'
    :param is_closed: Whether the traverse is a closed loop
    :param end_x: Expected ending X coordinate (for open traverse)
    :param end_y: Expected ending Y coordinate (for open traverse)
    :param end_name: Name of the ending point
    """
    observations = [Observation(**obs) for obs in observations_json]
    start_point = Point(name=start_name, x=start_x, y=start_y)
    
    end_point = None
    if end_x is not None and end_y is not None:
        end_point = Point(name=end_name or "END", x=end_x, y=end_y)
        
    data = TraverseData(
        start_point=start_point,
        end_point=end_point,
        start_azimuth=start_azimuth,
        observations=observations,
        is_closed=is_closed
    )
    
    result = service.process_theodolite_traverse(data)
    return result.model_dump()

if __name__ == "__main__":
    mcp.run()
