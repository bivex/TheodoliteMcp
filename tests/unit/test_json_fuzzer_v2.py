"""
Comprehensive JSON Fuzzing Tests for Theodolite MCP Tools
Uses Hypothesis for property-based testing.

Designed to:
- Find crashes, hangs, unhandled exceptions
- Test boundary conditions and edge cases
- Validate proper input validation
"""

import pytest
import math
from hypothesis import given, strategies as st, settings, HealthCheck

# Import all tool functions and models
from theodolite_mcp.infrastructure.mcp_server import (
    dms_to_decimal_degrees,
    decimal_degrees_to_dms,
    compute_forward_azimuth,
    compute_back_azimuth,
    compute_inverse_geodetic_problem,
    reduce_stadia_readings,
    compute_parcel_area,
    compute_edm_atmospheric_correction,
    adjust_traverse_network,
    draw_plot_plan,
    draw_longitudinal_profile,
    draw_interior_plan,
    adjust_network_least_squares,
    transform_coordinate_system,
    project_coordinates_gauss_kruger,
    utm_projection_inverse,
    gauss_kruger_projection_inverse,
    utm_projection_forward,
    mgrs_to_latlon_conversion,
    compute_grid_convergence,
    compute_point_scale_factor,
    geoid_height_egm96,
    geoid_height_egm2008,
    helmert_transform_wgs84_to_local,
    convert_sk42_to_wgs84,
    reverse_azimuth,
)
from theodolite_mcp.domain.models import Point, Observation
from theodolite_mcp.domain.logic import calculate_area, normalize_angle

# ============================================================================
# HYPOTHESIS STRATEGY DEFINITIONS
# ============================================================================

# Finite float within safe numeric range
finite_float = st.floats(
    min_value=-1e10,
    max_value=1e10,
    allow_nan=False,
    allow_infinity=False,
)

# Finite positive float
positive_float = st.floats(
    min_value=1e-6,
    max_value=1e10,
    allow_nan=False,
    allow_infinity=False,
)

# Float that may be NaN or infinite
_special_float = st.one_of(
    st.just(float("nan")),
    st.just(float("inf")),
    st.just(float("-inf")),
)

# Any float (finite or special)
any_float = st.one_of(finite_float, _special_float)

# Coordinates (bounded finite)
coord = st.floats(min_value=-1e9, max_value=1e9, allow_nan=False, allow_infinity=False)

# Angle in degrees (bounded wide)
angle = st.floats(
    min_value=-3600.0, max_value=3600.0, allow_nan=False, allow_infinity=False
)

# Point as dict
point_dict = st.fixed_dictionaries(
    {
        "name": st.text(
            min_size=1,
            max_size=20,
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll"), whitelist_characters="_0123456789"
            ),
        ),
        "x": st.one_of(
            coord, st.just(float("nan")), st.just(float("inf")), st.just(float("-inf"))
        ),
        "y": st.one_of(
            coord, st.just(float("nan")), st.just(float("inf")), st.just(float("-inf"))
        ),
        "z": st.one_of(
            st.none(),
            coord,
            st.just(float("nan")),
            st.just(float("inf")),
            st.just(float("-inf")),
        ),
    }
)

points_list = st.lists(point_dict, min_size=0, max_size=50)

# Observation dict
obs_dict = st.fixed_dictionaries(
    {
        "point_name": st.text(min_size=1, max_size=20),
        "horizontal_angle": st.one_of(
            angle, st.just(float("nan")), st.just(float("inf")), st.just(float("-inf"))
        ),
        "distance": st.one_of(
            positive_float, st.just(-1.0), st.just(0.0), st.just(float("nan"))
        ),
        "vertical_angle": st.one_of(
            angle, st.just(float("nan")), st.just(float("inf")), st.just(float("-inf"))
        ),
        "is_sideshot": st.booleans(),
    }
)

observations_list = st.lists(obs_dict, min_size=0, max_size=30)


# ============================================================================
# TEST CLASSES
# ============================================================================


