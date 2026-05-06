import math
import pytest
from theodolite_mcp.domain.geodesy import (
    WGS84,
    KRASOVSKY,
    Ellipsoid,
    helmert_transform,
    geodetic_to_ecef,
    ecef_to_geodetic,
    gauss_kruger_forward,
)
from theodolite_mcp.domain.logic import (
    calculate_inverse,
    calculate_azimuth_from_points,
    dms_to_decimal,
    decimal_to_dms,
    calculate_ppm_correction,
    apply_combined_factor,
    calculate_area,
)
from theodolite_mcp.domain.least_squares import ObservationLS, adjust_network_2d
from theodolite_mcp.domain.models import Point, EDMParameters


def test_gauss_kruger_basic_projection():
    """Test basic Gauss-Krüger projection (military grid foundation)"""
    # Equator, prime meridian, central meridian 0
    x, y = gauss_kruger_forward(lat=0.0, lon=0.0, lat0=0.0, lon0=0.0, ell=KRASOVSKY)
    assert x == pytest.approx(0.0, abs=1e-6)
    assert y == pytest.approx(0.0, abs=1e-6)


def test_gauss_kruger_moscow_zone7():
    """Test Gauss-Krüger projection for Moscow (Zone 7, central meridian 39°E)"""
    # Moscow coordinates: 55.7558°N, 37.6173°E
    x, y = gauss_kruger_forward(
        lat=55.7558, lon=37.6173, lat0=55.7558, lon0=39.0, ell=KRASOVSKY
    )
    # Northing for 55°N should exceed 6,000,000m
    assert x > 6_000_000
    # Easting offset from central meridian (1.3827°W) should be ~153,000m
    assert abs(y) < 200_000


def test_helmert_transform_wgs84_to_pulkovo1942():
    """Test 7-parameter Helmert transformation (WGS84 to Soviet military grid)"""
    # WGS84 test point: 55.7558°N, 37.6173°E, 100m elevation
    lat, lon, h = 55.7558, 37.6173, 100.0
    x, y, z = geodetic_to_ecef(lat, lon, h, WGS84)

    # Standard WGS84 to Pulkovo 1942 parameters
    dx, dy, dz = -24.82, 123.79, 94.23
    rx, ry, rz = -0.2054, -0.5417, -0.7218  # arcseconds
    s = -0.614  # ppm

    x_pul, y_pul, z_pul = helmert_transform(x, y, z, dx, dy, dz, rx, ry, rz, s)
    lat_pul, lon_pul, h_pul = ecef_to_geodetic(x_pul, y_pul, z_pul, KRASOVSKY)

    # Transformed coordinates should be within ~200m (0.01° at 55°N)
    assert lat_pul == pytest.approx(lat, abs=1e-2)
    assert lon_pul == pytest.approx(lon, abs=1e-2)
    assert h_pul == pytest.approx(h, abs=10.0)


def test_ecef_roundtrip_wgs84():
    """Test WGS84 geodetic ↔ ECEF roundtrip"""
    test_cases = [
        (0.0, 0.0, 0.0),  # Equator/prime meridian
        (45.0, 90.0, 100.0),  # Mid-latitude
        (-33.0, 151.0, 50.0),  # Southern hemisphere
    ]

    for lat, lon, h in test_cases:
        x, y, z = geodetic_to_ecef(lat, lon, h, WGS84)
        lat_calc, lon_calc, h_calc = ecef_to_geodetic(x, y, z, WGS84)
        assert lat_calc == pytest.approx(lat, abs=1e-6)
        assert lon_calc == pytest.approx(lon, abs=1e-6)
        assert h_calc == pytest.approx(h, abs=1e-3)


def test_inverse_geodetic_problem():
    """Test inverse geodetic problem (azimuth/distance calculation)"""
    # North azimuth
    p1 = Point(name="A", x=0.0, y=0.0, z=0.0)
    p2 = Point(name="B", x=100.0, y=0.0)
    res = calculate_inverse(p1, p2)
    assert res["azimuth"] == pytest.approx(0.0, abs=1e-4)
    assert res["distance"] == pytest.approx(100.0, abs=1e-3)

    # East azimuth
    p3 = Point(name="C", x=0.0, y=100.0)
    res = calculate_inverse(p1, p3)
    assert res["azimuth"] == pytest.approx(90.0, abs=1e-4)

    # With elevation (slope distance)
    p4 = Point(name="D", x=100.0, y=0.0, z=50.0)
    res = calculate_inverse(p1, p4)
    assert res["dz"] == pytest.approx(50.0, abs=1e-3)
    assert res["slope_distance"] == pytest.approx(math.hypot(100.0, 50.0), abs=1e-3)


