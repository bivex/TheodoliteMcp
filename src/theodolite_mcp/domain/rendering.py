import io
import math
from typing import List, Optional, Tuple, Dict
import matplotlib
matplotlib.use('Agg')
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
import matplotlib.patches as patches
import textwrap

from .models import PlotPlan, Point, Zone
from .logic import calculate_azimuth_from_points, calculate_area

# --- ISO 128-20:1996 & ISO 128-23:1999 Standards Constants ---
# Line Group 0.7 (Table 2, ISO 128-23)
# All units in points (1 pt = 1/72 inch). 1 mm = 72/25.4 pt ≈ 2.835 pt.
MM_TO_PT = 72 / 25.4

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
        "unit_m": "м"
    },
    "uk": {
        "project": "Проєкт:",
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
        "unit_m": "м"
    },
    "en": {
        "project": "Project:",
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
        "unit_m": "m"
    }
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

def _draw_zones(ax, zones: List[Zone], show_areas: bool = False, standard: str = "construction"):
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
        # Opaque white bbox (alpha=1.0) creates the 'window' in the hatching
        ax.text(zx, zy, str(i + 1), fontsize=8.5, fontweight='bold', ha='center', va='center', zorder=10,
                bbox=dict(boxstyle='circle,pad=0.2', facecolor='white', edgecolor='black', 
                          linewidth=D_SYMBOL/MM_TO_PT, alpha=1.0))
        
        if show_areas:
            # Inscription below the zone number
            ax.text(zx, zy - 1.2, f"{area:.1f} m²", fontsize=7, ha='center', va='top', zorder=10, 
                    bbox=dict(boxstyle='round,pad=0.1', facecolor='white', edgecolor='none', alpha=1.0))

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
            fontsize=fontsize, ha='center', va='bottom', zorder=10)

def _draw_vertex_labels(ax, points: List[Point], fontsize: float = 8):
    cx, cy = _centroid(points)
    for p in points:
        dx, dy = p.x - cx, p.y - cy
        dist = math.hypot(dx, dy)
        offset_x, offset_y = (dx / dist * 1.6, dy / dist * 1.6) if dist > 0 else (1.6, 1.6)
        ax.text(p.x + offset_x, p.y + offset_y, p.name, fontsize=fontsize, ha='center', va='center', zorder=5)

