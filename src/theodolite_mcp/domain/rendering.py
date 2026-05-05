import io
import math
import os
from typing import List, Optional, Tuple, Dict
import matplotlib
matplotlib.use('Agg')
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
import matplotlib.patches as patches
from matplotlib.font_manager import FontProperties
import textwrap

from .models import PlotPlan, Point, Zone
from .logic import calculate_azimuth_from_points, calculate_area

# --- ISO 128-20:1996 & ISO 128-23:1999 Standards Constants ---
# Line Group 0.7 (Table 2, ISO 128-23)
# All units in points (1 pt = 1/72 inch). 1 mm = 72/25.4 pt ≈ 2.835 pt.
MM_TO_PT = 72 / 25.4

# ISO 5457:1999 Paper Formats (in mm)
PAPER_SIZES = {
    "A0": (1189, 841),
    "A1": (841, 594),
    "A2": (594, 420),
    "A3": (420, 297),
    "A4": (297, 210),
}

# ISO 5457 Margins (mm)
MARGIN_LEFT = 20.0
MARGIN_OTHER = 10.0

# ISO 7200:2004 Title Block (Stamp) Constants (mm)
STAMP_WIDTH = 185.0
STAMP_HEIGHT = 55.0

# Font handling (ISO 3098)
FONT_PATH = os.path.join(os.path.dirname(__file__), "osifont.ttf")
def _get_font(size=7, bold=False, italic=False):
    if os.path.exists(FONT_PATH):
        weight = 'bold' if bold else 'normal'
        style = 'italic' if italic else 'normal'
        return FontProperties(fname=FONT_PATH, size=size, weight=weight, style=style)
    # Fallback to standard fonts if ttf is missing
    return {'fontsize': size, 'fontweight': 'bold' if bold else 'normal', 'style': 'italic' if italic else 'normal'}

D = 0.35 * MM_TO_PT          # Narrow (d)
D_WIDE = 0.7 * MM_TO_PT      # Wide (2d)
D_EXTRA_WIDE = 1.4 * MM_TO_PT # Extra-wide (4d)
D_SYMBOL = 0.5 * MM_TO_PT    # Graphical Symbols

# ISO 128-20:1996 Dash/Gap Proportions
# Long dash = 24d, Dash = 12d, Gap = 3d, Dot = 0.5d
LD = 24 * D
DS = 12 * D
GP = 3 * D
DT = 0.5 * D

# Line Types (ISO 128-20 numbers)
TYPE_01 = "-"                                      # Continuous
TYPE_02 = (0, (DS, GP))                            # Dashed
TYPE_04 = (0, (LD, GP, DT, GP))                   # Long dashed dotted
TYPE_05 = (0, (LD, GP, DT, GP, DT, GP))           # Long dashed double-dotted
# ISO 128-25: 01+03 (Railway line) for tight bulkheads - approximated as a wide dashed-dotted or similar
TYPE_RAILWAY = (0, (DS, DT, DS, DT)) 

# Localization Dictionary
I18N: Dict[str, Dict[str, str]] = {
    "ru": {
        "project": "Проект:",
        "project_no": "№ Проекта:",
        "org": "Орг.:",
        "date": "Дата:",
        "stage": "Стадия:",
        "scale": "Масштаб:",
        "draft": "Чертеж (П)",
        "explication": "ЭКСПЛИКАЦИЯ ЗОН",
        "total_area": "Общая площадь:",
        "sotki": "сот.",
        "num": "№",
        "name": "Наименование",
        "area_sqm": "S, м²",
        "north": "С",
        "others": "... и другие",
        "unit_m": "м",
        "bow": "НОС",
        "stern": "КОРМА"
    },
    "uk": {
        "project": "Проєкт:",
        "project_no": "№ Проєкту:",
        "org": "Орг.:",
        "date": "Дата:",
        "stage": "Стадія:",
        "scale": "Масштаб:",
        "draft": "Креслення (П)",
        "explication": "ЕКСПЛІКАЦІЯ ЗОН",
        "total_area": "Загальна площа:",
        "sotki": "сот.",
        "num": "№",
        "name": "Найменування",
        "area_sqm": "S, м²",
        "north": "Пн",
        "others": "... та інші",
        "unit_m": "м",
        "bow": "НІС",
        "stern": "КОРМА"
    },
    "en": {
        "project": "Project:",
        "project_no": "Proj No:",
        "org": "Org:",
        "date": "Date:",
        "stage": "Stage:",
        "scale": "Scale:",
        "draft": "Draft (P)",
        "explication": "ZONE EXPLICATION",
        "total_area": "Total Area:",
        "sotki": "units",
        "num": "No.",
        "name": "Description",
        "area_sqm": "S, m²",
        "north": "N",
        "others": "... and others",
        "unit_m": "m",
        "bow": "BOW",
        "stern": "STERN"
    }
}

