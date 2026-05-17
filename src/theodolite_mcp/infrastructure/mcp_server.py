from mcp.server.fastmcp import FastMCP, Image
from pydantic import Field
from typing import Annotated, Optional, Dict
import os
from theodolite_mcp.domain.models import (
    TraverseData,
    Point,
    Observation,
    StadiaMeasurement,
    TraverseResult,
    Zone,
    PlotPlan,
    EDMParameters,
    ProfilePlan,
    ProfilePoint,
    InteriorPlan,
    Wall,
    Opening,
    Room,
    FurnitureItem,
    AsBuiltPoint,
    VolumeGrid,
    GridCell,
    PipeSegment,
    ValveSymbol,
    EquipmentSymbol,
    FittingSymbol,
    InstrumentSymbol,
    PipeSupport,
    PipelineSchematic,
)
from ..domain.least_squares import ObservationLS
from ..application.services import SurveyService
from ..domain.logic import (
    dms_to_decimal,
    decimal_to_dms,
    normalize_angle,
    calculate_azimuth_from_points,
    calculate_stadia,
    calculate_inverse,
    generate_markdown_report,
    calculate_area,
    calculate_ppm_correction,
)
from ..domain.geodesy import (
    WGS84,
    KRASOVSKY,
    helmert_transform,
    geodetic_to_ecef,
    ecef_to_geodetic,
    gauss_kruger_forward,
    gauss_kruger_inverse,
    utm_forward,
    utm_inverse,
    mgrs_to_latlon,
    calculate_grid_convergence,
    calculate_point_scale_factor,
    geoid_height_approx,
    sk42_to_wgs84,
)
import math

mcp = FastMCP("Survey Computation Engine")
service = SurveyService()


@mcp.tool()
def dms_to_decimal_degrees(
    degrees: Annotated[int, Field(description="Degrees component (0-360)")],
    minutes: Annotated[int, Field(description="Minutes component (0-59)")],
    seconds: Annotated[float, Field(description="Seconds component (0-59.999...)")],
) -> float:
    """Converts Degrees, Minutes, Seconds to decimal degrees."""
    try:
        return dms_to_decimal(degrees, minutes, seconds)
    except Exception as e:
        raise ValueError(f"dms_to_decimal_degrees error: {e}") from e


@mcp.tool()
def decimal_degrees_to_dms(
    decimal: Annotated[
        float, Field(description="Angle in decimal degrees (e.g., 123.4567)")
    ],
) -> dict:
    """Converts decimal degrees to Degrees, Minutes, Seconds."""
    try:
        d, m, s = decimal_to_dms(decimal)
        return {"degrees": d, "minutes": m, "seconds": round(s, 2)}
    except Exception as e:
        raise ValueError(f"decimal_degrees_to_dms error: {e}") from e


@mcp.tool()
def compute_forward_azimuth(
    x1: Annotated[float, Field(description="X coordinate of start point")],
    y1: Annotated[float, Field(description="Y coordinate of start point")],
    x2: Annotated[float, Field(description="X coordinate of end point")],
    y2: Annotated[float, Field(description="Y coordinate of end point")],
) -> float:
    """Calculates the forward azimuth (bearing) from point 1 to point 2."""
    try:
        p1 = Point(name="P1", x=x1, y=y1)
        p2 = Point(name="P2", x=x2, y=y2)
        return calculate_azimuth_from_points(p1, p2)
    except Exception as e:
        raise ValueError(f"compute_forward_azimuth error: {e}") from e


@mcp.tool()
def compute_back_azimuth(
    azimuth: Annotated[float, Field(description="Forward azimuth in decimal degrees")],
) -> float:
    """Calculates the back azimuth (reverse bearing)."""
    try:
        return normalize_angle(azimuth + 180.0)
    except Exception as e:
        raise ValueError(f"compute_back_azimuth error: {e}") from e


@mcp.tool()
def compute_inverse_geodetic_problem(
    x1: Annotated[float, Field(description="X coordinate of point 1")],
    y1: Annotated[float, Field(description="Y coordinate of point 1")],
    x2: Annotated[float, Field(description="X coordinate of point 2")],
    y2: Annotated[float, Field(description="Y coordinate of point 2")],
    z1: Annotated[
        Optional[float],
        Field(
            default=None, description="Z coordinate (elevation) of point 1, optional"
        ),
    ] = None,
    z2: Annotated[
        Optional[float],
        Field(
            default=None, description="Z coordinate (elevation) of point 2, optional"
        ),
    ] = None,
) -> dict:
    """
    Solves the inverse geodetic problem: calculates azimuth, horizontal distance,
    and vertical data between two known points.
    """
    try:
        p1 = Point(name="P1", x=x1, y=y1, z=z1)
        p2 = Point(name="P2", x=x2, y=y2, z=z2)
        return calculate_inverse(p1, p2)
    except Exception as e:
        raise ValueError(f"compute_inverse_geodetic_problem error: {e}") from e


@mcp.tool()
def reduce_stadia_readings(
    top_hair: Annotated[float, Field(description="Top stadia hair reading")],
    bottom_hair: Annotated[float, Field(description="Bottom stadia hair reading")],
    vertical_angle: Annotated[float, Field(description="Vertical angle in degrees")],
    hi: Annotated[
        float, Field(default=0.0, description="Instrument height above ground")
    ] = 0.0,
    ht: Annotated[
        float, Field(default=0.0, description="Target height above ground")
    ] = 0.0,
) -> dict:
    """
    Tacheometric reduction: computes horizontal distance and elevation from stadia readings.
    """
    try:
        m = StadiaMeasurement(
            top_hair=top_hair,
            bottom_hair=bottom_hair,
            vertical_angle=vertical_angle,
            instrument_height=hi,
            target_height=ht,
        )
        return calculate_stadia(m).model_dump()
    except Exception as e:
        raise ValueError(f"reduce_stadia_readings error: {e}") from e


@mcp.tool()
def compute_parcel_area(
    points_json: Annotated[
        list[dict],
        Field(
            description="List of polygon vertices as {x: float, y: float} dictionaries"
        ),
    ],
) -> float:
    """Calculates the area of a polygon from a list of coordinates (x, y)."""
    try:
        points = [Point(**pt) for pt in points_json]
        return calculate_area(points)
    except Exception as e:
        raise ValueError(f"compute_parcel_area error: {e}") from e


@mcp.tool()
def compute_edm_atmospheric_correction(
    temp_c: Annotated[float, Field(description="Air temperature in Celsius")],
    pressure_hpa: Annotated[
        float, Field(description="Atmospheric pressure in hPa (millibars)")
    ],
    freq_const: Annotated[
        float,
        Field(default=281.8, description="EDM frequency constant (default: 281.8)"),
    ] = 281.8,
) -> float:
    """
    Calculates the atmospheric PPM (Parts Per Million) correction for EDM measurements.
    """
    try:
        params = EDMParameters(
            temperature_c=temp_c, pressure_hpa=pressure_hpa, frequency_const=freq_const
        )
        return calculate_ppm_correction(params)
    except Exception as e:
        raise ValueError(f"compute_edm_atmospheric_correction error: {e}") from e


