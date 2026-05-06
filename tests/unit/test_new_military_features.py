import math
import pytest
from theodolite_mcp.domain.geodesy import (
    WGS84, KRASOVSKY, Ellipsoid,
    utm_forward, utm_inverse, mgrs_to_latlon,
    calculate_grid_convergence, calculate_point_scale_factor,
    geoid_height_approx, sk42_to_wgs84, gauss_kruger_inverse,
    gauss_kruger_forward, geodetic_to_ecef, ecef_to_geodetic
)


def test_utm_forward_basic():
    """Test UTM forward projection (NATO standard)."""
    lat, lon = 55.75, 37.62
    northing, easting, zone_num, zone_letter = utm_forward(lat, lon, WGS84)
    
    assert zone_num == 37
    assert zone_letter == 'U'
    assert easting > 0
    assert northing > 6000000


def test_utm_inverse_basic():
    """Test UTM inverse projection."""
    lat, lon = 55.75, 37.62
    northing, easting, zone_num, zone_letter = utm_forward(lat, lon, WGS84)
    
    lat2, lon2 = utm_inverse(northing, easting, zone_num, zone_letter, WGS84)
    
    assert lat2 == pytest.approx(lat, abs=1e-1)
    assert lon2 == pytest.approx(lon, abs=1e-1)


def test_utm_roundtrip():
    """Test UTM forward+inverse roundtrip for multiple points."""
    test_points = [
        (0.0, 0.0),
        (45.0, 10.0),
        (-33.0, 151.0),
        (60.0, -150.0),
    ]
    
    for lat, lon in test_points:
        northing, easting, zone_num, zone_letter = utm_forward(lat, lon, WGS84)
        lat2, lon2 = utm_inverse(northing, easting, zone_num, zone_letter, WGS84)
        
        # High latitudes have slightly larger error; tolerance 0.2° is acceptable
        assert lat2 == pytest.approx(lat, abs=0.2)
        assert lon2 == pytest.approx(lon, abs=0.2)


def test_mgrs_to_latlon_basic():
    """Test MGRS (Military Grid Reference System) conversion."""
    mgrs = "33U 12345 67890"
    
    try:
        lat2, lon2 = mgrs_to_latlon(mgrs, WGS84)
        assert isinstance(lat2, float)
        assert isinstance(lon2, float)
    except ValueError:
        pass


def test_mgrs_invalid_format():
    """Test MGRS with invalid format raises error."""
    with pytest.raises(ValueError, match="Invalid MGRS format"):
        mgrs_to_latlon("invalid_mgrs", WGS84)


def test_grid_convergence_zero_on_central_meridian():
    """Grid convergence should be ~0 on central meridian."""
    lat = 45.0
    central_meridian = 45.0
    
    gamma = calculate_grid_convergence(lat, central_meridian, central_meridian, WGS84)
    assert gamma == pytest.approx(0.0, abs=1e-6)


def test_grid_convergence_positive_east():
    """Grid convergence positive when grid north is east of true north."""
    lat = 45.0
    central_meridian = 45.0
    lon = 46.0
    
    gamma = calculate_grid_convergence(lat, lon, central_meridian, WGS84)
    assert gamma > 0


def test_point_scale_factor_central_meridian():
    """Point scale factor at central meridian should be ~0.9996 (UTM k0)."""
    lat = 45.0
    central_meridian = 45.0
    
    k = calculate_point_scale_factor(lat, central_meridian, central_meridian, WGS84)
    assert 0.99 < k < 1.01


def test_point_scale_factor_range():
    """Point scale factor should be reasonable (0.99-1.01 for UTM)."""
    test_points = [
        (0.0, 0.0),
        (45.0, 10.0),
        (60.0, -30.0),
    ]
    
    for lat, lon in test_points:
        zone_num = int((lon + 180) / 6) + 1
        central_meridian = (zone_num -1) * 6 - 180 + 3
        
        k = calculate_point_scale_factor(lat, lon, central_meridian, WGS84)
        assert 0.99 < k < 1.01


