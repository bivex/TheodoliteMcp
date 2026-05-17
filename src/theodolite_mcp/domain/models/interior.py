from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from .base import Point


class Opening(BaseModel):
    type: str  # "door", "window", "arch"
    start_distance: float = Field(..., alias="position")
    width: float
    height: Optional[float] = 2.1
    direction: int = 1  # 1 or -1 for door opening side
    swing_angle: float = 90.0  # Opening arc angle
    status: str = "existing"  # "existing", "demolish", "new"

    model_config = ConfigDict(populate_by_name=True)


class Wall(BaseModel):
    start_pt: Point
    end_pt: Point
    thickness: float = 0.3  # 300mm default
    material: str = "brick"
    status: str = "existing"  # "existing", "demolish", "new"
    openings: List[Opening] = []


class Room(BaseModel):
    name: str
    number: str
    points: List[Point]
    floor_material: str = "concrete"
    floor_pattern: Optional[str] = None  # "tiles", "parquet", "planks", "grid"
    floor_tile_size: Optional[List[float]] = [0.6, 0.6]  # [width, length] in meters
    floor_angle: float = 0.0  # Rotation of floor pattern
    wall_finish: Optional[str] = None
    ceiling_height: float = 2.7
    tags: List[str] = []


class FurnitureItem(BaseModel):
    type: str  # "bed", "sofa", "table", "chair", "wc", "bath", "sink", "stove", "fridge", "washer"
    center_pt: Point
    width: float
    length: float
    rotation: float = 0.0  # Degrees
    status: str = "new"  # "existing", "new"
    label: Optional[str] = None
    price: Optional[float] = None
    currency: str = "UAH"
    ergonomics_padding: float = 0.0  # Required clear distance around object


class EngineeringItem(BaseModel):
    type: str  # "socket", "switch", "lamp", "radiator", "ac", "vent", "water_outlet", "boiler"
    point: Point
    rotation: float = 0.0
    level: float = 0.0  # Height from floor
    label: Optional[str] = None
    price: Optional[float] = None
    currency: str = "UAH"


class DimensionLine(BaseModel):
    points: List[Point]  # Chained points for dimension line
    offset: float = 0.5  # Distance from objects
    label_format: str = "{:.0f}"  # mm by default in interior


class SecurityItem(BaseModel):
    type: str  # "camera", "motion_sensor", "door_sensor", "glass_break", "keypad", "siren"
    point: Point
    rotation: float = 0.0
    fov_angle: float = 90.0  # For cameras and motion sensors
    range: float = 5.0  # Effective distance in meters
    label: Optional[str] = None


class InteriorPlan(BaseModel):
    title: str = "Floor Plan"
    project_number: str = "A-001"
    organization: str = "Architecture Studio"
    date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    walls: List[Wall]
    rooms: List[Room] = []
    furniture: List[FurnitureItem] = []
    engineering: List[EngineeringItem] = []
    security: List[SecurityItem] = []
    dimensions: List[DimensionLine] = []
    layer: str = "full"  # "full", "furniture", "electrical", "construction", "security"
    show_ergonomics: bool = False  # Highlight clearance violations
    language: str = "ru"
    paper_format: str = "A4"
    orientation: str = "landscape"
    scale: int = 50  # 1:50 default
    dpi: int = 300


class InteriorReport(BaseModel):
    plan: InteriorPlan
    tile_counts: dict[str, dict[str, int]] = {}  # room_name -> {total, cut}
    material_list: list[dict[str, str]] = []
    furniture_list: list[dict[str, str]] = []
    engineering_list: list[dict[str, str]] = []
    security_list: list[dict[str, str]] = []
    ergonomics_warnings: list[str] = []
    total_area: float = 0.0
    total_cost: float = 0.0
    currency: str = "UAH"