@mcp.tool()
def adjust_traverse_network(
    start_x: Annotated[
        float, Field(description="X coordinate of traverse start point")
    ],
    start_y: Annotated[
        float, Field(description="Y coordinate of traverse start point")
    ],
    start_z: Annotated[
        Optional[float],
        Field(
            default=None,
            description="Z coordinate (elevation) of start point, optional",
        ),
    ] = None,
    start_name: Annotated[
        str, Field(default="P1", description="Label/name for the start point")
    ] = "P1",
    start_azimuth: Annotated[
        float,
        Field(default=0.0, description="Known starting azimuth direction (degrees)"),
    ] = 0.0,
    closing_azimuth: Annotated[
        Optional[float],
        Field(
            default=None,
            description="Known closing azimuth for closed traverse, optional",
        ),
    ] = None,
    observations_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of traverse observations (angles, distances)",
        ),
    ] = None,
    is_closed: Annotated[
        bool, Field(default=False, description="Whether the traverse is a closed loop")
    ] = False,
    avg_elevation: Annotated[
        float,
        Field(default=0.0, description="Average elevation for geodetic corrections"),
    ] = 0.0,
    grid_scale_factor: Annotated[
        float,
        Field(default=1.0, description="Grid scale factor for projection corrections"),
    ] = 1.0,
    end_x: Annotated[
        Optional[float],
        Field(
            default=None,
            description="X coordinate of known end point for open traverse",
        ),
    ] = None,
    end_y: Annotated[
        Optional[float],
        Field(
            default=None,
            description="Y coordinate of known end point for open traverse",
        ),
    ] = None,
    end_name: Annotated[
        Optional[str], Field(default=None, description="Label/name for the end point")
    ] = None,
    generate_report: Annotated[
        bool,
        Field(default=True, description="Include markdown adjustment report in output"),
    ] = True,
) -> dict:
    """
    Performs Bowditch (Compass Rule) adjustment on a traverse network with geodetic corrections.
    Includes support for closed loops and open traverses between known azimuths.
    """
    try:
        if observations_json is None:
            observations_json = []
        observations = [Observation(**obs) for obs in observations_json]
        start_point = Point(name=start_name, x=start_x, y=start_y, z=start_z)

        end_point = None
        if end_x is not None and end_y is not None:
            end_point = Point(name=end_name or "END", x=end_x, y=end_y)

        data = TraverseData(
            start_point=start_point,
            end_point=end_point,
            start_azimuth=start_azimuth,
            closing_azimuth=closing_azimuth,
            observations=observations,
            is_closed=is_closed,
            average_elevation=avg_elevation,
            grid_scale_factor=grid_scale_factor,
        )

        result = service.process_theodolite_traverse(data)
        dump = result.model_dump()

        if generate_report:
            dump["report_md"] = generate_markdown_report(result)

        return dump
    except Exception as e:
        raise ValueError(f"adjust_traverse_network error: {e}") from e


@mcp.tool()
def draw_plot_plan(
    title: Annotated[
        str,
        Field(
            default="Cadastral Plan", description="Plan title displayed on the drawing"
        ),
    ] = "Cadastral Plan",
    boundary_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of boundary vertices as {x: float, y: float} dicts",
        ),
    ] = None,
    zones_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of zone definitions with name, points, and styling",
        ),
    ] = None,
    landscape_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of landscape items (tree_conifer, tree_deciduous, shrub, lamp_post, bench)",
        ),
    ] = None,
    utilities_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of underground utility lines (water, sewage, electricity, gas)",
        ),
    ] = None,
    security_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of security items (camera, motion_sensor, keypad, siren)",
        ),
    ] = None,
    language: Annotated[
        str,
        Field(
            default="ru",
            description="Drawing language: 'ru' (Russian) or 'en' (English)",
        ),
    ] = "ru",
    standard: Annotated[
        str,
        Field(
            default="construction",
            description="Drawing standard: 'construction' (ISO 128-23) or 'shipbuilding' (ISO 129-4)",
        ),
    ] = "construction",
    show_vertex_labels: Annotated[
        bool,
        Field(default=True, description="Display vertex point labels (P1, P2, ...)"),
    ] = True,
    show_distances: Annotated[
        bool,
        Field(default=True, description="Display distance labels on boundary edges"),
    ] = True,
    show_azimuths: Annotated[
        bool, Field(default=True, description="Display azimuth/direction labels")
    ] = True,
    show_areas: Annotated[
        bool, Field(default=True, description="Display computed area for each zone")
    ] = True,
    show_north_arrow: Annotated[
        bool, Field(default=True, description="Display north arrow indicator")
    ] = True,
    show_scale_bar: Annotated[
        bool, Field(default=True, description="Display scale bar")
    ] = True,
    coordinate_labels: Annotated[
        bool,
        Field(default=False, description="Display numeric coordinates at each vertex"),
    ] = False,
    width: Annotated[
        float, Field(default=10.0, description="Plan width in inches")
    ] = 10.0,
    height: Annotated[
        float, Field(default=10.0, description="Plan height in inches")
    ] = 10.0,
    dpi: Annotated[
        int, Field(default=150, description="Image resolution in dots per inch")
    ] = 150,
    output_path: Annotated[
        Optional[str],
        Field(default=None, description="Optional file path to save PNG output"),
    ] = None,
) -> Image:
    """
    Generate a visual cadastral/site plan showing land plot boundaries,
    zone areas, distance labels, azimuth labels, north arrow, and scale bar.
    Returns a PNG image.
    Standard options: 'construction' (ISO 128-23), 'shipbuilding' (ISO 129-4).
    """
    try:
        if boundary_json is None:
            boundary_json = []
        if zones_json is None:
            zones_json = []
        boundary_points = [Point(**pt) for pt in boundary_json]
        zones = []
        for z in zones_json:
            pts = [Point(**p) for p in z.get("points", [])]
            zones.append(
                Zone(
                    name=z.get("name", "Zone"),
                    points=pts,
                    fill_color=z.get("fill_color"),
                    fill_alpha=z.get("fill_alpha", 0.3),
                )
            )
        landscape = []
        if landscape_json:
            for l in landscape_json:
                landscape.append(LandscapeItem(
                    type=l["type"],
                    point=Point(**l["point"]),
                    size=l.get("size", 1.0),
                    label=l.get("label"),
                    light_range=l.get("light_range", 0.0)
                ))
                
        utilities = []
        if utilities_json:
            for u in utilities_json:
                u_pts = [Point(**p) for p in u.get("points", [])]
                utilities.append(UtilityLine(
                    type=u["type"],
                    points=u_pts,
                    depth=u.get("depth", 0.0),
                    label=u.get("label")
                ))

        security = [SecurityItem(**s) for s in security_json] if security_json else []
        plan = PlotPlan(
            title=title,
            boundary_points=boundary_points,
            zones=zones,
            landscape=landscape,
            utilities=utilities,
            security=security,
            language=language,
            standard=standard,
            show_vertex_labels=show_vertex_labels,
            show_distances=show_distances,
            show_azimuths=show_azimuths,
            show_areas=show_areas,
            show_north_arrow=show_north_arrow,
            show_scale_bar=show_scale_bar,
            coordinate_labels=coordinate_labels,
            width_inches=width,
            height_inches=height,
            dpi=dpi,
        )

        png_bytes = service.render_plot(plan, output_path=output_path)
        return Image(data=png_bytes, format="png")
    except Exception as e:
        raise ValueError(f"draw_plot_plan error: {e}") from e


@mcp.tool()
def mcp_export_to_dxf(
    title: Annotated[
        str,
        Field(
            default="Cadastral Plan", description="Plan title stored in DXF metadata"
        ),
    ] = "Cadastral Plan",
    boundary_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of boundary vertices as {x: float, y: float} dicts",
        ),
    ] = None,
    zones_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of zone definitions with name, points, and styling",
        ),
    ] = None,
    filename: Annotated[
        str,
        Field(
            default="exported_plan.dxf",
            description="Output DXF filename (saved in 'output/' directory)",
        ),
    ] = "exported_plan.dxf",
    coordinate_labels: Annotated[
        bool,
        Field(default=False, description="Add coordinate text labels to each vertex"),
    ] = False,
) -> str:
    """
    Exports a cadastral/site plan to a professional DXF file for AutoCAD/Civil 3D.
    Saves the file locally in the 'output' directory and returns the full path.
    The output includes layers for BOUNDARY, POINTS, BUILDINGS, WATER, and GREEN zones.
    """
    try:
        if boundary_json is None:
            boundary_json = []
        if zones_json is None:
            zones_json = []
        boundary_points = [Point(**pt) for pt in boundary_json]
        zones = []
        for z in zones_json:
            pts = [Point(**p) for p in z.get("points", [])]
            zones.append(
                Zone(
                    name=z.get("name", "Zone"),
                    points=pts,
                    fill_color=z.get("fill_color"),
                )
            )
        plan = PlotPlan(
            title=title,
            boundary_points=boundary_points,
            zones=zones,
            coordinate_labels=coordinate_labels,
        )

        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        full_path = os.path.join(output_dir, filename)

        path = service.export_dxf(plan, full_path)
        return f"✅ DXF file successfully exported to: {os.path.abspath(path)}"
    except Exception as e:
        raise ValueError(f"mcp_export_to_dxf error: {e}") from e