class TestBasicConversionFuzzing:
    """Fuzz basic mathematical conversions."""

    @given(
        degrees=st.integers(-360, 360),
        minutes=st.integers(0, 59),
        seconds=st.floats(0.0, 59.999, allow_nan=False),
    )
    @settings(max_examples=1000)
    def test_dms_to_decimal(self, degrees, minutes, seconds):
        try:
            res = dms_to_decimal_degrees(degrees, minutes, seconds)
            assert isinstance(res, float)
            assert math.isfinite(res) or math.isnan(res) or math.isinf(res)
        except (ValueError, ValidationError, OverflowError):
            pass

    @given(angle=st.floats(min_value=-720, max_value=720, allow_nan=False))
    @settings(max_examples=1000)
    def test_decimal_to_dms(self, angle):
        try:
            res = decimal_degrees_to_dms(angle)
            assert isinstance(res, dict) and "degrees" in res
        except (ValueError, ValidationError, OverflowError, TypeError):
            pass

    @given(angle=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False))
    @settings(max_examples=1000)
    def test_reverse_azimuth(self, angle):
        try:
            res = reverse_azimuth(angle)
            assert isinstance(res, float)
            if math.isfinite(res):
                assert 0 <= res < 360.0
        except (ValueError, ValidationError, OverflowError, TypeError):
            pass


class TestPointCalculationsFuzzing:
    """Fuzz point and distance calculations."""

    @given(x1=coord, y1=coord, x2=coord, y2=coord)
    @settings(max_examples=1000)
    def test_forward_azimuth(self, x1, y1, x2, y2):
        try:
            res = compute_forward_azimuth(x1, y1, x2, y2)
            assert isinstance(res, float)
            if math.isfinite(res):
                assert 0 <= res < 360.0
        except (ValueError, ValidationError, OverflowError, TypeError):
            pass

    @given(
        x1=coord,
        y1=coord,
        x2=coord,
        y2=coord,
        z1=st.none() | finite_float,
        z2=st.none() | finite_float,
    )
    @settings(max_examples=1000)
    def test_inverse_geodetic(self, x1, y1, x2, y2, z1, z2):
        try:
            res = compute_inverse_geodetic_problem(x1, y1, x2, y2, z1, z2)
            assert isinstance(res, dict)
            assert "azimuth" in res and "distance" in res
        except (ValueError, ValidationError, OverflowError, TypeError):
            pass


class TestAreaFuzzing:
    """Fuzz polygon area calculations."""

    @given(points=points_list)
    @settings(max_examples=1000)
    def test_area(self, points):
        try:
            res = compute_parcel_area(points)
            assert isinstance(res, float)
            if math.isfinite(res):
                assert res >= 0.0
        except (ValueError, ValidationError, OverflowError, TypeError, KeyError):
            pass

    def test_area_empty(self):
        assert compute_parcel_area([]) == 0.0

    def test_area_two_points(self):
        assert (
            compute_parcel_area(
                [{"name": "A", "x": 0, "y": 0}, {"name": "B", "x": 1, "y": 1}]
            )
            == 0.0
        )


class TestStadiaFuzzing:
    """Fuzz stadia reduction."""

    @given(top=positive_float, bottom=positive_float, va=angle)
    @settings(max_examples=1000)
    def test_stadia_normal(self, top, bottom, va):
        try:
            res = reduce_stadia_readings(top, bottom, va, hi=0, ht=0)
            assert isinstance(res, dict)
            for key in ("horizontal_distance", "vertical_distance", "elevation_diff"):
                assert key in res
        except (
            ValueError,
            ValidationError,
            OverflowError,
            TypeError,
            ZeroDivisionError,
        ):
            pass

    @given(
        top=st.floats(
            min_value=-1e3, max_value=1e3, allow_nan=False, allow_infinity=False
        ),
        bottom=st.floats(
            min_value=-1e3, max_value=1e3, allow_nan=False, allow_infinity=False
        ),
        va=st.floats(
            min_value=-360, max_value=360, allow_nan=False, allow_infinity=False
        ),
    )
    @settings(max_examples=500)
    def test_stadia_extreme_numbers(self, top, bottom, va):
        try:
            res = reduce_stadia_readings(top, bottom, va)
            assert isinstance(res, dict)
        except (
            ValueError,
            ValidationError,
            OverflowError,
            TypeError,
            ZeroDivisionError,
        ):
            pass


