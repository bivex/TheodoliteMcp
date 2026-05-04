from typing import List, Optional
from pydantic import BaseModel, Field

class Point(BaseModel):
    name: str
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None

class StadiaMeasurement(BaseModel):
    top_hair: float
    bottom_hair: float
    vertical_angle: float  # Elevation angle in decimal degrees
    instrument_height: float = 0.0
    target_height: float = 0.0
    constant_k: float = 100.0
    constant_c: float = 0.0

class StadiaResult(BaseModel):
    horizontal_distance: float
    vertical_distance: float
    elevation_diff: float

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