SHIP_SYMBOLS = {
    "cl": "CL", # Center Line
    "bl": "BL", # Base Line
    "wl": "WL", # Water Line
    "fr": "FR"  # Frame
}

ZONE_COLORS = [
    '#F5F5DC', '#E8F5E9', '#FFF3E0', '#E3F2FD',
    '#FCE4EC', '#F3E5F5', '#EFEBE9', '#FAFAFA',
]

def _auto_color(index: int) -> str:
    return ZONE_COLORS[index % len(ZONE_COLORS)]

def _polygon_coords(points: List[Point]) -> Tuple[List[float], List[float]]:
    xs = [p.x for p in points]
    ys = [p.y for p in points]
    xs.append(points[0].x)
    ys.append(points[0].y)
    return xs, ys

def _centroid(points: List[Point]) -> Tuple[float, float]:
    n = len(points)
    if n == 0: return 0, 0
    return sum(p.x for p in points) / n, sum(p.y for p in points) / n

def _edge_midpoint(p1: Point, p2: Point) -> Tuple[float, float]:
    return (p1.x + p2.x) / 2, (p1.y + p2.y) / 2

def _perpendicular_offset(p1: Point, p2: Point, distance: float = 1.0) -> Tuple[float, float]:
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    length = math.hypot(dx, dy)
    if length == 0: return 0, 0
    nx, ny = -dy / length * distance, dx / length * distance
    return nx, ny

def _get_hatch(name: str) -> Optional[str]:
    name = name.lower()
    if any(k in name for k in ['дом', 'house', 'building', 'здание']): return '///'
    if any(k in name for k in ['огород', 'garden', 'planting', 'теплица']): return '...'
    if any(k in name for k in ['сад', 'orchard', 'trees', 'цветник']): return 'oo'
    if any(k in name for k in ['парковка', 'parking', 'paving', 'дорожка']): return 'xxx'
    return None

def _draw_boundary(ax, points: List[Point], color: str = 'black', standard: str = "construction"):
    # ISO 128-23 vs ISO 128-25
    if standard == "shipbuilding":
        # ISO 128-25, 01.2: Continuous wide line for outer plating/hull
        lw = D_WIDE
        ls = TYPE_01
    else:
        # ISO 128-23, 04.3: Long dashed dotted extra-wide line (Boundary lines)
        lw = D_EXTRA_WIDE
        ls = TYPE_04
    
    xs, ys = _polygon_coords(points)
    ax.plot(xs, ys, color=color, linewidth=lw, linestyle=ls, zorder=3)