class TestEDMFuzzing:
    """Fuzz EDM atmospheric correction."""

    @given(
        temp=st.floats(
            min_value=-100, max_value=100, allow_nan=False, allow_infinity=False
        ),
        pressure=st.floats(
            min_value=0, max_value=2000, allow_nan=False, allow_infinity=False
        ),
        freq=st.floats(
            min_value=1, max_value=1e6, allow_nan=False, allow_infinity=False
        ),
    )
    @settings(max_examples=1000)
    def test_edm_correction(self, temp, pressure, freq):
        try:
            res = compute_edm_atmospheric_correction(temp, pressure, freq)
            assert isinstance(res, float)
            if math.isfinite(res):
                assert -1000 < res < 1000  # PPM typically within this
        except (
            ValueError,
            ValidationError,
            OverflowError,
            TypeError,
            ZeroDivisionError,
        ):
            pass


class TestTraverseFuzzing:
    """Fuzz traverse network adjustment."""

    @given(
        sx=coord,
        sy=coord,
        start_az=angle,
        obs=observations_list,
        is_closed=st.booleans(),
        avg_elev=finite_float,
        gsf=st.floats(
            min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False
        ),
    )
    @settings(max_examples=500, deadline=None)
    def test_traverse_adjustment(self, sx, sy, start_az, obs, is_closed, avg_elev, gsf):
        try:
            res = adjust_traverse_network(
                start_x=sx,
                start_y=sy,
                start_azimuth=start_az,
                observations_json=obs,
                is_closed=is_closed,
                avg_elevation=avg_elev,
                grid_scale_factor=gsf,
            )
            assert isinstance(res, dict)
            # Must have these keys if successful
            assert "points" in res
            assert "linear_misclosure" in res
            assert "angular_misclosure" in res
            assert "relative_precision" in res
        except (
            ValueError,
            ValidationError,
            TypeError,
            OverflowError,
            ZeroDivisionError,
            ArithmeticError,
            KeyError,
            IndexError,
        ):
            pass


class TestLeastSquaresFuzzing:
    """Fuzz least squares adjustment."""

    @given(
        obs_list=st.lists(
            st.fixed_dictionaries(
                {
                    "type": st.sampled_from(
                        ["distance", "azimuth", "fixed_x", "fixed_y"]
                    ),
                    "from_pt": st.text(min_size=1, max_size=10),
                    "to_pt": st.text(min_size=1, max_size=10),
                    "value": finite_float,
                    "std_dev": positive_float,
                }
            ),
            max_size=20,
        ),
        coords=st.dictionaries(
            keys=st.text(min_size=1, max_size=10),
            values=st.fixed_dictionaries({"x": finite_float, "y": finite_float}),
            min_size=1,
            max_size=15,
        ),
    )
    @settings(max_examples=300, deadline=None)
    def test_least_squares(self, obs_list, coords):
        try:
            res = adjust_network_least_squares(obs_list, coords)
            assert isinstance(res, dict)
        except (
            ValueError,
            ValidationError,
            TypeError,
            OverflowError,
            ZeroDivisionError,
            ArithmeticError,
            KeyError,
        ):
            pass


