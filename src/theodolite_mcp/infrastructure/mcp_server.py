from mcp.server.fastmcp import FastMCP, Image
from pydantic import Field
from typing import Optional, Union, Dict, Any
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
    AsBuiltPoint,
    VolumeGrid,
    GridCell,
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
import math

mcp = FastMCP("Survey Computation Engine")
service = SurveyService()


@mcp.tool()
def dms_to_decimal_degrees(
    degrees: int = Field(description="Degrees component (0-360)"),
    minutes: int = Field(description="Minutes component (0-59)"),
    seconds: float = Field(description="Seconds component (0-59.999...)"),
) -> float:
    """Converts Degrees, Minutes, Seconds to decimal degrees."""
    return dms_to_decimal(degrees, minutes, seconds)


@mcp.tool()
def decimal_degrees_to_dms(
    decimal: float = Field(description="Angle in decimal degrees (e.g., 123.4567)"),
) -> dict:
    """Converts decimal degrees to Degrees, Minutes, Seconds."""
    d, m, s = decimal_to_dms(decimal)
    return {"degrees": d, "minutes": m, "seconds": round(s, 2)}


@mcp.tool()
def compute_forward_azimuth(
    x1: float = Field(description="X coordinate of start point"),
    y1: float = Field(description="Y coordinate of start point"),
    x2: float = Field(description="X coordinate of end point"),
    y2: float = Field(description="Y coordinate of end point"),
) -> float:
    """Calculates the forward azimuth (bearing) from point 1 to point 2."""
    p1 = Point(name="P1", x=x1, y=y1)
    p2 = Point(name="P2", x=x2, y=y2)
    return calculate_azimuth_from_points(p1, p2)


@mcp.tool()
def compute_back_azimuth(
    azimuth: float = Field(description="Forward azimuth in decimal degrees"),
) -> float:
    """Calculates the back azimuth (reverse bearing)."""
    return normalize_angle(azimuth + 180.0)


@mcp.tool()
def compute_inverse_geodetic_problem(
    x1: float = Field(description="X coordinate of point 1"),
    y1: float = Field(description="Y coordinate of point 1"),
    x2: float = Field(description="X coordinate of point 2"),
    y2: float = Field(description="Y coordinate of point 2"),
    z1: Optional[float] = Field(
        default=None, description="Z coordinate (elevation) of point 1, optional"
    ),
    z2: Optional[float] = Field(
        default=None, description="Z coordinate (elevation) of point 2, optional"
    ),
) -> dict:
    """
    Solves the inverse geodetic problem: calculates azimuth, horizontal distance,
    and vertical data between two known points.
    """
    p1 = Point(name="P1", x=x1, y=y1, z=z1)
    p2 = Point(name="P2", x=x2, y=y2, z=z2)
    return calculate_inverse(p1, p2)


@mcp.tool()
def reduce_stadia_readings(
    top_hair: float = Field(description="Top stadia hair reading"),
    bottom_hair: float = Field(description="Bottom stadia hair reading"),
    vertical_angle: float = Field(description="Vertical angle in degrees"),
    hi: float = Field(default=0.0, description="Instrument height above ground"),
    ht: float = Field(default=0.0, description="Target height above ground"),
) -> dict:
    """
    Tacheometric reduction: computes horizontal distance and elevation from stadia readings.
    """
    m = StadiaMeasurement(
        top_hair=top_hair,
        bottom_hair=bottom_hair,
        vertical_angle=vertical_angle,
        instrument_height=hi,
        target_height=ht,
    )
    return calculate_stadia(m).model_dump()


@mcp.tool()
def compute_parcel_area(
    points_json: list[dict] = Field(
        description="List of polygon vertices as {x: float, y: float} dictionaries"
    ),
) -> float:
    """Calculates the area of a polygon from a list of coordinates (x, y)."""
    points = [Point(**pt) for pt in points_json]
    return calculate_area(points)