@mcp.tool()
def draw_longitudinal_profile(
    title: Annotated[
        str, Field(default="Longitudinal Profile", description="Profile title")
    ] = "Longitudinal Profile",
    points_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of profile points with station, elevation, and optional design data",
        ),
    ] = None,
    language: Annotated[
        str,
        Field(
            default="ru",
            description="Drawing language: 'ru' (Russian) or 'en' (English)",
        ),
    ] = "ru",
    paper_format: Annotated[
        str, Field(default="A3", description="Paper size: A0, A1, A2, A3, A4, etc.")
    ] = "A3",
    h_scale: Annotated[
        int, Field(default=1000, description="Horizontal scale (e.g., 1000 for 1:1000)")
    ] = 1000,
    v_scale: Annotated[
        int, Field(default=100, description="Vertical scale (e.g., 100 for 1:100)")
    ] = 100,
) -> Image:
    """
    Generates a professional longitudinal profile (PNG) for pipelines or roads.
    Includes the 'podval' table with stations, distances, and elevations.
    """
    try:
        if points_json is None:
            points_json = []
        pts = [ProfilePoint(**p) for p in points_json]
        plan = ProfilePlan(
            title=title,
            points=pts,
            language=language,
            paper_format=paper_format,
            horiz_scale=h_scale,
            vert_scale=v_scale,
        )
        png_bytes = service.render_profile(plan)
        return Image(data=png_bytes, format="png")
    except Exception as e:
        raise ValueError(f"draw_longitudinal_profile error: {e}") from e


@mcp.tool()
def mcp_export_profile_to_dxf(
    title: Annotated[
        str,
        Field(
            default="Longitudinal Profile", description="Profile title stored in DXF"
        ),
    ] = "Longitudinal Profile",
    points_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of profile points with station, elevation, and optional design data",
        ),
    ] = None,
    filename: Annotated[
        str,
        Field(
            default="exported_profile.dxf",
            description="Output DXF filename (saved in 'output/' directory)",
        ),
    ] = "exported_profile.dxf",
    h_scale: Annotated[
        int, Field(default=1000, description="Horizontal scale (e.g., 1000 for 1:1000)")
    ] = 1000,
    v_scale: Annotated[
        int, Field(default=100, description="Vertical scale (e.g., 100 for 1:100)")
    ] = 100,
) -> str:
    """
    Exports a longitudinal profile to a professional DXF file for AutoCAD.
    Saves the file locally in the 'output' directory and returns the full path.
    Includes layers for GROUND, DESIGN, TABLE, and ORDINATES.
    """
    try:
        if points_json is None:
            points_json = []
        pts = [ProfilePoint(**p) for p in points_json]
        plan = ProfilePlan(
            title=title, points=pts, horiz_scale=h_scale, vert_scale=v_scale
        )

        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        full_path = os.path.join(output_dir, filename)

        path = service.export_profile_dxf(plan, full_path)
        return f"✅ Profile DXF successfully exported to: {os.path.abspath(path)}"
    except Exception as e:
        raise ValueError(f"mcp_export_profile_to_dxf error: {e}") from e


@mcp.tool()
def validate_dxf(
    dxf_path: Annotated[
        str,
        Field(
            description="Path to DXF file (absolute or relative to current working directory)"
        ),
    ],
    check_geometry: Annotated[
        bool,
        Field(
            default=True,
            description="Enable expensive geometry checks (self-intersection, overlapping contours)",
        ),
    ] = True,
) -> dict:
    """
    Validates a DXF file for common issues affecting cadastral/surveying plans.
    Checks performed:
    - Orphan entities (no layer or unexpected layer)
    - Overlapping/self-intersecting contours
    - Invalid text labels (empty, NaN, Infinity, extreme coordinates)
    - Zero-length line/polyline segments
    - Duplicate/shared vertices between contours
    Returns a detailed report with summary and issue list.
    """
    try:
        report = service.validate_dxf(dxf_path, check_geometry)
        return {
            "valid": report.is_valid,
            "has_errors": report.has_critical_errors,
            "summary": report.summary(),
            "file": report.file_path,
            "total_entities": report.total_entities,
            "layers": report.layers_found,
            "counts": {
                "polylines": report.polyline_entities,
                "lines": report.line_entities,
                "texts": report.text_entities,
            },
            "issues": [
                {
                    "entity_type": i.entity_type,
                    "layer": i.layer,
                    "handle": i.handle,
                    "severity": i.severity.value,
                    "message": i.message,
                    "location": i.location,
                }
                for i in report.issues
            ],
        }
    except Exception as e:
        raise ValueError(f"validate_dxf error: {e}") from e


@mcp.tool()
def draw_interior_plan(
    title: Annotated[
        str, Field(default="Floor Plan", description="Architectural drawing title")
    ] = "Floor Plan",
    walls_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of wall definitions with start_pt, end_pt, thickness, and openings",
        ),
    ] = None,
    rooms_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of room/polygon boundaries with points and labels",
        ),
    ] = None,
    furniture_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of furniture blocks (bed, sofa, wc, bath, sink, stove, fridge, washer)",
        ),
    ] = None,
    engineering_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of engineering items (socket, switch, lamp, radiator, ac, vent, boiler)",
        ),
    ] = None,
    security_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of security items (camera, motion_sensor, keypad, siren)",
        ),
    ] = None,
    dimensions_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of chained dimension lines with points and offset",
        ),
    ] = None,
    layer: Annotated[
        str,
        Field(
            default="full",
            description="Active layer: 'full', 'furniture', 'electrical', 'construction'",
        ),
    ] = "full",
    language: Annotated[
        str,
        Field(
            default="ru",
            description="Drawing language: 'ru' (Russian) or 'en' (English)",
        ),
    ] = "ru",
    paper_format: Annotated[
        str, Field(default="A4", description="Paper size: A0, A1, A2, A3, A4, etc.")
    ] = "A4",
    scale: Annotated[
        int,
        Field(default=50, description="Drawing scale denominator (e.g., 50 for 1:50)"),
    ] = 50,
    output_path: Annotated[
        Optional[str],
        Field(default=None, description="Optional file path to save PNG output"),
    ] = None,
) -> Image:
    """
    Generates a professional architectural floor plan (PNG).
    IMPORTANT: All coordinates and dimensions MUST be in METERS.
    Supports walls, openings (doors with arcs), furniture, engineering systems, and layers.
    """
    try:
        if walls_json is None:
            walls_json = []
        if rooms_json is None:
            rooms_json = []
        if furniture_json is None:
            furniture_json = []
        if engineering_json is None:
            engineering_json = []
        if dimensions_json is None:
            dimensions_json = []

        walls = []
        for w in walls_json:
            openings = [Opening(**op) for op in w.get("openings", [])]
            walls.append(
                Wall(
                    start_pt=Point(**w["start_pt"]),
                    end_pt=Point(**w["end_pt"]),
                    thickness=w.get("thickness", 0.3),
                    material=w.get("material", "brick"),
                    status=w.get("status", "existing"),
                    openings=openings,
                )
            )

        rooms = []
        for r in rooms_json:
            pts = [Point(**p) for p in r.get("points", [])]
            rooms.append(
                Room(
                    name=r.get("name", "Room"),
                    number=r.get("number", "1"),
                    points=pts,
                    floor_material=r.get("floor_material", "concrete"),
                    floor_pattern=r.get("floor_pattern"),
                    floor_tile_size=r.get("floor_tile_size", [0.6, 0.6]),
                    floor_angle=r.get("floor_angle", 0.0),
                    wall_finish=r.get("wall_finish"),
                )
            )

        furniture = []
        for f in furniture_json:
            furniture.append(
                FurnitureItem(
                    type=f["type"],
                    center_pt=Point(**f["center_pt"]),
                    width=f["width"],
                    length=f["length"],
                    rotation=f.get("rotation", 0.0),
                    status=f.get("status", "new"),
                    label=f.get("label"),
                    ergonomics_padding=f.get("ergonomics_padding", 0.0),
                )
            )

        engineering = [EngineeringItem(**e) for e in engineering_json]
        security = [SecurityItem(**s) for s in security_json]
        dimensions = []
        for d in dimensions_json:
            pts = [Point(**p) for p in d.get("points", [])]
            dimensions.append(
                DimensionLine(
                    points=pts,
                    offset=d.get("offset", 0.5),
                    label_format=d.get("label_format", "{:.0f}"),
                )
            )

        plan = InteriorPlan(
            title=title,
            walls=walls,
            rooms=rooms,
            furniture=furniture,
            engineering=engineering,
            security=security,
            dimensions=dimensions,
            layer=layer,
            show_ergonomics=show_ergonomics if "show_ergonomics" in locals() else False,
            language=language,
            paper_format=paper_format,
            scale=scale,
        )
        png_bytes = service.render_interior(plan, output_path=output_path)
        return Image(data=png_bytes, format="png")
    except Exception as e:
        raise ValueError(f"draw_interior_plan error: {e}") from e


