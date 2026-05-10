import ezdxf
from theodolite_mcp.domain.models import PlotPlan, Point, Zone, ProfilePlan
from theodolite_mcp.domain.models.schematic import (
    PipelineSchematic, PipeMedium,
)
import os


def export_plan_to_dxf(plan: PlotPlan, output_path: str):
    """
    Exports a PlotPlan to a DXF file with standardized layers.
    """
    doc = ezdxf.new("R2010")  # Use DXF R2010 version
    msp = doc.modelspace()

    # 1. Setup Layers
    doc.layers.add(name="0_BOUNDARY", color=7)  # White/Black
    doc.layers.add(name="0_POINTS", color=1)  # Red
    doc.layers.add(name="0_TEXT", color=7)
    doc.layers.add(name="ZONE_BUILDINGS", color=4)  # Blue
    doc.layers.add(name="ZONE_WATER", color=5)  # Cyan
    doc.layers.add(name="ZONE_GREEN", color=3)  # Green
    doc.layers.add(name="ZONE_OTHER", color=8)  # Dark Gray

    # 2. Determine dynamic text height based on coordinate span
    xs: list[float] = []
    ys: list[float] = []
    for p in plan.boundary_points:
        xs.append(p.x)
        ys.append(p.y)
    for zone in plan.zones:
        for zp in zone.points:
            xs.append(zp.x)
            ys.append(zp.y)
    if plan.as_built_points:
        for ab in plan.as_built_points:
            xs.append(ab.actual_x)
            ys.append(ab.actual_y)
    if xs and ys:
        x_span = max(xs) - min(xs)
        y_span = max(ys) - min(ys)
        text_height = max(1.0, (x_span + y_span) * 0.001)
    else:
        text_height = 1.0  # fallback

    # 3. Draw Boundary
    if plan.boundary_points:
        points = [(p.x, p.y) for p in plan.boundary_points]
        # Ensure it's closed for polyline if first and last match
        msp.add_lwpolyline(points, close=True, dxfattribs={"layer": "0_BOUNDARY"})

    # 4. Draw Points as Blocks/Points
    for p in plan.boundary_points:
        msp.add_point((p.x, p.y), dxfattribs={"layer": "0_POINTS"})
        if plan.show_vertex_labels:
            label = p.name
            if plan.coordinate_labels:
                label += f" (X:{p.x:.2f}, Y:{p.y:.2f})"
            msp.add_text(
                label, dxfattribs={"layer": "0_TEXT", "height": text_height}
            ).set_placement((p.x + 0.5, p.y + 0.5))

    # 5. Draw Zones
    for zone in plan.zones:
        name_l = zone.name.lower()
        layer = "ZONE_OTHER"
        if any(k in name_l for k in ["дом", "house", "building", "здание"]):
            layer = "ZONE_BUILDINGS"
        elif any(k in name_l for k in ["вода", "water", "lake", "stream"]):
            layer = "ZONE_WATER"
        elif any(k in name_l for k in ["сад", "trees", "park", "grass"]):
            layer = "ZONE_GREEN"

        if zone.points:
            z_points = [(pt.x, pt.y) for pt in zone.points]
            msp.add_lwpolyline(z_points, close=True, dxfattribs={"layer": layer})

            # Label zone center
            cx = sum(pt.x for pt in zone.points) / len(zone.points)
            cy = sum(pt.y for pt in zone.points) / len(zone.points)
            # Zone name slightly larger than point labels
            msp.add_text(
                zone.name, dxfattribs={"layer": "0_TEXT", "height": text_height * 1.2}
            ).set_placement((cx, cy))

    # 6. Save
    doc.saveas(output_path)
    return output_path


