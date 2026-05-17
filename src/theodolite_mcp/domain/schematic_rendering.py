"""ISO 6412 / ISO 14617 / ISO 3511 Pipeline Schematic Rendering.

Renders engineering pipeline schematics for boiler/heating installations
with standard symbols for pipes, valves, equipment, fittings, and instruments.
"""
import io
import math
from typing import Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure
from matplotlib.patches import Circle, Rectangle, FancyArrowPatch, Arc, Polygon
from matplotlib.backends.backend_svg import FigureCanvasSVG

from theodolite_mcp.domain.models.schematic import (
    PipeSegment, ValveSymbol, EquipmentSymbol, FittingSymbol,
    InstrumentSymbol, PipeSupport, PipelineSchematic,
    PipeMedium, ValveType, EquipmentType, FittingType, PipeSupportType,
)
from theodolite_mcp.domain.rendering import (
    D, D_WIDE, D_EXTRA_WIDE, D_SYMBOL, MM_TO_PT,
    TYPE_01, TYPE_02, TYPE_04, TYPE_05,
    PAPER_SIZES, MARGIN_LEFT, MARGIN_OTHER, STAMP_WIDTH, STAMP_HEIGHT,
    LabelTracker, I18N, _get_font, _draw_stamp, _draw_sheet_reference_grid,
)

# ---------------------------------------------------------------------------
# Media style lookup (ISO 6412 conventions)
# ---------------------------------------------------------------------------
MEDIA_STYLES: Dict[str, Dict] = {
    PipeMedium.HEATING_SUPPLY: {"color": "#CC0000", "ls": TYPE_01, "label_ru": "Подача тепл.", "label_en": "Heating Supply", "label_uk": "Подача тепл."},
    PipeMedium.HEATING_RETURN: {"color": "#0000CC", "ls": TYPE_01, "label_ru": "Обратка тепл.", "label_en": "Heating Return", "label_uk": "Зворотня тепл."},
    PipeMedium.COLD_WATER:    {"color": "#00AA00", "ls": TYPE_01, "label_ru": "ХВС", "label_en": "Cold Water", "label_uk": "ХВП"},
    PipeMedium.HOT_WATER:     {"color": "#CC0000", "ls": TYPE_02, "label_ru": "ГВС", "label_en": "Hot Water", "label_uk": "ГВП"},
    PipeMedium.GAS:           {"color": "#CCAA00", "ls": TYPE_01, "label_ru": "Газ", "label_en": "Gas", "label_uk": "Газ"},
    PipeMedium.STEAM:         {"color": "#888888", "ls": TYPE_01, "label_ru": "Пар", "label_en": "Steam", "label_uk": "Пара"},
    PipeMedium.CONDENSATE:    {"color": "#00AAAA", "ls": TYPE_02, "label_ru": "Конденсат", "label_en": "Condensate", "label_uk": "Конденсат"},
    PipeMedium.DRAINAGE:      {"color": "#8B4513", "ls": TYPE_04, "label_ru": "Канализ.", "label_en": "Drainage", "label_uk": "Канал."},
    PipeMedium.CUSTOM:        {"color": "#333333", "ls": TYPE_01, "label_ru": "Прочее", "label_en": "Custom", "label_uk": "Інше"},
}

# DN → line weight mapping
def _dn_lw(dn: int) -> float:
    if dn >= 100:
        return D_EXTRA_WIDE
    if dn >= 50:
        return D_WIDE
    return D


# ---------------------------------------------------------------------------
# Rotation helper (same pattern as _draw_furniture)
# ---------------------------------------------------------------------------
def _rot(px: float, py: float, cx: float, cy: float, angle_deg: float):
    """Rotate point (px,py) around (cx,cy) by angle_deg degrees."""
    rad = math.radians(angle_deg)
    c, s = math.cos(rad), math.sin(rad)
    dx, dy = px - cx, py - cy
    return cx + dx * c - dy * s, cy + dx * s + dy * c


def _rot_points(pts, cx, cy, angle_deg):
    return [_rot(x, y, cx, cy, angle_deg) for x, y in pts]


