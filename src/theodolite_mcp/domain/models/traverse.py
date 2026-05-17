from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from .base import Point

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
    model_config = ConfigDict(extra="forbid")
    point_name: str
    horizontal_angle: float  # in decimal degrees
    distance: float = 0.0
    vertical_angle: float = 0.0 # Zenith or Elevation angle
    is_sideshot: bool = False # If true, point is not part of the main traverse line

class EDMParameters(BaseModel):
    pressure_hpa: float = 1013.25
    temperature_c: float = 15.0
    frequency_const: float = 281.8 # Typical for many total stations

class TraverseData(BaseModel):
    start_point: Point
    end_point: Optional[Point] = None
    start_azimuth: float
    closing_azimuth: Optional[float] = None # For open traverses connecting two known lines
    observations: List[Observation]
    is_closed: bool = False
    average_elevation: float = 0.0 # For sea-level correction
    grid_scale_factor: float = 1.0 # For projection correction (UTM/State Plane)

class TraverseResult(BaseModel):
    points: List[Point]
    angular_misclosure: float
    linear_misclosure: float
    relative_precision: float
    total_length: float
    area: Optional[float] = None
    precision_status: Optional[str] = None