def _draw_zones(ax, zones: List[Zone], show_areas: bool = False, standard: str = "construction", m_per_pt: float = 0.1):
    for i, zone in enumerate(zones):
        color = zone.fill_color or _auto_color(i)
        hatch = _get_hatch(zone.name)
        xs, ys = _polygon_coords(zone.points)
        area = calculate_area(zone.points) or 0
        name_lower = zone.name.lower()
        
        # 1. Color fill (ISO 128-50 toning)
        ax.fill(xs, ys, color=color, alpha=0.12, zorder=1)
        
        # 2. Hatching (ISO 128-50)
        if hatch:
            h_density = hatch if area < 300 else hatch[0]
            ax.fill(xs, ys, fill=False, hatch=h_density, edgecolor='black', linewidth=0, alpha=0.15, zorder=2)
        
        # 3. Line Style (ISO 128-23 vs ISO 128-25)
        is_building = any(k in name_lower for k in ['дом', 'здание', 'building', 'house'])
        is_bulkhead = any(k in name_lower for k in ['переборка', 'bulkhead', 'deck', 'палуба'])
        is_tight = any(k in name_lower for k in ['tight', 'непрониц'])

        if standard == "shipbuilding":
            if is_tight:
                # ISO 128-25: 01+03 Railway line for tight bulkheads
                lw = D_WIDE
                ls = TYPE_RAILWAY
            elif is_bulkhead:
                # ISO 128-25, 01.2: Continuous wide for structural members
                lw = D_WIDE
                ls = TYPE_01
            else:
                # ISO 128-25, 01.1: Continuous narrow for others
                lw = D
                ls = TYPE_01
        else:
            # Construction standard
            if is_building:
                lw = D_WIDE
                ls = TYPE_01
            else:
                lw = D_EXTRA_WIDE
                ls = TYPE_04
            
        ax.plot(xs, ys, color='black', linewidth=lw, linestyle=ls, zorder=3)
        
        # 3. Inscriptions & Labels (ISO 128-50: Interruption of hatching)
        zx, zy = _centroid(zone.points)
        
        # Determine if we should use a leader for the zone number
        # If it's a line (area < 0.1) or shipbuilding (more crowded), use leader
        if area < 0.5 or standard == "shipbuilding":
            _draw_leader(ax, zx, zy, str(i + 1), offset_x=4, offset_y=4, 
                         terminator="dot", m_per_pt=m_per_pt, fontsize=8)
        else:
            # Opaque white bbox (alpha=1.0) creates the 'window' in the hatching
            ax.text(zx, zy, str(i + 1), fontproperties=_get_font(8.5, bold=True), ha='center', va='center', zorder=10,
                    bbox=dict(boxstyle='circle,pad=0.2', facecolor='white', edgecolor='black', 
                              linewidth=D_SYMBOL/MM_TO_PT, alpha=1.0))
        
        if show_areas and area >= 0.5:
            # Inscription below the zone number
            ax.text(zx, zy - 1.2, f"{area:.1f} m²", fontproperties=_get_font(7), ha='center', va='top', zorder=10, 
                    bbox=dict(boxstyle='round,pad=0.15', facecolor='white', edgecolor='none', alpha=1.0))

def _draw_leader(ax, target_x: float, target_y: float, text: str, 
                 offset_x: float = 5.0, offset_y: float = 5.0, 
                 terminator: str = "dot", m_per_pt: float = 0.1, fontsize: float = 7):
    """
    ISO 128-22: Leader and reference lines.
    terminator: 'dot' (area), 'arrow' (edge/line), or 'none'.
    """
    d_m = D * m_per_pt
    # Shelf length adapted to text (approx 1.8mm per char + margins)
    shelf_len = (len(text) * 1.8 + 2.0) * MM_TO_PT * m_per_pt
    
    # Leader end (start of shelf)
    lx, ly = target_x + offset_x, target_y + offset_y
    
    # 1. Leader line (Narrow 01.1)
    ax.plot([target_x, lx], [target_y, ly], color='black', linewidth=D, linestyle=TYPE_01, zorder=6)
    
    # 2. Terminator
    if terminator == "dot":
        # ISO 128-22: dot dia = 5 * line width
        dot_radius = 2.5 * D * m_per_pt
        circle = patches.Circle((target_x, target_y), dot_radius, color='black', zorder=7)
        ax.add_patch(circle)
    elif terminator == "arrow":
        # ISO 128-22: 15 deg arrowhead
        angle = math.atan2(ly - target_y, lx - target_x)
        # Small vector for annotation head orientation
        ax.annotate("", xy=(target_x, target_y), 
                    xytext=(target_x + math.cos(angle)*0.01, target_y + math.sin(angle)*0.01),
                    arrowprops=dict(arrowstyle='-|>', color='black', mutation_scale=10, 
                                    linewidth=D/MM_TO_PT, shrinkA=0, shrinkB=0), zorder=7)

    # 3. Reference line (Shelf) - strictly horizontal
    shelf_dir = 1 if offset_x >= 0 else -1
    ax.plot([lx, lx + shelf_dir * shelf_len], [ly, ly], color='black', linewidth=D, linestyle=TYPE_01, zorder=6)
    
    # 4. Text - preferably above shelf, gap = 2 * line width
    ax.text(lx + shelf_dir * shelf_len/2, ly + 2*d_m, text, 
            fontproperties=_get_font(fontsize), ha='center', va='bottom', zorder=10)