# ---------------------------------------------------------------------------
# Pipe segments
# ---------------------------------------------------------------------------
def _draw_pipe_segment(ax, pipe: PipeSegment, m_per_pt: float):
    style = MEDIA_STYLES.get(pipe.medium, MEDIA_STYLES[PipeMedium.CUSTOM])
    color = pipe.custom_color or style["color"]
    lw = _dn_lw(pipe.nominal_diameter)

    x1, y1 = pipe.start_pt.x, pipe.start_pt.y
    x2, y2 = pipe.end_pt.x, pipe.end_pt.y

    ax.plot([x1, x2], [y1, y2], color=color, linestyle=style["ls"],
            linewidth=lw, solid_capstyle="round", zorder=2)

    # Insulation: parallel dashed lines
    if pipe.insulated:
        dx, dy = x2 - x1, y2 - y1
        seg_len = math.hypot(dx, dy)
        if seg_len > 0:
            offset = 0.15 * (pipe.nominal_diameter / 1000.0)
            nx, ny = -dy / seg_len * offset, dx / seg_len * offset
            for sign in (1, -1):
                ox, oy = sign * nx, sign * ny
                ax.plot([x1 + ox, x2 + ox], [y1 + oy, y2 + oy],
                        color=color, linestyle=TYPE_02, linewidth=D * 0.5,
                        alpha=0.6, zorder=1)

    # Flow direction arrow
    if pipe.flow_direction != "none" and (x1 != x2 or y1 != y2):
        dx, dy = x2 - x1, y2 - y1
        seg_len = math.hypot(dx, dy)
        arrow_size = min(seg_len * 0.12, 0.15)
        if pipe.flow_direction == "backward":
            dx, dy = -dx, -dy
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ux, uy = dx / seg_len, dy / seg_len
        tip_x, tip_y = mx + ux * arrow_size, my + uy * arrow_size
        base_x, base_y = mx - ux * arrow_size, my - uy * arrow_size
        perp_x, perp_y = -uy * arrow_size * 0.5, ux * arrow_size * 0.5
        tri = [(tip_x, tip_y),
               (base_x + perp_x, base_y + perp_y),
               (base_x - perp_x, base_y - perp_y)]
        ax.add_patch(Polygon(tri, closed=True, fc=color, ec=color, zorder=3))

    # DN label at midpoint
    seg_len = math.hypot(x2 - x1, y2 - y1)
    if seg_len > 0.3:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        dx, dy = x2 - x1, y2 - y1
        nx, ny = -dy / seg_len, dx / seg_len
        offset = 0.08
        ax.text(mx + nx * offset, my + ny * offset, f"DN{pipe.nominal_diameter}",
                fontproperties=_get_font(8, m_per_pt=m_per_pt),
                ha="center", va="center", color=color, zorder=5)


