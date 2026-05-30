"""Tests for SVG output across all drawing tools."""

import pytest
from theodolite_mcp.domain.models import (
    Point, Wall, Opening, Room, InteriorPlan, FurnitureItem,
    PlotPlan, Zone, AsBuiltPoint,
)
from theodolite_mcp.domain.models.profile import ProfilePlan, ProfilePoint
from theodolite_mcp.domain.models.schematic import (
    PipelineSchematic, PipeSegment, ValveSymbol, EquipmentSymbol,
    PipeMedium, ValveType, EquipmentType, InstrumentSymbol,
)
from theodolite_mcp.domain.rendering import (
    render_plot_plan, render_profile_plan, render_interior_plan,
)
from theodolite_mcp.domain.schematic_rendering import render_pipeline_schematic


def _assert_valid_svg(data: bytes):
    assert isinstance(data, bytes)
    assert len(data) > 100
    assert b"<svg" in data
    assert b"</svg>" in data


# ── Plot Plan SVG ──────────────────────────────────────────────────────

class TestPlotPlanSVG:
    def test_with_boundary(self):
        plan = PlotPlan(
            title="Boundary SVG",
            boundary_points=[
                Point(x=0, y=0), Point(x=100, y=0),
                Point(x=100, y=100), Point(x=0, y=100),
            ],
        )
        svg = render_plot_plan(plan, output_format="svg")
        _assert_valid_svg(svg)

    def test_with_zones(self):
        plan = PlotPlan(
            title="Zoned SVG",
            boundary_points=[
                Point(x=0, y=0), Point(x=50, y=0),
                Point(x=50, y=50), Point(x=0, y=50),
            ],
            zones=[
                Zone(name="Building", points=[
                    Point(x=5, y=5), Point(x=25, y=5),
                    Point(x=25, y=25), Point(x=5, y=25),
                ], fill_color="#FF0000"),
            ],
        )
        svg = render_plot_plan(plan, output_format="svg")
        _assert_valid_svg(svg)

    def test_as_built_report(self):
        plan = PlotPlan(
            title="As-Built SVG",
            boundary_points=[],
            as_built_points=[
                AsBuiltPoint(
                    name="P1",
                    design_x=10.0, design_y=20.0,
                    actual_x=10.05, actual_y=19.98,
                ),
            ],
        )
        svg = render_plot_plan(plan, output_format="svg")
        _assert_valid_svg(svg)

    def test_language_en(self):
        plan = PlotPlan(
            title="English Plan",
            boundary_points=[Point(x=0, y=0), Point(x=10, y=10)],
            language="en",
        )
        svg = render_plot_plan(plan, output_format="svg")
        _assert_valid_svg(svg)

    def test_multiple_zones(self):
        plan = PlotPlan(
            title="Multi-Zone SVG",
            boundary_points=[
                Point(x=0, y=0), Point(x=100, y=0),
                Point(x=100, y=100), Point(x=0, y=100),
            ],
            zones=[
                Zone(name="Zone A", points=[
                    Point(x=0, y=0), Point(x=50, y=0),
                    Point(x=50, y=50), Point(x=0, y=50),
                ]),
                Zone(name="Zone B", points=[
                    Point(x=50, y=50), Point(x=100, y=50),
                    Point(x=100, y=100), Point(x=50, y=100),
                ], fill_color="#0000FF"),
            ],
        )
        svg = render_plot_plan(plan, output_format="svg")
        _assert_valid_svg(svg)


# ── Profile Plan SVG ───────────────────────────────────────────────────

