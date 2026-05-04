import pytest
from theodolite_mcp.domain.logic import calculate_azimuth_from_points, normalize_angle
from theodolite_mcp.domain.models import Point

def test_azimuth_north():
    p1 = Point(name="A", x=0, y=0)
    p2 = Point(name="B", x=10, y=0)
    assert calculate_azimuth_from_points(p1, p2) == pytest.approx(0)

def test_azimuth_east():
    p1 = Point(name="A", x=0, y=0)
    p2 = Point(name="B", x=0, y=10)
    assert calculate_azimuth_from_points(p1, p2) == pytest.approx(90)

def test_azimuth_south():
    p1 = Point(name="A", x=0, y=0)
    p2 = Point(name="B", x=-10, y=0)
    assert calculate_azimuth_from_points(p1, p2) == pytest.approx(180)

def test_azimuth_west():
    p1 = Point(name="A", x=0, y=0)
    p2 = Point(name="B", x=0, y=-10)
    assert calculate_azimuth_from_points(p1, p2) == pytest.approx(270)

def test_azimuth_identical_points():
    p1 = Point(name="A", x=0, y=0)
    p2 = Point(name="B", x=0, y=0)
    with pytest.raises(ValueError, match="Points are identical"):
        calculate_azimuth_from_points(p1, p2)

def test_normalize_angle():
    assert normalize_angle(360) == 0
    assert normalize_angle(370) == 10
    assert normalize_angle(-10) == 350
    assert normalize_angle(-370) == 350