def test_artillery_azimuth_dms():
    """Test DMS conversion for artillery azimuths (military standard)"""
    # 45°30'15" = 45.504166...°
    decimal = dms_to_decimal(45, 30, 15)
    assert decimal == pytest.approx(45.5041666667, abs=1e-6)

    # Convert back to DMS
    d, m, s = decimal_to_dms(decimal)
    assert d == 45
    assert m == 30
    assert s == pytest.approx(15.0, abs=1e-3)

    # Negative azimuth (270° = -90° in signed DMS)
    decimal = dms_to_decimal(-90, 0, 0)
    assert decimal == pytest.approx(-90.0, abs=1e-6)


def test_edm_atmospheric_correction():
    """Test EDM atmospheric correction (critical for field surveying)"""
    # Standard conditions: 20°C, 1013.25 hPa, frequency constant 281.8
    params = EDMParameters(
        temperature_c=20.0, pressure_hpa=1013.25, frequency_const=281.8
    )
    ppm = calculate_ppm_correction(params)
    # Expected correction ~3.0 ppm
    assert ppm == pytest.approx(3.0, abs=0.5)

    # Hot conditions: 40°C, 1013.25 hPa (higher temp increases correction)
    params = EDMParameters(
        temperature_c=40.0, pressure_hpa=1013.25, frequency_const=281.8
    )
    ppm_hot = calculate_ppm_correction(params)
    assert ppm_hot > 3.0  # Higher temperature increases correction
    assert ppm_hot == pytest.approx(20.85, abs=0.5)


def test_combined_scale_factor():
    """Test combined scale factor (elevation + grid distortion)"""
    distance = 1000.0  # meters
    elevation = 100.0  # meters
    grid_factor = 0.9996  # Typical UTM scale factor

    adjusted = apply_combined_factor(distance, elevation, grid_factor)
    R = 6371000.0
    expected = distance * (R / (R + elevation)) * grid_factor
    assert adjusted == pytest.approx(expected, abs=1e-6)


def test_least_squares_network_adjustment():
    """Test 2D least squares adjustment (military control network)"""
    initial_coords = {
        "A": {"x": 0.0, "y": 0.0},  # Fixed reference point
        "B": {"x": 100.0, "y": 0.0},  # Free point
        "C": {"x": 100.0, "y": 100.0},  # Free point
    }

    observations = [
        # Fixed coordinates for A
        ObservationLS(from_pt="A", to_pt="A", value=0.0, std_dev=0.01, type="fixed_x"),
        ObservationLS(from_pt="A", to_pt="A", value=0.0, std_dev=0.01, type="fixed_y"),
        # Distance observations
        ObservationLS(
            from_pt="A", to_pt="B", value=100.0, std_dev=0.1, type="distance"
        ),
        ObservationLS(
            from_pt="B", to_pt="C", value=100.0, std_dev=0.1, type="distance"
        ),
        ObservationLS(
            from_pt="A", to_pt="C", value=141.421, std_dev=0.1, type="distance"
        ),
        # Azimuth observation A→B
        ObservationLS(from_pt="A", to_pt="B", value=0.0, std_dev=0.01, type="azimuth"),
    ]

    result = adjust_network_2d(observations, initial_coords)

    # Adjusted coordinates should match expected values
    assert result.adjusted_coordinates["A"]["x"] == pytest.approx(0.0, abs=1e-6)
    assert result.adjusted_coordinates["A"]["y"] == pytest.approx(0.0, abs=1e-6)
    assert result.adjusted_coordinates["B"]["x"] == pytest.approx(100.0, abs=1e-3)
    assert result.adjusted_coordinates["B"]["y"] == pytest.approx(0.0, abs=1e-3)
    assert result.adjusted_coordinates["C"]["x"] == pytest.approx(100.0, abs=1e-3)
    assert result.adjusted_coordinates["C"]["y"] == pytest.approx(100.0, abs=1e-3)


def test_military_base_parcel_area():
    """Test area calculation for military base parcels"""
    # 1000m x 1000m square base
    points = [
        Point(name="B1", x=0.0, y=0.0),
        Point(name="B2", x=1000.0, y=0.0),
        Point(name="B3", x=1000.0, y=1000.0),
        Point(name="B4", x=0.0, y=1000.0),
    ]
    area = calculate_area(points)
    assert area == pytest.approx(1_000_000.0, abs=1e-6)

    # Triangle (half area)
    points_tri = points[:3]
    area_tri = calculate_area(points_tri)
    assert area_tri == pytest.approx(500_000.0, abs=1e-6)


def test_krasovsky_ellipsoid_properties():
    """Test KRASOVSKY ellipsoid (Soviet military standard)"""
    assert KRASOVSKY.a == pytest.approx(6378245.0, abs=1e-6)
    assert KRASOVSKY.f_inv == pytest.approx(298.3, abs=1e-6)
    assert KRASOVSKY.b == pytest.approx(6356863.019, abs=1e-3)
    assert KRASOVSKY.e2 == pytest.approx(0.0066934216, abs=1e-8)