def _draw_distances(ax, points: List[Point], standard: str = "construction", fontsize: float = 7, show_azimuths: bool = False, m_per_pt: float = 0.1):
    # ISO 128-23 / ISO 129-1 / ISO 129-4
    # Line width D is in points. 
    # Extension lines shall extend approx 8 * line width beyond dimension line.
    overshoot = 8 * (D / MM_TO_PT) * (MM_TO_PT * m_per_pt) # simplified: 8 * D * m_per_pt
    overshoot = 8 * D * m_per_pt
    gap = 2 * D * m_per_pt # Small gap from feature
    text_offset = 1.2 * MM_TO_PT * m_per_pt # ~1.2mm above line
    
    # Distance from object to dimension line (standard suggests ~7-10mm, let's use 8mm)
    dim_offset_m = 8.0 * MM_TO_PT * m_per_pt

    for i in range(len(points)):
        p1, p2 = points[i], points[(i + 1) % len(points)]
        dist = math.hypot(p2.x - p1.x, p2.y - p1.y)
        if dist < 0.1: continue
        
        mx, my = _edge_midpoint(p1, p2)
        ox_unit, oy_unit = _perpendicular_offset(p1, p2, distance=1.0)
        
        # Dimension line positions
        ox_line, oy_line = ox_unit * dim_offset_m, oy_unit * dim_offset_m
        
        # 1. Dimension line (Narrow 01.1)
        ax.plot([p1.x + ox_line, p2.x + ox_line], [p1.y + oy_line, p2.y + oy_line], 
                color='black', linewidth=D, linestyle=TYPE_01, zorder=4)
        
        # 2. Extension lines (Narrow 01.1)
        # From (p1 + gap) to (p1 + ox_line + overshoot)
        p1_start_x, p1_start_y = p1.x + ox_unit * gap, p1.y + oy_unit * gap
        p1_end_x, p1_end_y = p1.x + ox_line + ox_unit * overshoot, p1.y + oy_line + oy_unit * overshoot
        ax.plot([p1_start_x, p1_end_x], [p1_start_y, p1_end_y], 
                color='black', linewidth=D, linestyle=TYPE_01, zorder=4)
        
        p2_start_x, p2_start_y = p2.x + ox_unit * gap, p2.y + oy_unit * gap
        p2_end_x, p2_end_y = p2.x + ox_line + ox_unit * overshoot, p2.y + oy_line + oy_unit * overshoot
        ax.plot([p2_start_x, p2_end_x], [p2_start_y, p2_end_y], 
                color='black', linewidth=D, linestyle=TYPE_01, zorder=4)
        
        if standard == "shipbuilding":
            # ISO 129-4: Closed 30° arrowheads
            angle = math.atan2(p2.y - p1.y, p2.x - p1.x)
            # Draw at p1+offset
            ax.annotate("", xy=(p1.x + ox_line, p1.y + oy_line), 
                        xytext=(p1.x + ox_line + math.cos(angle)*0.01, p1.y + oy_line + math.sin(angle)*0.01),
                        arrowprops=dict(arrowstyle='-|>', color='black', mutation_scale=10, 
                                        linewidth=D_WIDE/MM_TO_PT, shrinkA=0, shrinkB=0), zorder=5)
            # Draw at p2+offset
            ax.annotate("", xy=(p2.x + ox_line, p2.y + oy_line), 
                        xytext=(p2.x + ox_line - math.cos(angle)*0.01, p2.y + oy_line - math.sin(angle)*0.01),
                        arrowprops=dict(arrowstyle='-|>', color='black', mutation_scale=10, 
                                        linewidth=D_WIDE/MM_TO_PT, shrinkA=0, shrinkB=0), zorder=5)
        else:
            # ISO 129-1: Architectural ticks (Wide line 01.2)
            # Standard ticks are 45 deg, length approx 2-3mm
            tick_len = 2.0 * MM_TO_PT * m_per_pt
            for p_base in [(p1.x + ox_line, p1.y + oy_line), (p2.x + ox_line, p2.y + oy_line)]:
                t_angle = math.atan2(p2.y - p1.y, p2.x - p1.x) + math.pi/4
                tx, ty = math.cos(t_angle) * tick_len, math.sin(t_angle) * tick_len
                ax.plot([p_base[0] - tx, p_base[0] + tx], [p_base[1] - ty, p_base[1] + ty], 
                        color='black', linewidth=D_WIDE, linestyle=TYPE_01, zorder=5)
            
        # Distance text positioning
        angle_deg = math.degrees(math.atan2(p2.y - p1.y, p2.x - p1.x))
        if angle_deg > 90: angle_deg -= 180
        if angle_deg < -90: angle_deg += 180
        
        # Text offset (above line)
        tx_off, ty_off = ox_unit * text_offset, oy_unit * text_offset
        
        # Distance (above line)
        ax.text(mx + ox_line + tx_off, my + oy_line + ty_off, f'{dist:.2f}', 
                fontsize=fontsize, ha='center', va='bottom', rotation=angle_deg, zorder=10, style='italic')
        
        # Azimuth (below line)
        if show_azimuths:
            az = calculate_azimuth_from_points(p1, p2)
            ax.text(mx + ox_line - tx_off, my + oy_line - ty_off, f'{az:.1f}°', 
                    fontsize=fontsize-1.5, ha='center', va='top', rotation=angle_deg, zorder=10)

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
            fontsize=7, ha='center', va='top', fontweight='bold')

def _calculate_auto_scale(x_span: float, width_inches: float) -> str:
    if width_inches <= 0: return 'N/A'
    raw_scale = (x_span * 1000) / (width_inches * 25.4)
    std_scales = [10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000, 2500, 5000, 10000]
    for s in std_scales:
        if s >= raw_scale: return f'1:{s}'
    return f'1:{int(raw_scale)}'

def _draw_stamp(fig, title: str, scale_str: str, lang: str = "ru"):
    texts = I18N.get(lang, I18N["ru"])
    # Stamp frame (Wide line 01.2)
    ax_stamp = fig.add_axes([0.65, 0.05, 0.3, 0.15])
    ax_stamp.set_xticks([]); ax_stamp.set_yticks([]); ax_stamp.set_facecolor('white')
    for spine in ax_stamp.spines.values(): spine.set_linewidth(D_WIDE/MM_TO_PT)
    
    # Internal grid (Narrow line 01.1)
    ax_stamp.axhline(0.33, color='black', lw=D/MM_TO_PT)
    ax_stamp.axhline(0.66, color='black', lw=D/MM_TO_PT)
    ax_stamp.axvline(0.3, color='black', lw=D/MM_TO_PT)
    
    import textwrap
    wrapped_title = '\n'.join(textwrap.wrap(title, width=22))
    font_props = {'fontsize': 7.5, 'family': 'sans-serif', 'style': 'italic'}
    
    ax_stamp.text(0.05, 0.8, texts["project"], **font_props, va='center')
    ax_stamp.text(0.35, 0.8, wrapped_title, fontsize=8, fontweight='bold', va='center')
    ax_stamp.text(0.05, 0.5, texts["stage"], **font_props, va="center")
    ax_stamp.text(0.35, 0.5, texts["draft"], fontsize=8, va='center')
    ax_stamp.text(0.05, 0.15, texts["scale"], **font_props, va='center')
    ax_stamp.text(0.35, 0.15, scale_str, fontsize=8, va='center')