@mcp.tool()
def compute_edm_atmospheric_correction(
    temp_c: float = Field(description="Air temperature in Celsius"),
    pressure_hpa: float = Field(description="Atmospheric pressure in hPa (millibars)"),
    freq_const: float = Field(
        default=281.8, description="EDM frequency constant (default: 281.8)"
    ),
) -> float:
    """
    Calculates the atmospheric PPM (Parts Per Million) correction for EDM measurements.
    """
    params = EDMParameters(
        temperature_c=temp_c, pressure_hpa=pressure_hpa, frequency_const=freq_const
    )
    return calculate_ppm_correction(params)


@mcp.tool()
def adjust_traverse_network(
    start_x: float = Field(description="X coordinate of traverse start point"),
    start_y: float = Field(description="Y coordinate of traverse start point"),
    start_z: Optional[float] = Field(
        default=None, description="Z coordinate (elevation) of start point, optional"
    ),
    start_name: str = Field(default="P1", description="Label/name for the start point"),
    start_azimuth: float = Field(
        default=0.0, description="Known starting azimuth direction (degrees)"
    ),
    closing_azimuth: Optional[float] = Field(
        default=None, description="Known closing azimuth for closed traverse, optional"
    ),
    observations_json: list[dict] = Field(
        default=[], description="List of traverse observations (angles, distances)"
    ),
    is_closed: bool = Field(
        default=False, description="Whether the traverse is a closed loop"
    ),
    avg_elevation: float = Field(
        default=0.0, description="Average elevation for geodetic corrections"
    ),
    grid_scale_factor: float = Field(
        default=1.0, description="Grid scale factor for projection corrections"
    ),
    end_x: Optional[float] = Field(
        default=None, description="X coordinate of known end point for open traverse"
    ),
    end_y: Optional[float] = Field(
        default=None, description="Y coordinate of known end point for open traverse"
    ),
    end_name: Optional[str] = Field(
        default=None, description="Label/name for the end point"
    ),
    generate_report: bool = Field(
        default=True, description="Include markdown adjustment report in output"
    ),
) -> dict:
    """
    Performs Bowditch (Compass Rule) adjustment on a traverse network with geodetic corrections.
    Includes support for closed loops and open traverses between known azimuths.
    """
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


