import pytest
import math
import numpy as np
from theodolite_mcp.domain.least_squares import ObservationLS, adjust_network_2d
from theodolite_mcp.domain.geodesy import (
    WGS84,
    helmert_transform,
    geodetic_to_ecef,
    ecef_to_geodetic,
    gauss_kruger_forward,
)

# --- Least Squares Edge Cases ---


def test_lsa_under_constrained():
    """Test network with not enough fixed points (should return iterations=max or fail gracefully)."""
    initial = {"P1": {"x": 0, "y": 0}, "P2": {"x": 10, "y": 0}}
    # Only one distance, no fixed points -> Under-constrained
    obs = [
        ObservationLS(
            from_pt="P1", to_pt="P2", value=10.0, std_dev=0.01, type="distance"
        )
    ]

    res = adjust_network_2d(obs, initial)
    # The current implementation returns iterations=max if it doesn't converge or breaks on singular
    assert res.iterations > 0
    assert (
        res.standard_deviations == {}
    )  # Should not have precision for singular matrix


def test_lsa_disconnected_point():
    """Test network where one point has no observations."""
    initial = {"P1": {"x": 0, "y": 0}, "P2": {"x": 10, "y": 0}, "P3": {"x": 5, "y": 5}}
    obs = [
        ObservationLS(from_pt="P1", to_pt="P1", value=0, std_dev=0.001, type="fixed_x"),
        ObservationLS(from_pt="P1", to_pt="P1", value=0, std_dev=0.001, type="fixed_y"),
        ObservationLS(
            from_pt="P1", to_pt="P2", value=10.0, std_dev=0.01, type="distance"
        ),
    ]
    # P3 is disconnected
    res = adjust_network_2d(obs, initial)
    assert "P3" in res.adjusted_coordinates
    # Disconnected point shouldn't have valid std_dev
    assert "P3" not in res.standard_deviations


# --- Geodesy Edge Cases ---


def test_geodesy_equator():
    """Test geodetic conversion at the equator."""
    lat, lon, h = 0.0, 0.0, 0.0
    x, y, z = geodetic_to_ecef(lat, lon, h, WGS84)
    # At (0,0,0), X should be semi-major axis, Y and Z should be 0
    assert pytest.approx(x, abs=1e-3) == WGS84.a
    assert pytest.approx(y, abs=1e-3) == 0.0
    assert pytest.approx(z, abs=1e-3) == 0.0


def test_geodesy_roundtrip():
    """Test consistency of Geodetic <-> ECEF conversions."""
    lat, lon, h = 45.0, 45.0, 1000.0
    x, y, z = geodetic_to_ecef(lat, lon, h, WGS84)
    lat2, lon2, h2 = ecef_to_geodetic(x, y, z, WGS84)
    assert pytest.approx(lat) == lat2
    assert pytest.approx(lon) == lon2
    assert pytest.approx(h) == h2


def test_helmert_identity():
    """Test Helmert transform with zero parameters (Identity)."""
    x, y, z = 1000000.0, 2000000.0, 3000000.0
    xt, yt, zt = helmert_transform(x, y, z, 0, 0, 0, 0, 0, 0, 0)
    assert xt == x
    assert yt == y
    assert zt == z


def test_gauss_kruger_on_meridian():
    """Test projection exactly on the central meridian."""
    lat = 50.0
    lon = 30.0
    cm = 30.0
    x, y = gauss_kruger_forward(lat, lon, cm)
    # Y (Easting) should be false easting of 500,000 m on central meridian
    assert pytest.approx(y, abs=1e-3) == 500000.0
    # X (Northing) should be > 0
    assert x > 5000000.0
