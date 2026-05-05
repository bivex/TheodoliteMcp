import pytest
from theodolite_mcp.domain.models import Point, PlotPlan
from theodolite_mcp.domain.rendering import _calculate_auto_scale, render_plot_plan

def test_auto_scale_calculation():
    # 100m span over 185mm (approx STAMP_WIDTH)
    # raw_scale = (100 * 1000) / 185 = 540.5
    # Should pick 1000 or 500? In our list: [500, 1000] -> 1000
    scale = _calculate_auto_scale(100.0, 185.0)
    assert scale == 1000

    # 10m span over 200mm
    # raw_scale = (10 * 1000) / 200 = 50
    # Should pick 50
    scale = _calculate_auto_scale(10.0, 200.0)
    assert scale == 50

def test_render_iso_a4():
    boundary = [
        Point(name="1", x=0, y=0),
        Point(name="2", x=50, y=0),
        Point(name="3", x=50, y=50),
        Point(name="4", x=0, y=50),
    ]
    plan = PlotPlan(
        title="Test A4",
        boundary_points=boundary,
        paper_format="A4",
        orientation="landscape"
    )
    png_bytes = render_plot_plan(plan)
    assert len(png_bytes) > 0
    assert png_bytes.startswith(b'\x89PNG')

def test_render_iso_a3_portrait():
    boundary = [
        Point(name="1", x=0, y=0),
        Point(name="2", x=100, y=0),
        Point(name="3", x=100, y=200),
        Point(name="4", x=0, y=200),
    ]
    plan = PlotPlan(
        title="Test A3 Portrait",
        boundary_points=boundary,
        paper_format="A3",
        orientation="portrait"
    )
    png_bytes = render_plot_plan(plan)
    assert len(png_bytes) > 0
    assert png_bytes.startswith(b'\x89PNG')