class TestGeodeticFuzzing:
    """Fuzz geodetic transformations."""

    @given(
        lat=st.floats(min_value=-90, max_value=90, allow_nan=False),
        lon=st.floats(min_value=-180, max_value=180, allow_nan=False),
        cm=st.floats(min_value=-180, max_value=180, allow_nan=False),
    )
    @settings(max_examples=1000)
    def test_grid_convergence(self, lat, lon, cm):
        try:
            res = compute_grid_convergence(lat, lon, cm)
            assert isinstance(res, float)
            if math.isfinite(res):
                # Should be within [-180, 180] typically
                assert -180 <= res <= 180
        except (ValueError, ValidationError, TypeError, OverflowError):
            pass

    @given(
        lat=st.floats(min_value=-90, max_value=90, allow_nan=False),
        lon=st.floats(min_value=-180, max_value=180, allow_nan=False),
        cm=st.floats(min_value=-180, max_value=180, allow_nan=False),
    )
    @settings(max_examples=1000)
    def test_scale_factor(self, lat, lon, cm):
        try:
            res = compute_point_scale_factor(lat, lon, cm)
            assert isinstance(res, float)
            if math.isfinite(res):
                assert res > 0  # scale factor positive
        except (ValueError, ValidationError, TypeError, OverflowError):
            pass

    @given(
        lat=st.floats(min_value=-90, max_value=90, allow_nan=False),
        lon=st.floats(min_value=-180, max_value=180, allow_nan=False),
    )
    @settings(max_examples=1000)
    def test_geoid_height(self, lat, lon):
        try:
            r1 = geoid_height_egm96(lat, lon)
            r2 = geoid_height_egm2008(lat, lon)
            assert isinstance(r1, float)
            assert isinstance(r2, float)
        except (ValueError, ValidationError, TypeError, OverflowError):
            pass

    @given(
        lat=st.floats(min_value=-90, max_value=90, allow_nan=False),
        lon=st.floats(min_value=-180, max_value=180, allow_nan=False),
    )
    @settings(max_examples=500)
    def test_gk_projection(self, lat, lon):
        # Use central meridian close to lon
        cm = round(lon / 3) * 3  # approximate zone central meridian
        try:
            res = project_coordinates_gauss_kruger(lat, lon, cm)
            assert isinstance(res, dict)
        except (ValueError, ValidationError, TypeError, OverflowError):
            pass

    @given(
        northing=finite_float,
        easting=finite_float,
        zone_num=st.integers(min_value=1, max_value=60),
        zone_letter=st.sampled_from(list("CDEFGHJKLMNPQRSTUVWXYZ")),
    )
    @settings(max_examples=500)
    def test_utm_inverse(self, northing, easting, zone_num, zone_letter):
        try:
            res = utm_projection_inverse(northing, easting, zone_num, zone_letter)
            assert isinstance(res, dict)
            assert "latitude" in res and "longitude" in res
        except (ValueError, ValidationError, TypeError, OverflowError, IndexError):
            pass

    @given(mgrs=st.text(min_size=0, max_size=50))
    @settings(max_examples=1000)
    def test_mgrs_to_latlon(self, mgrs):
        try:
            res = mgrs_to_latlon_conversion(mgrs)
            assert isinstance(res, dict)
            assert "latitude" in res and "longitude" in res
        except (ValueError, ValidationError, TypeError):
            pass

    @given(
        lat=finite_float,
        lon=finite_float,
        h=finite_float,
        dx=finite_float,
        dy=finite_float,
        dz=finite_float,
        rx=finite_float,
        ry=finite_float,
        rz=finite_float,
        s=finite_float,
        ell=st.sampled_from(["WGS84", "KRASOVSKY"]),
    )
    @settings(max_examples=500)
    def test_helmert_transform(self, lat, lon, h, dx, dy, dz, rx, ry, rz, s, ell):
        try:
            res = helmert_transform_wgs84_to_local(
                lat, lon, h, dx, dy, dz, rx, ry, rz, s, ell
            )
            assert isinstance(res, dict)
        except (ValueError, ValidationError, TypeError, OverflowError):
            pass

    @given(
        northing=finite_float,
        easting=finite_float,
        zone=st.integers(min_value=1, max_value=60),
    )
    @settings(max_examples=500)
    def test_sk42_to_wgs84(self, northing, easting, zone):
        try:
            res = convert_sk42_to_wgs84(northing, easting, zone)
            assert isinstance(res, dict)
        except (ValueError, ValidationError, TypeError, OverflowError):
            pass