def _draw_vertex_labels(ax, points: List[Point], fontsize: float = 8, standard: str = "construction", 
                        m_per_pt: float = 0.1, show_coords: bool = False):
    cx, cy = _centroid(points)
    used_positions = []
    used_points = []
    
    for i, p in enumerate(points):
        # Skip if we already labeled this coordinate (e.g. closed loop closing point)
        if any(math.hypot(p.x - ox, p.y - oy) < 0.001 for ox, oy in used_points):
            continue
        used_points.append((p.x, p.y))

        name = p.name
        if show_coords:
            name += f"\n({p.x:.2f}, {p.y:.2f})"
            
        if standard == "shipbuilding" and name.isdigit():
            name = f"FR{name}"
            
        dx, dy = p.x - cx, p.y - cy
        dist = math.hypot(dx, dy)
        
        # Default offset
        off_val = 3.5
        vx, vy = (dx / dist * off_val, dy / dist * off_val) if dist > 0 else (off_val, off_val)
        
        # Check if this position is too close to any previously used position
        pos_x, pos_y = p.x + vx, p.y + vy
        collision = False
        for ux, uy in used_positions:
            if math.hypot(pos_x - ux, pos_y - uy) < 4.0 * MM_TO_PT * m_per_pt:
                collision = True
                break
        
        if collision:
            # Shift further and use a leader
            _draw_leader(ax, p.x, p.y, name, offset_x=vx*3, offset_y=vy*3, 
                         terminator="none", m_per_pt=m_per_pt, fontsize=fontsize-1)
        else:
            ax.text(pos_x, pos_y, name, fontproperties=_get_font(fontsize), ha='center', va='center', zorder=5,
                    bbox=dict(facecolor='white', edgecolor='none', alpha=0.8, pad=0.05))
            used_positions.append((pos_x, pos_y))