class TestProfilePlanSVG:
    def test_basic_profile(self):
        plan = ProfilePlan(
            title="Profile SVG",
            points=[
                ProfilePoint(station=0, ground_z=100.0),
                ProfilePoint(station=50, ground_z=102.5),
                ProfilePoint(station=100, ground_z=98.0),
            ],
        )
        svg = render_profile_plan(plan, output_format="svg")
        _assert_valid_svg(svg)

    def test_with_design_line(self):
        plan = ProfilePlan(
            title="Design Profile SVG",
            points=[
                ProfilePoint(station=0, ground_z=100.0, design_z=101.0),
                ProfilePoint(station=50, ground_z=102.5, design_z=101.5),
                ProfilePoint(station=100, ground_z=98.0, design_z=102.0),
            ],
        )
        svg = render_profile_plan(plan, output_format="svg")
        _assert_valid_svg(svg)

    def test_single_point(self):
        plan = ProfilePlan(
            title="Single Point SVG",
            points=[ProfilePoint(station=0, ground_z=50.0)],
        )
        svg = render_profile_plan(plan, output_format="svg")
        _assert_valid_svg(svg)

    def test_language_en(self):
        plan = ProfilePlan(
            title="English Profile",
            points=[
                ProfilePoint(station=0, ground_z=100.0),
                ProfilePoint(station=25, ground_z=101.0),
            ],
            language="en",
        )
        svg = render_profile_plan(plan, output_format="svg")
        _assert_valid_svg(svg)


# ── Interior Plan SVG ──────────────────────────────────────────────────

class TestInteriorPlanSVG:
    def test_with_walls(self):
        plan = InteriorPlan(
            title="Walls SVG",
            walls=[
                Wall(start_pt=Point(x=0, y=0), end_pt=Point(x=5, y=0), thickness=0.3),
                Wall(start_pt=Point(x=5, y=0), end_pt=Point(x=5, y=4), thickness=0.3),
                Wall(start_pt=Point(x=5, y=4), end_pt=Point(x=0, y=4), thickness=0.3),
                Wall(start_pt=Point(x=0, y=4), end_pt=Point(x=0, y=0), thickness=0.3),
            ],
            rooms=[Room(name="Room 1", number="101", points=[
                Point(x=0.5, y=0.5), Point(x=4.5, y=3.5)
            ])],
        )
        svg = render_interior_plan(plan, output_format="svg")
        _assert_valid_svg(svg)

    def test_with_door_opening(self):
        plan = InteriorPlan(
            title="Door SVG",
            walls=[
                Wall(start_pt=Point(x=0, y=0), end_pt=Point(x=5, y=0), thickness=0.25,
                     openings=[Opening(type="door", start_distance=1.0, width=0.9)]),
            ],
        )
        svg = render_interior_plan(plan, output_format="svg")
        _assert_valid_svg(svg)

    def test_with_furniture(self):
        plan = InteriorPlan(
            title="Furniture SVG",
            walls=[
                Wall(start_pt=Point(x=0, y=0), end_pt=Point(x=6, y=0), thickness=0.2),
                Wall(start_pt=Point(x=6, y=0), end_pt=Point(x=6, y=5), thickness=0.2),
                Wall(start_pt=Point(x=6, y=5), end_pt=Point(x=0, y=5), thickness=0.2),
                Wall(start_pt=Point(x=0, y=5), end_pt=Point(x=0, y=0), thickness=0.2),
            ],
            furniture=[
                FurnitureItem(type="bed", center_pt=Point(x=1.5, y=3.5), width=1.6, length=2.0),
                FurnitureItem(type="wc", center_pt=Point(x=5, y=1), width=0.5, length=0.7),
            ],
        )
        svg = render_interior_plan(plan, output_format="svg")
        _assert_valid_svg(svg)

    def test_language_en(self):
        plan = InteriorPlan(
            title="English Interior",
            walls=[
                Wall(start_pt=Point(x=0, y=0), end_pt=Point(x=3, y=0), thickness=0.2),
            ],
            language="en",
        )
        svg = render_interior_plan(plan, output_format="svg")
        _assert_valid_svg(svg)


# ── Pipeline Schematic SVG ─────────────────────────────────────────────

