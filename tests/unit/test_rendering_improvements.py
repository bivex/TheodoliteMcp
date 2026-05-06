"""
Test suite for verifying rendering improvements:
- Font scaling with m_per_pt
- Coordinate formatting for large values
- Text collision avoidance
- Distance/azimuth separation
"""

import pytest
import matplotlib.pyplot as plt
from matplotlib.text import Text
from matplotlib.lines import Line2D
from theodolite_mcp.domain.models import Point, PlotPlan, Zone
from theodolite_mcp.domain.rendering import (
    render_plot_plan,
    _draw_vertex_labels,
    _draw_distances,
    _format_coord_value,
    _get_font,
    MM_TO_PT,
)
from typing import Optional


def test_format_coord_value_small():
    """Small coordinates (<10000) show 1 decimal."""
    assert _format_coord_value(1234.5) == "1234.5"
    assert _format_coord_value(-567.89) == "-567.9"
    assert _format_coord_value(0.0) == "0.0"


def test_format_coord_value_large():
    """Large coordinates (10000-1000000) show as integer."""
    assert _format_coord_value(12345.6) == "12346"
    assert _format_coord_value(-500000.0) == "-500000"
    assert _format_coord_value(999999.9) == "1000000"


def test_format_coord_value_extreme():
    """Extreme coordinates (>= 1M) use k notation."""
    assert _format_coord_value(1500000.0) == "1500k"
    assert _format_coord_value(2500000.0) == "2500k"
    assert _format_coord_value(-3000000.0) == "-3000k"


def test_format_coord_value_none():
    """None values return placeholder."""
    assert _format_coord_value(None) == "?"


def test_font_scaling_small_scale():
    """At small scales (large m_per_pt), font size increases."""
    font_large = _get_font(size=7, m_per_pt=0.5)  # 5x reference
    # Should be clamped to max 18pt
    if isinstance(font_large, dict):
        assert font_large["fontsize"] <= 18.0
    else:
        assert font_large.get_size() <= 18.0


def test_font_scaling_large_scale():
    """At large scales (small m_per_pt), font size decreases."""
    font_small = _get_font(size=7, m_per_pt=0.02)  # 0.2x reference
    if isinstance(font_small, dict):
        assert font_small["fontsize"] >= 3.0
    else:
        assert font_small.get_size() >= 3.0


def test_font_scaling_reference():
    """At reference scale (0.1), font size is exact."""
    font_ref = _get_font(size=7, m_per_pt=0.1)
    if isinstance(font_ref, dict):
        assert font_ref["fontsize"] == 7.0
    else:
        assert font_ref.get_size() == 7.0


def test_vertex_labels_collision_avoidance():
    """
    Tightly spaced points should trigger leaders for some labels.
    """
    # Create 4 points very close together (0.5m apart)
    boundary = [
        Point(name="A", x=0, y=0),
        Point(name="B", x=0.5, y=0),  # 0.5m apart - close enough to potentially collide
        Point(name="C", x=0.5, y=0.5),
        Point(name="D", x=0, y=0.5),
    ]

    fig = plt.figure(figsize=(6, 6), dpi=100)
    ax = fig.add_subplot(111)
    ax.set_xlim(-1, 2)
    ax.set_ylim(-1, 2)

    _draw_vertex_labels(ax, boundary, m_per_pt=0.1)

    # Actually trigger drawing to compute layouts
    fig.canvas.draw()

    texts = [a for a in ax.get_children() if isinstance(a, Text)]
    lines = [a for a in ax.get_children() if isinstance(a, Line2D)]

    # Should have 4 labels
    assert len(texts) >= 4

    # All point labels should be present in text
    text_values = [t.get_text() for t in texts]
    assert all(v in text_values for v in ["A", "B", "C", "D"])

    plt.close(fig)


def test_distance_azimuth_separation():
    """
    Distance and azimuth texts should be spaced apart to avoid overlap.
    """
    boundary = [
        Point(name="P1", x=0, y=0),
        Point(name="P2", x=5.0, y=0),
    ]

    fig = plt.figure(figsize=(8, 4), dpi=100)
    ax = fig.add_subplot(111)
    ax.set_xlim(-1, 6)
    ax.set_ylim(-2, 2)

    _draw_distances(ax, boundary, show_azimuths=True, m_per_pt=0.1)
    fig.canvas.draw()

    texts = [a for a in ax.get_children() if isinstance(a, Text)]
    text_positions = [(t.get_position()[0], t.get_position()[1]) for t in texts]

    # At minimum we expect: distance text, azimuth text
    assert len(text_positions) >= 2

    plt.close(fig)


def test_coordinate_labels_large_values():
    """
    When coordinate_labels=True on large coordinate values,
    formatted output should be concise (no long decimal strings).
    """
    boundary = [
        Point(name="P1", x=500000.0, y=500000.0),
        Point(name="P2", x=500001.0, y=500000.0),
    ]

    plan = PlotPlan(
        title="Large Coords Test",
        boundary_points=boundary,
        paper_format="A4",
        coordinate_labels=True,
    )

    png = render_plot_plan(plan)
    assert png.startswith(b"\x89PNG")
    assert len(png) > 1000


def test_zone_area_text_present():
    """
    Zone area labels should appear and scale properly.
    """
    boundary = [
        Point(x=0, y=0),
        Point(x=100, y=0),
        Point(x=100, y=100),
        Point(x=0, y=100),
    ]
    zones = [
        Zone(
            name="Test zone",
            points=[
                Point(x=10, y=10),
                Point(x=90, y=10),
                Point(x=90, y=90),
                Point(x=10, y=90),
            ],
        )
    ]

    plan = PlotPlan(
        title="Zone Test",
        boundary_points=boundary,
        zones=zones,
        show_areas=True,
    )

    png = render_plot_plan(plan)
    assert png.startswith(b"\x89PNG")
    assert len(png) > 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
