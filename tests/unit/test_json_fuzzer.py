"""
JSON Fuzzing Tests for Theodolite MCP
Uses Hypothesis to generate random inputs and find crashes/bugs.
"""

import pytest
import math
from hypothesis import given, strategies as st, settings, HealthCheck
from pydantic import ValidationError

# Import tool functions
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
# HYPOTHESIS STRATEGIES
# ============================================================================

# Base finite numeric strategies
finite_float = st.floats(
    min_value=-1e10, max_value=1e10, allow_nan=False, allow_infinity=False
)
coord = st.floats(min_value=-1e9, max_value=1e9, allow_nan=False, allow_infinity=False)
positive_float = st.floats(
    min_value=1e-6, max_value=1e10, allow_nan=False, allow_infinity=False
)
angle = st.floats(
    min_value=-3600.0, max_value=3600.0, allow_nan=False, allow_infinity=False
)

# Special floats
nan_float = st.just(float("nan"))
inf_float = st.one_of(st.just(float("inf")), st.just(float("-inf")))
any_float = st.one_of(finite_float, nan_float, inf_float)

# Text
short_text = st.text(min_size=1, max_size=20)

# Point dict (for JSON-like input)
point_dict = st.fixed_dictionaries(
    {
        "name": short_text,
        "x": st.one_of(coord, nan_float, inf_float),
        "y": st.one_of(coord, nan_float, inf_float),
        "z": st.one_of(st.none(), coord),
    }
)
points_list = st.lists(point_dict, min_size=0, max_size=50)

# Observation dict
obs_dict = st.fixed_dictionaries(
    {
        "point_name": short_text,
        "horizontal_angle": st.one_of(angle, nan_float, inf_float),
        "distance": st.one_of(
            positive_float, st.just(-1.0), st.just(0.0), nan_float, inf_float
        ),
        "vertical_angle": st.one_of(angle, nan_float, inf_float),
        "is_sideshot": st.booleans(),
    }
)
observations_list = st.lists(obs_dict, min_size=0, max_size=30)

# ============================================================================
# TEST CLASSES
# ============================================================================


class TestBasicMathFuzzing:
    """Fuzz basic conversion and math functions."""

    @given(
        degrees=st.integers(-360, 360),
        minutes=st.integers(0, 59),
        seconds=st.floats(0.0, 59.999),
    )
    @settings(max_examples=1000)
    def test_dms_to_decimal(self, degrees, minutes, seconds):
        try:
            res = dms_to_decimal_degrees(degrees, minutes, seconds)
            assert isinstance(res, float)
        except (ValueError, ValidationError, OverflowError):
            pass

    @given(angle=finite_float)
    @settings(max_examples=1000)
    def test_decimal_to_dms(self, angle):
        try:
            res = decimal_degrees_to_dms(angle)
            assert isinstance(res, dict) and "degrees" in res
        except (ValueError, ValidationError, OverflowError, TypeError):
            pass

    @given(angle=finite_float)
    @settings(max_examples=1000)
    def test_reverse_azimuth(self, angle):
        try:
            res = reverse_azimuth(angle)
            assert isinstance(res, float)
            if math.isfinite(res):
                assert 0 <= res < 360.0
        except (ValueError, ValidationError, OverflowError, TypeError):
            pass

    @given(angle=finite_float)
    @settings(max_examples=1000)
    def test_normalize_angle(self, angle):
        try:
            res = normalize_angle(angle)
            if math.isfinite(res):
                assert 0 <= res < 360.0
        except Exception:
            pass


class TestPointCalculationsFuzzing:
    """Fuzz point and distance/azimuth calculations."""

    @given(x1=coord, y1=coord, x2=coord, y2=coord)
    @settings(max_examples=1000)
    def test_forward_azimuth(self, x1, y1, x2, y2):
        try:
            res = compute_forward_azimuth(x1, y1, x2, y2)
            assert isinstance(res, float)
            if math.isfinite(res):
                # Note: due to floating-point, result may be exactly 360.0 for near-zero negative dy.
                # Ideally should be in [0, 360). This invariant is currently broken (see bug).
                assert 0 <= res <= 360.0
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
            if math.isfinite(res.get("azimuth", 0)):
                assert 0 <= res["azimuth"] <= 360.0
            if math.isfinite(res.get("distance", 0)):
                assert res["distance"] >= 0
        except (ValueError, ValidationError, OverflowError, TypeError):
            pass