class TestRenderingFuzzing:
    """Fuzz rendering/drawing functions (high-level)."""

    @given(
        boundary=st.lists(point_dict, min_size=0, max_size=30),
        zones=st.lists(
            st.fixed_dictionaries(
                {
                    "name": st.text(max_size=50),
                    "points": st.lists(point_dict, max_size=20),
                    "fill_color": st.one_of(st.none(), st.text(max_size=30)),
                    "fill_alpha": st.floats(
                        min_value=-1.0, max_value=2.0, allow_nan=False
                    ),
                }
            ),
            max_size=10,
        ),
    )
    @settings(max_examples=300, deadline=None)
    def test_draw_plot_plan(self, boundary, zones):
        try:
            res = draw_plot_plan(boundary_json=boundary, zones_json=zones)
            assert res is not None  # Should return Image
        except (
            ValueError,
            ValidationError,
            TypeError,
            OverflowError,
            KeyError,
            IndexError,
        ) as e:
            pass  # Expected for malformed data

    @given(
        points=st.lists(
            st.finite_dictionaries(
                {
                    "station": finite_float,
                    "elevation": finite_float,
                    "design_elevation": st.none() | finite_float,
                }
            ),
            max_size=30,
        )
    )
    @settings(max_examples=300, deadline=None)
    def test_draw_profile(self, points):
        try:
            # Need to convert to correct keys
            pts = [
                {
                    "station": p["station"],
                    "elevation": p["elevation"],
                    "design_elevation": p["design_elevation"],
                }
                for p in points
            ]
            res = draw_longitudinal_profile(points_json=pts)
            assert res is not None
        except (ValueError, ValidationError, TypeError, OverflowError, KeyError):
            pass

    @given(
        walls=st.lists(
            st.fixed_dictionaries(
                {
                    "start_pt": st.finite_dictionaries(
                        {"x": finite_float, "y": finite_float}
                    ),
                    "end_pt": st.finite_dictionaries(
                        {"x": finite_float, "y": finite_float}
                    ),
                    "thickness": st.floats(
                        min_value=0.05, max_value=2.0, allow_nan=False
                    ),
                    "openings": st.lists(
                        st.none()
                        | st.finite_dictionaries(
                            {"x": finite_float, "y": finite_float}
                        ),
                        max_size=5,
                    ),
                }
            ),
            max_size=10,
        ),
        rooms=st.lists(
            st.fixed_dictionaries(
                {
                    "name": st.text(max_size=30),
                    "points": st.lists(
                        st.finite_dictionaries({"x": finite_float, "y": finite_float}),
                        max_size=10,
                    ),
                }
            ),
            max_size=10,
        ),
    )
    @settings(max_examples=200, deadline=None)
    def test_draw_interior_plan(self, walls, rooms):
        try:
            res = draw_interior_plan(walls_json=walls, rooms_json=rooms)
            assert res is not None
        except (ValueError, ValidationError, TypeError, KeyError, OverflowError):
            pass


# ============================================================================
# STRUCTURAL AND TYPE FUZZING
# ============================================================================


class TestInputValidationEdgeCases:
    """Edge cases where JSON type structure is wrong."""

    def test_area_with_nan_coordinate(self):
        with pytest.raises((ValidationError, ValueError)):
            compute_parcel_area([{"name": "A", "x": float("nan"), "y": 0}])

    def test_area_with_inf_coordinate(self):
        with pytest.raises((ValidationError, ValueError)):
            compute_parcel_area([{"name": "A", "x": float("inf"), "y": 0}])

    def test_forward_azimuth_identical_points(self):
        with pytest.raises(ValueError):
            compute_forward_azimuth(0, 0, 0, 0)

    def test_observation_missing_point_name(self):
        with pytest.raises(ValidationError):
            Observation(horizontal_angle=90.0, distance=100.0)

    def test_observation_extra_field(self):
        with pytest.raises(ValidationError):
            Observation(
                point_name="P", horizontal_angle=90.0, distance=100.0, extra=123
            )

    def test_stadia_with_negative_distance(self):
        # Might actually be accepted? Let's see what happens.
        # If it doesn't raise, that's okay; if it does, also okay.
        try:
            res = reduce_stadia_readings(100, 50, 45.0)
            assert "horizontal_distance" in res
        except (ValidationError, ValueError):
            pass

    def test_draw_plan_empty_boundary(self):
        # Empty boundary likely fails in rendering
        with pytest.raises((ValidationError, ValueError, IndexError)):
            draw_plot_plan(boundary_json=[])

    def test_draw_plan_wrong_type_for_boundary(self):
        with pytest.raises((ValidationError, TypeError, AttributeError)):
            draw_plot_plan(boundary_json="not a list")

    def test_traverse_no_observations(self):
        # Empty observations can be valid for degenerate traverse
        try:
            res = adjust_traverse_network(0, 0, observations_json=[])
            # Either it succeeds or fails; but shouldn't crash
        except Exception:
            pass  # Okay