@mcp.tool()
def get_interior_specifications(
    walls_json: Annotated[list[dict], Field(..., description="List of wall definitions")],
    rooms_json: Annotated[list[dict], Field(..., description="List of room/polygon boundaries")],
    furniture_json: Annotated[Optional[list[dict]], Field(default=None, description="List of furniture blocks with optional price/currency")] = None,
    engineering_json: Annotated[Optional[list[dict]], Field(default=None, description="List of engineering items (radiator, boiler, etc.) with optional price/currency")] = None,
) -> dict:
    """
    Generates professional specifications: BOM, total cost estimate, Tile calculation, and Area report.
    """
    try:
        if furniture_json is None: furniture_json = []
        if engineering_json is None: engineering_json = []

        walls = []
        for w in walls_json:
            openings = [Opening(**op) for op in w.get("openings", [])]
            walls.append(Wall(**w, openings=openings))

        rooms = []
        for r in rooms_json:
            pts = [Point(**p) for p in r.get("points", [])]
            rooms.append(Room(**r, points=pts))

        furniture = [FurnitureItem(**f) for f in furniture_json]
        engineering = [EngineeringItem(**e) for e in engineering_json]

        plan = InteriorPlan(walls=walls, rooms=rooms, furniture=furniture, engineering=engineering)
        report = service.generate_interior_report(plan)
        return report.model_dump()
    except Exception as e:
        raise ValueError(f"get_interior_specifications error: {e}") from e

@mcp.tool()
def draw_construction_as_built_report(
    title: Annotated[
        str, Field(default="As-Built Survey Report", description="Report title")
    ] = "As-Built Survey Report",
    as_built_points_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of as-built survey points with design vs. as-built coordinates",
        ),
    ] = None,
    volume_grid_json: Annotated[
        Optional[dict],
        Field(
            default=None,
            description="Optional volume grid data for earthwork calculation",
        ),
    ] = None,
    language: Annotated[
        str,
        Field(
            default="ru",
            description="Drawing language: 'ru' (Russian) or 'en' (English)",
        ),
    ] = "ru",
    paper_format: Annotated[
        str, Field(default="A3", description="Paper size: A0, A1, A2, A3, A4, etc.")
    ] = "A3",
) -> Image:
    """
    Generates a construction report showing deviations (plan/fact) and earthwork volumes.
    Returns a PNG image with deviation arrows and/or a volume cartogram.
    """
    try:
        if as_built_points_json is None:
            as_built_points_json = []
        pts = [AsBuiltPoint(**p) for p in as_built_points_json]

        v_grid = None
        if volume_grid_json:
            cells = [GridCell(**c) for c in volume_grid_json.get("cells", [])]
            v_grid = VolumeGrid(
                title=volume_grid_json.get("title", "Volume Grid"),
                cells=cells,
                total_cut=volume_grid_json.get("total_cut", 0),
                total_fill=volume_grid_json.get("total_fill", 0),
                net_volume=volume_grid_json.get("net_volume", 0),
            )

        plan = PlotPlan(
            title=title,
            boundary_points=[],  # Usually optional for deviation reports
            as_built_points=pts,
            volume_grid=v_grid,
            language=language,
            paper_format=paper_format,
        )

        png_bytes = service.render_plot(plan)
        return Image(data=png_bytes, format="png")
    except Exception as e:
        raise ValueError(f"draw_construction_as_built_report error: {e}") from e


@mcp.tool()
def adjust_network_least_squares(
    observations_json: Annotated[
        list[dict],
        Field(
            description="List of survey observations with type, stations, measurements, and precision"
        ),
    ],
    initial_coords: Annotated[
        Dict[str, Dict[str, float]],
        Field(
            description="Dictionary of initial point coordinates by station name, e.g. {'P1': {'x': 100.0, 'y': 200.0}, ...}"
        ),
    ],
    max_iterations: Annotated[
        int,
        Field(default=10, description="Maximum number of iteration cycles"),
    ] = 10,
    tolerance: Annotated[
        float,
        Field(
            default=1e-5,
            description="Convergence tolerance for coordinate corrections (meters)",
        ),
    ] = 1e-5,
) -> dict:
    """
    Performs a 2D Least Squares Adjustment on a surveying network.
    Supports distances and azimuths with precision estimates.
    """
    try:
        obs = [ObservationLS(**o) for o in observations_json]
        result = service.adjust_network_least_squares(
            obs, initial_coords, max_iterations, tolerance
        )
        return result.model_dump()
    except Exception as e:
        raise ValueError(f"adjust_network_least_squares error: {e}") from e


@mcp.tool()
def transform_coordinate_system(
    lat: Annotated[
        float, Field(description="Latitude of WGS84 point in decimal degrees")
    ],
    lon: Annotated[
        float, Field(description="Longitude of WGS84 point in decimal degrees")
    ],
    h: Annotated[float, Field(description="Ellipsoidal height (H) in meters")],
    dx: Annotated[float, Field(description="Helmert translation X (meters)")],
    dy: Annotated[float, Field(description="Helmert translation Y (meters)")],
    dz: Annotated[float, Field(description="Helmert translation Z (meters)")],
    rx: Annotated[float, Field(description="Helmert rotation X (arc-seconds)")],
    ry: Annotated[float, Field(description="Helmert rotation Y (arc-seconds)")],
    rz: Annotated[float, Field(description="Helmert rotation Z (arc-seconds)")],
    s: Annotated[
        float, Field(description="Helmert scale factor (PPM, parts per million)")
    ],
) -> dict:
    """
    Performs a 7-parameter Helmert transformation from WGS84 to a local system.
    rx, ry, rz in arc-seconds, s in PPM.
    """
    try:
        params = {
            "dx": dx,
            "dy": dy,
            "dz": dz,
            "rx_sec": rx,
            "ry_sec": ry,
            "rz_sec": rz,
            "s_ppm": s,
        }
        return service.transform_wgs84_to_local(lat, lon, h, params)
    except Exception as e:
        raise ValueError(f"transform_coordinate_system error: {e}") from e


@mcp.tool()
def project_coordinates_gauss_kruger(
    lat: Annotated[float, Field(description="Latitude in decimal degrees (WGS84)")],
    lon: Annotated[float, Field(description="Longitude in decimal degrees (WGS84)")],
    central_meridian: Annotated[
        float, Field(description="Central meridian of GK zone in decimal degrees")
    ],
) -> dict:
    """
    Projects geodetic coordinates to Gauss-Krüger (X, Y) grid.
    Uses Krasovsky ellipsoid (standard for S-42/USK-2000).
    """
    try:
        return service.project_to_grid(lat, lon, central_meridian)
    except Exception as e:
        raise ValueError(f"project_coordinates_gauss_kruger error: {e}") from e


# ========== Military Geodesy Tools ==========


@mcp.tool()
def utm_projection_inverse(
    northing: Annotated[float, Field(description="UTM northing in meters")],
    easting: Annotated[float, Field(description="UTM easting in meters")],
    zone_number: Annotated[int, Field(description="UTM zone number (1-60)")],
    zone_letter: Annotated[
        str, Field(description="UTM zone letter (C-X, excluding O and I)")
    ],
) -> dict:
    """
    UTM inverse projection (NATO Military Grid Standard).
    Converts UTM coordinates to latitude/longitude.
    """
    try:
        lat, lon = utm_inverse(northing, easting, zone_number, zone_letter, WGS84)
        return {"latitude": round(lat, 8), "longitude": round(lon, 8)}
    except Exception as e:
        raise ValueError(f"utm_projection_inverse error: {e}") from e


