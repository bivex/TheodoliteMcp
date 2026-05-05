from typing import List, Optional
from pydantic import BaseModel, Field

class Point(BaseModel):
    name: str = "P"
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None

class AsBuiltPoint(BaseModel):
    name: str
    design_x: float
    design_y: float
    actual_x: float
    actual_y: float
    design_z: Optional[float] = None
    actual_z: Optional[float] = None

class GridCell(BaseModel):
    center_x: float
    center_y: float
    size_m: float
    design_z: float
    actual_z: float
    volume: float # Positive for fill, negative for cut

class VolumeGrid(BaseModel):
    title: str = "Earthwork Cartogram"
    cells: List[GridCell]
    total_cut: float
    total_fill: float
    net_volume: float

class ProfilePoint(BaseModel):
    station: float # Distance along the line (e.g. 0.0, 100.0)
    ground_z: float
    design_z: Optional[float] = None
    remark: str = ""

class ProfilePlan(BaseModel):
    title: str = "Longitudinal Profile"
    project_number: str = "P-PROF-001"
    organization: str = "Engineering Bureau"
    date: str = "2026-05-05"
    points: List[ProfilePoint]
    language: str = "ru"
    paper_format: str = "A3"
    orientation: str = "landscape"
    horiz_scale: int = 1000
    vert_scale: int = 100 # Default 10x exaggeration
    dpi: int = 300

class Opening(BaseModel):
    type: str  # "door", "window"
    start_distance: float = Field(..., alias="position")
    width: float
    height: Optional[float] = 2.1
    direction: int = 1 # 1 or -1 for door opening side

    class Config:
        populate_by_name = True

class Wall(BaseModel):
    start_pt: Point
    end_pt: Point
    thickness: float = 0.3 # 300mm default
    material: str = "brick"
    status: str = "existing" # "existing", "demolish", "new"
    openings: List[Opening] = []

class Room(BaseModel):
    name: str
    number: str
    points: List[Point]
    floor_material: str = "concrete"

class FurnitureItem(BaseModel):
    type: str # "bed", "sofa", "table", "chair", "wc", "bath", "sink", "stove"
    center_pt: Point
    width: float
    length: float
    rotation: float = 0.0 # Degrees

class InteriorPlan(BaseModel):
    title: str = "Floor Plan"
    project_number: str = "A-001"
    organization: str = "Architecture Studio"
    date: str = "2026-05-05"
    walls: List[Wall]
    rooms: List[Room] = []
    furniture: List[FurnitureItem] = []
    language: str = "ru"
    paper_format: str = "A4"
    orientation: str = "landscape"
    scale: int = 50 # 1:50 default
    dpi: int = 300

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


class Zone(BaseModel):
    name: str
    points: List[Point]
    fill_color: Optional[str] = None
    fill_alpha: float = 0.3

class PlotPlan(BaseModel):
    title: str = "Cadastral Plan"
    project_number: str = "P-001"
    organization: str = "Engineering Bureau"
    date: str = "2026-05-05"
    boundary_points: List[Point]
    zones: List[Zone] = []
    language: str = "ru"  # "ru", "uk", "en"
    standard: str = "construction"  # "construction" (ISO 128-23) or "shipbuilding" (ISO 129-4)
    paper_format: str = "A4" # "A4", "A3", "A2", "A1", "A0"
    orientation: str = "landscape" # "landscape", "portrait"
    show_vertex_labels: bool = True
    show_distances: bool = True
    show_azimuths: bool = True
    show_areas: bool = True
    show_north_arrow: bool = True
    show_scale_bar: bool = True
    coordinate_labels: bool = False
    as_built_points: List[AsBuiltPoint] = []
    volume_grid: Optional[VolumeGrid] = None
    width_inches: float = 11.69 # Default A4 Landscape width
    height_inches: float = 8.27  # Default A4 Landscape height
    dpi: int = 300