# ---------------------------------------------------------------------------
# Valve symbols (ISO 14617)
# ---------------------------------------------------------------------------
def _draw_valve_symbol(ax, valve: ValveSymbol, m_per_pt: float):
    cx, cy = valve.center_pt.x, valve.center_pt.y
    s = max(0.15, valve.nominal_diameter / 1000.0 * 0.8)
    ang = valve.rotation
    lw = D_SYMBOL

    vt = valve.valve_type

    if vt == ValveType.GATE:
        # Bowtie: two triangles apex to apex
        pts_l = _rot_points([(-s, -s * 0.7), (0, 0), (-s, s * 0.7)], 0, 0, ang)
        pts_r = _rot_points([(s, -s * 0.7), (0, 0), (s, s * 0.7)], 0, 0, ang)
        pts_all = pts_l + pts_r
        ax.plot(*zip(*[pts_all[0], pts_all[1]]), color="black", lw=lw, zorder=6)
        ax.plot(*zip(*[pts_all[1], pts_all[2]]), color="black", lw=lw, zorder=6)
        ax.plot(*zip(*[pts_all[3], pts_all[4]]), color="black", lw=lw, zorder=6)
        ax.plot(*zip(*[pts_all[4], pts_all[5]]), color="black", lw=lw, zorder=6)

    elif vt == ValveType.BALL:
        # Circle with line through
        r = s * 0.6
        circle = Circle((cx, cy), r, fill=False, ec="black", lw=lw, zorder=6)
        ax.add_patch(circle)
        p1 = _rot(cx - s, cy, cx, cy, ang)
        p2 = _rot(cx + s, cy, cx, cy, ang)
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="black", lw=lw, zorder=6)

    elif vt == ValveType.GLOBE:
        # Circle with cross
        r = s * 0.6
        circle = Circle((cx, cy), r, fill=False, ec="black", lw=lw, zorder=6)
        ax.add_patch(circle)
        p1 = _rot(cx - r * 0.7, cy, cx, cy, ang)
        p2 = _rot(cx + r * 0.7, cy, cx, cy, ang)
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="black", lw=lw, zorder=7)
        p3 = _rot(cx, cy - r * 0.7, cx, cy, ang)
        p4 = _rot(cx, cy + r * 0.7, cx, cy, ang)
        ax.plot([p3[0], p4[0]], [p3[1], p4[1]], color="black", lw=lw, zorder=7)

    elif vt == ValveType.CHECK:
        # Triangle pointing in flow direction
        pts = _rot_points([(s, 0), (-s * 0.5, s * 0.7), (-s * 0.5, -s * 0.7)], 0, 0, ang)
        tri = Polygon(pts, closed=True, fc="white", ec="black", lw=lw, zorder=6)
        ax.add_patch(tri)

    elif vt == ValveType.BUTTERFLY:
        # Two triangles pointing outward (like bowtie but filled)
        pts_l = _rot_points([(-s, -s * 0.5), (0, 0), (-s, s * 0.5)], 0, 0, ang)
        pts_r = _rot_points([(s, -s * 0.5), (0, 0), (s, s * 0.5)], 0, 0, ang)
        tri_l = Polygon(pts_l, closed=True, fc="#DDDDDD", ec="black", lw=lw, zorder=6)
        tri_r = Polygon(pts_r, closed=True, fc="#DDDDDD", ec="black", lw=lw, zorder=6)
        ax.add_patch(tri_l)
        ax.add_patch(tri_r)

    elif vt == ValveType.THREE_WAY_MIXING:
        # T-shape with valve body
        p_l = _rot(cx - s, cy, cx, cy, ang)
        p_r = _rot(cx + s, cy, cx, cy, ang)
        p_t = _rot(cx, cy + s, cx, cy, ang)
        ax.plot([p_l[0], p_r[0]], [p_l[1], p_r[1]], color="black", lw=lw, zorder=6)
        ax.plot([cx, p_t[0]], [cy, p_t[1]], color="black", lw=lw, zorder=6)
        # Small bowtie at center
        pts_l2 = _rot_points([(-s * 0.3, -s * 0.3), (0, 0), (-s * 0.3, s * 0.3)], 0, 0, ang)
        pts_r2 = _rot_points([(s * 0.3, -s * 0.3), (0, 0), (s * 0.3, s * 0.3)], 0, 0, ang)
        for pts in (pts_l2, pts_r2):
            ax.plot(*zip(*pts), color="black", lw=lw * 0.7, zorder=7)

    elif vt == ValveType.PRESSURE_REDUCING:
        # Circle with arrow going through diagonally
        r = s * 0.6
        circle = Circle((cx, cy), r, fill=False, ec="black", lw=lw, zorder=6)
        ax.add_patch(circle)
        p1 = _rot(cx - s, cy, cx, cy, ang)
        p2 = _rot(cx + s, cy, cx, cy, ang)
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="black", lw=lw, zorder=6)
        # Diagonal arrow inside
        pa = _rot(cx - r * 0.4, cy - r * 0.4, cx, cy, ang)
        pb = _rot(cx + r * 0.4, cy + r * 0.4, cx, cy, ang)
        ax.annotate("", xy=pb, xytext=pa,
                     arrowprops=dict(arrowstyle="->", color="black", lw=lw * 0.7),
                     zorder=7)

    elif vt == ValveType.SAFETY_RELIEF:
        # Spring-loaded: bowtie + zigzag above
        pts_l = _rot_points([(-s * 0.6, -s * 0.4), (0, 0), (-s * 0.6, s * 0.4)], 0, 0, ang)
        pts_r = _rot_points([(s * 0.6, -s * 0.4), (0, 0), (s * 0.6, s * 0.4)], 0, 0, ang)
        for pts in (pts_l, pts_r):
            ax.plot(*zip(*pts), color="black", lw=lw, zorder=6)
        # Spring zigzag above
        zigzag = _rot_points([
            (0, s * 0.5), (-s * 0.3, s * 0.7), (s * 0.3, s * 0.9),
            (-s * 0.3, s * 1.1), (s * 0.3, s * 1.3),
        ], 0, 0, ang)
        ax.plot(*zip(*zigzag), color="black", lw=D, zorder=6)
        # Exhaust arrow
        top = _rot(cx, cy + s * 1.5, cx, cy, ang)
        ax.annotate("", xy=top, xytext=_rot(cx, cy + s * 1.3, cx, cy, ang),
                     arrowprops=dict(arrowstyle="->", color="black", lw=D),
                     zorder=6)

    # Tag label
    if valve.tag:
        tag_pos = _rot(cx, cy + s * 1.5, cx, cy, ang)
        ax.text(tag_pos[0], tag_pos[1], valve.tag,
                fontproperties=_get_font(10, bold=True, m_per_pt=m_per_pt),
                ha="center", va="bottom", color="black", zorder=8,
                bbox=dict(boxstyle="round,pad=0.05", fc="white", ec="none", alpha=0.8))