@mcp.tool()
def gauss_kruger_projection_inverse(
    northing: Annotated[
        float, Field(description="GK northing (meters from false origin)")
    ],
    easting: Annotated[
        float,
        Field(
            description="GK easting (meters from central meridian + 500,000 false easting)"
        ),
    ],
    zone_central_meridian: Annotated[
        float, Field(description="Central meridian of GK zone in decimal degrees")
    ],
    ellipsoid: Annotated[
        str,
        Field(
            default="KRASOVSKY",
            description="Ellipsoid: 'WGS84' or 'KRASOVSKY' (Soviet military standard)",
        ),
    ] = "KRASOVSKY",
) -> dict:
    """
    Gauss-Krüger inverse projection (Soviet military grid).
    Converts GK coordinates (Pulkovo 1942 / SK-42) to latitude/longitude.
    """
    try:
        ell = KRASOVSKY if ellipsoid == "KRASOVSKY" else WGS84
        lat, lon = gauss_kruger_inverse(northing, easting, zone_central_meridian, ell)
        return {"latitude": round(lat, 8), "longitude": round(lon, 8)}
    except Exception as e:
        raise ValueError(f"gauss_kruger_projection_inverse error: {e}") from e


@mcp.tool()
def utm_projection_forward(
    lat: Annotated[float, Field(description="Latitude in decimal degrees")],
    lon: Annotated[float, Field(description="Longitude in decimal degrees")],
) -> dict:
    """
    UTM forward projection (NATO Military Grid Standard).
    Returns northing, easting, zone number, and zone letter.
    """
    try:
        north, east, zone, letter = utm_forward(lat, lon, WGS84)
        return {
            "northing": round(north, 3),
            "easting": round(east, 3),
            "zone_number": zone,
            "zone_letter": letter,
        }
    except Exception as e:
        raise ValueError(f"utm_projection_forward error: {e}") from e


@mcp.tool()
def mgrs_to_latlon_conversion(
    mgrs: Annotated[
        str, Field(description="MGRS coordinate (e.g., '33U 12345 67890')")
    ],
) -> dict:
    """
    Convert MGRS (Military Grid Reference System) to latitude/longitude.
    """
    try:
        lat, lon = mgrs_to_latlon(mgrs, WGS84)
        return {"latitude": round(lat, 8), "longitude": round(lon, 8)}
    except Exception as e:
        raise ValueError(f"mgrs_to_latlon_conversion error: {e}") from e


@mcp.tool()
def compute_grid_convergence(
    lat: Annotated[float, Field(description="Latitude in decimal degrees")],
    lon: Annotated[float, Field(description="Longitude in decimal degrees")],
    central_meridian: Annotated[
        float, Field(description="Central meridian of UTM zone (e.g., 39 for zone 37U)")
    ],
) -> float:
    """
    Calculate grid convergence (meridian convergence) in decimal degrees.
    Grid Azimuth = True Azimuth - Grid Convergence.
    Positive = grid north is east of true north.
    """
    try:
        return round(calculate_grid_convergence(lat, lon, central_meridian, WGS84), 6)
    except Exception as e:
        raise ValueError(f"compute_grid_convergence error: {e}") from e


@mcp.tool()
def compute_point_scale_factor(
    lat: Annotated[float, Field(description="Latitude in decimal degrees")],
    lon: Annotated[float, Field(description="Longitude in decimal degrees")],
    central_meridian: Annotated[
        float, Field(description="Central meridian of UTM zone")
    ],
) -> float:
    """
    Calculate point scale factor (k) for UTM/Transverse Mercator projection.
    At central meridian, k ≈ 0.9996 for UTM.
    """
    try:
        return round(calculate_point_scale_factor(lat, lon, central_meridian, WGS84), 8)
    except Exception as e:
        raise ValueError(f"compute_point_scale_factor error: {e}") from e


@mcp.tool()
def geoid_height_egm96(
    lat: Annotated[float, Field(description="Latitude in decimal degrees")],
    lon: Annotated[float, Field(description="Longitude in decimal degrees")],
) -> float:
    """
    Approximate geoid height (N) using EGM96 model.
    N = height of geoid above ellipsoid in meters.
    """
    try:
        return round(geoid_height_approx(lat, lon, model="EGM96"), 2)
    except Exception as e:
        raise ValueError(f"geoid_height_egm96 error: {e}") from e


@mcp.tool()
def geoid_height_egm2008(
    lat: Annotated[float, Field(description="Latitude in decimal degrees")],
    lon: Annotated[float, Field(description="Longitude in decimal degrees")],
) -> float:
    """
    Approximate geoid height (N) using EGM2008 model.
    N = height of geoid above ellipsoid in meters.
    """
    try:
        return round(geoid_height_approx(lat, lon, model="EGM2008"), 2)
    except Exception as e:
        raise ValueError(f"geoid_height_egm2008 error: {e}") from e


@mcp.tool()
def helmert_transform_wgs84_to_local(
    lat: Annotated[
        float, Field(description="Latitude of WGS84 point (decimal degrees)")
    ],
    lon: Annotated[
        float, Field(description="Longitude of WGS84 point (decimal degrees)")
    ],
    h: Annotated[float, Field(description="Ellipsoidal height in meters")],
    dx: Annotated[float, Field(description="Helmert translation X (meters)")],
    dy: Annotated[float, Field(description="Helmert translation Y (meters)")],
    dz: Annotated[float, Field(description="Helmert translation Z (meters)")],
    rx_sec: Annotated[float, Field(description="Helmert rotation X (arc-seconds)")],
    ry_sec: Annotated[float, Field(description="Helmert rotation Y (arc-seconds)")],
    rz_sec: Annotated[float, Field(description="Helmert rotation Z (arc-seconds)")],
    s_ppm: Annotated[
        float, Field(description="Helmert scale factor (PPM - parts per million)")
    ],
    target_ellipsoid: Annotated[
        str,
        Field(
            default="KRASOVSKY",
            description="Target ellipsoid: 'WGS84' or 'KRASOVSKY' (Soviet standard)",
        ),
    ] = "KRASOVSKY",
) -> dict:
    """
    7-parameter Helmert transformation: WGS84 → local geodetic system.
    For military coordinate system conversions (Pulkovo 1942, SK-42, etc.).
    """
    try:
        ell = KRASOVSKY if target_ellipsoid == "KRASOVSKY" else WGS84
        params = {
            "dx": dx,
            "dy": dy,
            "dz": dz,
            "rx_sec": rx_sec,
            "ry_sec": ry_sec,
            "rz_sec": rz_sec,
            "s_ppm": s_ppm,
        }
        result = service.transform_wgs84_to_local(
            lat, lon, h, params, target_ellipsoid=ell
        )
        return {
            "latitude": round(result["lat"], 8),
            "longitude": round(result["lon"], 8),
            "height": round(result["h"], 3),
        }
    except Exception as e:
        raise ValueError(f"helmert_transform_wgs84_to_local error: {e}") from e


@mcp.tool()
def convert_sk42_to_wgs84(
    northing: Annotated[float, Field(description="SK-42 northing (meters)")],
    easting: Annotated[float, Field(description="SK-42 easting (meters)")],
    zone: Annotated[int, Field(description="Gauss-Kruger zone number (1-60)")],
) -> dict:
    """
    Convert Soviet SK-42 (Pulkovo 1942) coordinates to WGS84.
    SK-42 uses Krassovsky ellipsoid with GK zones.
    """
    try:
        lat, lon, h = sk42_to_wgs84(northing, easting, zone)
        return {
            "latitude": round(lat, 8),
            "longitude": round(lon, 8),
            "height": round(h, 3),
        }
    except Exception as e:
        raise ValueError(f"convert_sk42_to_wgs84 error: {e}") from e


@mcp.tool()
def reverse_azimuth(
    azimuth: Annotated[float, Field(description="Forward azimuth in decimal degrees")],
) -> float:
    """
    Calculate the reverse (back) azimuth.
    Back Azimuth = (Forward Azimuth ± 180°) normalized to [0, 360).
    """
    try:
        return round(normalize_angle(azimuth + 180.0), 4)
    except Exception as e:
        raise ValueError(f"reverse_azimuth error: {e}") from e


if __name__ == "__main__":
    mcp.run()


# ========== SVG EXPORT TOOLS ==========


