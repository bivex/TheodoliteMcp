from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from .base import Point


class PipeMedium:
    """Media type constants with standard color coding (ISO 6412)."""
    HEATING_SUPPLY = "heating_supply"
    HEATING_RETURN = "heating_return"
    COLD_WATER = "cold_water"
    HOT_WATER = "hot_water"
    GAS = "gas"
    STEAM = "steam"
    CONDENSATE = "condensate"
    DRAINAGE = "drainage"
    CUSTOM = "custom"


class ValveType:
    """ISO 14617 valve symbol types."""
    GATE = "gate"
    BALL = "ball"
    GLOBE = "globe"
    CHECK = "check"
    BUTTERFLY = "butterfly"
    THREE_WAY_MIXING = "3way_mixing"
    PRESSURE_REDUCING = "prv"
    SAFETY_RELIEF = "safety"


class EquipmentType:
    """ISO 14617 equipment symbol types for boiler/heating installations."""
    CENTRIFUGAL_PUMP = "centrifugal_pump"
    CIRCULATION_PUMP = "circulation_pump"
    SHELL_TUBE_HX = "shell_tube_hx"
    PLATE_HX = "plate_hx"
    BOILER = "boiler"
    RADIATOR = "radiator"
    MANIFOLD = "manifold"
    EXPANSION_VESSEL = "expansion_vessel"
    STORAGE_TANK = "storage_tank"
    Y_STRAINER = "y_strainer"
    MESH_FILTER = "mesh_filter"
    PRESSURE_GAUGE = "pressure_gauge"
    THERMOMETER = "thermometer"
    FLOW_METER = "flow_meter"
    HEAT_METER = "heat_meter"


class FittingType:
    """ISO 14617 fitting symbol types."""
    ELBOW_90 = "elbow_90"
    ELBOW_45 = "elbow_45"
    TEE = "tee"
    REDUCER = "reducer"
    UNION = "union"
    FLANGE = "flange"
    CROSS = "cross"


class PipeSupportType:
    """Pipe support/hanger types."""
    ANCHOR = "anchor"
    GUIDE = "guide"
    HANGER = "hanger"
    SPRING = "spring"


class PipeSegment(BaseModel):
    """A single pipe run between two points (ISO 6412)."""
    start_pt: Point
    end_pt: Point
    medium: str = PipeMedium.HEATING_SUPPLY
    nominal_diameter: int = 25  # DN in mm
    insulated: bool = False
    flow_direction: str = "forward"  # "forward", "backward", "none"
    custom_color: Optional[str] = None


class ValveSymbol(BaseModel):
    """A valve placed on the schematic (ISO 14617)."""
    center_pt: Point
    valve_type: str = ValveType.GATE
    rotation: float = 0.0
    nominal_diameter: int = 25
    tag: Optional[str] = None


class EquipmentSymbol(BaseModel):
    """Equipment placed on the schematic (ISO 14617)."""
    center_pt: Point
    equipment_type: str = EquipmentType.BOILER
    rotation: float = 0.0
    tag: Optional[str] = None
    width: float = 0.5
    height: float = 0.5
    label: Optional[str] = None


class FittingSymbol(BaseModel):
    """A fitting placed on the schematic (ISO 14617)."""
    center_pt: Point
    fitting_type: str = FittingType.ELBOW_90
    rotation: float = 0.0
    nominal_diameter: int = 25


class InstrumentSymbol(BaseModel):
    """ISO 3511 P&ID instrument bubble."""
    center_pt: Point
    measured_variable: str = "T"  # T=Temperature, P=Pressure, F=Flow, L=Level
    suffix: str = "I"  # I=Indicator, R=Recorder, C=Controller, T=Transmitter
    tag_number: str = "001"
    in_dcs: bool = False  # True=square+circle (DCS), False=circle (field)


class PipeSupport(BaseModel):
    """A pipe support symbol."""
    center_pt: Point
    support_type: str = PipeSupportType.GUIDE


class PipelineSchematic(BaseModel):
    """Top-level model for an ISO 6412/14617/3511 pipeline schematic."""
    title: str = "Pipeline Schematic"
    project_number: str = "P-001"
    organization: str = "Engineering Bureau"
    date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    pipes: List[PipeSegment] = []
    valves: List[ValveSymbol] = []
    equipment: List[EquipmentSymbol] = []
    fittings: List[FittingSymbol] = []
    instruments: List[InstrumentSymbol] = []
    supports: List[PipeSupport] = []
    language: str = "ru"
    paper_format: str = "A3"
    orientation: str = "landscape"
    scale: int = 50
    dpi: int = 300
    show_legend: bool = True
    show_tags: bool = True