# ---------------------------------------------------------------------------
# Equipment symbols (ISO 14617)
# ---------------------------------------------------------------------------
def _draw_equipment_symbol(ax, eq: EquipmentSymbol, m_per_pt: float):
    cx, cy = eq.center_pt.x, eq.center_pt.y
    w, h = eq.width, eq.height
    ang = eq.rotation
    lw = D_SYMBOL
    et = eq.equipment_type

    if et in (EquipmentType.CENTRIFUGAL_PUMP, EquipmentType.CIRCULATION_PUMP):
        r = min(w, h) / 2
        circle = Circle((cx, cy), r, fill=False, ec="black", lw=lw, zorder=6)
        ax.add_patch(circle)
        # Triangle blade (impeller)
        blade = _rot_points([
            (0, -r * 0.8), (-r * 0.5, r * 0.4), (r * 0.5, r * 0.4)
        ], 0, 0, ang)
        tri = Polygon(blade, closed=True, fc="white", ec="black", lw=D, zorder=7)
        ax.add_patch(tri)
        # Inlet/outlet lines
        p_in = _rot(cx, cy - r * 1.2, cx, cy, ang)
        p_out = _rot(cx + r * 1.2, cy, cx, cy, ang)
        p_in_end = _rot(cx, cy - r * 1.5, cx, cy, ang)
        p_out_end = _rot(cx + r * 1.5, cy, cx, cy, ang)
        ax.plot([p_in[0], p_in_end[0]], [p_in[1], p_in_end[1]], color="black", lw=lw, zorder=6)
        ax.plot([p_out[0], p_out_end[0]], [p_out[1], p_out_end[1]], color="black", lw=lw, zorder=6)
        # Filled dot at center for circulation pump
        if et == EquipmentType.CIRCULATION_PUMP:
            ax.plot(cx, cy, "ko", markersize=2, zorder=8)

    elif et == EquipmentType.BOILER:
        # Rectangle with flame wavy lines
        hw, hh = w / 2, h / 2
        corners = _rot_points([(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)], 0, 0, ang)
        rect_pts = corners + [corners[0]]
        ax.plot(*zip(*rect_pts), color="black", lw=D_WIDE, zorder=6)
        # Flame wavy lines inside
        for i in range(3):
            yy = -hh * 0.5 + i * hh * 0.5
            wave = []
            for t in range(9):
                xx = -hw * 0.6 + t * hw * 0.15
                wy = yy + math.sin(t * 1.2) * hh * 0.12
                wave.append(_rot(cx + xx, cy + wy, cx, cy, ang))
            if len(wave) > 1:
                ax.plot(*zip(*wave), color="#CC4400", lw=D, zorder=7)

    elif et == EquipmentType.SHELL_TUBE_HX:
        hw, hh = w / 2, h / 2
        corners = _rot_points([(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)], 0, 0, ang)
        rect_pts = corners + [corners[0]]
        ax.plot(*zip(*rect_pts), color="black", lw=D_WIDE, zorder=6)
        # Internal circles (tubes)
        for dx_f in (-0.3, 0, 0.3):
            c_pos = _rot(cx + hw * dx_f, cy, cx, cy, ang)
            c = Circle(c_pos, hh * 0.2, fill=False, ec="black", lw=D, zorder=7)
            ax.add_patch(c)

    elif et == EquipmentType.PLATE_HX:
        hw, hh = w / 2, h / 2
        corners = _rot_points([(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)], 0, 0, ang)
        rect_pts = corners + [corners[0]]
        ax.plot(*zip(*rect_pts), color="black", lw=D_WIDE, zorder=6)
        # Wavy internal line (plates)
        wave = []
        for t in range(11):
            xx = -hw * 0.8 + t * hw * 0.16
            wy = math.sin(t * 1.5) * hh * 0.6
            wave.append(_rot(cx + xx, cy + wy, cx, cy, ang))
        if len(wave) > 1:
            ax.plot(*zip(*wave), color="black", lw=D, zorder=7)

    elif et == EquipmentType.EXPANSION_VESSEL:
        r = min(w, h) / 2
        circle = Circle((cx, cy), r, fill=False, ec="black", lw=lw, zorder=6)
        ax.add_patch(circle)
        # Level line
        p1 = _rot(cx - r * 0.8, cy + r * 0.2, cx, cy, ang)
        p2 = _rot(cx + r * 0.8, cy + r * 0.2, cx, cy, ang)
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="#0066CC", lw=D, zorder=7)

    elif et == EquipmentType.STORAGE_TANK:
        hw, hh = w / 2, h / 2
        corners = _rot_points([(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)], 0, 0, ang)
        rect_pts = corners + [corners[0]]
        ax.plot(*zip(*rect_pts), color="black", lw=D_WIDE, zorder=6)
        # Rounded bottom arc
        arc_pts = []
        for t in range(11):
            angle = math.pi + t * math.pi / 10
            xx = hw * 0.8 * math.cos(angle)
            yy = -hh + hh * 0.15 * math.sin(angle) - hh * 0.1
            arc_pts.append(_rot(cx + xx, cy + yy, cx, cy, ang))
        if len(arc_pts) > 1:
            ax.plot(*zip(*arc_pts), color="black", lw=D, zorder=7)
        # Level indicator
        p1 = _rot(cx - hw * 0.6, cy, cx, cy, ang)
        p2 = _rot(cx + hw * 0.6, cy, cx, cy, ang)
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="#0066CC", lw=D, linestyle=TYPE_02, zorder=7)

    elif et in (EquipmentType.Y_STRAINER, EquipmentType.MESH_FILTER):
        # Diamond/Y shape
        if et == EquipmentType.Y_STRAINER:
            pts = _rot_points([
                (-w * 0.4, 0), (0, -h * 0.3),
                (w * 0.4, 0), (0, h * 0.3)
            ], 0, 0, ang)
        else:
            pts = _rot_points([
                (-w * 0.4, -h * 0.4), (w * 0.4, -h * 0.4),
                (w * 0.4, h * 0.4), (-w * 0.4, h * 0.4)
            ], 0, 0, ang)
        diamond = Polygon(pts, closed=True, fc="white", ec="black", lw=lw, zorder=6)
        ax.add_patch(diamond)
        # Internal grid lines
        for i in range(3):
            dx = -w * 0.2 + i * w * 0.2
            p1 = _rot(cx + dx, cy - h * 0.25, cx, cy, ang)
            p2 = _rot(cx + dx, cy + h * 0.25, cx, cy, ang)
            ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="black", lw=D * 0.5, zorder=7)

    elif et == EquipmentType.PRESSURE_GAUGE:
        r = min(w, h) / 2
        circle = Circle((cx, cy), r, fill=False, ec="black", lw=lw, zorder=6)
        ax.add_patch(circle)
        # Pointer
        p1 = _rot(cx, cy, cx, cy, ang)
        p2 = _rot(cx + r * 0.7, cy + r * 0.3, cx, cy, ang)
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="black", lw=D, zorder=7)
        # "P" label
        ax.text(cx, cy - r * 0.3, "P",
                fontproperties=_get_font(12, bold=True, m_per_pt=m_per_pt),
                ha="center", va="center", color="black", zorder=8)

    elif et == EquipmentType.THERMOMETER:
        r = min(w, h) / 2
        circle = Circle((cx, cy), r, fill=False, ec="black", lw=lw, zorder=6)
        ax.add_patch(circle)
        # Bulb at bottom
        bulb = _rot(cx, cy - r * 0.7, cx, cy, ang)
        bulb_c = Circle(bulb, r * 0.25, fc="red", ec="black", lw=D, zorder=7)
        ax.add_patch(bulb_c)
        # Stem
        p1 = _rot(cx, cy - r * 0.45, cx, cy, ang)
        p2 = _rot(cx, cy + r * 0.5, cx, cy, ang)
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="black", lw=D, zorder=7)

    elif et == EquipmentType.FLOW_METER:
        r = min(w, h) / 2
        circle = Circle((cx, cy), r, fill=False, ec="black", lw=lw, zorder=6)
        ax.add_patch(circle)
        # F inside
        ax.text(cx, cy, "F",
                fontproperties=_get_font(12, bold=True, m_per_pt=m_per_pt),
                ha="center", va="center", color="black", zorder=8)

    elif et == EquipmentType.HEAT_METER:
        r = min(w, h) / 2
        circle = Circle((cx, cy), r, fill=False, ec="black", lw=lw, zorder=6)
        ax.add_patch(circle)
        # Q inside
        ax.text(cx, cy, "Q",
                fontproperties=_get_font(12, bold=True, m_per_pt=m_per_pt),
                ha="center", va="center", color="black", zorder=8)

    # Tag + label
    tag_offset = max(w, h) / 2 + 0.1
    if eq.tag:
        tag_pos = _rot(cx, cy + tag_offset, cx, cy, ang)
        ax.text(tag_pos[0], tag_pos[1], eq.tag,
                fontproperties=_get_font(10, bold=True, m_per_pt=m_per_pt),
                ha="center", va="bottom", color="black", zorder=8,
                bbox=dict(boxstyle="round,pad=0.05", fc="white", ec="none", alpha=0.8))
    if eq.label:
        lbl_pos = _rot(cx, cy - tag_offset, cx, cy, ang)
        ax.text(lbl_pos[0], lbl_pos[1], eq.label,
                fontproperties=_get_font(8, m_per_pt=m_per_pt),
                ha="center", va="top", color="#333333", zorder=8)