def _draw_distances(ax, points: List[Point], standard: str = "construction", fontsize: float = 7, show_azimuths: bool = False, m_per_pt: float = 0.1):
    # Calculate centroid to determine 'inside' direction
    cx, cy = _centroid(points)
    
    overshoot = 8 * D * m_per_pt
    gap = 2 * D * m_per_pt
    text_offset = 1.2 * MM_TO_PT * m_per_pt
    dim_offset_m = 8.0 * MM_TO_PT * m_per_pt

    for i in range(len(points)):
        p1, p2 = points[i], points[(i + 1) % len(points)]
        dist = math.hypot(p2.x - p1.x, p2.y - p1.y)
        if dist < 0.1: continue
        
        mx, my = _edge_midpoint(p1, p2)
        ox_unit, oy_unit = _perpendicular_offset(p1, p2, distance=1.0)
        
        # ISO 129-1: Dimensions should be outside. 
        # Check if (mx + ox_unit, my + oy_unit) is closer to centroid than (mx, my)
        dist_to_centroid_before = math.hypot(mx - cx, my - cy)
        dist_to_centroid_after = math.hypot(mx + ox_unit - cx, my + oy_unit - cy)
        
        if dist_to_centroid_after < dist_to_centroid_before:
            # We are pointing inside, flip it
            ox_unit, oy_unit = -ox_unit, -oy_unit
            
        ox_line, oy_line = ox_unit * dim_offset_m, oy_unit * dim_offset_m
        
        # 1. Dimension line
        ax.plot([p1.x + ox_line, p2.x + ox_line], [p1.y + oy_line, p2.y + oy_line], 
                color='black', linewidth=D, linestyle=TYPE_01, zorder=4)
        
        # 2. Extension lines
        p1_start_x, p1_start_y = p1.x + ox_unit * gap, p1.y + oy_unit * gap
        p1_end_x, p1_end_y = p1.x + ox_line + ox_unit * overshoot, p1.y + oy_line + oy_unit * overshoot
        ax.plot([p1_start_x, p1_end_x], [p1_start_y, p1_end_y], 
                color='black', linewidth=D, linestyle=TYPE_01, zorder=4)
        
        p2_start_x, p2_start_y = p2.x + ox_unit * gap, p2.y + oy_unit * gap
        p2_end_x, p2_end_y = p2.x + ox_line + ox_unit * overshoot, p2.y + oy_line + oy_unit * overshoot
        ax.plot([p2_start_x, p2_end_x], [p2_start_y, p2_end_y], 
                color='black', linewidth=D, linestyle=TYPE_01, zorder=4)
        
        if standard == "shipbuilding":
            angle = math.atan2(p2.y - p1.y, p2.x - p1.x)
            # Arrow scale
            ascl = 5 * MM_TO_PT * m_per_pt
            ax.annotate("", xy=(p1.x + ox_line, p1.y + oy_line), 
                        xytext=(p1.x + ox_line + math.cos(angle)*ascl, p1.y + oy_line + math.sin(angle)*ascl),
                        arrowprops=dict(arrowstyle='-|>', color='black', mutation_scale=10, 
                                        linewidth=D/MM_TO_PT, shrinkA=0, shrinkB=0), zorder=5)
            ax.annotate("", xy=(p2.x + ox_line, p2.y + oy_line), 
                        xytext=(p2.x + ox_line - math.cos(angle)*ascl, p2.y + oy_line - math.sin(angle)*ascl),
                        arrowprops=dict(arrowstyle='-|>', color='black', mutation_scale=10, 
                                        linewidth=D/MM_TO_PT, shrinkA=0, shrinkB=0), zorder=5)
        else:
            tick_len = 2.0 * MM_TO_PT * m_per_pt
            for p_base in [(p1.x + ox_line, p1.y + oy_line), (p2.x + ox_line, p2.y + oy_line)]:
                t_angle = math.atan2(p2.y - p1.y, p2.x - p1.x) + math.pi/4
                tx, ty = math.cos(t_angle) * tick_len, math.sin(t_angle) * tick_len
                ax.plot([p_base[0] - tx, p_base[0] + tx], [p_base[1] - ty, p_base[1] + ty], 
                        color='black', linewidth=D_WIDE, linestyle=TYPE_01, zorder=5)
            
        angle_deg = math.degrees(math.atan2(p2.y - p1.y, p2.x - p1.x))
        if angle_deg > 90: angle_deg -= 180
        if angle_deg < -90: angle_deg += 180
        
        tx_off, ty_off = ox_unit * text_offset, oy_unit * text_offset
        
        # Distance (ISO 129-1: placement)
        # Check if distance text fits between dimension lines
        # Approx 2mm per digit + padding
        text_width_mm = (len(f'{dist:.2f}') * 2.0 + 2.0)
        text_fits = (dist / m_per_pt / MM_TO_PT) > text_width_mm
        
        if text_fits:
            ax.text(mx + ox_line + tx_off, my + oy_line + ty_off, f'{dist:.2f}', 
                    fontproperties=_get_font(fontsize, italic=True), ha='center', va='bottom', rotation=angle_deg, zorder=10,
                    bbox=dict(facecolor='white', edgecolor='none', alpha=1.0, pad=0.1))
        else:
            # ISO 129-1: Small gap - move text outside or use leader
            # Here we move it slightly further and use a leader if very small
            _draw_leader(ax, mx + ox_line, my + oy_line, f'{dist:.2f}', 
                         offset_x=ox_unit * 10, offset_y=oy_unit * 10, 
                         terminator="none", m_per_pt=m_per_pt, fontsize=fontsize-0.5)
        
        # Azimuth (below line)
        if show_azimuths:
            az = calculate_azimuth_from_points(p1, p2)
            ax.text(mx + ox_line - tx_off, my + oy_line - ty_off, f'{az:.1f}°', 
                    fontproperties=_get_font(fontsize-1.5), ha='center', va='top', rotation=angle_deg, zorder=10)