@mcp.tool()
def draw_plot_plan_svg(
    title: Annotated[
        str,
        Field(
            default="Cadastral Plan", description="Plan title displayed on the drawing"
        ),
    ] = "Cadastral Plan",
    boundary_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of boundary vertices as {x: float, y: float} dicts",
        ),
    ] = None,
    zones_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of zone definitions with name, points, and styling",
        ),
    ] = None,
    landscape_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of landscape items (tree_conifer, tree_deciduous, shrub, lamp_post, bench)",
        ),
    ] = None,
    utilities_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of underground utility lines (water, sewage, electricity, gas)",
        ),
    ] = None,
    security_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of security items (camera, motion_sensor, keypad, siren)",
        ),
    ] = None,
    language: Annotated[
        str,
        Field(
            default="ru",
            description="Drawing language: 'ru' (Russian) or 'en' (English)",
        ),
    ] = "ru",
    standard: Annotated[
        str,
        Field(
            default="construction",
            description="Drawing standard: 'construction' (ISO 128-23) or 'shipbuilding' (ISO 129-4)",
        ),
    ] = "construction",
    show_vertex_labels: Annotated[
        bool,
        Field(default=True, description="Display vertex point labels (P1, P2, ...)"),
    ] = True,
    show_distances: Annotated[
        bool,
        Field(default=True, description="Display distance labels on boundary edges"),
    ] = True,
    show_azimuths: Annotated[
        bool, Field(default=True, description="Display azimuth/direction labels")
    ] = True,
    show_areas: Annotated[
        bool, Field(default=True, description="Display computed area for each zone")
    ] = True,
    show_north_arrow: Annotated[
        bool, Field(default=True, description="Display north arrow indicator")
    ] = True,
    show_scale_bar: Annotated[
        bool, Field(default=True, description="Display scale bar")
    ] = True,
    coordinate_labels: Annotated[
        bool,
        Field(default=False, description="Display numeric coordinates at each vertex"),
    ] = False,
    width: Annotated[
        float, Field(default=10.0, description="Plan width in inches")
    ] = 10.0,
    height: Annotated[
        float, Field(default=10.0, description="Plan height in inches")
    ] = 10.0,
    dpi: Annotated[
        int, Field(default=150, description="Image resolution in dots per inch")
    ] = 150,
    output_path: Annotated[
        Optional[str],
        Field(default=None, description="Optional file path to save SVG output"),
    ] = None,
) -> str:
    """
    Generate a cadastral/site plan as an SVG vector drawing.
    Returns the SVG XML string. Optionally saves to file if output_path provided.
    """
    try:
        if boundary_json is None:
            boundary_json = []
        if zones_json is None:
            zones_json = []
        boundary_points = [Point(**pt) for pt in boundary_json]
        zones = []
        for z in zones_json:
            pts = [Point(**p) for p in z.get("points", [])]
            zones.append(
                Zone(
                    name=z.get("name", "Zone"),
                    points=pts,
                    fill_color=z.get("fill_color"),
                    fill_alpha=z.get("fill_alpha", 0.3),
                )
            )
        landscape = []
        if landscape_json:
            for l in landscape_json:
                landscape.append(LandscapeItem(
                    type=l["type"],
                    point=Point(**l["point"]),
                    size=l.get("size", 1.0),
                    label=l.get("label"),
                    light_range=l.get("light_range", 0.0)
                ))
                
        utilities = []
        if utilities_json:
            for u in utilities_json:
                u_pts = [Point(**p) for p in u.get("points", [])]
                utilities.append(UtilityLine(
                    type=u["type"],
                    points=u_pts,
                    depth=u.get("depth", 0.0),
                    label=u.get("label")
                ))

        security = [SecurityItem(**s) for s in security_json] if security_json else []
        plan = PlotPlan(
            title=title,
            boundary_points=boundary_points,
            zones=zones,
            landscape=landscape,
            utilities=utilities,
            security=security,
            language=language,
            standard=standard,
            show_vertex_labels=show_vertex_labels,
            show_distances=show_distances,
            show_azimuths=show_azimuths,
            show_areas=show_areas,
            show_north_arrow=show_north_arrow,
            show_scale_bar=show_scale_bar,
            coordinate_labels=coordinate_labels,
            width_inches=width,
            height_inches=height,
            dpi=dpi,
        )
        svg_bytes = service.render_plot(
            plan, output_path=output_path, output_format="svg"
        )
        return svg_bytes.decode("utf-8")
    except Exception as e:
        raise ValueError(f"draw_plot_plan_svg error: {e}") from e


@mcp.tool()
def draw_longitudinal_profile_svg(
    title: Annotated[
        str, Field(default="Longitudinal Profile", description="Profile title")
    ] = "Longitudinal Profile",
    points_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of profile points with station, elevation, and optional design data",
        ),
    ] = None,
    language: Annotated[
        str,
        Field(
            default="ru",
            description="Drawing language: 'ru' (Russian) or 'en' (English)",
        ),
    ] = "ru",
    paper_format: Annotated[
        str, Field(default="A3", description="Paper size: A0, A1, A2, A3, A4, etc.")
    ] = "A3",
    h_scale: Annotated[
        int, Field(default=1000, description="Horizontal scale (e.g., 1000 for 1:1000)")
    ] = 1000,
    v_scale: Annotated[
        int, Field(default=100, description="Vertical scale (e.g., 100 for 1:100)")
    ] = 100,
    dpi: Annotated[
        int, Field(default=150, description="Image resolution in dots per inch")
    ] = 150,
    output_path: Annotated[
        Optional[str],
        Field(default=None, description="Optional file path to save SVG output"),
    ] = None,
) -> str:
    """
    Generates a professional longitudinal profile as SVG (vector) for pipelines or roads.
    Returns the SVG XML string. Optionally saves to file if output_path provided.
    """
    try:
        if points_json is None:
            points_json = []
        pts = [ProfilePoint(**p) for p in points_json]
        plan = ProfilePlan(
            title=title,
            points=pts,
            language=language,
            paper_format=paper_format,
            horiz_scale=h_scale,
            vert_scale=v_scale,
        )
        svg_bytes = service.render_profile(
            plan, output_path=output_path, output_format="svg"
        )
        return svg_bytes.decode("utf-8")
    except Exception as e:
        raise ValueError(f"draw_longitudinal_profile_svg error: {e}") from e


@mcp.tool()
def draw_interior_plan_svg(
    title: Annotated[
        str, Field(default="Floor Plan", description="Architectural drawing title")
    ] = "Floor Plan",
    walls_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of wall definitions with start_pt, end_pt, thickness, and openings",
        ),
    ] = None,
    rooms_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of room/polygon boundaries with points and labels",
        ),
    ] = None,
    furniture_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of furniture blocks (bed, sofa, wc, bath, sink, stove, fridge, washer)",
        ),
    ] = None,
    engineering_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of engineering items (socket, switch, lamp, radiator, ac, vent, boiler)",
        ),
    ] = None,
    security_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of security items (camera, motion_sensor, keypad, siren)",
        ),
    ] = None,
    dimensions_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of chained dimension lines with points and offset",
        ),
    ] = None,
    layer: Annotated[
        str,
        Field(
            default="full",
            description="Active layer: 'full', 'furniture', 'electrical', 'construction'",
        ),
    ] = "full",
    language: Annotated[
        str,
        Field(
            default="ru",
            description="Drawing language: 'ru' (Russian) or 'en' (English)",
        ),
    ] = "ru",
    paper_format: Annotated[
        str, Field(default="A4", description="Paper size: A0, A1, A2, A3, A4, etc.")
    ] = "A4",
    scale: Annotated[
        int,
        Field(default=50, description="Drawing scale denominator (e.g., 50 for 1:50)"),
    ] = 50,
    dpi: Annotated[
        int, Field(default=150, description="Image resolution in dots per inch")
    ] = 150,
    output_path: Annotated[
        Optional[str],
        Field(default=None, description="Optional file path to save SVG output"),
    ] = None,
) -> str:
    """
    Generates a professional architectural floor plan as SVG (vector).
    IMPORTANT: All coordinates and dimensions MUST be in METERS.
    Returns the SVG XML string. Optionally saves to file if output_path provided.
    """
    try:
        if walls_json is None:
            walls_json = []
        if rooms_json is None:
            rooms_json = []
        if furniture_json is None:
            furniture_json = []
        if engineering_json is None:
            engineering_json = []
        if dimensions_json is None:
            dimensions_json = []

        walls = []
        for w in walls_json:
            openings = [Opening(**op) for op in w.get("openings", [])]
            walls.append(
                Wall(
                    start_pt=Point(**w["start_pt"]),
                    end_pt=Point(**w["end_pt"]),
                    thickness=w.get("thickness", 0.3),
                    material=w.get("material", "brick"),
                    status=w.get("status", "existing"),
                    openings=openings,
                )
            )

        rooms = []
        for r in rooms_json:
            pts = [Point(**p) for p in r.get("points", [])]
            rooms.append(
                Room(
                    name=r.get("name", "Room"),
                    number=r.get("number", "1"),
                    points=pts,
                    floor_material=r.get("floor_material", "concrete"),
                    wall_finish=r.get("wall_finish"),
                )
            )

        furniture = [FurnitureItem(**f) for f in furniture_json]
        engineering = [EngineeringItem(**e) for e in engineering_json]
        security = [SecurityItem(**s) for s in security_json]
        dimensions = []
        for d in dimensions_json:
            pts = [Point(**p) for p in d.get("points", [])]
            dimensions.append(
                DimensionLine(
                    points=pts,
                    offset=d.get("offset", 0.5),
                    label_format=d.get("label_format", "{:.0f}"),
                )
            )

        plan = InteriorPlan(
            title=title,
            walls=walls,
            rooms=rooms,
            furniture=furniture,
            engineering=engineering,
            security=security,
            dimensions=dimensions,
            layer=layer,
            language=language,
            paper_format=paper_format,
            scale=scale,
            dpi=dpi,
        )
        svg_bytes = service.render_interior(
            plan, output_path=output_path, output_format="svg"
        )
        return svg_bytes.decode("utf-8")
    except Exception as e:
        raise ValueError(f"draw_interior_plan_svg error: {e}") from e