# ---------------------------------------------------------------------------
# Fitting symbols (ISO 14617)
# ---------------------------------------------------------------------------
def _draw_fitting_symbol(ax, fitting: FittingSymbol, m_per_pt: float):
    cx, cy = fitting.center_pt.x, fitting.center_pt.y
    s = max(0.1, fitting.nominal_diameter / 1000.0 * 0.6)
    ang = fitting.rotation
    lw = D_SYMBOL
    ft = fitting.fitting_type

    if ft == FittingType.ELBOW_90:
        # Arc
        p_start = _rot(cx + s, cy, cx, cy, ang)
        p_end = _rot(cx, cy + s, cx, cy, ang)
        ax.plot([p_start[0], cx], [p_start[1], cy], color="black", lw=lw, zorder=6)
        ax.plot([cx, p_end[0]], [cy, p_end[1]], color="black", lw=lw, zorder=6)

    elif ft == FittingType.ELBOW_45:
        p_start = _rot(cx + s, cy, cx, cy, ang)
        p_end = _rot(cx + s * 0.7, cy + s * 0.7, cx, cy, ang)
        ax.plot([p_start[0], cx], [p_start[1], cy], color="black", lw=lw, zorder=6)
        ax.plot([cx, p_end[0]], [cy, p_end[1]], color="black", lw=lw, zorder=6)

    elif ft == FittingType.TEE:
        p_l = _rot(cx - s, cy, cx, cy, ang)
        p_r = _rot(cx + s, cy, cx, cy, ang)
        p_t = _rot(cx, cy + s, cx, cy, ang)
        ax.plot([p_l[0], p_r[0]], [p_l[1], p_r[1]], color="black", lw=lw, zorder=6)
        ax.plot([cx, p_t[0]], [cy, p_t[1]], color="black", lw=lw, zorder=6)

    elif ft == FittingType.REDUCER:
        p_l = _rot(cx - s, cy + s * 0.3, cx, cy, ang)
        p_r_top = _rot(cx + s, cy + s * 0.6, cx, cy, ang)
        p_r_bot = _rot(cx + s, cy - s * 0.6, cx, cy, ang)
        p_l2 = _rot(cx - s, cy - s * 0.3, cx, cy, ang)
        ax.plot([p_l[0], p_r_top[0]], [p_l[1], p_r_top[1]], color="black", lw=lw, zorder=6)
        ax.plot([p_l2[0], p_r_bot[0]], [p_l2[1], p_r_bot[1]], color="black", lw=lw, zorder=6)

    elif ft == FittingType.UNION:
        p_l = _rot(cx - s, cy, cx, cy, ang)
        p_r = _rot(cx + s, cy, cx, cy, ang)
        ax.plot([p_l[0], cx], [p_l[1], cy], color="black", lw=lw, zorder=6)
        ax.plot([cx, p_r[0]], [cy, p_r[1]], color="black", lw=lw, zorder=6)
        # Union mark: double line
        m1 = _rot(cx, cy + s * 0.3, cx, cy, ang)
        m2 = _rot(cx, cy - s * 0.3, cx, cy, ang)
        ax.plot([m1[0], m2[0]], [m1[1], m2[1]], color="black", lw=lw * 0.7, zorder=7)

    elif ft == FittingType.FLANGE:
        p_l = _rot(cx - s, cy, cx, cy, ang)
        p_r = _rot(cx + s, cy, cx, cy, ang)
        ax.plot([p_l[0], p_r[0]], [p_l[1], p_r[1]], color="black", lw=lw, zorder=6)
        # Flange marks: two perpendicular lines
        for sign in (-1, 1):
            f1 = _rot(cx + sign * s * 0.5, cy + s * 0.4, cx, cy, ang)
            f2 = _rot(cx + sign * s * 0.5, cy - s * 0.4, cx, cy, ang)
            ax.plot([f1[0], f2[0]], [f1[1], f2[1]], color="black", lw=lw, zorder=7)

    elif ft == FittingType.CROSS:
        p_l = _rot(cx - s, cy, cx, cy, ang)
        p_r = _rot(cx + s, cy, cx, cy, ang)
        p_t = _rot(cx, cy + s, cx, cy, ang)
        p_b = _rot(cx, cy - s, cx, cy, ang)
        ax.plot([p_l[0], p_r[0]], [p_l[1], p_r[1]], color="black", lw=lw, zorder=6)
        ax.plot([p_t[0], p_b[0]], [p_t[1], p_b[1]], color="black", lw=lw, zorder=6)


