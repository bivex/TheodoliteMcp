from mcp.server.fastmcp import FastMCP, Image
from ..domain.models import (
    TraverseData, Point, Observation, StadiaMeasurement,
    TraverseResult, Zone, PlotPlan, EDMParameters,
    ProfilePlan, ProfilePoint,
    InteriorPlan, Wall, Opening, Room,
    AsBuiltPoint, VolumeGrid, GridCell
)
from ..domain.least_squares import ObservationLS
from ..application.services import SurveyService
from ..domain.logic import (
    dms_to_decimal, decimal_to_dms, normalize_angle,
    calculate_azimuth_from_points, calculate_stadia,
    calculate_inverse, generate_markdown_report, calculate_area,
    calculate_ppm_correction,
)
import math

mcp = FastMCP("Survey Computation Engine")
service = SurveyService()

@mcp.tool()
def dms_to_decimal_degrees(degrees: int, minutes: int, seconds: float) -> float:
    """Converts Degrees, Minutes, Seconds to decimal degrees."""
    return dms_to_decimal(degrees, minutes, seconds)

@mcp.tool()
def decimal_degrees_to_dms(decimal: float) -> dict:
    """Converts decimal degrees to Degrees, Minutes, Seconds."""
    d, m, s = decimal_to_dms(decimal)
    return {"degrees": d, "minutes": m, "seconds": round(s, 2)}

@mcp.tool()
def compute_forward_azimuth(x1: float, y1: float, x2: float, y2: float) -> float:
    """Calculates the forward azimuth (bearing) from point 1 to point 2."""
    p1 = Point(name="P1", x=x1, y=y1)
    p2 = Point(name="P2", x=x2, y=y2)
    return calculate_azimuth_from_points(p1, p2)

@mcp.tool()
def compute_back_azimuth(azimuth: float) -> float:
    """Calculates the back azimuth (reverse bearing)."""
    return normalize_angle(azimuth + 180.0)

@mcp.tool()
def compute_inverse_geodetic_problem(x1: float, y1: float, x2: float, y2: float, 
                                     z1: float = None, z2: float = None) -> dict:
    """
    Solves the inverse geodetic problem: calculates azimuth, horizontal distance, 
    and vertical data between two known points.
    """
    p1 = Point(name="P1", x=x1, y=y1, z=z1)
    p2 = Point(name="P2", x=x2, y=y2, z=z2)
    return calculate_inverse(p1, p2)

@mcp.tool()
def reduce_stadia_readings(
    top_hair: float, 
    bottom_hair: float, 
    vertical_angle: float,
    hi: float = 0.0, 
    ht: float = 0.0
) -> dict:
    """
    Tacheometric reduction: computes horizontal distance and elevation from stadia readings.
    """
    m = StadiaMeasurement(
        top_hair=top_hair, 
        bottom_hair=bottom_hair, 
        vertical_angle=vertical_angle,
        instrument_height=hi, 
        target_height=ht
    )
    return calculate_stadia(m).model_dump()

@mcp.tool()
def compute_parcel_area(points_json: list[dict]) -> float:
    """Calculates the area of a polygon from a list of coordinates (x, y)."""
    points = [Point(**pt) for pt in points_json]
    return calculate_area(points)

@mcp.tool()
def compute_edm_atmospheric_correction(temp_c: float, pressure_hpa: float, 
                                        freq_const: float = 281.8) -> float:
    """
    Calculates the atmospheric PPM (Parts Per Million) correction for EDM measurements.
    """
    params = EDMParameters(temperature_c=temp_c, pressure_hpa=pressure_hpa, frequency_const=freq_const)
    return calculate_ppm_correction(params)

@mcp.tool()
def adjust_traverse_network(
    start_x: float,
    start_y: float,
    start_z: float = None,
    start_name: str = "P1",
    start_azimuth: float = 0.0,
    closing_azimuth: float = None,
    observations_json: list[dict] = [],
    is_closed: bool = False,
    avg_elevation: float = 0.0,
    grid_scale_factor: float = 1.0,
    end_x: float = None,
    end_y: float = None,
    end_name: str = None,
    generate_report: bool = True
):
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
        grid_scale_factor=grid_scale_factor
    )
    
    result = service.process_theodolite_traverse(data)
    dump = result.model_dump()
    
    if generate_report:
        dump["report_md"] = generate_markdown_report(result)
        
    return dump

