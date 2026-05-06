import io
import pytest
from theodolite_mcp.domain.models import Point, PlotPlan, Zone
from theodolite_mcp.domain.rendering import (
    render_plot_plan,
    _calculate_auto_scale,
    PAPER_SIZES,
)


def _make_large_plot(coord_mult=1.0, num_points=5, zone_names=None):
    """Helper to create plot with scalable coordinates."""
    base = 500000.0 * coord_mult  # Simulating large UTM-like coordinates
    boundary = [
        Point(name="P1", x=base, y=base),
        Point(name="P2", x=base + 1000.0, y=base),
        Point(name="P3", x=base + 1000.0, y=base + 1000.0),
        Point(name="P4", x=base, y=base + 1000.0),
    ]
    zones = []
    if zone_names:
        for i, name in enumerate(zone_names):
            zp = [
                Point(name=f"Z{i + 1}A", x=base + i * 200, y=base + i * 200),
                Point(name=f"Z{i + 1}B", x=base + i * 200 + 200, y=base + i * 200),
                Point(
                    name=f"Z{i + 1}C", x=base + i * 200 + 200, y=base + i * 200 + 200
                ),
                Point(name=f"Z{i + 1}D", x=base + i * 200, y=base + i * 200 + 200),
            ]
            zones.append(Zone(name=name, points=zp))

    return PlotPlan(
        title="Large Geodesy Test",
        boundary_points=boundary,
        zones=zones,
        paper_format="A3",
        orientation="landscape",
        show_vertex_labels=True,
        show_distances=True,
        show_azimuths=True,
        show_areas=True,
    )


def test_large_utm_coordinates_render():
    """Test rendering with large UTM-like coordinates (500k+)."""
    plan = _make_large_plot(coord_mult=1.0)
    png_bytes = render_plot_plan(plan)
    assert png_bytes.startswith(b"\x89PNG")
    assert len(png_bytes) > 10000  # Should be a valid PNG with content


def test_very_large_coordinates_millions():
    """Test rendering with coordinates in millions (military grid reference)."""
    plan = _make_large_plot(coord_mult=10.0)  # 5,000,000+ coordinates
    png_bytes = render_plot_plan(plan)
    assert png_bytes.startswith(b"\x89PNG")
    # Check it doesn't crash or produce invalid output
    assert len(png_bytes) > 5000


def test_extreme_coordinates_boundary():
    """Test that extreme coordinates don't cause rendering overflow."""
    # Coordinates near max float range (but reasonable for geodesy)
    base = 999999.0
    boundary = [
        Point(name="P1", x=base, y=base),
        Point(name="P2", x=base + 500.0, y=base),
        Point(name="P3", x=base + 500.0, y=base + 500.0),
        Point(name="P4", x=base, y=base + 500.0),
    ]
    plan = PlotPlan(
        title="Extreme Coords",
        boundary_points=boundary,
        paper_format="A3",
        orientation="landscape",
    )
    png_bytes = render_plot_plan(plan)
    assert png_bytes.startswith(b"\x89PNG")


def test_auto_scale_large_span():
    """Test auto-scale calculation for large coordinate spans."""
    # 100km span on A3 landscape (420mm - margins)
    avail_width = (
        420.0 - 20.0 - 10.0 - 20.0
    )  # A3 w - MARGIN_LEFT - MARGIN_OTHER - padding
    scale = _calculate_auto_scale(100000.0, avail_width)  # 100km
    # raw_scale = (100000 * 1000) / 370 ≈ 270270
    # Function returns raw_scale if no standard scale matches
    assert scale >= 1000
    assert scale > 100000  # Actual scale is ~270270 for 100km on A3


def test_auto_scale_very_large_span():
    """Test auto-scale for very large areas (e.g., military training grounds)."""
    # 500km span
    avail_width = 841.0 - 20.0 - 10.0 - 20.0  # A1 landscape (approx 791mm)
    scale = _calculate_auto_scale(500000.0, avail_width)
    # raw_scale = (500000 * 1000) / 791 ≈ 632111
    assert scale >= 10000
    assert scale > 500000  # Actual scale is ~632111 for 500km on A1