def _draw_scale_bar(ax, x_span: float, width_inches: float, lang: str = "ru"):
    texts = I18N.get(lang, I18N["ru"])
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    
    # Position: Bottom right of the main plot
    sb_len_m = 10.0
    if x_span > 200: sb_len_m = 50.0
    if x_span > 1000: sb_len_m = 200.0
    if x_span < 20: sb_len_m = 5.0
    
    x_pos = xlim[1] - (xlim[1] - xlim[0]) * 0.25
    y_pos = ylim[0] + (ylim[1] - ylim[0]) * 0.08
    
    ax.plot([x_pos, x_pos + sb_len_m], [y_pos, y_pos], color='black', linewidth=D_WIDE, zorder=10)
    ax.plot([x_pos, x_pos], [y_pos, y_pos + (ylim[1]-ylim[0])*0.015], color='black', linewidth=D_WIDE, zorder=10)
    ax.plot([x_pos + sb_len_m, x_pos + sb_len_m], [y_pos, y_pos + (ylim[1]-ylim[0])*0.015], color='black', linewidth=D_WIDE, zorder=10)
    
    ax.text(x_pos + sb_len_m/2, y_pos - (ylim[1]-ylim[0])*0.02, f"{int(sb_len_m)}{texts['unit_m']}", 
            fontproperties=_get_font(7, bold=True), ha='center', va='top')

def _calculate_auto_scale(x_span: float, available_width_mm: float) -> int:
    """ISO 5455:1981 - Strict standard scales."""
    if available_width_mm <= 0: return 100
    raw_scale = (x_span * 1000) / available_width_mm
    # Standard engineering scales (ISO 5455)
    std_scales = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000]
    # Add common construction scales 
    std_scales.extend([2.5, 25, 250, 2500, 25000])
    std_scales.sort()
    
    for s in std_scales:
        if s >= raw_scale: return int(s)
    return int(raw_scale)

def _draw_stamp(fig, plan: PlotPlan, scale_str: str, pw_mm: float, ph_mm: float, lang: str = "ru"):
    texts = I18N.get(lang, I18N["ru"])
    # ISO 7200 Title Block - Absolute positioning in mm
    # Position: Bottom Right of the inner frame
    # Frame is at (MARGIN_LEFT, MARGIN_OTHER) to (pw_mm - MARGIN_OTHER, ph_mm - MARGIN_OTHER)
    
    left_mm = pw_mm - MARGIN_OTHER - STAMP_WIDTH
    bottom_mm = MARGIN_OTHER
    
    # Normalize for add_axes
    ax_stamp = fig.add_axes([left_mm / pw_mm, bottom_mm / ph_mm, STAMP_WIDTH / pw_mm, STAMP_HEIGHT / ph_mm])
    ax_stamp.set_xticks([]); ax_stamp.set_yticks([]); ax_stamp.set_facecolor('white')
    for spine in ax_stamp.spines.values(): spine.set_linewidth(D_WIDE/MM_TO_PT)
    
    # Internal grid (ISO 7200 inspired layout)
    ax_stamp.axhline(0.2, color='black', lw=D/MM_TO_PT)
    ax_stamp.axhline(0.4, color='black', lw=D/MM_TO_PT)
    ax_stamp.axhline(0.6, color='black', lw=D/MM_TO_PT)
    ax_stamp.axvline(0.2, color='black', lw=D/MM_TO_PT)
    
    # Row 1: Project Number
    ax_stamp.text(0.02, 0.9, texts["project_no"], fontproperties=_get_font(6.5, italic=True), va='center')
    ax_stamp.text(0.22, 0.9, plan.project_number, fontproperties=_get_font(7.5, bold=True), va='center')
    
    # Row 2: Organization
    ax_stamp.text(0.02, 0.7, texts["org"], fontproperties=_get_font(6.5, italic=True), va='center')
    ax_stamp.text(0.22, 0.7, plan.organization, fontproperties=_get_font(7.5, bold=True), va='center')
    
    # Row 3: Title (Project)
    ax_stamp.text(0.02, 0.5, texts["project"], fontproperties=_get_font(6.5, italic=True), va='center')
    wrapped_title = '\n'.join(textwrap.wrap(plan.title, width=45))
    ax_stamp.text(0.22, 0.5, wrapped_title, fontproperties=_get_font(7.5, bold=True), va='center')
    
    # Row 4: Date, Stage, Scale
    ax_stamp.text(0.02, 0.3, texts["date"], fontproperties=_get_font(6.5, italic=True), va='center')
    ax_stamp.text(0.22, 0.3, plan.date, fontproperties=_get_font(6.5), va='center')
    
    # Scale box
    ax_stamp.axvline(0.5, ymin=0, ymax=0.4, color='black', lw=D/MM_TO_PT)
    ax_stamp.text(0.52, 0.3, texts["scale"], fontproperties=_get_font(6.5, italic=True), va='center')
    ax_stamp.text(0.75, 0.3, scale_str, fontproperties=_get_font(7.5, bold=True), va='center')
    
    # Row 5: Drawing Name
    ax_stamp.text(0.02, 0.1, texts["draft"], fontproperties=_get_font(6.5, italic=True), va='center')
    ax_stamp.text(0.22, 0.1, plan.title, fontproperties=_get_font(7.5, bold=True), va='center')