def export_profile_to_dxf(plan: ProfilePlan, output_path: str):
    """
    Exports a longitudinal profile to a DXF file for AutoCAD.
    Includes layers for GROUND, DESIGN, TABLE, and ORDINATES.
    """
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    # 1. Layers
    doc.layers.add(name="V-PROF-GROUND", color=7)
    doc.layers.add(name="V-PROF-DESIGN", color=1)  # Red
    doc.layers.add(name="V-PROF-TABLE", color=7)
    doc.layers.add(name="V-PROF-TEXT", color=7)
    doc.layers.add(name="V-PROF-ORDINATES", color=8)  # Gray

    # Scales
    h_scale = plan.horiz_scale
    v_scale = plan.vert_scale
    exaggeration = h_scale / v_scale

    # 2. Determine dynamic text height based on station and elevation ranges
    points = plan.points
    if points:
        stations = [p.station for p in points]
        grounds = [p.ground_z for p in points]
        designs = [p.design_z for p in points if p.design_z is not None]
        all_z = grounds + designs
        x_span = max(stations) - min(stations) if stations else 0
        y_span = max(all_z) - min(all_z) if all_z else 0
        text_height = max(1.0, (x_span + y_span) * 0.001)
    else:
        text_height = 1.0

    # 3. Draw Lines
    ground_pts = [(p.station, p.ground_z * exaggeration) for p in points]
    msp.add_lwpolyline(ground_pts, dxfattribs={"layer": "V-PROF-GROUND"})

    design_pts = [
        (p.station, p.design_z * exaggeration) for p in points if p.design_z is not None
    ]
    if design_pts:
        msp.add_lwpolyline(design_pts, dxfattribs={"layer": "V-PROF-DESIGN"})

    # 4. Draw Ordinates and Table (Simplified logic for CAD)
    y_table_top = (min(p.ground_z for p in points) - 10) * exaggeration

    for p in points:
        # Ordinate line
        msp.add_line(
            (p.station, p.ground_z * exaggeration),
            (p.station, y_table_top),
            dxfattribs={"layer": "V-PROF-ORDINATES"},
        )

        # Table labels (Vertical)
        msp.add_text(
            f"{p.ground_z:.2f}",
            dxfattribs={"layer": "V-PROF-TEXT", "height": text_height, "rotation": 90},
        ).set_placement((p.station + 0.2, y_table_top - 5))
        if p.design_z is not None:
            msp.add_text(
                f"{p.design_z:.2f}",
                dxfattribs={
                    "layer": "V-PROF-TEXT",
                    "height": text_height,
                    "rotation": 90,
                    "color": 1,
                },
            ).set_placement((p.station + 0.8, y_table_top - 5))

    # Table borders
    table_bottom = y_table_top - 15
    msp.add_line(
        (points[0].station, y_table_top),
        (points[-1].station, y_table_top),
        dxfattribs={"layer": "V-PROF-TABLE"},
    )
    msp.add_line(
        (points[0].station, table_bottom),
        (points[-1].station, table_bottom),
        dxfattribs={"layer": "V-PROF-TABLE"},
    )

    doc.saveas(output_path)
    return output_path


# ---------------------------------------------------------------------------
# Media → DXF layer color mapping
# ---------------------------------------------------------------------------
_MEDIA_LAYER_COLORS = {
    PipeMedium.HEATING_SUPPLY: 1,    # Red
    PipeMedium.HEATING_RETURN: 5,    # Blue
    PipeMedium.COLD_WATER: 3,        # Green
    PipeMedium.HOT_WATER: 1,         # Red
    PipeMedium.GAS: 40,              # Yellow
    PipeMedium.STEAM: 8,             # Gray
    PipeMedium.CONDENSATE: 4,        # Cyan
    PipeMedium.DRAINAGE: 30,         # Brown
    PipeMedium.CUSTOM: 7,            # White
}


def _ensure_pipe_layers(doc, media_types_used):
    """Create DXF layers for each pipe medium used."""
    for medium in media_types_used:
        layer_name = f"PIPE_{medium.upper()}"
        color = _MEDIA_LAYER_COLORS.get(medium, 7)
        if not doc.layers.has_entry(layer_name):
            doc.layers.add(name=layer_name, color=color)
    for layer_name, color in [
        ("SYMBOLS_VALVES", 7),
        ("SYMBOLS_EQUIPMENT", 7),
        ("SYMBOLS_FITTINGS", 7),
        ("SYMBOLS_INSTRUMENTS", 7),
        ("SYMBOLS_SUPPORTS", 8),
        ("INSULATION", 8),
        ("TEXT_TAGS", 7),
        ("TEXT_LABELS", 7),
    ]:
        if not doc.layers.has_entry(layer_name):
            doc.layers.add(name=layer_name, color=color)