@mcp.tool()
def draw_plot_plan(
    title: str = Field(
        default="Cadastral Plan", description="Plan title displayed on the drawing"
    ),
    boundary_json: list[dict] = Field(
        default=[],
        description="List of boundary vertices as {x: float, y: float} dicts",
    ),
    zones_json: list[dict] = Field(
        default=[],
        description="List of zone definitions with name, points, and styling",
    ),
    language: str = Field(
        default="ru", description="Drawing language: 'ru' (Russian) or 'en' (English)"
    ),
    standard: str = Field(
        default="construction",
        description="Drawing standard: 'construction' (ISO 128-23) or 'shipbuilding' (ISO 129-4)",
    ),
    show_vertex_labels: bool = Field(
        default=True, description="Display vertex point labels (P1, P2, ...)"
    ),
    show_distances: bool = Field(
        default=True, description="Display distance labels on boundary edges"
    ),
    show_azimuths: bool = Field(
        default=True, description="Display azimuth/direction labels"
    ),
    show_areas: bool = Field(
        default=True, description="Display computed area for each zone"
    ),
    show_north_arrow: bool = Field(
        default=True, description="Display north arrow indicator"
    ),
    show_scale_bar: bool = Field(default=True, description="Display scale bar"),
    coordinate_labels: bool = Field(
        default=False, description="Display numeric coordinates at each vertex"
    ),
    width: float = Field(default=10.0, description="Plan width in inches"),
    height: float = Field(default=10.0, description="Plan height in inches"),
    dpi: int = Field(default=150, description="Image resolution in dots per inch"),
    output_path: Optional[str] = Field(
        default=None, description="Optional file path to save PNG output"
    ),
) -> Image:
    """
    Generate a visual cadastral/site plan showing land plot boundaries,
    zone areas, distance labels, azimuth labels, north arrow, and scale bar.
    Returns a PNG image.
    Standard options: 'construction' (ISO 128-23), 'shipbuilding' (ISO 129-4).
    """
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
    plan = PlotPlan(
        title=title,
        boundary_points=boundary_points,
        zones=zones,
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


@mcp.tool()
def export_to_dxf(
    title: str = Field(
        default="Cadastral Plan", description="Plan title stored in DXF metadata"
    ),
    boundary_json: list[dict] = Field(
        default=[],
        description="List of boundary vertices as {x: float, y: float} dicts",
    ),
    zones_json: list[dict] = Field(
        default=[],
        description="List of zone definitions with name, points, and styling",
    ),
    filename: str = Field(
        default="exported_plan.dxf",
        description="Output DXF filename (saved in 'output/' directory)",
    ),
    coordinate_labels: bool = Field(
        default=False, description="Add coordinate text labels to each vertex"
    ),
) -> str:
    """
    Exports a cadastral/site plan to a professional DXF file for AutoCAD/Civil 3D.
    Saves the file locally in the 'output' directory and returns the full path.
    The output includes layers for BOUNDARY, POINTS, BUILDINGS, WATER, and GREEN zones.
    """
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


@mcp.tool()
def draw_longitudinal_profile(
    title: str = Field(default="Longitudinal Profile", description="Profile title"),
    points_json: list[dict] = Field(
        default=[],
        description="List of profile points with station, elevation, and optional design data",
    ),
    language: str = Field(
        default="ru", description="Drawing language: 'ru' (Russian) or 'en' (English)"
    ),
    paper_format: str = Field(
        default="A3", description="Paper size: A0, A1, A2, A3, A4, etc."
    ),
    h_scale: int = Field(
        default=1000, description="Horizontal scale (e.g., 1000 for 1:1000)"
    ),
    v_scale: int = Field(
        default=100, description="Vertical scale (e.g., 100 for 1:100)"
    ),
) -> Image:
    """
    Generates a professional longitudinal profile (PNG) for pipelines or roads.
    Includes the 'podval' table with stations, distances, and elevations.
    """
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


@mcp.tool()
def export_profile_to_dxf(
    title: str = Field(
        default="Longitudinal Profile", description="Profile title stored in DXF"
    ),
    points_json: list[dict] = Field(
        default=[],
        description="List of profile points with station, elevation, and optional design data",
    ),
    filename: str = Field(
        default="exported_profile.dxf",
        description="Output DXF filename (saved in 'output/' directory)",
    ),
    h_scale: int = Field(
        default=1000, description="Horizontal scale (e.g., 1000 for 1:1000)"
    ),
    v_scale: int = Field(
        default=100, description="Vertical scale (e.g., 100 for 1:100)"
    ),
) -> str:
    """
    Exports a longitudinal profile to a professional DXF file for AutoCAD.
    Saves the file locally in the 'output' directory and returns the full path.
    Includes layers for GROUND, DESIGN, TABLE, and ORDINATES.
    """
    pts = [ProfilePoint(**p) for p in points_json]
    plan = ProfilePlan(title=title, points=pts, horiz_scale=h_scale, vert_scale=v_scale)

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    full_path = os.path.join(output_dir, filename)

    path = service.export_profile_dxf(plan, full_path)
    return f"✅ Profile DXF successfully exported to: {os.path.abspath(path)}"


@mcp.tool()
def draw_interior_plan(
    title: str = Field(default="Floor Plan", description="Architectural drawing title"),
    walls_json: list[dict] = Field(
        default=[],
        description="List of wall definitions with start_pt, end_pt, thickness, and openings",
    ),
    rooms_json: list[dict] = Field(
        default=[], description="List of room/polygon boundaries with points and labels"
    ),
    furniture_json: list[dict] = Field(
        default=[],
        description="List of furniture blocks (bed, sofa, wc, bath, sink, stove)",
    ),
    language: str = Field(
        default="ru", description="Drawing language: 'ru' (Russian) or 'en' (English)"
    ),
    paper_format: str = Field(
        default="A4", description="Paper size: A0, A1, A2, A3, A4, etc."
    ),
    scale: int = Field(
        default=50, description="Drawing scale denominator (e.g., 50 for 1:50)"
    ),
    output_path: Optional[str] = Field(
        default=None, description="Optional file path to save PNG output"
    ),
) -> Image:
    """
    Generates a professional architectural floor plan (PNG).
    IMPORTANT: All coordinates and dimensions MUST be in METERS.
    Supports walls with thickness, door/window openings, and furniture blocks (bed, sofa, wc, bath, sink, stove).
    """
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
            Room(name=r.get("name", "Room"), number=r.get("number", "1"), points=pts)
        )

    # furniture = [FurnitureItem(type=f["type"], center_pt=Point(**f["center_pt"]), width=f["width"], length=f["length"], rotation=f.get("rotation", 0.0)) for f in furniture_json]

    plan = InteriorPlan(
        title=title,
        walls=walls,
        rooms=rooms,
        # furniture=furniture,
        language=language,
        paper_format=paper_format,
        scale=scale,
    )
    png_bytes = service.render_interior(plan, output_path=output_path)
    return Image(data=png_bytes, format="png")


