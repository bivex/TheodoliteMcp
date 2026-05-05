from typing import List, Optional
from pydantic import BaseModel, Field
from .base import Point

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
