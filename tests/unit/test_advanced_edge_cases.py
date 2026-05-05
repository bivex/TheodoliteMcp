import pytest
import math
from theodolite_mcp.domain.geodesy import WGS84, geodetic_to_ecef, ecef_to_geodetic
from theodolite_mcp.domain.least_squares import ObservationLS, adjust_network_2d
from theodolite_mcp.domain.logic import calculate_area
from theodolite_mcp.domain.models import Point

# --- Advanced Geodesy Edge Cases ---

def test_geodesy_poles():
    """Test conversions exactly at the North and South Poles."""
    # North Pole
    x, y, z = geodetic_to_ecef(90.0, 0.0, 0.0, WGS84)
    assert pytest.approx(x, abs=1e-7) == 0.0
    assert pytest.approx(y, abs=1e-7) == 0.0
    assert pytest.approx(z, abs=1e-3) == WGS84.a * (1 - 1/WGS84.f_inv)
    
    # South Pole
    x, y, z = geodetic_to_ecef(-90.0, 0.0, 0.0, WGS84)
    assert pytest.approx(z, abs=1e-3) == -WGS84.a * (1 - 1/WGS84.f_inv)

def test_geodesy_longitude_wrap():
    """Test longitude values at the boundary (-180/180)."""
    x1, y1, z1 = geodetic_to_ecef(50.0, 180.0, 0.0, WGS84)
    x2, y2, z2 = geodetic_to_ecef(50.0, -180.0, 0.0, WGS84)
    assert pytest.approx(x1) == x2
    # Y should be approx 0 at 180/-180 meridian
    assert pytest.approx(y1, abs=1e-7) == 0.0
    assert pytest.approx(y2, abs=1e-7) == 0.0
    assert pytest.approx(z1) == z2

def test_rendering_massive_coordinates():
    """Test rendering of a site with regional dimensions (1000km)."""
    from theodolite_mcp.domain.rendering import render_plot_plan
    from theodolite_mcp.domain.models import PlotPlan, Point
    
    boundary = [
        Point(name="A", x=0, y=0),
        Point(name="B", x=1000000, y=0), # 1000 km
        Point(name="C", x=1000000, y=1000000),
        Point(name="D", x=0, y=1000000),
        Point(name="A", x=0, y=0)
    ]
    plan = PlotPlan(
        title="Regional Mapping Test",
        boundary_points=boundary,
        paper_format="A3"
    )
    png_bytes = render_plot_plan(plan)
    assert len(png_bytes) > 0
    # The scale should be massive (e.g. 1:5,000,000)

# --- Advanced LSA Edge Cases ---

def test_lsa_zero_distance_observation():
    """Verify that a zero or near-zero distance observation doesn't cause a crash."""
    initial = {"P1": {"x": 0, "y": 0}, "P2": {"x": 0, "y": 0.0001}}
    obs = [
        ObservationLS(from_pt="P1", to_pt="P1", value=0, std_dev=0.001, type="fixed_x"),
        ObservationLS(from_pt="P1", to_pt="P1", value=0, std_dev=0.001, type="fixed_y"),
        ObservationLS(from_pt="P1", to_pt="P2", value=0.0, std_dev=0.01, type="distance"),
    ]
    # LSA should ideally handle small values or exit gracefully
    res = adjust_network_2d(obs, initial)
    assert res.iterations >= 0 # Should not crash

def test_lsa_collinear_points():
    """Collinear triangulation is a classic bad geometry in surveying."""
    initial = {
        "P1": {"x": 0, "y": 0}, 
        "P2": {"x": 10, "y": 0},
        "P3": {"x": 5, "y": 0.001} # Almost on the line P1-P2
    }
    obs = [
        ObservationLS(from_pt="P1", to_pt="P1", value=0, std_dev=0.001, type="fixed_x"),
        ObservationLS(from_pt="P1", to_pt="P1", value=0, std_dev=0.001, type="fixed_y"),
        ObservationLS(from_pt="P2", to_pt="P2", value=10, std_dev=0.001, type="fixed_x"),
        ObservationLS(from_pt="P2", to_pt="P2", value=0, std_dev=0.001, type="fixed_y"),
        ObservationLS(from_pt="P1", to_pt="P3", value=5.0, std_dev=0.01, type="distance"),
        ObservationLS(from_pt="P2", to_pt="P3", value=5.0, std_dev=0.01, type="distance"),
    ]
    # This is a poorly conditioned problem
    res = adjust_network_2d(obs, initial)
    # Even if it converges, the std_dev of Y should be very large
    if "P3" in res.standard_deviations:
        assert res.standard_deviations["P3"]["y"] > res.standard_deviations["P3"]["x"]

# --- Logic/Mathematics Edge Cases ---

def test_area_degenerate_polygon():
    """Area of a line or a point should be zero."""
    line = [Point(name="1", x=0, y=0), Point(name="2", x=10, y=10), Point(name="1", x=0, y=0)]
    assert calculate_area(line) == 0.0

def test_area_negative_coordinates():
    """Gauss formula should work correctly in all quadrants."""
    square = [
        Point(name="1", x=-10, y=-10),
        Point(name="2", x=10, y=-10),
        Point(name="3", x=10, y=10),
        Point(name="4", x=-10, y=10),
        Point(name="1", x=-10, y=-10)
    ]
    assert calculate_area(square) == 400.0

def test_area_self_intersecting():
    """A figure-eight polygon area."""
    # (0,0) -> (10,10) -> (10,0) -> (0,10) -> (0,0)
    # The two loops have opposite signs in Gauss formula
    points = [
        Point(name="1", x=0, y=0),
        Point(name="2", x=10, y=10),
        Point(name="3", x=10, y=0),
        Point(name="4", x=0, y=10),
        Point(name="1", x=0, y=0)
    ]
    # Area should be 0 as the two triangles cancel out
    assert calculate_area(points) == 0.0