def _dxf_valve(msp, valve, text_height):
    cx, cy = valve.center_pt.x, valve.center_pt.y
    s = max(0.15, valve.nominal_diameter / 1000.0 * 0.8)
    layer = "SYMBOLS_VALVES"
    vt = valve.valve_type

    if vt == "gate":
        msp.add_line((cx - s, cy - s * 0.7), (cx, cy), dxfattribs={"layer": layer})
        msp.add_line((cx, cy), (cx - s, cy + s * 0.7), dxfattribs={"layer": layer})
        msp.add_line((cx + s, cy - s * 0.7), (cx, cy), dxfattribs={"layer": layer})
        msp.add_line((cx, cy), (cx + s, cy + s * 0.7), dxfattribs={"layer": layer})
    elif vt == "ball":
        msp.add_circle((cx, cy), s * 0.6, dxfattribs={"layer": layer})
        msp.add_line((cx - s, cy), (cx + s, cy), dxfattribs={"layer": layer})
    elif vt == "check":
        msp.add_line((cx - s * 0.5, cy - s * 0.7), (cx + s, cy), dxfattribs={"layer": layer})
        msp.add_line((cx - s * 0.5, cy + s * 0.7), (cx + s, cy), dxfattribs={"layer": layer})
        msp.add_line((cx - s * 0.5, cy - s * 0.7), (cx - s * 0.5, cy + s * 0.7), dxfattribs={"layer": layer})
    else:
        msp.add_circle((cx, cy), s * 0.5, dxfattribs={"layer": layer})

    if valve.tag:
        msp.add_text(valve.tag, dxfattribs={
            "layer": "TEXT_TAGS", "height": text_height,
        }).set_placement((cx, cy + s * 1.2))


def _dxf_equipment(msp, eq, text_height):
    cx, cy = eq.center_pt.x, eq.center_pt.y
    hw, hh = eq.width / 2, eq.height / 2
    layer = "SYMBOLS_EQUIPMENT"
    et = eq.equipment_type

    if et in ("centrifugal_pump", "circulation_pump"):
        r = min(hw, hh)
        msp.add_circle((cx, cy), r, dxfattribs={"layer": layer})
        msp.add_line((cx, cy - r * 0.8), (cx - r * 0.5, cy + r * 0.4), dxfattribs={"layer": layer})
        msp.add_line((cx - r * 0.5, cy + r * 0.4), (cx + r * 0.5, cy + r * 0.4), dxfattribs={"layer": layer})
        msp.add_line((cx + r * 0.5, cy + r * 0.4), (cx, cy - r * 0.8), dxfattribs={"layer": layer})
    elif et == "boiler":
        msp.add_lwpolyline(
            [(cx - hw, cy - hh), (cx + hw, cy - hh), (cx + hw, cy + hh), (cx - hw, cy + hh)],
            close=True, dxfattribs={"layer": layer},
        )
    else:
        msp.add_lwpolyline(
            [(cx - hw, cy - hh), (cx + hw, cy - hh), (cx + hw, cy + hh), (cx - hw, cy + hh)],
            close=True, dxfattribs={"layer": layer},
        )

    if eq.tag:
        msp.add_text(eq.tag, dxfattribs={
            "layer": "TEXT_TAGS", "height": text_height,
        }).set_placement((cx, cy + hh + text_height * 0.5))
    if eq.label:
        msp.add_text(eq.label, dxfattribs={
            "layer": "TEXT_LABELS", "height": text_height * 0.8,
        }).set_placement((cx, cy - hh - text_height))


def _dxf_instrument(msp, instr, text_height):
    cx, cy = instr.center_pt.x, instr.center_pt.y
    r = 0.12
    layer = "SYMBOLS_INSTRUMENTS"

    if instr.in_dcs:
        msp.add_lwpolyline(
            [(cx - r, cy - r), (cx + r, cy - r), (cx + r, cy + r), (cx - r, cy + r)],
            close=True, dxfattribs={"layer": layer},
        )

    msp.add_circle((cx, cy), r, dxfattribs={"layer": layer})

    tag = f"{instr.measured_variable}{instr.suffix}-{instr.tag_number}"
    msp.add_text(tag, dxfattribs={
        "layer": "TEXT_TAGS", "height": text_height * 0.7, "horiz_align": 4,
    }).set_placement((cx, cy))


