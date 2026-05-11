import pytest
from theodolite_mcp.domain.models.schematic import (
    PipelineSchematic, Point, PipeSegment, ValveSymbol, 
    EquipmentSymbol, FittingSymbol, InstrumentSymbol, PipeSupport,
    PipeMedium, ValveType, EquipmentType, FittingType
)
from theodolite_mcp.domain.schematic_rendering import render_pipeline_schematic

def test_render_minimal_schematic():
    plan = PipelineSchematic(
        title="Minimal Schematic",
        pipes=[
            PipeSegment(
                start_pt=Point(x=0, y=0),
                end_pt=Point(x=5, y=0),
                medium=PipeMedium.HEATING_SUPPLY,
                nominal_diameter=50
            )
        ]
    )
    png_bytes = render_pipeline_schematic(plan)
    assert len(png_bytes) > 0
    assert png_bytes.startswith(b'\x89PNG')

def test_render_complex_schematic_png():
    plan = PipelineSchematic(
        title="Complex Test Schematic",
        pipes=[
            PipeSegment(start_pt=Point(x=0, y=0), end_pt=Point(x=10, y=0), medium=PipeMedium.HEATING_SUPPLY),
            PipeSegment(start_pt=Point(x=10, y=0), end_pt=Point(x=10, y=5), medium=PipeMedium.HEATING_SUPPLY),
        ],
        valves=[
            ValveSymbol(center_pt=Point(x=5, y=0), valve_type=ValveType.GATE, tag="V1"),
            ValveSymbol(center_pt=Point(x=10, y=2.5), valve_type=ValveType.CHECK, rotation=90, tag="V2"),
        ],
        equipment=[
            EquipmentSymbol(center_pt=Point(x=0, y=0), equipment_type=EquipmentType.BOILER, tag="B1", label="Main Boiler"),
            EquipmentSymbol(center_pt=Point(x=10, y=5), equipment_type=EquipmentType.CIRCULATION_PUMP, tag="P1"),
        ],
        fittings=[
            FittingSymbol(center_pt=Point(x=10, y=0), fitting_type=FittingType.ELBOW_90),
        ],
        instruments=[
            InstrumentSymbol(center_pt=Point(x=3, y=0), measured_variable="T", tag_number="101"),
        ],
        supports=[
            PipeSupport(center_pt=Point(x=7, y=0)),
        ]
    )
    png_bytes = render_pipeline_schematic(plan, output_format="png")
    assert len(png_bytes) > 0
    assert png_bytes.startswith(b'\x89PNG')

def test_render_complex_schematic_svg():
    plan = PipelineSchematic(
        title="SVG Test Schematic",
        pipes=[
            PipeSegment(start_pt=Point(x=0, y=0), end_pt=Point(x=5, y=0))
        ]
    )
    svg_bytes = render_pipeline_schematic(plan, output_format="svg")
    assert len(svg_bytes) > 0
    assert b"<svg" in svg_bytes
    assert b"</svg>" in svg_bytes

def test_schematic_all_valve_types():
    # Smoke test for all valve types to ensure no rendering errors
    valve_types = [
        ValveType.GATE, ValveType.BALL, ValveType.GLOBE, ValveType.CHECK,
        ValveType.BUTTERFLY, ValveType.THREE_WAY_MIXING, 
        ValveType.PRESSURE_REDUCING, ValveType.SAFETY_RELIEF
    ]
    valves = [
        ValveSymbol(center_pt=Point(x=i, y=0), valve_type=vt)
        for i, vt in enumerate(valve_types)
    ]
    plan = PipelineSchematic(title="All Valves", valves=valves)
    png_bytes = render_pipeline_schematic(plan)
    assert len(png_bytes) > 0

def test_schematic_all_equipment_types():
    # Smoke test for all equipment types
    eq_types = [
        EquipmentType.CENTRIFUGAL_PUMP, EquipmentType.CIRCULATION_PUMP,
        EquipmentType.BOILER, EquipmentType.SHELL_TUBE_HX, EquipmentType.PLATE_HX,
        EquipmentType.EXPANSION_VESSEL, EquipmentType.STORAGE_TANK,
        EquipmentType.Y_STRAINER, EquipmentType.MESH_FILTER,
        EquipmentType.PRESSURE_GAUGE, EquipmentType.THERMOMETER,
        EquipmentType.FLOW_METER, EquipmentType.HEAT_METER
    ]
    equipment = [
        EquipmentSymbol(center_pt=Point(x=i%4, y=i//4), equipment_type=et)
        for i, et in enumerate(eq_types)
    ]
    plan = PipelineSchematic(title="All Equipment", equipment=equipment)
    png_bytes = render_pipeline_schematic(plan)
    assert len(png_bytes) > 0
