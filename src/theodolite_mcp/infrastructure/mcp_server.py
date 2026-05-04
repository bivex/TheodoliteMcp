from mcp.server.fastmcp import FastMCP
from ..domain.models import TraverseData, Point, Observation, StadiaMeasurement, TraverseResult
from ..application.services import SurveyService
from ..domain.logic import (
    dms_to_decimal, decimal_to_dms, normalize_angle, 
    calculate_azimuth_from_points, calculate_stadia, 
    calculate_inverse, generate_markdown_report, calculate_area
)
import math

mcp = FastMCP("Survey Computation Engine")
service = SurveyService()

@mcp.tool()
def dms_to_decimal_degrees(degrees: int, minutes: int, seconds: float) -> float:
    """Converts Degrees, Minutes, Seconds to decimal degrees."""
    return dms_to_decimal(degrees, minutes, seconds)

@mcp.tool()
def decimal_degrees_to_dms(decimal: float) -> dict:
    """Converts decimal degrees to Degrees, Minutes, Seconds."""
    d, m, s = decimal_to_dms(decimal)
    return {"degrees": d, "minutes": m, "seconds": round(s, 2)}

@mcp.tool()
def compute_forward_azimuth(x1: float, y1: float, x2: float, y2: float) -> float:
    """Calculates the forward azimuth (bearing) from point 1 to point 2."""
    p1 = Point(name="P1", x=x1, y=y1)
    p2 = Point(name="P2", x=x2, y=y2)
    return calculate_azimuth_from_points(p1, p2)

@mcp.tool()
def compute_back_azimuth(azimuth: float) -> float:
    """Calculates the back azimuth (reverse bearing)."""
    return normalize_angle(azimuth + 180.0)

@mcp.tool()
def compute_inverse_geodetic_problem(x1: float, y1: float, x2: float, y2: float, 
                                     z1: float = None, z2: float = None) -> dict:
    """
    Solves the inverse geodetic problem: calculates azimuth, horizontal distance, 
    and vertical data between two known points.
    """
    p1 = Point(name="P1", x=x1, y=y1, z=z1)
    p2 = Point(name="P2", x=x2, y=y2, z=z2)
    return calculate_inverse(p1, p2)

@mcp.tool()
def reduce_stadia_readings(
    top_hair: float, 
    bottom_hair: float, 
    vertical_angle: float,
    hi: float = 0.0, 
    ht: float = 0.0
) -> dict:
    """
    Tacheometric reduction: computes horizontal distance and elevation from stadia readings.
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
def compute_parcel_area(points_json: list[dict]) -> float:
    """Calculates the area of a polygon from a list of coordinates (x, y)."""
    points = [Point(**pt) for pt in points_json]
    return calculate_area(points)

@mcp.tool()
def adjust_traverse_network(
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
    Performs Bowditch (Compass Rule) adjustment on a traverse network.
    Returns adjusted coordinates, misclosure analysis, and a professional report.
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