# ---------------------------------------------------------------------------
# Instrument bubbles (ISO 3511)
# ---------------------------------------------------------------------------
def _draw_instrument_bubble(ax, instr: InstrumentSymbol, m_per_pt: float):
    cx, cy = instr.center_pt.x, instr.center_pt.y
    r = 0.12  # Fixed bubble radius
    lw = D_SYMBOL

    tag = f"{instr.measured_variable}{instr.suffix}-{instr.tag_number}"

    if instr.in_dcs:
        # Square + circle for DCS/shared display
        rect = Rectangle((cx - r, cy - r), 2 * r, 2 * r,
                          fill=False, ec="black", lw=lw, zorder=6)
        ax.add_patch(rect)

    circle = Circle((cx, cy), r, fill=False, ec="black", lw=lw, zorder=7)
    ax.add_patch(circle)

    # Line from bubble to connection point
    ax.plot([cx, cx], [cy - r * 1.5, cy - r], color="black", lw=D, zorder=5)

    # Tag text inside bubble
    ax.text(cx, cy, tag,
            fontproperties=_get_font(8, bold=True, m_per_pt=m_per_pt),
            ha="center", va="center", color="black", zorder=8)


# ---------------------------------------------------------------------------
# Pipe supports
# ---------------------------------------------------------------------------
def _draw_pipe_support(ax, support: PipeSupport, m_per_pt: float):
    cx, cy = support.center_pt.x, support.center_pt.y
    s = 0.06
    lw = D

    st = support.support_type
    if st == PipeSupportType.ANCHOR:
        # Fixed: filled triangle
        tri = [(cx - s, cy - s), (cx + s, cy - s), (cx, cy + s)]
        ax.add_patch(Polygon(tri, closed=True, fc="black", ec="black", lw=lw, zorder=6))
    elif st == PipeSupportType.GUIDE:
        # Sliding: open triangle
        tri = [(cx - s, cy - s), (cx + s, cy - s), (cx, cy + s)]
        ax.add_patch(Polygon(tri, closed=True, fc="white", ec="black", lw=lw, zorder=6))
    elif st == PipeSupportType.HANGER:
        # U-shape hanger
        ax.plot([cx - s, cx - s, cx + s, cx + s],
                [cy, cy - s * 1.5, cy - s * 1.5, cy],
                color="black", lw=lw, zorder=6)
    elif st == PipeSupportType.SPRING:
        # Spring symbol: zigzag
        pts = [(cx - s * 0.5, cy + s), (cx + s * 0.5, cy + s * 0.5),
               (cx - s * 0.5, cy), (cx + s * 0.5, cy - s * 0.5),
               (cx - s * 0.5, cy - s)]
        ax.plot(*zip(*pts), color="black", lw=lw, zorder=6)