def test_large_zone_count_rendering():
    """Test rendering with many zones (large military base sections)."""
    zone_names = [f"Section {i + 1}" for i in range(20)]
    plan = _make_large_plot(coord_mult=1.0, zone_names=zone_names)
    png_bytes = render_plot_plan(plan)
    assert png_bytes.startswith(b"\x89PNG")
    assert len(png_bytes) > 20000  # More zones = larger PNG


def test_different_paper_sizes_large_data():
    """Test large geodesy on different paper sizes."""
    plan = _make_large_plot(coord_mult=1.0)
    for fmt in ["A4", "A3", "A2", "A1", "A0"]:
        plan.paper_format = fmt
        png_bytes = render_plot_plan(plan)
        assert png_bytes.startswith(b"\x89PNG"), f"Failed for {fmt}"
        # A0 should produce larger PNG
        assert len(png_bytes) > 10000


def test_coordinate_labels_large_values():
    """Test that coordinate labels work with large values."""
    plan = _make_large_plot(coord_mult=1.0)
    plan.coordinate_labels = True  # Show full coordinates
    png_bytes = render_plot_plan(plan)
    assert png_bytes.startswith(b"\x89PNG")


def test_shipbuilding_large_coordinates():
    """Test shipbuilding standard with large coordinates."""
    plan = _make_large_plot(coord_mult=1.0)
    plan.standard = "shipbuilding"
    plan.language = "en"
    png_bytes = render_plot_plan(plan)
    assert png_bytes.startswith(b"\x89PNG")


def test_render_output_valid_png():
    """Verify rendered output is a valid PNG with correct structure."""
    plan = _make_large_plot(coord_mult=1.0)
    png_bytes = render_plot_plan(plan)

    # Check PNG signature
    assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"

    # Check IHDR chunk exists (starts at byte 8)
    # IHDR length (4 bytes), IHDR tag (4 bytes)
    assert png_bytes[12:16] == b"IHDR"

    # Check IEND chunk at the end
    assert png_bytes[-8:-4] == b"IEND"


def test_rendering_does_not_crash_with_zero_area():
    """Test edge case where area might be zero or very small."""
    boundary = [
        Point(name="P1", x=500000.0, y=500000.0),
        Point(name="P2", x=500001.0, y=500000.0),
        Point(name="P3", x=500001.0, y=500001.0),
        Point(name="P4", x=500000.0, y=500001.0),
    ]
    plan = PlotPlan(
        title="Small Area", boundary_points=boundary, paper_format="A4", show_areas=True
    )
    png_bytes = render_plot_plan(plan)
    assert png_bytes.startswith(b"\x89PNG")


def test_large_coordinates_negative():
    """Test rendering with negative large coordinates (southern hemisphere)."""
    boundary = [
        Point(name="P1", x=-500000.0, y=-500000.0),
        Point(name="P2", x=-499000.0, y=-500000.0),
        Point(name="P3", x=-499000.0, y=-499000.0),
        Point(name="P4", x=-500000.0, y=-499000.0),
    ]
    plan = PlotPlan(
        title="Negative Coords", boundary_points=boundary, paper_format="A3"
    )
    png_bytes = render_plot_plan(plan)
    assert png_bytes.startswith(b"\x89PNG")


def test_mixed_large_negative_coordinates():
    """Test rendering with mixed positive/negative large coordinates."""
    boundary = [
        Point(name="P1", x=-500000.0, y=500000.0),
        Point(name="P2", x=500000.0, y=500000.0),
        Point(name="P3", x=500000.0, y=-500000.0),
        Point(name="P4", x=-500000.0, y=-500000.0),
    ]
    plan = PlotPlan(
        title="Mixed Coords",
        boundary_points=boundary,
        paper_format="A2",
        orientation="landscape",
    )
    png_bytes = render_plot_plan(plan)
    assert png_bytes.startswith(b"\x89PNG")
    assert len(png_bytes) > 10000