# ---------------------------------------------------------------------------
# Pipeline Schematic Tools (ISO 6412 / ISO 14617 / ISO 3511)
# ---------------------------------------------------------------------------


@mcp.tool()
def draw_heating_system(
    boiler_label: Annotated[str, Field(default="Coal Boiler", description="Label for the boiler")] = "Coal Boiler",
    radiator_count: Annotated[int, Field(default=3, description="Number of radiators to connect")] = 3,
    title: Annotated[str, Field(default="Heating System Schematic", description="Drawing title")] = "Heating System Schematic",
    language: Annotated[str, Field(default="ru", description="Language: 'ru' or 'en'")] = "ru",
    output_path: Annotated[Optional[str], Field(default=None, description="Path to save PNG")] = None,
) -> Image:
    """
    Automatically generates a professional heating system schematic (ISO 6412/14617).
    Connects one boiler to multiple radiators via supply and return manifolds.
    Includes pumps, valves, and expansion vessel.
    """
    try:
        from theodolite_mcp.domain.models.schematic import (
            PipelineSchematic, PipeSegment, EquipmentSymbol, ValveSymbol, 
            EquipmentType, ValveType, PipeMedium
        )
        
        # Localized labels
        labels = {
            "en": {"pump": "Heating Pump", "s_manifold": "Supply Manifold", "r_manifold": "Return Manifold"},
            "uk": {"pump": "Циркуляційний насос", "s_manifold": "Подаючий колектор", "r_manifold": "Зворотній колектор"},
            "ru": {"pump": "Циркуляционный насос", "s_manifold": "Подающий коллектор", "r_manifold": "Обратный коллектор"},
        }
        l = labels.get(language, labels["en"])
        
        pipes, equipment, valves = [], [], []
        
        # 1. Boiler at the left
        equipment.append(EquipmentSymbol(
            center_pt=Point(x=2, y=10),
            equipment_type=EquipmentType.BOILER,
            tag="B1",
            label=boiler_label,
            width=2.0,
            height=3.0
        ))
        
        # 2. Boiler Supply Line
        pipes.append(PipeSegment(start_pt=Point(x=3, y=11), end_pt=Point(x=5, y=11), medium=PipeMedium.HEATING_SUPPLY))
        valves.append(ValveSymbol(center_pt=Point(x=4, y=11), valve_type=ValveType.BALL, tag="V1"))
        
        # 3. Circulation Pump
        equipment.append(EquipmentSymbol(
            center_pt=Point(x=6, y=11),
            equipment_type=EquipmentType.CIRCULATION_PUMP,
            tag="P1",
            label=l["pump"],
            width=0.8,
            height=0.8
        ))
        pipes.append(PipeSegment(start_pt=Point(x=7, y=11), end_pt=Point(x=9, y=11), medium=PipeMedium.HEATING_SUPPLY))
        
        # 4. Supply Manifold
        equipment.append(EquipmentSymbol(
            center_pt=Point(x=12, y=11),
            equipment_type=EquipmentType.MANIFOLD,
            tag="M1",
            label=l["s_manifold"],
            width=4.0,
            height=0.6
        ))
        
        # 5. Return Manifold
        equipment.append(EquipmentSymbol(
            center_pt=Point(x=12, y=5),
            equipment_type=EquipmentType.MANIFOLD,
            tag="M2",
            label=l["r_manifold"],
            width=4.0,
            height=0.6
        ))
        
        # 6. Radiators
        for i in range(radiator_count):
            rx = 10 + i * 2.5
            # Radiator symbol
            equipment.append(EquipmentSymbol(
                center_pt=Point(x=rx, y=8),
                equipment_type=EquipmentType.RADIATOR,
                tag=f"R{i+1}",
                width=1.2,
                height=1.0
            ))
            # Connections to manifolds
            pipes.append(PipeSegment(start_pt=Point(x=rx, y=10.7), end_pt=Point(x=rx, y=8.5), medium=PipeMedium.HEATING_SUPPLY))
            pipes.append(PipeSegment(start_pt=Point(x=rx, y=7.5), end_pt=Point(x=rx, y=5.3), medium=PipeMedium.HEATING_RETURN))
            
        # 7. Return to Boiler
        pipes.append(PipeSegment(start_pt=Point(x=10, y=5), end_pt=Point(x=3, y=5), medium=PipeMedium.HEATING_RETURN))
        pipes.append(PipeSegment(start_pt=Point(x=3, y=5), end_pt=Point(x=3, y=8.5), medium=PipeMedium.HEATING_RETURN))
        
        # 8. Expansion Vessel
        pipes.append(PipeSegment(start_pt=Point(x=5, y=5), end_pt=Point(x=5, y=3.5), medium=PipeMedium.HEATING_RETURN))
        equipment.append(EquipmentSymbol(
            center_pt=Point(x=5, y=3),
            equipment_type=EquipmentType.EXPANSION_VESSEL,
            tag="EV1",
            width=1.0,
            height=1.0
        ))

        plan = PipelineSchematic(
            title=title,
            pipes=pipes,
            equipment=equipment,
            valves=valves,
            language=language
        )
        png_bytes = service.render_schematic(plan, output_path=output_path)
        return Image(data=png_bytes, format="png")
    except Exception as e:
        raise ValueError(f"draw_heating_system error: {e}") from e