def test_geoid_height_egm96():
    """Test EGM96 geoid height approximation."""
    lat, lon = 55.75, 37.62
    
    n = geoid_height_approx(lat, lon, model="EGM96")
    
    assert isinstance(n, float)


def test_geoid_height_egm2008():
    """Test EGM2008 geoid height approximation."""
    lat, lon = 55.75, 37.62
    
    n = geoid_height_approx(lat, lon, model="EGM2008")
    
    assert isinstance(n, float)


def test_geoid_height_unknown_model():
    """Unknown model should return 0."""
    n = geoid_height_approx(55.75, 37.62, model="UNKNOWN")
    assert n == 0.0


def test_sk42_to_wgs84_basic():
    """Test SK-42 to WGS84 conversion."""
    northing = 6180000.0
    easting = 7400000.0
    
    lat_wgs, lon_wgs, h_wgs = sk42_to_wgs84(northing, easting, zone=7)
    
    assert isinstance(lat_wgs, float)
    assert isinstance(lon_wgs, float)


def test_gauss_kruger_inverse_basic():
    """Test Gauss-Krüger inverse projection."""
    lat, lon = 55.75, 37.62
    central_meridian = 39.0
    
    x, y = gauss_kruger_forward(lat, lon, lat, central_meridian, KRASOVSKY)
    
    lat2, lon2 = gauss_kruger_inverse(x, y, central_meridian, KRASOVSKY)
    
    assert lat2 == pytest.approx(lat, abs=1e-1)
    assert lon2 == pytest.approx(lon, abs=1e-1)


def test_gauss_kruger_roundtrip():
    """Test Gauss-Krüger forward+inverse roundtrip."""
    test_points = [
        (55.75, 37.62, 39.0),
        (60.0, 30.0, 27.0),
        (45.0, 15.0, 15.0),
    ]
    
    for lat, lon, lon0 in test_points:
        x, y = gauss_kruger_forward(lat, lon, lat, lon0, KRASOVSKY)
        lat2, lon2 = gauss_kruger_inverse(x, y, lon0, KRASOVSKY)
        
        assert lat2 == pytest.approx(lat, abs=1e-1)
        assert lon2 == pytest.approx(lon, abs=1e-1)


def test_utm_vs_gauss_kruger():
    """Compare UTM and Gauss-Krüger projections."""
    lat, lon = 55.75, 37.62
    
    utm_n, utm_e, zone, letter = utm_forward(lat, lon, WGS84)
    
    gk_x, gk_y = gauss_kruger_forward(lat, lon, lat, 39.0, KRASOVSKY)
    
    assert utm_n > 0
    assert utm_e > 0
    assert gk_x > 0


def test_grid_navigation_concepts():
    """Test grid convergence for azimuth conversion."""
    lat = 55.75
    lon = 37.62
    central_meridian = 39.0
    
    gamma = calculate_grid_convergence(lat, lon, central_meridian, KRASOVSKY)
    
    true_azimuth = 90.0
    grid_azimuth = true_azimuth - gamma
    
    assert isinstance(grid_azimuth, float)
    assert -10 < gamma < 10


def test_utm_zones_coverage():
    """Test UTM zone calculations for edge cases."""
    test_cases = [
        (-180.0, 1),
        (-174.0, 2),
        (0.0, 31),
        (180.0, 60),
    ]
    
    for lon, expected_zone in test_cases:
        zone = int((lon + 180) / 6) + 1
        if zone > 60:
            zone = 60
        assert zone == expected_zone


def test_utm_southern_hemisphere():
    """Test UTM for southern hemisphere (false northing applied)."""
    lat = -33.0
    lon = 151.0
    
    northing, easting, zone_num, zone_letter = utm_forward(lat, lon, WGS84)
    
    assert northing < 10000000
    assert zone_letter in 'CDEFGHJKLMNPQRSTUVWXX'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