def _draw_explication(fig, zones: List[Zone], total_area: float, pw_mm: float, ph_mm: float, lang: str = "ru"):
    texts = I18N.get(lang, I18N["ru"])
    # Position: Bottom Left of the inner frame, next to Margin Left
    width_mm = 80.0
    height_mm = STAMP_HEIGHT
    left_mm = MARGIN_LEFT
    bottom_mm = MARGIN_OTHER
    
    ax_leg = fig.add_axes([left_mm / pw_mm, bottom_mm / ph_mm, width_mm / pw_mm, height_mm / ph_mm])
    ax_leg.set_axis_off()
    
    y_pos = 0.95
    ax_leg.text(0, y_pos, texts["explication"], fontproperties=_get_font(8, bold=True, italic=True))
    y_pos -= 0.12
    ax_leg.text(0, y_pos, f"{texts['total_area']} {total_area:.1f} м²", fontproperties=_get_font(7, bold=True, italic=True))
    y_pos -= 0.12
    
    # Headers
    ax_leg.text(0, y_pos, texts["num"], fontproperties=_get_font(6.5, bold=True, italic=True))
    ax_leg.text(0.12, y_pos, texts["name"], fontproperties=_get_font(6.5, bold=True, italic=True))
    ax_leg.text(0.8, y_pos, texts["area_sqm"], fontproperties=_get_font(6.5, bold=True, italic=True))
    y_pos -= 0.1
    
    for i, zone in enumerate(zones):
        if y_pos < 0.05:
            ax_leg.text(0, y_pos, texts["others"], fontproperties=_get_font(6, italic=True))
            break
        area = calculate_area(zone.points) or 0
        ax_leg.text(0, y_pos, str(i + 1), fontproperties=_get_font(6.5, italic=True))
        ax_leg.text(0.12, y_pos, zone.name[:18], fontproperties=_get_font(6.5, italic=True))
        ax_leg.text(0.8, y_pos, f'{area:.1f}', fontproperties=_get_font(6.5, italic=True))
        y_pos -= 0.08

def _draw_north_arrow(ax, lang: str = "ru"):
    texts = I18N.get(lang, I18N["ru"])
    xlim, ylim = ax.get_xlim(), ax.get_ylim()
    # Position fixed relative to axis viewport
    x, y = xlim[0] + (xlim[1] - xlim[0]) * 0.08, ylim[1] - (ylim[1] - ylim[0]) * 0.1
    arrow_len = (ylim[1] - ylim[0]) * 0.06
    ax.annotate('', xy=(x, y + arrow_len), xytext=(x, y), arrowprops=dict(arrowstyle='fancy', color='black', linewidth=D_SYMBOL))
    ax.text(x, y + arrow_len + arrow_len*0.3, texts["north"], fontproperties=_get_font(9, bold=True), ha='center')

