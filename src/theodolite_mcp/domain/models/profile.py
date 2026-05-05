from typing import List, Optional
from pydantic import BaseModel
from .base import Point

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