def export_schematic_to_dxf(plan: PipelineSchematic, output_path: str):
    """Export a PipelineSchematic to DXF with per-medium layers."""
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    media_used = set(p.medium for p in plan.pipes)
    _ensure_pipe_layers(doc, media_used)

    # Text height
    all_pts = []
    for p in plan.pipes:
        all_pts.extend([(p.start_pt.x, p.start_pt.y), (p.end_pt.x, p.end_pt.y)])
    for e in plan.equipment:
        all_pts.append((e.center_pt.x, e.center_pt.y))
    if all_pts:
        xs = [p[0] for p in all_pts]
        ys = [p[1] for p in all_pts]
        span = max(max(xs) - min(xs), max(ys) - min(ys), 1.0)
        text_height = span * 0.015
    else:
        text_height = 0.5

    # Pipes
    for pipe in plan.pipes:
        layer = f"PIPE_{pipe.medium.upper()}"
        msp.add_line(
            (pipe.start_pt.x, pipe.start_pt.y),
            (pipe.end_pt.x, pipe.end_pt.y),
            dxfattribs={"layer": layer},
        )
        mx = (pipe.start_pt.x + pipe.end_pt.x) / 2
        my = (pipe.start_pt.y + pipe.end_pt.y) / 2
        msp.add_text(f"DN{pipe.nominal_diameter}", dxfattribs={
            "layer": "TEXT_LABELS", "height": text_height * 0.7,
        }).set_placement((mx, my + text_height))

        if pipe.insulated:
            dx = pipe.end_pt.x - pipe.start_pt.x
            dy = pipe.end_pt.y - pipe.start_pt.y
            seg_len = (dx ** 2 + dy ** 2) ** 0.5
            if seg_len > 0:
                offset = 0.15 * (pipe.nominal_diameter / 1000.0)
                nx, ny = -dy / seg_len * offset, dx / seg_len * offset
                for sign in (1, -1):
                    msp.add_line(
                        (pipe.start_pt.x + sign * nx, pipe.start_pt.y + sign * ny),
                        (pipe.end_pt.x + sign * nx, pipe.end_pt.y + sign * ny),
                        dxfattribs={"layer": "INSULATION"},
                    )

    # Fittings
    for fitting in plan.fittings:
        cx, cy = fitting.center_pt.x, fitting.center_pt.y
        s = max(0.1, fitting.nominal_diameter / 1000.0 * 0.6)
        layer = "SYMBOLS_FITTINGS"
        ft = fitting.fitting_type
        if ft in ("tee", "cross"):
            msp.add_line((cx - s, cy), (cx + s, cy), dxfattribs={"layer": layer})
            msp.add_line((cx, cy - s), (cx, cy + s), dxfattribs={"layer": layer})
        elif ft == "elbow_90":
            msp.add_line((cx + s, cy), (cx, cy), dxfattribs={"layer": layer})
            msp.add_line((cx, cy), (cx, cy + s), dxfattribs={"layer": layer})
        elif ft == "reducer":
            msp.add_line((cx - s, cy - s * 0.3), (cx + s, cy - s * 0.6), dxfattribs={"layer": layer})
            msp.add_line((cx - s, cy + s * 0.3), (cx + s, cy + s * 0.6), dxfattribs={"layer": layer})
        else:
            msp.add_line((cx - s, cy), (cx + s, cy), dxfattribs={"layer": layer})

    for valve in plan.valves:
        _dxf_valve(msp, valve, text_height)

    for eq in plan.equipment:
        _dxf_equipment(msp, eq, text_height)

    for instr in plan.instruments:
        _dxf_instrument(msp, instr, text_height)

    for support in plan.supports:
        cx, cy = support.center_pt.x, support.center_pt.y
        s = 0.06
        layer = "SYMBOLS_SUPPORTS"
        msp.add_lwpolyline(
            [(cx - s, cy - s), (cx + s, cy - s), (cx, cy + s)],
            close=True, dxfattribs={"layer": layer},
        )

    doc.saveas(output_path)
    return output_path