@mcp.tool()
def draw_pipeline_schematic(
    title: Annotated[
        str,
        Field(default="Pipeline Schematic", description="Schematic drawing title"),
    ] = "Pipeline Schematic",
    project_number: Annotated[
        str, Field(default="P-001", description="Project number")
    ] = "P-001",
    organization: Annotated[
        str, Field(default="Engineering Bureau", description="Organization name")
    ] = "Engineering Bureau",
    pipes_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of pipe segments with start_pt, end_pt, medium, nominal_diameter, insulated, flow_direction",
        ),
    ] = None,
    valves_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of valve symbols: center_pt, valve_type (gate/ball/globe/check/butterfly/3way_mixing/prv/safety), rotation, nominal_diameter, tag",
        ),
    ] = None,
    equipment_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of equipment symbols: center_pt, equipment_type (centrifugal_pump/circulation_pump/boiler/shell_tube_hx/plate_hx/expansion_vessel/storage_tank/y_strainer/mesh_filter/pressure_gauge/thermometer/flow_meter/heat_meter), width, height, tag, label",
        ),
    ] = None,
    fittings_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of fitting symbols: center_pt, fitting_type (elbow_90/elbow_45/tee/reducer/union/flange/cross), rotation, nominal_diameter",
        ),
    ] = None,
    instruments_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of ISO 3511 instrument bubbles: center_pt, measured_variable (T/P/F/L), suffix (I/R/C/T/A), tag_number, in_dcs",
        ),
    ] = None,
    supports_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of pipe supports: center_pt, support_type (anchor/guide/hanger/spring)",
        ),
    ] = None,
    language: Annotated[
        str,
        Field(default="ru", description="Drawing language: 'ru', 'en', 'uk'"),
    ] = "ru",
    paper_format: Annotated[
        str, Field(default="A3", description="Paper size: A0, A1, A2, A3, A4")
    ] = "A3",
    scale: Annotated[
        int,
        Field(default=50, description="Drawing scale denominator (e.g., 50 for 1:50)"),
    ] = 50,
    show_legend: Annotated[
        bool, Field(default=True, description="Show symbol legend on the drawing")
    ] = True,
    show_tags: Annotated[
        bool, Field(default=True, description="Show equipment/valve tag labels")
    ] = True,
    output_path: Annotated[
        Optional[str],
        Field(default=None, description="Optional file path to save PNG output"),
    ] = None,
) -> Image:
    """
    Generates an ISO 6412/14617/3511 pipeline schematic for boiler/heating installations.
    Supports pipe segments with flow arrows, insulation, valve symbols, equipment symbols,
    fitting symbols, P&ID instrument bubbles, and pipe supports.
    All coordinates and dimensions MUST be in METERS.
    """
    try:
        pipes = [PipeSegment(**p) for p in (pipes_json or [])]
        valves = [ValveSymbol(**v) for v in (valves_json or [])]
        equipment = [EquipmentSymbol(**e) for e in (equipment_json or [])]
        fittings = [FittingSymbol(**f) for f in (fittings_json or [])]
        instruments = [InstrumentSymbol(**i) for i in (instruments_json or [])]
        supports = [PipeSupport(**s) for s in (supports_json or [])]

        plan = PipelineSchematic(
            title=title,
            project_number=project_number,
            organization=organization,
            pipes=pipes,
            valves=valves,
            equipment=equipment,
            fittings=fittings,
            instruments=instruments,
            supports=supports,
            language=language,
            paper_format=paper_format,
            scale=scale,
            show_legend=show_legend,
            show_tags=show_tags,
        )
        png_bytes = service.render_schematic(plan, output_path=output_path)
        return Image(data=png_bytes, format="png")
    except Exception as e:
        raise ValueError(f"draw_pipeline_schematic error: {e}") from e


@mcp.tool()
def draw_pipeline_schematic_svg(
    title: Annotated[
        str,
        Field(default="Pipeline Schematic", description="Schematic drawing title"),
    ] = "Pipeline Schematic",
    project_number: Annotated[
        str, Field(default="P-001", description="Project number")
    ] = "P-001",
    organization: Annotated[
        str, Field(default="Engineering Bureau", description="Organization name")
    ] = "Engineering Bureau",
    pipes_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of pipe segments with start_pt, end_pt, medium, nominal_diameter, insulated, flow_direction",
        ),
    ] = None,
    valves_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of valve symbols: center_pt, valve_type, rotation, nominal_diameter, tag",
        ),
    ] = None,
    equipment_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of equipment symbols: center_pt, equipment_type, width, height, tag, label",
        ),
    ] = None,
    fittings_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of fitting symbols: center_pt, fitting_type, rotation, nominal_diameter",
        ),
    ] = None,
    instruments_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of ISO 3511 instrument bubbles: center_pt, measured_variable, suffix, tag_number, in_dcs",
        ),
    ] = None,
    supports_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of pipe supports: center_pt, support_type",
        ),
    ] = None,
    language: Annotated[
        str,
        Field(default="ru", description="Drawing language: 'ru', 'en', 'uk'"),
    ] = "ru",
    paper_format: Annotated[
        str, Field(default="A3", description="Paper size: A0, A1, A2, A3, A4")
    ] = "A3",
    scale: Annotated[
        int,
        Field(default=50, description="Drawing scale denominator"),
    ] = 50,
    show_legend: Annotated[
        bool, Field(default=True, description="Show symbol legend")
    ] = True,
    show_tags: Annotated[
        bool, Field(default=True, description="Show tag labels")
    ] = True,
    output_path: Annotated[
        Optional[str],
        Field(default=None, description="Optional file path to save SVG output"),
    ] = None,
) -> str:
    """Generates a pipeline schematic in SVG format (ISO 6412/14617/3511)."""
    try:
        pipes = [PipeSegment(**p) for p in (pipes_json or [])]
        valves = [ValveSymbol(**v) for v in (valves_json or [])]
        equipment = [EquipmentSymbol(**e) for e in (equipment_json or [])]
        fittings = [FittingSymbol(**f) for f in (fittings_json or [])]
        instruments = [InstrumentSymbol(**i) for i in (instruments_json or [])]
        supports = [PipeSupport(**s) for s in (supports_json or [])]

        plan = PipelineSchematic(
            title=title,
            project_number=project_number,
            organization=organization,
            pipes=pipes,
            valves=valves,
            equipment=equipment,
            fittings=fittings,
            instruments=instruments,
            supports=supports,
            language=language,
            paper_format=paper_format,
            scale=scale,
            show_legend=show_legend,
            show_tags=show_tags,
        )
        svg_bytes = service.render_schematic(
            plan, output_path=output_path, output_format="svg"
        )
        return svg_bytes.decode("utf-8")
    except Exception as e:
        raise ValueError(f"draw_pipeline_schematic_svg error: {e}") from e


@mcp.tool()
def mcp_export_schematic_to_dxf(
    title: Annotated[
        str,
        Field(default="Pipeline Schematic", description="Schematic title stored in DXF"),
    ] = "Pipeline Schematic",
    project_number: Annotated[
        str, Field(default="P-001", description="Project number")
    ] = "P-001",
    organization: Annotated[
        str, Field(default="Engineering Bureau", description="Organization")
    ] = "Engineering Bureau",
    pipes_json: Annotated[
        Optional[list[dict]],
        Field(
            default=None,
            description="List of pipe segments",
        ),
    ] = None,
    valves_json: Annotated[
        Optional[list[dict]],
        Field(default=None, description="List of valve symbols"),
    ] = None,
    equipment_json: Annotated[
        Optional[list[dict]],
        Field(default=None, description="List of equipment symbols"),
    ] = None,
    fittings_json: Annotated[
        Optional[list[dict]],
        Field(default=None, description="List of fitting symbols"),
    ] = None,
    instruments_json: Annotated[
        Optional[list[dict]],
        Field(default=None, description="List of ISO 3511 instrument bubbles"),
    ] = None,
    supports_json: Annotated[
        Optional[list[dict]],
        Field(default=None, description="List of pipe supports"),
    ] = None,
    filename: Annotated[
        str,
        Field(
            default="exported_schematic.dxf",
            description="Output DXF filename (saved in 'output/' directory)",
        ),
    ] = "exported_schematic.dxf",
) -> str:
    """Exports a pipeline schematic to DXF for AutoCAD/Civil 3D. Layers per pipe medium and symbol type."""
    try:
        pipes = [PipeSegment(**p) for p in (pipes_json or [])]
        valves = [ValveSymbol(**v) for v in (valves_json or [])]
        equipment = [EquipmentSymbol(**e) for e in (equipment_json or [])]
        fittings = [FittingSymbol(**f) for f in (fittings_json or [])]
        instruments = [InstrumentSymbol(**i) for i in (instruments_json or [])]
        supports = [PipeSupport(**s) for s in (supports_json or [])]

        plan = PipelineSchematic(
            title=title,
            project_number=project_number,
            organization=organization,
            pipes=pipes,
            valves=valves,
            equipment=equipment,
            fittings=fittings,
            instruments=instruments,
            supports=supports,
        )

        output_dir = os.path.join(os.getcwd(), "output")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename)
        return service.export_schematic_dxf(plan, output_path)
    except Exception as e:
        raise ValueError(f"mcp_export_schematic_to_dxf error: {e}") from e