def _draw_explication(fig, zones: List[Zone], total_area: float, lang: str = "ru"):
    texts = I18N.get(lang, I18N["ru"])
    ax_leg = fig.add_axes([0.05, 0.05, 0.35, 0.25])
    ax_leg.set_axis_off()
    font_props = {'family': 'sans-serif', 'style': 'italic'}
    y_pos = 0.95
    ax_leg.text(0, y_pos, texts["explication"], fontsize=9, fontweight='bold', **font_props)
    y_pos -= 0.1
    ax_leg.text(0, y_pos, f"{texts['total_area']} {total_area:.1f} м² ({total_area/100:.2f} {texts['sotki']})", fontsize=8, fontweight='bold', **font_props)
    y_pos -= 0.1
    ax_leg.text(0, y_pos, texts["num"], fontsize=7.5, fontweight='bold', **font_props)
    ax_leg.text(0.1, y_pos, texts["name"], fontsize=7.5, fontweight='bold', **font_props)
    ax_leg.text(0.7, y_pos, texts["area_sqm"], fontsize=7.5, fontweight='bold', **font_props)
    y_pos -= 0.08
    for i, zone in enumerate(zones):
        if y_pos < 0.05:
            ax_leg.text(0, y_pos, texts["others"], fontsize=7.5, fontstyle='italic')
            break
        area = calculate_area(zone.points) or 0
        ax_leg.text(0, y_pos, str(i + 1), fontsize=7.5, **font_props)
        ax_leg.text(0.1, y_pos, zone.name[:24], fontsize=7.5, **font_props)
        ax_leg.text(0.7, y_pos, f'{area:.1f}', fontsize=7.5, **font_props)
        y_pos -= 0.06

def _draw_north_arrow(ax, lang: str = "ru"):
    texts = I18N.get(lang, I18N["ru"])
    xlim, ylim = ax.get_xlim(), ax.get_ylim()
    # Position fixed relative to axis viewport
    x, y = xlim[0] + (xlim[1] - xlim[0]) * 0.05, ylim[1] - (ylim[1] - ylim[0]) * 0.12
    arrow_len = (ylim[1] - ylim[0]) * 0.08
    ax.annotate('', xy=(x, y + arrow_len), xytext=(x, y), arrowprops=dict(arrowstyle='fancy', color='black', linewidth=D_SYMBOL/MM_TO_PT))
    ax.text(x, y + arrow_len + arrow_len*0.25, texts["north"], fontsize=10.5, fontweight='bold', ha='center')

def render_plot_plan(plan: PlotPlan) -> bytes:
    dpi = plan.dpi if plan.dpi >= 150 else 150
    lang = plan.language or "ru"
    fig = Figure(figsize=(plan.width_inches, plan.height_inches), dpi=dpi)
    ax = fig.add_axes([0.1, 0.35, 0.8, 0.55])
    
    all_points = list(plan.boundary_points)
    for zone in plan.zones: all_points.extend(zone.points)
    if not all_points:
        fig.savefig(io.BytesIO(), format='png'); return b''
        
    xs, ys = [p.x for p in all_points], [p.y for p in all_points]
    x_min, x_max, y_min, y_max = min(xs), max(xs), min(ys), max(ys)
    x_span, y_span = x_max - x_min or 1, y_max - y_min or 1
    
    scale_str = _calculate_auto_scale(x_span * 1.5, plan.width_inches * 0.8)
    ax.set_xlim(x_min - x_span*0.28, x_max + x_span*0.28)
    ax.set_ylim(y_min - y_span*0.28, y_max + y_span*0.28)
    ax.set_aspect('equal')
    
    # ISO 128-23: Narrow line for grid (01.1)
    ax.grid(True, which='both', color='#F0F0F0', linestyle=TYPE_01, linewidth=D, zorder=0)
    ax.tick_params(labelsize=7.5)
    ax.set_xlabel("X (m)", fontsize=7.5, style='italic'); ax.set_ylabel("Y (m)", fontsize=7.5, style='italic')
    
    # Calculate scale factor: meters per point
    # Width of axes in points = (width_inches * 0.8) * 72
    ax_width_pt = plan.width_inches * 0.8 * 72
    m_per_pt = (x_max - x_min + x_span*0.56) / ax_width_pt if ax_width_pt > 0 else 0.1
    
    if plan.zones: _draw_zones(ax, plan.zones, show_areas=plan.show_areas, standard=plan.standard)
    _draw_boundary(ax, plan.boundary_points, standard=plan.standard)
    
    if plan.show_vertex_labels: _draw_vertex_labels(ax, plan.boundary_points)
    if plan.show_distances: 
        _draw_distances(ax, plan.boundary_points, standard=plan.standard, fontsize=7.5, 
                        show_azimuths=plan.show_azimuths, m_per_pt=m_per_pt)
    
    if plan.show_scale_bar:
        _draw_scale_bar(ax, x_span, plan.width_inches, lang=lang)
        
    _draw_north_arrow(ax, lang=lang)
    
    total_area = calculate_area(plan.boundary_points) or 0
    _draw_explication(fig, plan.zones, total_area, lang=lang)
    _draw_stamp(fig, plan.title, scale_str, lang=lang)
    
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, facecolor='white')
    buf.seek(0)
    return buf.getvalue()