@mcp.tool()
def draw_construction_as_built_report(
    title: str = Field(default="As-Built Survey Report", description="Report title"),
    as_built_points_json: list[dict] = Field(
        default=[],
        description="List of as-built survey points with design vs. as-built coordinates",
    ),
    volume_grid_json: Optional[dict] = Field(
        default=None, description="Optional volume grid data for earthwork calculation"
    ),
    language: str = Field(
        default="ru", description="Drawing language: 'ru' (Russian) or 'en' (English)"
    ),
    paper_format: str = Field(
        default="A3", description="Paper size: A0, A1, A2, A3, A4, etc."
    ),
) -> Image:
    """
    Generates a construction report showing deviations (plan/fact) and earthwork volumes.
    Returns a PNG image with deviation arrows and/or a volume cartogram.
    """
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


@mcp.tool()
def adjust_network_least_squares(
    observations_json: list[dict] = Field(
        description="List of survey observations with type, stations, measurements, and precision"
    ),
    initial_coords: Dict[str, Dict[str, float]] = Field(
        description="Dictionary of initial point coordinates by station name, e.g. {'P1': {'x': 100.0, 'y': 200.0}, ...}"
    ),
) -> dict:
    """
    Performs a 2D Least Squares Adjustment on a surveying network.
    Supports distances and azimuths with precision estimates.
    """
    obs = [ObservationLS(**o) for o in observations_json]
    result = service.adjust_network_least_squares(obs, initial_coords)
    return result.model_dump()


@mcp.tool()
def transform_coordinate_system(
    lat: float = Field(description="Latitude of WGS84 point in decimal degrees"),
    lon: float = Field(description="Longitude of WGS84 point in decimal degrees"),
    h: float = Field(description="Ellipsoidal height (H) in meters"),
    dx: float = Field(description="Helmert translation X (meters)"),
    dy: float = Field(description="Helmert translation Y (meters)"),
    dz: float = Field(description="Helmert translation Z (meters)"),
    rx: float = Field(description="Helmert rotation X (arc-seconds)"),
    ry: float = Field(description="Helmert rotation Y (arc-seconds)"),
    rz: float = Field(description="Helmert rotation Z (arc-seconds)"),
    s: float = Field(description="Helmert scale factor (PPM, parts per million)"),
) -> dict:
    """
    Performs a 7-parameter Helmert transformation from WGS84 to a local system.
    rx, ry, rz in arc-seconds, s in PPM.
    """
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


@mcp.tool()
def project_coordinates_gauss_kruger(
    lat: float = Field(description="Latitude in decimal degrees (WGS84)"),
    lon: float = Field(description="Longitude in decimal degrees (WGS84)"),
    central_meridian: float = Field(
        description="Central meridian of GK zone in decimal degrees"
    ),
) -> dict:
    """
    Projects geodetic coordinates to Gauss-Krüger (X, Y) grid.
    Uses Krasovsky ellipsoid (standard for S-42/USK-2000).
    """
    return service.project_to_grid(lat, lon, 0.0, central_meridian)


if __name__ == "__main__":
    mcp.run()
