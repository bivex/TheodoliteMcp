from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from .base import Point


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
    volume: float  # Positive for fill, negative for cut


class VolumeGrid(BaseModel):
    title: str = "Earthwork Cartogram"
    cells: List[GridCell]
    total_cut: float
    total_fill: float
    net_volume: float


class Zone(BaseModel):
    name: str
    points: List[Point]
    fill_color: Optional[str] = None
    fill_alpha: float = 0.3


class PlotPlan(BaseModel):
    title: str = "Cadastral Plan"
    project_number: str = "P-001"
    organization: str = "Engineering Bureau"
    date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    boundary_points: List[Point]
    zones: List[Zone] = []
    language: str = "ru"  # "ru", "uk", "en"
    standard: str = (
        "construction"  # "construction" (ISO 128-23) or "shipbuilding" (ISO 129-4)
    )
    paper_format: str = "A4"  # "A4", "A3", "A2", "A1", "A0"
    orientation: str = "landscape"  # "landscape", "portrait"
    show_vertex_labels: bool = True
    show_distances: bool = True
    show_azimuths: bool = True
    show_areas: bool = True
    show_north_arrow: bool = True
    show_scale_bar: bool = True
    coordinate_labels: bool = False
    collision_avoidance: bool = True  # Smart label placement to avoid overlaps
    as_built_points: List[AsBuiltPoint] = []
    volume_grid: Optional[VolumeGrid] = None
    width_inches: float = 11.69  # Default A4 Landscape width
    height_inches: float = 8.27  # Default A4 Landscape height
    dpi: int = 300