class TestPipelineSchematicSVG:
    def test_minimal(self):
        plan = PipelineSchematic(
            title="Minimal SVG",
            pipes=[
                PipeSegment(start_pt=Point(x=0, y=0), end_pt=Point(x=5, y=0))
            ],
        )
        svg = render_pipeline_schematic(plan, output_format="svg")
        _assert_valid_svg(svg)

    def test_with_valves_and_equipment(self):
        plan = PipelineSchematic(
            title="Complex SVG",
            pipes=[
                PipeSegment(start_pt=Point(x=0, y=0), end_pt=Point(x=10, y=0),
                            medium=PipeMedium.HEATING_SUPPLY, nominal_diameter=50),
            ],
            valves=[
                ValveSymbol(center_pt=Point(x=5, y=0), valve_type=ValveType.GATE, tag="V1"),
            ],
            equipment=[
                EquipmentSymbol(center_pt=Point(x=0, y=0), equipment_type=EquipmentType.BOILER,
                                tag="B1", label="Boiler"),
            ],
            instruments=[
                InstrumentSymbol(center_pt=Point(x=3, y=0), measured_variable="T", tag_number="01"),
            ],
        )
        svg = render_pipeline_schematic(plan, output_format="svg")
        _assert_valid_svg(svg)

    def test_heating_system(self):
        """Simulate the heating system tool's plan."""
        pipes = [
            PipeSegment(start_pt=Point(x=3, y=9.5), end_pt=Point(x=8, y=9.5),
                        medium=PipeMedium.HEATING_SUPPLY, nominal_diameter=32),
            PipeSegment(start_pt=Point(x=3, y=4.5), end_pt=Point(x=8, y=4.5),
                        medium=PipeMedium.HEATING_RETURN, nominal_diameter=32),
        ]
        equipment = [
            EquipmentSymbol(center_pt=Point(x=2, y=7), equipment_type=EquipmentType.BOILER,
                            tag="B1", label="Boiler", width=2.0, height=3.0),
            EquipmentSymbol(center_pt=Point(x=6, y=4.5),
                            equipment_type=EquipmentType.CIRCULATION_PUMP,
                            tag="PU1", label="Pump", width=0.8, height=0.8),
        ]
        valves = [
            ValveSymbol(center_pt=Point(x=4, y=9.5), valve_type=ValveType.BALL, tag="V1"),
        ]
        plan = PipelineSchematic(
            title="Heating System SVG", pipes=pipes, equipment=equipment, valves=valves
        )
        svg = render_pipeline_schematic(plan, output_format="svg")
        _assert_valid_svg(svg)


# ── PNG vs SVG parity ──────────────────────────────────────────────────

class TestPNGSVGParity:
    """Both formats should succeed for the same input data."""

    def test_plot_plan_both_formats(self):
        plan = PlotPlan(
            title="Parity Test",
            boundary_points=[
                Point(x=0, y=0), Point(x=50, y=0),
                Point(x=50, y=50), Point(x=0, y=50),
            ],
        )
        png = render_plot_plan(plan, output_format="png")
        svg = render_plot_plan(plan, output_format="svg")
        assert png.startswith(b"\x89PNG")
        assert b"<svg" in svg

    def test_profile_plan_both_formats(self):
        plan = ProfilePlan(
            title="Parity Profile",
            points=[
                ProfilePoint(station=0, ground_z=100.0),
                ProfilePoint(station=50, ground_z=105.0),
            ],
        )
        png = render_profile_plan(plan, output_format="png")
        svg = render_profile_plan(plan, output_format="svg")
        assert png.startswith(b"\x89PNG")
        assert b"<svg" in svg

    def test_interior_plan_both_formats(self):
        plan = InteriorPlan(
            title="Parity Interior",
            walls=[Wall(start_pt=Point(x=0, y=0), end_pt=Point(x=5, y=0), thickness=0.2)],
        )
        png = render_interior_plan(plan, output_format="png")
        svg = render_interior_plan(plan, output_format="svg")
        assert png.startswith(b"\x89PNG")
        assert b"<svg" in svg

    def test_schematic_both_formats(self):
        plan = PipelineSchematic(
            title="Parity Schematic",
            pipes=[PipeSegment(start_pt=Point(x=0, y=0), end_pt=Point(x=5, y=0))],
        )
        png = render_pipeline_schematic(plan, output_format="png")
        svg = render_pipeline_schematic(plan, output_format="svg")
        assert png.startswith(b"\x89PNG")
        assert b"<svg" in svg
