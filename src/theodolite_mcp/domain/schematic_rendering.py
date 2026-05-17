"""ISO 6412 / ISO 14617 / ISO 3511 Pipeline Schematic Rendering.

Expert version with robust collision detection, perfect symbol matching, 
and full Ukrainian localization.
"""
import io
import math
import logging
from typing import Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure
from matplotlib.patches import Circle, Rectangle, Polygon
from matplotlib.backends.backend_svg import FigureCanvasSVG
import matplotlib.patheffects as path_effects

from theodolite_mcp.domain.models.schematic import (
    PipeSegment, ValveSymbol, EquipmentSymbol, FittingSymbol,
    InstrumentSymbol, PipeSupport, PipelineSchematic,
    PipeMedium, ValveType, EquipmentType, FittingType, PipeSupportType,
    Point as ModelPoint,
)
from theodolite_mcp.domain.rendering import (
    D, D_WIDE, D_EXTRA_WIDE, D_SYMBOL, MM_TO_PT,
    TYPE_01, TYPE_02, TYPE_04, TYPE_05,
    PAPER_SIZES, MARGIN_LEFT, MARGIN_OTHER, STAMP_WIDTH, STAMP_HEIGHT,
    LabelTracker as BaseLabelTracker, I18N, _get_font, _draw_stamp, _draw_sheet_reference_grid,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Media style lookup (ISO 6412 conventions)
# ---------------------------------------------------------------------------
MEDIA_STYLES: Dict[str, Dict] = {
    PipeMedium.HEATING_SUPPLY: {"color": "#CC0000", "ls": TYPE_01, "label_ru": "Подача тепл.", "label_en": "Heating Supply", "label_uk": "Подача тепл."},
    PipeMedium.HEATING_RETURN: {"color": "#0000CC", "ls": TYPE_01, "label_ru": "Обратка тепл.", "label_en": "Heating Return", "label_uk": "Зворотня тепл."},
    PipeMedium.COLD_WATER:    {"color": "#00AA00", "ls": TYPE_01, "label_ru": "ХВС", "label_en": "Cold Water", "label_uk": "ХВП (Холодна)"},
    PipeMedium.HOT_WATER:     {"color": "#D32F2F", "ls": TYPE_02, "label_ru": "ГВС", "label_en": "Hot Water", "label_uk": "ГВП (Гаряча)"},
    PipeMedium.GAS:           {"color": "#CCAA00", "ls": TYPE_01, "label_ru": "Газ", "label_en": "Gas", "label_uk": "Газ"},
    PipeMedium.STEAM:         {"color": "#888888", "ls": TYPE_01, "label_ru": "Пар", "label_en": "Steam", "label_uk": "Пара"},
    PipeMedium.CONDENSATE:    {"color": "#00AAAA", "ls": TYPE_02, "label_ru": "Конденсат", "label_en": "Condensate", "label_uk": "Конденсат"},
    PipeMedium.DRAINAGE:      {"color": "#8B4513", "ls": TYPE_04, "label_ru": "Канализ.", "label_en": "Drainage", "label_uk": "Канал."},
    PipeMedium.CUSTOM:        {"color": "#333333", "ls": TYPE_01, "label_ru": "Прочее", "label_en": "Custom", "label_uk": "Інше"},
}

def _dn_lw(dn: int) -> float:
    if dn >= 100: return D_EXTRA_WIDE
    if dn >= 50: return D_WIDE
    return D

# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------
def _add_text_halo(text_obj):
    """Add a white outline to text to make it readable over lines."""
    text_obj.set_path_effects([path_effects.withStroke(linewidth=3, foreground="white", alpha=0.8)])

class LabelTracker:
    """Advanced rectangle-based collision tracker for label placement."""
    def __init__(self, debug: bool = False):
        self.boxes: List[Tuple[float, float, float, float]] = []
        self.debug = debug

    def text_bounds(self, x: float, y: float, text: str, fontsize: float, m_per_pt: float, ha="center", va="center") -> Tuple[float, float, float, float]:
        char_w = fontsize * 0.7 * MM_TO_PT * m_per_pt
        char_h = fontsize * 1.3 * MM_TO_PT * m_per_pt
        lines = str(text).split("\n")
        max_len = max(len(line) for line in lines) if lines else 1
        w, h = max_len * char_w, len(lines) * char_h
        x1 = x if ha == "left" else (x - w if ha == "right" else x - w/2)
        y1 = y if va == "bottom" else (y - h if va == "top" else y - h/2)
        return (x1 - 0.2, y1 - 0.2, x1 + w + 0.2, y1 + h + 0.2)

    def collides(self, box: Tuple[float, float, float, float]) -> bool:
        x1, y1, x2, y2 = box
        for bx1, by1, bx2, by2 in self.boxes:
            if not (x2 < bx1 or x1 > bx2 or y2 < by1 or y1 > by2): return True
        return False

    def draw_debug(self, ax, box: Tuple[float, float, float, float], color="red"):
        if self.debug:
            x1, y1, x2, y2 = box
            ax.add_patch(Rectangle((x1, y1), x2-x1, y2-y1, fill=False, ec=color, lw=0.5, alpha=0.5, ls="--", zorder=20))

def _rot(px: float, py: float, cx: float, cy: float, angle_deg: float):
    rad = math.radians(angle_deg)
    c, s = math.cos(rad), math.sin(rad)
    dx, dy = px - cx, py - cy
    return cx + dx * c - dy * s, cy + dx * s + dy * c

def _rot_points(pts, cx, cy, angle_deg):
    return [_rot(x + cx, y + cy, cx, cy, angle_deg) for x, y in pts]

# ---------------------------------------------------------------------------
# Elements
# ---------------------------------------------------------------------------
def _draw_pipe_segment(ax, pipe: PipeSegment, m_per_pt: float, tracker: Optional[LabelTracker] = None):
    style = MEDIA_STYLES.get(pipe.medium, MEDIA_STYLES[PipeMedium.CUSTOM])
    color, lw = pipe.custom_color or style["color"], _dn_lw(pipe.nominal_diameter)
    x1, y1, x2, y2 = pipe.start_pt.x, pipe.start_pt.y, pipe.end_pt.x, pipe.end_pt.y
    ax.plot([x1, x2], [y1, y2], color=color, linestyle=style["ls"], linewidth=lw, solid_capstyle="round", zorder=2)
    
    if pipe.flow_direction != "none" and (x1 != x2 or y1 != y2):
        dx, dy = x2 - x1, y2 - y1
        seg_len = math.hypot(dx, dy)
        arrow_size = min(seg_len * 0.15, 0.3) 
        if pipe.flow_direction == "backward": dx, dy = -dx, -dy
        mx, my, ux, uy = (x1 + x2) / 2, (y1 + y2) / 2, dx / seg_len, dy / seg_len
        tip = (mx + ux * arrow_size, my + uy * arrow_size)
        perp_x, perp_y = -uy * arrow_size * 0.4, ux * arrow_size * 0.4
        base1 = (mx - ux * arrow_size * 0.4 + perp_x, my - uy * arrow_size * 0.4 + perp_y)
        base2 = (mx - ux * arrow_size * 0.4 - perp_x, my - uy * arrow_size * 0.4 - perp_y)
        ax.add_patch(Polygon([tip, base1, base2], closed=True, fc=color, ec=color, zorder=3))

    if math.hypot(x2 - x1, y2 - y1) > 0.4:
        mx, my, seg_len = (x1 + x2) / 2, (y1 + y2) / 2, math.hypot(x2 - x1, y2 - y1)
        nx, ny = -(y2-y1)/seg_len, (x2-x1)/seg_len
        txt = f"DN{pipe.nominal_diameter}"
        offset = 0.5 
        best_pos = (mx + nx * offset, my + ny * offset)
        if tracker:
            bbox = tracker.text_bounds(best_pos[0], best_pos[1], txt, 8, m_per_pt)
            if tracker.collides(bbox):
                best_pos = (mx - nx * offset, my - ny * offset)
                bbox = tracker.text_bounds(best_pos[0], best_pos[1], txt, 8, m_per_pt)
            tracker.boxes.append(bbox); tracker.draw_debug(ax, bbox, color="blue")
        t = ax.text(best_pos[0], best_pos[1], txt, fontproperties=_get_font(8, m_per_pt=m_per_pt), ha="center", va="center", color=color, zorder=5)
        _add_text_halo(t)

def _draw_valve_symbol(ax, valve: ValveSymbol, m_per_pt: float, tracker: Optional[LabelTracker] = None):
    cx, cy, s, ang, lw, vt = valve.center_pt.x, valve.center_pt.y, max(0.25, (valve.nominal_diameter or 25) / 1000.0 * 1.2), valve.rotation, D_SYMBOL, valve.valve_type
    if valve.nominal_diameter and valve.nominal_diameter >= 4000: lw = D_SYMBOL * 2.5
    
    if vt == ValveType.GATE:
        for p in [([-s, -s*0.7], [0, 0], [-s, s*0.7]), ([s, -s*0.7], [0, 0], [s, s*0.7])]:
            ax.plot(*zip(*_rot_points(p, cx, cy, ang)), color="black", lw=lw, zorder=6)
    elif vt == ValveType.BALL:
        ax.add_patch(Circle((cx, cy), s*0.6, fill=False, ec="black", lw=lw, zorder=6))
        ax.plot(*zip(*_rot_points([(-s, 0), (s, 0)], cx, cy, ang)), color="black", lw=lw, zorder=6)
    elif vt == ValveType.GLOBE:
        r = s * 0.6
        ax.add_patch(Circle((cx, cy), r, fill=False, ec="black", lw=lw, zorder=6))
        ax.plot(*zip(*_rot_points([(-r, 0), (r, 0)], cx, cy, ang)), color="black", lw=lw, zorder=7)
        ax.plot(*zip(*_rot_points([(0, -r), (0, r)], cx, cy, ang)), color="black", lw=lw, zorder=7)
    elif vt == ValveType.CHECK:
        ax.add_patch(Polygon(_rot_points([(s, 0), (-s*0.5, s*0.7), (-s*0.5, -s*0.7)], cx, cy, ang), closed=True, fc="white", ec="black", lw=lw, zorder=6))
    elif vt == ValveType.BUTTERFLY:
        pts_l = _rot_points([(-s, -s * 0.5), (0, 0), (-s, s * 0.5)], cx, cy, ang)
        pts_r = _rot_points([(s, -s * 0.5), (0, 0), (s, s * 0.5)], cx, cy, ang)
        ax.add_patch(Polygon(pts_l, closed=True, fc="#DDDDDD", ec="black", lw=lw, zorder=6))
        ax.add_patch(Polygon(pts_r, closed=True, fc="#DDDDDD", ec="black", lw=lw, zorder=6))
    elif vt == ValveType.THREE_WAY_MIXING:
        ax.plot(*zip(*_rot_points([(-s, 0), (s, 0)], cx, cy, ang)), color="black", lw=lw, zorder=6)
        ax.plot(*zip(*_rot_points([(0, 0), (0, s)], cx, cy, ang)), color="black", lw=lw, zorder=6)
    elif vt == ValveType.PRESSURE_REDUCING:
        r = s * 0.6
        ax.add_patch(Circle((cx, cy), r, fill=False, ec="black", lw=lw, zorder=6))
        ax.plot(*zip(*_rot_points([(-s, 0), (s, 0)], cx, cy, ang)), color="black", lw=lw, zorder=6)
    elif vt == ValveType.SAFETY_RELIEF:
        for p in [([-s*0.6, -s*0.4], [0,0], [-s*0.6, s*0.4]), ([s*0.6, -s*0.4], [0,0], [s*0.6, s*0.4])]:
            ax.plot(*zip(*_rot_points(p, cx, cy, ang)), color="black", lw=lw, zorder=6)

    if valve.tag:
        tag_offset = max(0.6, s * 2.8)
        txt, best_pos = str(valve.tag), _rot(cx, cy + tag_offset, cx, cy, ang)
        if tracker:
            bbox = tracker.text_bounds(best_pos[0], best_pos[1], txt, 10, m_per_pt, va="bottom")
            if tracker.collides(bbox):
                best_pos = _rot(cx, cy - tag_offset, cx, cy, ang)
                bbox = tracker.text_bounds(best_pos[0], best_pos[1], txt, 10, m_per_pt, va="top")
            tracker.boxes.append(bbox); tracker.draw_debug(ax, bbox, color="green")
        t = ax.text(best_pos[0], best_pos[1], txt, fontproperties=_get_font(10, bold=True, m_per_pt=m_per_pt),
                ha="center", va="bottom" if best_pos[1] >= cy else "top", color="black", zorder=8,
                bbox=dict(boxstyle="round,pad=0.1", fc="white", lw=0, alpha=0.9))
        _add_text_halo(t)


def _draw_equipment_symbol(ax, eq: EquipmentSymbol, m_per_pt: float, tracker: Optional[LabelTracker] = None):
    cx, cy, w, h, ang, lw, et = eq.center_pt.x, eq.center_pt.y, eq.width, eq.height, eq.rotation, D_SYMBOL, eq.equipment_type
    if w >= 8: lw = D_SYMBOL * 2.5
    hw, hh = w / 2, h / 2
    if et in (EquipmentType.CENTRIFUGAL_PUMP, EquipmentType.CIRCULATION_PUMP):
        r = min(w, h) / 2
        ax.add_patch(Circle((cx, cy), r, fill=False, ec="black", lw=lw, zorder=6))
        ax.add_patch(Polygon(_rot_points([(r, 0), (-r*0.5, r*0.86), (-r*0.5, -r*0.86)], cx, cy, ang), closed=True, fc="black", ec="black", zorder=7))
    elif et in (EquipmentType.BOILER, EquipmentType.SHELL_TUBE_HX, EquipmentType.PLATE_HX, EquipmentType.STORAGE_TANK):
        rect_pts = _rot_points([(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)], cx, cy, ang)
        ax.plot(*zip(*(rect_pts + [rect_pts[0]])), color="black", lw=D_WIDE, zorder=6)
        if et == EquipmentType.BOILER:
            for i in range(3):
                yy, wave = -hh * 0.5 + i * hh * 0.5, []
                for t in range(21): wave.append(_rot(cx - hw * 0.6 + t * hw * 0.06, cy + yy + math.sin(t * 0.6) * hh * 0.15, cx, cy, ang))
                ax.plot(*zip(*wave), color="#CC4400", lw=D*1.5, zorder=7)
        elif et == EquipmentType.STORAGE_TANK:
            arc_pts = []
            for t in range(11):
                angle = math.pi + t * math.pi / 10
                arc_pts.append(_rot(cx + hw * 0.8 * math.cos(angle), cy - hh + hh * 0.15 * math.sin(angle) - hh * 0.1, cx, cy, ang))
            ax.plot(*zip(*arc_pts), color="black", lw=D, zorder=7)
    elif et == EquipmentType.RADIATOR:
        rect_pts = _rot_points([(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)], cx, cy, ang)
        ax.plot(*zip(*(rect_pts + [rect_pts[0]])), color="black", lw=D_WIDE, zorder=6)
        # Fins for radiator
        fins = 5
        for i in range(fins):
            off = -hw + (i+1) * (2*hw / (fins+1))
            ax.plot(*zip(*_rot_points([(off, -hh), (off, hh)], cx, cy, ang)), color="black", lw=D, zorder=7)
    elif et == EquipmentType.MANIFOLD:
        rect_pts = _rot_points([(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)], cx, cy, ang)
        ax.fill(*zip(*rect_pts), color="#EEEEEE", alpha=0.5, zorder=5)
        ax.plot(*zip(*(rect_pts + [rect_pts[0]])), color="black", lw=D_WIDE, zorder=6)
        # Ports for manifold
        ports = 4
        for i in range(ports):
            off = -hw + (i+1) * (2*hw / (ports+1))
            ax.add_patch(Circle(_rot(cx + off, cy, cx, cy, ang), 0.05, ec="black", fc="white", lw=D, zorder=7))
    elif et == EquipmentType.EXPANSION_VESSEL:
        r = min(w, h) / 2
        ax.add_patch(Circle((cx, cy), r, fill=False, ec="black", lw=lw, zorder=6))
        ax.plot(*zip(*_rot_points([(-r*0.8, r*0.2), (r*0.8, r*0.2)], cx, cy, ang)), color="#0066CC", lw=D*2.0, zorder=7)
    elif et in (EquipmentType.Y_STRAINER, EquipmentType.MESH_FILTER):
        if et == EquipmentType.Y_STRAINER: pts = _rot_points([(-w*0.4, 0), (0, -h*0.3), (w*0.4, 0), (0, h*0.3)], cx, cy, ang)
        else: pts = _rot_points([(-w*0.4, -h*0.4), (w*0.4, -h*0.4), (w*0.4, h*0.4), (-w*0.4, h*0.4)], cx, cy, ang)
        ax.add_patch(Polygon(pts, closed=True, fc="white", ec="black", lw=lw, zorder=6))
    elif et in (EquipmentType.PRESSURE_GAUGE, EquipmentType.THERMOMETER, EquipmentType.FLOW_METER, EquipmentType.HEAT_METER):
        r = min(w, h) / 2
        ax.add_patch(Circle((cx, cy), r, fill=False, ec="black", lw=lw, zorder=6))
        lbl = {"pressure_gauge": "P", "thermometer": "T", "flow_meter": "F", "heat_meter": "Q"}.get(et, "")
        ax.text(cx, cy, lbl, fontproperties=_get_font(12, bold=True, m_per_pt=m_per_pt), ha="center", va="center", color="black", zorder=8)
    
    tag_offset = max(w, h) / 2 + 0.5
    if eq.tag:
        txt, best_pos = eq.tag, _rot(cx, cy + tag_offset, cx, cy, ang)
        if tracker:
            bbox = tracker.text_bounds(best_pos[0], best_pos[1], txt, 10, m_per_pt, va="bottom")
            if tracker.collides(bbox):
                best_pos = _rot(cx, cy + tag_offset + 0.7, cx, cy, ang)
                bbox = tracker.text_bounds(best_pos[0], best_pos[1], txt, 10, m_per_pt, va="bottom")
            tracker.boxes.append(bbox); tracker.draw_debug(ax, bbox, color="orange")
        t = ax.text(best_pos[0], best_pos[1], txt, fontproperties=_get_font(10, bold=True, m_per_pt=m_per_pt), ha="center", va="bottom", color="black", zorder=8, bbox=dict(boxstyle="round,pad=0.05", fc="white", lw=0, alpha=0.8))
        _add_text_halo(t)
    if eq.label:
        txt, best_pos = eq.label, _rot(cx, cy - tag_offset, cx, cy, ang)
        if tracker:
            bbox = tracker.text_bounds(best_pos[0], best_pos[1], txt, 8, m_per_pt, va="top")
            if tracker.collides(bbox):
                best_pos = _rot(cx, cy - tag_offset - 0.8, cx, cy, ang)
                bbox = tracker.text_bounds(best_pos[0], best_pos[1], txt, 8, m_per_pt, va="top")
            tracker.boxes.append(bbox); tracker.draw_debug(ax, bbox, color="purple")
        t = ax.text(best_pos[0], best_pos[1], txt, fontproperties=_get_font(8, m_per_pt=m_per_pt), ha="center", va="top", color="#333333", zorder=8)
        _add_text_halo(t)

def _draw_instrument_bubble(ax, instr: InstrumentSymbol, m_per_pt: float):
    cx, cy, r, lw = instr.center_pt.x, instr.center_pt.y, 0.4, D_SYMBOL
    tag = f"{instr.measured_variable}{instr.suffix}-{instr.tag_number}"
    if instr.in_dcs: ax.add_patch(Rectangle((cx - r, cy - r), 2 * r, 2 * r, fill=False, ec="black", lw=lw, zorder=6))
    ax.add_patch(Circle((cx, cy), r, fill=False, ec="black", lw=lw, zorder=7))
    ax.plot([cx, cx], [cy - r * 1.5, cy - r], color="black", lw=D, zorder=5)
    t = ax.text(cx, cy, tag, fontproperties=_get_font(8, bold=True, m_per_pt=m_per_pt), ha="center", va="center", color="black", zorder=8)
    _add_text_halo(t)

def _draw_fitting_symbol(ax, fitting: FittingSymbol, m_per_pt: float):
    cx, cy, s, ang, lw, ft = fitting.center_pt.x, fitting.center_pt.y, max(0.2, (fitting.nominal_diameter or 25) / 1000.0 * 1.0), fitting.rotation, D_SYMBOL, fitting.fitting_type
    if ft == FittingType.ELBOW_90:
        p_s, p_e = _rot(cx + s, cy, cx, cy, ang), _rot(cx, cy + s, cx, cy, ang)
        ax.plot([p_s[0], cx, p_e[0]], [p_s[1], cy, p_e[1]], color="black", lw=lw, zorder=6)

def _draw_pipe_support(ax, support: PipeSupport, m_per_pt: float):
    cx, cy, s, lw, st = support.center_pt.x, support.center_pt.y, 0.15, D, support.support_type
    if st == PipeSupportType.ANCHOR: ax.add_patch(Polygon([(cx-s, cy-s), (cx+s, cy-s), (cx, cy+s)], closed=True, fc="black", ec="black", lw=lw, zorder=6))
    elif st == PipeSupportType.GUIDE: ax.add_patch(Polygon([(cx-s, cy-s), (cx+s, cy-s), (cx, cy+s)], closed=True, fc="white", ec="black", lw=lw, zorder=6))

def _draw_symbol_legend(fig: Figure, plan: PipelineSchematic, pw_mm: float, ph_mm: float):
    lang = plan.language
    media = sorted(list(set(p.medium for p in plan.pipes)))
    valves = sorted(list(set(v.valve_type for v in plan.valves)))
    equip = sorted(list(set(e.equipment_type for e in plan.equipment)))
    instr = len(plan.instruments) > 0
    items = []
    for m in media: items.append(("pipe", m, MEDIA_STYLES.get(m, MEDIA_STYLES[PipeMedium.CUSTOM]).get(f"label_{lang}", m), MEDIA_STYLES.get(m)))
    if media: 
        lbl = "DN - Номінальний діаметр (мм)" if lang == "uk" else ("DN - Номинальный диаметр (мм)" if lang == "ru" else "DN - Nominal Diameter (mm)")
        items.append(("note", "DN", lbl, None))
    # Tag prefixes explanation
    prefix_map = {
        "V": {"uk": "V - Кран / Вентиль", "ru": "V - Кран / Вентиль", "en": "V - Valve"},
        "CV": {"uk": "CV - Зворотний клапан", "ru": "CV - Обратный клапан", "en": "CV - Check Valve"},
        "F": {"uk": "F - Фільтр", "ru": "F - Фильтр", "en": "F - Filter"},
        "B": {"uk": "B - Бойлер / Котел", "ru": "B - Бойлер / Котел", "en": "B - Boiler"},
        "GA": {"uk": "GA - Гідроакумулятор", "ru": "GA - Гидроаккумулятор", "en": "GA - Expansion Vessel"},
        "P": {"uk": "P - Насос", "ru": "P - Насос", "en": "P - Pump"},
        "T": {"uk": "T - Резервуар", "ru": "T - Резервуар", "en": "T - Tank"},
        "PI": {"uk": "PI - Манометр (Індикатор)", "ru": "PI - Манометр", "en": "PI - Pressure Indicator"},
        "PC": {"uk": "PC - Реле тиску (Контролер)", "ru": "PC - Реле давления", "en": "PC - Pressure Controller"},
    }
    prefixes_used = set()
    for v in plan.valves:
        if v.tag and "-" in v.tag: prefixes_used.add(v.tag.split("-")[0].upper())
    for e in plan.equipment:
        if e.tag and "-" in e.tag: prefixes_used.add(e.tag.split("-")[0].upper())
    for i in plan.instruments:
        pfx = f"{i.measured_variable}{i.suffix or ''}".upper().strip()
        if pfx: prefixes_used.add(pfx)
    
    for pfx in sorted(list(prefixes_used)):
        if pfx in prefix_map and not any(k == pfx for t, k, l, s in items):
            lbl = prefix_map[pfx].get(lang, prefix_map[pfx]["en"])
            items.append(("note", pfx, lbl, None))

    var_map = {
        "P": {"uk": "P - Тиск", "ru": "P - Давление", "en": "P - Pressure"},
        "T": {"uk": "T - Температура", "ru": "T - Температура", "en": "T - Temperature"},
        "F": {"uk": "F - Витрата", "ru": "F - Расход", "en": "F - Flow"},
        "Q": {"uk": "Q - Енергія/Тепло", "ru": "Q - Энергия/Тепло", "en": "Q - Energy/Heat"}
    }
    vars_used = set()

    for i in plan.instruments: vars_used.add(i.measured_variable)
    for e in plan.equipment:
        if e.equipment_type == EquipmentType.PRESSURE_GAUGE: vars_used.add("P")
        if e.equipment_type == EquipmentType.THERMOMETER: vars_used.add("T")
        if e.equipment_type == EquipmentType.FLOW_METER: vars_used.add("F")
        if e.equipment_type == EquipmentType.HEAT_METER: vars_used.add("Q")
    for v in sorted(list(vars_used)):
        if v in var_map: 
            lbl = var_map[v].get(lang, var_map[v]["en"])
            items.append(("note", v, lbl, None))
    uk_v = {"check": "Зворотний клапан", "ball": "Кран кульовий", "gate": "Засувка", "butterfly": "Затвор", "globe": "Вентиль", "3way_mixing": "Кран 3-хід.", "prv": "Редуктор тиску", "safety": "Запобіжний клапан"}
    ru_v = {"check": "Обратный клапан", "ball": "Кран шаровый", "gate": "Задвижка", "butterfly": "Затвор", "globe": "Вентиль", "3way_mixing": "Кран 3-ход.", "prv": "Редуктор давления", "safety": "Предохранительный клапан"}
    
    for v in valves:
        label = v.replace("_", " ").title()
        if lang == "uk": label = uk_v.get(v, label)
        elif lang == "ru": label = ru_v.get(v, label)
        items.append(("valve", v, label, None))

    uk_e = {"boiler": "Бойлер/Котел", "centrifugal_pump": "Насос", "circulation_pump": "Циркуляційний насос", "expansion_vessel": "Гідроакумулятор", "mesh_filter": "Фільтр", "storage_tank": "Резервуар", "pressure_gauge": "Манометр", "thermometer": "Термометр", "flow_meter": "Витратомір", "heat_meter": "Теплолічильник", "radiator": "Радіатор", "manifold": "Колектор"}
    ru_e = {"boiler": "Бойлер/Котел", "centrifugal_pump": "Насос", "circulation_pump": "Циркуляционный насос", "expansion_vessel": "Гидроаккумулятор", "mesh_filter": "Фильтр", "storage_tank": "Резервуар", "pressure_gauge": "Манометр", "thermometer": "Термометр", "flow_meter": "Расходомер", "heat_meter": "Теплосчетчик", "radiator": "Радиатор", "manifold": "Коллектор"}
    
    for e in equip:
        label = e.replace("_", " ").title()
        if lang == "uk": label = uk_e.get(e, label)
        elif lang == "ru": label = ru_e.get(e, label)
        items.append(("equipment", e, label, None))
        
    if instr: 
        lbl = "КВПіА" if lang == "uk" else ("КИПиА" if lang == "ru" else "P&ID")
        items.append(("instrument", "iso3511", lbl, None))
    if not items: return
    row_h, legend_w = 9.0, 95.0
    legend_h = (len(items) + 1.5) * row_h
    lx, ly = pw_mm - MARGIN_OTHER - legend_w - 5, ph_mm - MARGIN_OTHER - legend_h - 5
    ax_leg = fig.add_axes([lx/pw_mm, ly/ph_mm, legend_w/pw_mm, legend_h/ph_mm])
    ax_leg.set_xlim(0, legend_w); ax_leg.set_ylim(0, legend_h); ax_leg.axis("off")
    ax_leg.add_patch(Rectangle((0, 0), legend_w, legend_h, fc="white", ec="black", lw=D_WIDE, alpha=0.9, zorder=9))
    
    title_map = {"uk": "УМОВНІ ПОЗНАЧЕННЯ", "ru": "УСЛОВНЫЕ ОБОЗНАЧЕНИЯ", "en": "SYMBOL LEGEND"}
    title = title_map.get(lang, title_map["en"])
    ax_leg.text(legend_w/2, legend_h - row_h*0.7, title, fontproperties=_get_font(9, bold=True, lang=lang), ha="center", va="center", zorder=10)
    leg_m_per_pt = 1.0 / MM_TO_PT 
    for i, (itype, key, label, style) in enumerate(items):
        ry, sx, tx = legend_h - row_h*(i + 1.8), 10.0, 26.0
        if itype == "pipe" and style: ax_leg.plot([sx-6, sx+6], [ry, ry], color=style["color"], linewidth=D_EXTRA_WIDE*1.5, zorder=10)
        elif itype == "note": ax_leg.text(sx, ry, key, fontproperties=_get_font(8, bold=True, lang=lang), ha="center", va="center", zorder=10)
        elif itype == "valve": _draw_valve_symbol(ax_leg, ValveSymbol(center_pt=ModelPoint(x=sx, y=ry), valve_type=key, nominal_diameter=4000), leg_m_per_pt)
        elif itype == "equipment": _draw_equipment_symbol(ax_leg, EquipmentSymbol(center_pt=ModelPoint(x=sx, y=ry), equipment_type=key, width=9, height=9), leg_m_per_pt)
        elif itype == "instrument": _draw_instrument_bubble(ax_leg, InstrumentSymbol(center_pt=ModelPoint(x=sx, y=ry), measured_variable="X", suffix="Y"), leg_m_per_pt)
        ax_leg.text(tx, ry, label, fontproperties=_get_font(9, lang=lang), ha="left", va="center", zorder=10)

def render_pipeline_schematic(plan: PipelineSchematic, output_format: str = "png") -> bytes:
    pw_mm, ph_mm = PAPER_SIZES.get(plan.paper_format, PAPER_SIZES["A3"])
    if plan.orientation == "landscape" and pw_mm < ph_mm: pw_mm, ph_mm = ph_mm, pw_mm
    fig = Figure(figsize=(pw_mm/25.4, ph_mm/25.4)); fig.patch.set_facecolor("white")
    ax_f = fig.add_axes([0, 0, 1, 1]); ax_f.set_xlim(0, pw_mm); ax_f.set_ylim(0, ph_mm); ax_f.axis("off")
    ax_f.plot([MARGIN_LEFT, pw_mm-MARGIN_OTHER, pw_mm-MARGIN_OTHER, MARGIN_LEFT, MARGIN_LEFT], [MARGIN_OTHER, MARGIN_OTHER, ph_mm-MARGIN_OTHER, ph_mm-MARGIN_OTHER, MARGIN_OTHER], color="black", lw=D_WIDE)
    _draw_sheet_reference_grid(ax_f, pw_mm, ph_mm)
    pts = []
    for p in plan.pipes: pts.extend([(p.start_pt.x, p.start_pt.y), (p.end_pt.x, p.end_pt.y)])
    for v in plan.valves: pts.append((v.center_pt.x, v.center_pt.y))
    for e in plan.equipment: pts.append((e.center_pt.x, e.center_pt.y))
    xs, ys = [p[0] for p in (pts or [(0,0)])], [p[1] for p in (pts or [(1,1)])]
    min_x, max_x, min_y, max_y = min(xs), max(xs), min(ys), max(ys)
    data_w, data_h = max(max_x - min_x, 0.1), max(max_y - min_y, 0.1)
    
    # Safe drawing area avoids the legend (125mm on right)
    draw_w_mm, draw_h_mm = pw_mm - MARGIN_LEFT - 125.0, ph_mm - MARGIN_OTHER * 2
    
    # Use 30% padding to ensure labels don't spill out
    m_per_mm = max(data_w / draw_w_mm, data_h / draw_h_mm) * 1.3
    m_per_pt = m_per_mm / MM_TO_PT
    
    ax = fig.add_axes([MARGIN_LEFT/pw_mm, MARGIN_OTHER/ph_mm, draw_w_mm/pw_mm, draw_h_mm/ph_mm])
    cx_data, cy_data = (min_x + max_x) / 2, (min_y + max_y) / 2
    half_w_paper, half_h_paper = (draw_w_mm * m_per_mm) / 2, (draw_h_mm * m_per_mm) / 2
    ax.set_xlim(cx_data - half_w_paper, cx_data + half_w_paper)
    ax.set_ylim(cy_data - half_h_paper, cy_data + half_h_paper)
    ax.set_aspect("equal"); ax.axis("off")
    tracker = LabelTracker(debug=False)
    for p in plan.pipes: _draw_pipe_segment(ax, p, m_per_pt, tracker)
    for f in plan.fittings: _draw_fitting_symbol(ax, f, m_per_pt)
    for v in plan.valves: _draw_valve_symbol(ax, v, m_per_pt, tracker)
    for e in plan.equipment: _draw_equipment_symbol(ax, e, m_per_pt, tracker)
    for i in plan.instruments: _draw_instrument_bubble(ax, i, m_per_pt)
    for s in plan.supports: _draw_pipe_support(ax, s, m_per_pt)
    if plan.show_legend: _draw_symbol_legend(fig, plan, pw_mm, ph_mm)
    _draw_stamp(fig, plan, "NTS", pw_mm, ph_mm, plan.language)
    buf = io.BytesIO()
    if output_format.lower() == "svg": FigureCanvasSVG(fig).print_svg(buf)
    else: fig.savefig(buf, format="png", dpi=plan.dpi, facecolor="white")
    buf.seek(0)
    return buf.getvalue()
