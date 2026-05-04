import pytest
from theodolite_mcp.domain.models import Point, Observation, TraverseData
from theodolite_mcp.domain.logic import calculate_traverse

def test_closed_traverse_misclosure():
    # Square 100x100
    # Interior angles should sum to (4-2)*180 = 360
    # We provide 90.1 for all 4 angles -> 360.4 total -> 0.4 misclosure
    start_point = Point(name="P1", x=0, y=0)
    obs = [
        Observation(point_name="P2", horizontal_angle=90.1, distance=100.0),
        Observation(point_name="P3", horizontal_angle=90.1, distance=100.0),
        Observation(point_name="P4", horizontal_angle=90.1, distance=100.0),
        Observation(point_name="P1_back", horizontal_angle=90.1, distance=100.0),
    ]
    data = TraverseData(
        start_point=start_point,
        start_azimuth=0.0,
        observations=obs,
        is_closed=True
    )
    result = calculate_traverse(data)
    assert result.angular_misclosure == pytest.approx(0.4)
    # The last point should be exactly back at (0,0) due to adjustment
    assert result.points[-1].x == pytest.approx(0, abs=1e-7)
    assert result.points[-1].y == pytest.approx(0, abs=1e-7)

def test_traverse_linear_misclosure():
    # Open traverse to fixed point
    # Start (0,0), End (200, 0)
    # Measurement: (100.1, 0) and (100.1, 0) -> Total 200.2 -> 0.2 linear misclosure
    start_point = Point(name="A", x=0, y=0)
    end_point = Point(name="C", x=200, y=0)
    obs = [
        Observation(point_name="B", horizontal_angle=180.0, distance=100.1),
        Observation(point_name="C_meas", horizontal_angle=180.0, distance=100.1),
    ]
    data = TraverseData(
        start_point=start_point,
        end_point=end_point,
        start_azimuth=0.0,
        observations=obs,
        is_closed=False
    )
    result = calculate_traverse(data)
    assert result.linear_misclosure == pytest.approx(0.2)
    # Relative precision: 0.2 / 200.2
    assert result.relative_precision == pytest.approx(0.2 / 200.2)
    # Adjusted end point should match fixed end point
    assert result.points[-1].x == pytest.approx(200.0)
    assert result.points[-1].y == pytest.approx(0.0)

def test_compass_rule_proportionality():
    # One leg is 100m, another 200m. Linear error should be distributed 1:2
    start_point = Point(name="A", x=0, y=0)
    end_point = Point(name="C", x=300, y=0)
    obs = [
        Observation(point_name="B", horizontal_angle=180.0, distance=100.1),
        Observation(point_name="C_meas", horizontal_angle=180.0, distance=200.2),
    ]
    # Total distance 300.3. Total error 0.3.
    # Leg 1 (100.1m) error: 0.3 * (100.1 / 300.3) = 0.1
    # Leg 2 (200.2m) error: 0.3 * (200.2 / 300.3) = 0.2
    data = TraverseData(
        start_point=start_point,
        end_point=end_point,
        start_azimuth=0.0,
        observations=obs,
        is_closed=False
    )
    result = calculate_traverse(data)
    # Points: A(0,0), B_raw(100.1, 0), C_raw(300.3, 0)
    # B_adj: 100.1 - 0.1 = 100.0
    # C_adj: 300.3 - 0.3 = 300.0
    assert result.points[1].x == pytest.approx(100.0)
    assert result.points[2].x == pytest.approx(300.0)
