from mcp.server.fastmcp import FastMCP
from ..domain.models import TraverseData, Point, Observation, StadiaMeasurement, TraverseResult
from ..application.services import SurveyService
from ..domain.logic import (
    dms_to_decimal, decimal_to_dms, normalize_angle, 
    calculate_azimuth_from_points, calculate_stadia, 
    calculate_inverse, generate_markdown_report
)
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
def solve_inverse_problem(x1: float, y1: float, z1: float = None, 
                         x2: float, y2: float, z2: float = None) -> dict:
    """
    Calculates azimuth, horizontal distance, and vertical data between two points.
    Useful for layout and checking distances between survey marks.
    """
    p1 = Point(name="P1", x=x1, y=y1, z=z1)
    p2 = Point(name="P2", x=x2, y=y2, z=z2)
    return calculate_inverse(p1, p2)

@mcp.tool()
def calculate_stadia_reduction(
    top_hair: float, 
    bottom_hair: float, 
    vertical_angle: float,
    hi: float = 0.0, 
    ht: float = 0.0
) -> dict:
    """
    Tacheometric reduction: computes horizontal distance and elevation from stadia readings.
    :param top_hair: Top cross-hair reading on staff
    :param bottom_hair: Bottom cross-hair reading on staff
    :param vertical_angle: Vertical (elevation) angle in decimal degrees
    :param hi: Height of Instrument
    :param ht: Height of Target (center hair reading)
    """
    m = StadiaMeasurement(
        top_hair=top_hair, 
        bottom_hair=bottom_hair, 
        vertical_angle=vertical_angle,
        instrument_height=hi, 
        target_height=ht
    )
    return calculate_stadia(m).model_dump()

@mcp.tool()
def process_traverse(
    start_x: float,
    start_y: float,
    start_z: float = None,
    start_name: str = "P1",
    start_azimuth: float = 0.0,
    observations_json: list[dict] = [],
    is_closed: bool = False,
    end_x: float = None,
    end_y: float = None,
    end_name: str = None,
    generate_report: bool = True
):
    """
    Processes a theodolite traverse with misclosure adjustment and report generation.
    """
    observations = [Observation(**obs) for obs in observations_json]
    start_point = Point(name=start_name, x=start_x, y=start_y, z=start_z)
    
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
    dump = result.model_dump()
    
    if generate_report:
        dump["report_md"] = generate_markdown_report(result)
        
    return dump

if __name__ == "__main__":
    mcp.run()
