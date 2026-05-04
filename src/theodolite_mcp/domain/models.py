from typing import List, Optional
from pydantic import BaseModel, Field

class Point(BaseModel):
    name: str
    x: Optional[float] = None
    y: Optional[float] = None

class Observation(BaseModel):
    point_name: str
    horizontal_angle: float  # in decimal degrees
    distance: float = 0.0

class TraverseData(BaseModel):
    start_point: Point
    end_point: Optional[Point] = None
    start_azimuth: float
    observations: List[Observation]
    is_closed: bool = False

class TraverseResult(BaseModel):
    points: List[Point]
    angular_misclosure: float
    linear_misclosure: float
    relative_precision: float
    total_length: float
    area: Optional[float] = None
    precision_status: Optional[str] = None