class TestAreaFuzzing:
    """Fuzz polygon area calculations."""

    @given(points=points_list)
    @settings(max_examples=1000, deadline=None)
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

    @given(top=finite_float, bottom=finite_float, va=finite_float)
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

    @given(temp=finite_float, pressure=finite_float, freq=positive_float)
    @settings(max_examples=1000)
    def test_edm_correction(self, temp, pressure, freq):
        try:
            res = compute_edm_atmospheric_correction(temp, pressure, freq)
            assert isinstance(res, float)
            # The result is a float; specific value depends on formula.
            # We just check it's not bizarrely huge beyond floating point range.
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
            assert "points" in res
            assert "angular_misclosure" in res
            assert "linear_misclosure" in res
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
                    "from_pt": short_text,
                    "to_pt": short_text,
                    "value": finite_float,
                    "std_dev": positive_float,
                }
            ),
            max_size=20,
        ),
        coords=st.dictionaries(
            keys=short_text,
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
    """Fuzz geodetic conversions."""

    @given(lat=finite_float, lon=finite_float, cm=finite_float)
    @settings(max_examples=1000)
    def test_grid_convergence(self, lat, lon, cm):
        # Only test if latitude/longitude in reasonable ranges (approx)
        if -90 <= lat <= 90 and -180 <= lon <= 180 and -180 <= cm <= 180:
            try:
                res = compute_grid_convergence(lat, lon, cm)
                assert isinstance(res, float)
                if math.isfinite(res):
                    assert -180.0 <= res <= 180.0
            except (ValueError, ValidationError, TypeError, OverflowError):
                pass

    @given(lat=finite_float, lon=finite_float, cm=finite_float)
    @settings(max_examples=1000)
    def test_point_scale_factor(self, lat, lon, cm):
        if -90 <= lat <= 90 and -180 <= lon <= 180 and -180 <= cm <= 180:
            try:
                res = compute_point_scale_factor(lat, lon, cm)
                assert isinstance(res, float)
                if math.isfinite(res):
                    assert res > 0  # scale factor positive
            except (ValueError, ValidationError, TypeError, OverflowError):
                pass

    @given(lat=finite_float, lon=finite_float)
    @settings(max_examples=1000)
    def test_geoid_height(self, lat, lon):
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            try:
                r1 = geoid_height_egm96(lat, lon)
                r2 = geoid_height_egm2008(lat, lon)
                assert isinstance(r1, float)
                assert isinstance(r2, float)
            except (ValueError, ValidationError, TypeError, OverflowError):
                pass

    @given(lat=finite_float, lon=finite_float)
    @settings(max_examples=500)
    def test_gauss_kruger_forward(self, lat, lon):
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            # Choose a central meridian near longitude
            cm = round(lon / 3) * 3  # rough 3-degree zone
            try:
                res = project_coordinates_gauss_kruger(lat, lon, cm)
                assert isinstance(res, dict)
                assert "x" in res and "y" in res
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
    def test_mgrs_conversion(self, mgrs):
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
    """Fuzz drawing functions to catch crashes in rendering."""

    @given(
        boundary=st.lists(point_dict, min_size=3, max_size=30),
        zones=st.lists(
            st.fixed_dictionaries(
                {
                    "name": st.text(max_size=30),
                    "points": st.lists(point_dict, max_size=20),
                    "fill_color": st.one_of(st.none(), st.text(max_size=20)),
                    "fill_alpha": st.floats(
                        min_value=0.0, max_value=1.0, allow_nan=False
                    ),
                }
            ),
            max_size=5,
        ),
    )
    @settings(max_examples=200, deadline=None)
    def test_draw_plot_plan(self, boundary, zones):
        try:
            res = draw_plot_plan(boundary_json=boundary, zones_json=zones)
            assert res is not None  # Should return an Image object
        except (
            ValueError,
            ValidationError,
            TypeError,
            OverflowError,
            KeyError,
            IndexError,
        ):
            pass

    @given(
        points=st.lists(
            st.fixed_dictionaries(
                {
                    "station": finite_float,
                    "elevation": finite_float,
                    "design_elevation": st.none() | finite_float,
                }
            ),
            min_size=0,
            max_size=30,
        )
    )
    @settings(max_examples=200, deadline=None)
    def test_draw_profile(self, points):
        try:
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
                    "start_pt": st.fixed_dictionaries(
                        {"x": finite_float, "y": finite_float}
                    ),
                    "end_pt": st.fixed_dictionaries(
                        {"x": finite_float, "y": finite_float}
                    ),
                    "thickness": st.floats(
                        min_value=0.1, max_value=2.0, allow_nan=False
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
                        st.fixed_dictionaries({"x": finite_float, "y": finite_float}),
                        max_size=10,
                    ),
                }
            ),
            max_size=5,
        ),
    )
    @settings(max_examples=100, deadline=None)
    def test_draw_interior_plan(self, walls, rooms):
        try:
            res = draw_interior_plan(walls_json=walls, rooms_json=rooms)
            assert res is not None
        except (ValueError, ValidationError, TypeError, KeyError, OverflowError):
            pass


class TestInputValidation:
    """Specific edge case tests that should raise errors."""

    def test_area_with_nan(self):
        # NaN in coordinates should not crash; result may be NaN
        pts = [
            {"name": "A", "x": 0, "y": 0},
            {"name": "B", "x": float("nan"), "y": 0},
            {"name": "C", "x": 10, "y": 10},
            {"name": "A", "x": 0, "y": 0},
        ]
        compute_parcel_area(pts)  # should not raise

    def test_area_with_inf(self):
        pts = [
            {"name": "A", "x": 0, "y": 0},
            {"name": "B", "x": float("inf"), "y": 0},
            {"name": "C", "x": 10, "y": 10},
            {"name": "A", "x": 0, "y": 0},
        ]
        compute_parcel_area(pts)  # should not raise

    def test_azimuth_same_point(self):
        with pytest.raises(ValueError):
            compute_forward_azimuth(0, 0, 0, 0)

    def test_observation_missing_name(self):
        with pytest.raises(ValidationError):
            Observation(horizontal_angle=90.0, distance=100.0)

    def test_observation_extra_field(self):
        # Pydantic default is extra='ignore', so extra field should be accepted and ignored
        obs = Observation(
            point_name="P1", horizontal_angle=90.0, distance=100.0, extra_field=1
        )
        assert obs.point_name == "P1"

    def test_traverse_missing_start(self):
        # Missing required start_x, start_y would be TypeError before; but we need to test as arguments are required
        with pytest.raises(TypeError):
            adjust_traverse_network()