@mcp.tool()
def draw_plot_plan(
    title: str = "Cadastral Plan",
    boundary_json: list[dict] = [],
    zones_json: list[dict] = [],
    language: str = "ru",
    standard: str = "construction",
    show_vertex_labels: bool = True,
    show_distances: bool = True,
    show_azimuths: bool = True,
    show_areas: bool = True,
    show_north_arrow: bool = True,
    show_scale_bar: bool = True,
    coordinate_labels: bool = False,
    width: float = 10.0,
    height: float = 10.0,
    dpi: int = 150,
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
        zones.append(Zone(
            name=z.get("name", "Zone"),
            points=pts,
            fill_color=z.get("fill_color"),
            fill_alpha=z.get("fill_alpha", 0.3),
        ))
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

    png_bytes = service.render_plot(plan)
    return Image(data=png_bytes, format="png")

@mcp.tool()
def export_to_dxf(
    title: str = "Cadastral Plan",
    boundary_json: list[dict] = [],
    zones_json: list[dict] = [],
    filename: str = "exported_plan.dxf",
    coordinate_labels: bool = False,
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
        zones.append(Zone(
            name=z.get("name", "Zone"),
            points=pts,
            fill_color=z.get("fill_color"),
        ))
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
    title: str = "Longitudinal Profile",
    points_json: list[dict] = [],
    language: str = "ru",
    paper_format: str = "A3",
    h_scale: int = 1000,
    v_scale: int = 100,
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
        vert_scale=v_scale
    )
    png_bytes = service.render_profile(plan)
    return Image(data=png_bytes, format="png")

@mcp.tool()
def export_profile_to_dxf(
    title: str = "Longitudinal Profile",
    points_json: list[dict] = [],
    filename: str = "exported_profile.dxf",
    h_scale: int = 1000,
    v_scale: int = 100,
) -> str:
    """
    Exports a longitudinal profile to a professional DXF file for AutoCAD.
    Saves the file locally in the 'output' directory and returns the full path.
    Includes layers for GROUND, DESIGN, TABLE, and ORDINATES.
    """
    pts = [ProfilePoint(**p) for p in points_json]
    plan = ProfilePlan(
        title=title,
        points=pts,
        horiz_scale=h_scale,
        vert_scale=v_scale
    )

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    full_path = os.path.join(output_dir, filename)
    
    path = service.export_profile_dxf(plan, full_path)
    return f"✅ Profile DXF successfully exported to: {os.path.abspath(path)}"

@mcp.tool()
def draw_interior_plan(
    title: str = "Floor Plan",
    walls_json: list[dict] = [],
    rooms_json: list[dict] = [],
    language: str = "ru",
    paper_format: str = "A4",
    scale: int = 50,
) -> Image:
    """
    Generates a professional architectural floor plan (PNG).
    Supports walls with thickness, door/window openings, and room labels.
    """
    walls = []
    for w in walls_json:
        openings = [Opening(**op) for op in w.get("openings", [])]
        walls.append(Wall(
            start_pt=Point(**w["start_pt"]),
            end_pt=Point(**w["end_pt"]),
            thickness=w.get("thickness", 0.3),
            material=w.get("material", "brick"),
            status=w.get("status", "existing"),
            openings=openings
        ))
    
    rooms = []
    for r in rooms_json:
        pts = [Point(**p) for p in r.get("points", [])]
        rooms.append(Room(
            name=r.get("name", "Room"),
            number=r.get("number", "1"),
            points=pts
        ))
        
    plan = InteriorPlan(
        title=title,
        walls=walls,
        rooms=rooms,
        language=language,
        paper_format=paper_format,
        scale=scale
    )
    png_bytes = service.render_interior(plan)
    return Image(data=png_bytes, format="png")

@mcp.tool()
def draw_construction_as_built_report(
    title: str = "As-Built Survey Report",
    as_built_points_json: list[dict] = [],
    volume_grid_json: dict = None,
    language: str = "ru",
    paper_format: str = "A3",
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
            net_volume=volume_grid_json.get("net_volume", 0)
        )
        
    plan = PlotPlan(
        title=title,
        boundary_points=[], # Usually optional for deviation reports
        as_built_points=pts,
        volume_grid=v_grid,
        language=language,
        paper_format=paper_format
    )
    
    png_bytes = service.render_plot(plan)
    return Image(data=png_bytes, format="png")

@mcp.tool()
def adjust_network_least_squares(
    observations_json: list[dict],
    initial_coords: dict[str, dict[str, float]]
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
    lat: float, lon: float, h: float,
    dx: float, dy: float, dz: float,
    rx: float, ry: float, rz: float,
    s: float
) -> dict:
    """
    Performs a 7-parameter Helmert transformation from WGS84 to a local system.
    rx, ry, rz in arc-seconds, s in PPM.
    """
    params = {"dx": dx, "dy": dy, "dz": dz, "rx_sec": rx, "ry_sec": ry, "rz_sec": rz, "s_ppm": s}
    return service.transform_wgs84_to_local(lat, lon, h, params)

@mcp.tool()
def project_coordinates_gauss_kruger(
    lat: float, lon: float, 
    central_meridian: float
) -> dict:
    """
    Projects geodetic coordinates to Gauss-Krüger (X, Y) grid.
    Uses Krasovsky ellipsoid (standard for S-42/USK-2000).
    """
    return service.project_to_grid(lat, lon, 0.0, central_meridian)

if __name__ == "__main__":
    mcp.run()