# ---------------------------------------------------------------------------
# Legend
# ---------------------------------------------------------------------------
def _draw_symbol_legend(ax, plan: PipelineSchematic, m_per_pt: float):
    """Draw symbol legend in upper-right area of the schematic."""
    lang = plan.language
    media_used = set(p.medium for p in plan.pipes)
    valve_types_used = set(v.valve_type for v in plan.valves)
    eq_types_used = set(e.equipment_type for e in plan.equipment)
    instr_used = len(plan.instruments) > 0

    if not media_used and not valve_types_used and not eq_types_used and not instr_used:
        return

    items = []

    for medium in media_used:
        style = MEDIA_STYLES.get(medium, MEDIA_STYLES[PipeMedium.CUSTOM])
        label = style.get(f"label_{lang}", style["label_en"])
        items.append(("pipe", medium, label, style))

    for vt in sorted(valve_types_used):
        items.append(("valve", vt, vt.replace("_", " ").title(), None))

    for et in sorted(eq_types_used):
        items.append(("equipment", et, et.replace("_", " ").title(), None))

    if instr_used:
        items.append(("instrument", "iso3511", "P&ID (ISO 3511)", None))

    n_items = len(items)
    if n_items == 0:
        return

    row_h = 0.25  # Was 0.12
    legend_w = 2.5  # Was 1.2
    legend_h = n_items * row_h + row_h * 1.5

    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    # Anchor to top-right with margin
    lx = xlim[1] - legend_w - 0.2
    ly = ylim[1] - 0.2

    # Background
    rect = Rectangle((lx, ly - legend_h), legend_w, legend_h,
                      fc="white", ec="black", lw=D_WIDE, alpha=0.9, zorder=9)
    ax.add_patch(rect)

    # Title
    title = "УСЛОВНЫЕ ОБОЗНАЧЕНИЯ" if lang == "ru" else "SYMBOL LEGEND"
    ax.text(lx + legend_w / 2, ly - row_h * 0.7, title,
            fontproperties=_get_font(12, bold=True, m_per_pt=m_per_pt),
            ha="center", va="center", color="black", zorder=10)

    for i, (itype, key, label, style) in enumerate(items):
        ry = ly - row_h * (i + 2.0)
        sample_x = lx + 0.3
        text_x = lx + 0.7

        if itype == "pipe" and style:
            ax.plot([sample_x - 0.15, sample_x + 0.15], [ry, ry],
                    color=style["color"], linestyle=style["ls"],
                    linewidth=D_WIDE * 1.5, zorder=10)
        elif itype in ("valve", "equipment", "instrument"):
            # Larger sample symbol
            ax.plot([sample_x - 0.12, sample_x + 0.12], [ry, ry],
                    color="black", linewidth=D_SYMBOL * 1.5, zorder=10)
            ax.plot(sample_x, ry, "s", color="black", markersize=4, zorder=10)

        ax.text(text_x, ry, label,
                fontproperties=_get_font(10, m_per_pt=m_per_pt),
                ha="left", va="center", color="black", zorder=10)