def render_plot_plan(plan: PlotPlan) -> bytes:
    dpi = plan.dpi if plan.dpi >= 150 else 300
    lang = plan.language or "ru"
    
    # 1. Determine Paper Size (ISO 5457)
    base_w, base_h = PAPER_SIZES.get(plan.paper_format.upper(), PAPER_SIZES["A4"])
    if plan.orientation == "portrait":
        pw_mm, ph_mm = base_h, base_w
    else:
        pw_mm, ph_mm = base_w, base_h
    
    fig = Figure(figsize=(pw_mm / 25.4, ph_mm / 25.4), dpi=dpi)
    
    # 2. Draw Frame (ISO 5457)
    ax_frame = fig.add_axes([0, 0, 1, 1])
    ax_frame.set_axis_off()
    ax_frame.set_xlim(0, pw_mm); ax_frame.set_ylim(0, ph_mm)
    
    frame_rect = Rectangle((MARGIN_LEFT, MARGIN_OTHER), 
                           pw_mm - MARGIN_LEFT - MARGIN_OTHER, 
                           ph_mm - 2 * MARGIN_OTHER,
                           fill=False, color='black', linewidth=D_WIDE/MM_TO_PT)
    ax_frame.add_patch(frame_rect)
    
    # 3. Calculate Scale (ISO 5455)
    all_points = list(plan.boundary_points)
    for zone in plan.zones: all_points.extend(zone.points)
    
    if not all_points:
        fig.savefig(io.BytesIO(), format='png'); return b''
        
    xs, ys = [p.x for p in all_points], [p.y for p in all_points]
    x_min, x_max, y_min, y_max = min(xs), max(xs), min(ys), max(ys)
    x_span, y_span = x_max - x_min or 1, y_max - y_min or 1
    
    # Available area mm
    avail_w_mm = pw_mm - MARGIN_LEFT - MARGIN_OTHER - 20 # 10mm padding each side
    avail_h_mm = ph_mm - 2 * MARGIN_OTHER - STAMP_HEIGHT - 20
    
    scale_val = _calculate_auto_scale(max(x_span, y_span), min(avail_w_mm, avail_h_mm))
    scale_str = f"1:{scale_val}"
    
    m_per_mm = scale_val / 1000.0
    m_per_pt = m_per_mm / MM_TO_PT
    
    # 4. Main Drawing Axis
    # Center object in the available area
    main_w_norm = avail_w_mm / pw_mm
    main_h_norm = avail_h_mm / ph_mm
    main_left_norm = (MARGIN_LEFT + (pw_mm - MARGIN_LEFT - MARGIN_OTHER - avail_w_mm)/2) / pw_mm
    main_bottom_norm = (MARGIN_OTHER + STAMP_HEIGHT + 10) / ph_mm
    
    ax = fig.add_axes([main_left_norm, main_bottom_norm, main_w_norm, main_h_norm])
    ax.set_aspect('equal')
    
    cx, cy = (x_min + x_max) / 2, (y_min + y_max) / 2
    view_w_m = avail_w_mm * m_per_mm
    view_h_m = avail_h_mm * m_per_mm
    ax.set_xlim(cx - view_w_m/2, cx + view_w_m/2)
    ax.set_ylim(cy - view_h_m/2, cy + view_h_m/2)
    
    ax.grid(True, which='both', color='#F8F8F8', linestyle=TYPE_01, linewidth=D, zorder=0)
    ax.tick_params(labelsize=6.5)
    ax.set_xlabel("X (m)", fontproperties=_get_font(6.5, italic=True))
    ax.set_ylabel("Y (m)", fontproperties=_get_font(6.5, italic=True))
    
    if plan.zones: _draw_zones(ax, plan.zones, show_areas=plan.show_areas, standard=plan.standard, m_per_pt=m_per_pt)
    _draw_boundary(ax, plan.boundary_points, standard=plan.standard)
    
    if plan.show_vertex_labels: 
        _draw_vertex_labels(ax, plan.boundary_points, standard=plan.standard, 
                           m_per_pt=m_per_pt, show_coords=plan.coordinate_labels)
    if plan.show_distances: 
        _draw_distances(ax, plan.boundary_points, standard=plan.standard, fontsize=7, 
                        show_azimuths=plan.show_azimuths, m_per_pt=m_per_pt)
    
    if plan.show_scale_bar:
        _draw_scale_bar(ax, x_span, pw_mm / 25.4, lang=lang)
        
    if plan.standard == "shipbuilding":
        texts = I18N.get(lang, I18N["ru"])
        ax.text(ax.get_xlim()[0], cy, texts.get("stern", "STERN"), fontproperties=_get_font(8, bold=True), ha='left', va='center', rotation=90)
        ax.text(ax.get_xlim()[1], cy, texts.get("bow", "BOW"), fontproperties=_get_font(8, bold=True), ha='right', va='center', rotation=-90)
    else:
        _draw_north_arrow(ax, lang=lang)
    
    total_area = calculate_area(plan.boundary_points) or 0
    _draw_explication(fig, plan.zones, total_area, pw_mm, ph_mm, lang=lang)
    _draw_stamp(fig, plan, scale_str, pw_mm, ph_mm, lang=lang)
    
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, facecolor='white')
    buf.seek(0)
    return buf.getvalue()