# ---------------------------------------------------------------------------
# Main render function
# ---------------------------------------------------------------------------
def render_pipeline_schematic(plan: PipelineSchematic, output_format: str = "png") -> bytes:
    """Render an ISO 6412/14617/3511 pipeline schematic to PNG or SVG bytes."""
    pw_mm, ph_mm = PAPER_SIZES.get(plan.paper_format, PAPER_SIZES["A3"])
    if plan.orientation == "landscape" and pw_mm < ph_mm:
        pw_mm, ph_mm = ph_mm, pw_mm

    # Figure setup (same pattern as render_plot_plan)
    fig_w_in = pw_mm / 25.4
    fig_h_in = ph_mm / 25.4
    fig = Figure(figsize=(fig_w_in, fig_h_in))
    fig.patch.set_facecolor("white")

    # Frame axis
    ax_frame = fig.add_axes([0, 0, 1, 1])
    ax_frame.set_xlim(0, pw_mm)
    ax_frame.set_ylim(0, ph_mm)
    ax_frame.set_aspect("equal")
    ax_frame.axis("off")

    # ISO 5457 border
    ax_frame.plot(
        [MARGIN_LEFT, pw_mm - MARGIN_OTHER, pw_mm - MARGIN_OTHER, MARGIN_LEFT, MARGIN_LEFT],
        [MARGIN_OTHER, MARGIN_OTHER, ph_mm - MARGIN_OTHER, ph_mm - MARGIN_OTHER, MARGIN_OTHER],
        color="black", lw=D_WIDE,
    )

    _draw_sheet_reference_grid(ax_frame, pw_mm, ph_mm)

    # Drawing area
    draw_w_mm = pw_mm - MARGIN_LEFT - MARGIN_OTHER - STAMP_WIDTH
    draw_h_mm = ph_mm - MARGIN_OTHER * 2
    draw_left_mm = MARGIN_LEFT
    draw_bottom_mm = MARGIN_OTHER

    # Calculate scale from plan data extent
    all_pts = []
    for p in plan.pipes:
        all_pts.extend([(p.start_pt.x, p.start_pt.y), (p.end_pt.x, p.end_pt.y)])
    for v in plan.valves:
        all_pts.append((v.center_pt.x, v.center_pt.y))
    for e in plan.equipment:
        all_pts.append((e.center_pt.x, e.center_pt.y))
    for f in plan.fittings:
        all_pts.append((f.center_pt.x, f.center_pt.y))
    for i in plan.instruments:
        all_pts.append((i.center_pt.x, i.center_pt.y))
    for s in plan.supports:
        all_pts.append((s.center_pt.x, s.center_pt.y))

    if not all_pts:
        all_pts = [(0, 0), (1, 1)]

    xs = [p[0] for p in all_pts]
    ys = [p[1] for p in all_pts]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    data_w = max(max_x - min_x, 0.1)
    data_h = max(max_y - min_y, 0.1)

    scale = plan.scale
    # 1:scale means 1mm on paper = scale mm in reality = scale/1000.0 meters in reality.
    m_per_mm = scale / 1000.0
    m_per_pt = m_per_mm / MM_TO_PT

    # Center data in drawing area
    data_cx = (min_x + max_x) / 2
    data_cy = (min_y + max_y) / 2
    draw_cx_mm = draw_left_mm + draw_w_mm / 2
    draw_cy_mm = draw_bottom_mm + draw_h_mm / 2

    def to_mm(x, y):
        return (draw_cx_mm + (x - data_cx) / m_per_mm,
                draw_cy_mm + (y - data_cy) / m_per_mm)

    # Create main drawing axis in mm space
    ax = fig.add_axes([
        draw_left_mm / pw_mm,
        draw_bottom_mm / ph_mm,
        draw_w_mm / pw_mm,
        draw_h_mm / ph_mm,
    ])

    margin = max(data_w, data_h) * 0.1
    ax.set_xlim(min_x - margin, max_x + margin)
    ax.set_ylim(min_y - margin, max_y + margin)
    ax.set_aspect("equal")
    ax.axis("off")

    # Draw all elements
    for pipe in plan.pipes:
        _draw_pipe_segment(ax, pipe, m_per_pt)

    for fitting in plan.fittings:
        _draw_fitting_symbol(ax, fitting, m_per_pt)

    for valve in plan.valves:
        _draw_valve_symbol(ax, valve, m_per_pt)

    for eq in plan.equipment:
        _draw_equipment_symbol(ax, eq, m_per_pt)

    for instr in plan.instruments:
        _draw_instrument_bubble(ax, instr, m_per_pt)

    for support in plan.supports:
        _draw_pipe_support(ax, support, m_per_pt)

    # Legend
    if plan.show_legend:
        _draw_symbol_legend(ax, plan, m_per_pt)

    # Stamp (title block)
    scale_str = f"1:{plan.scale}"
    _draw_stamp(fig, plan, scale_str, pw_mm, ph_mm, plan.language)

    # Output
    buf = io.BytesIO()
    if output_format.lower() == "svg":
        fig.patch.set_facecolor("white")
        canvas = FigureCanvasSVG(fig)
        canvas.print_svg(buf)
    else:
        fig.savefig(buf, format="png", dpi=plan.dpi, facecolor="white")
    buf.seek(0)
    return buf.getvalue()
