import io
import math
from typing import List, Optional, Tuple
import matplotlib
matplotlib.use('Agg')
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
import matplotlib.patches as patches
import textwrap

from .models import PlotPlan, Point, Zone
from .logic import calculate_azimuth_from_points, calculate_area

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
    if any(k in name for k in ['дом', 'хозблок', 'здание', 'строение']): return '///'
    if any(k in name for k in ['огород', 'теплица', 'ягодник']): return '...'
    if any(k in name for k in ['сад', 'парк', 'цветник']): return 'oo'
    if any(k in name for k in ['парковка', 'дорожка', 'въезд']): return 'xxx'
    return None

def _draw_boundary(ax, points: List[Point], color: str = 'black', linewidth: float = 2.0):
    xs, ys = _polygon_coords(points)
    ax.plot(xs, ys, color=color, linewidth=linewidth, zorder=3)

def _draw_zones(ax, zones: List[Zone]):
    for i, zone in enumerate(zones):
        color = zone.fill_color or _auto_color(i)
        hatch = _get_hatch(zone.name)
        xs, ys = _polygon_coords(zone.points)
        ax.fill(xs, ys, color=color, alpha=0.2, zorder=1)
        if hatch:
            ax.fill(xs, ys, fill=False, hatch=hatch, edgecolor='black', linewidth=0, alpha=0.2, zorder=2)
        is_building = any(k in zone.name.lower() for k in ['дом', 'здание', 'хозблок'])
        lw = 1.2 if is_building else 0.6
        ax.plot(xs, ys, color='black', linewidth=lw, linestyle='-', zorder=3)
        zx, zy = _centroid(zone.points)
        ax.text(zx, zy, str(i + 1), fontsize=9, fontweight='bold', ha='center', va='center', zorder=10,
                bbox=dict(boxstyle='circle,pad=0.2', facecolor='white', edgecolor='black', alpha=0.8))

def _draw_vertex_labels(ax, points: List[Point], fontsize: float = 8):
    cx, cy = _centroid(points)
    for p in points:
        dx, dy = p.x - cx, p.y - cy
        dist = math.hypot(dx, dy)
        offset_x, offset_y = (dx / dist * 1.5, dy / dist * 1.5) if dist > 0 else (1.5, 1.5)
        ax.text(p.x + offset_x, p.y + offset_y, p.name, fontsize=fontsize, ha='center', va='center', zorder=5)

def _draw_distances(ax, points: List[Point], fontsize: float = 7):
    for i in range(len(points)):
        p1, p2 = points[i], points[(i + 1) % len(points)]
        dist = math.hypot(p2.x - p1.x, p2.y - p1.y)
        if dist < 0.1: continue
        mx, my = _edge_midpoint(p1, p2)
        ox_line, oy_line = _perpendicular_offset(p1, p2, distance=3.0)
        ax.plot([p1.x + ox_line, p2.x + ox_line], [p1.y + oy_line, p2.y + oy_line], color='black', linewidth=0.5, zorder=4)
        ax.plot([p1.x, p1.x + ox_line * 1.1], [p1.y, p1.y + oy_line * 1.1], color='black', linewidth=0.4, zorder=4)
        ax.plot([p2.x, p2.x + ox_line * 1.1], [p2.y, p2.y + oy_line * 1.1], color='black', linewidth=0.4, zorder=4)
        tick_len = 0.6
        for p in [(p1.x + ox_line, p1.y + oy_line), (p2.x + ox_line, p2.y + oy_line)]:
            angle = math.atan2(p2.y - p1.y, p2.x - p1.x) + math.pi/4
            tx, ty = math.cos(angle) * tick_len, math.sin(angle) * tick_len
            ax.plot([p[0] - tx, p[0] + tx], [p[1] - ty, p[1] + ty], color='black', linewidth=0.8, zorder=5)
        angle = math.degrees(math.atan2(p2.y - p1.y, p2.x - p1.x))
        if angle > 90: angle -= 180
        if angle < -90: angle += 180
        ax.text(mx + ox_line, my + oy_line + 0.5, f'{dist:.2f}', fontsize=fontsize, ha='center', va='bottom', rotation=angle, zorder=10)

def _calculate_auto_scale(x_span: float, width_inches: float) -> str:
    if width_inches <= 0: return 'N/A'
    raw_scale = (x_span * 1000) / (width_inches * 25.4)
    std_scales = [10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000, 2500, 5000, 10000]
    for s in std_scales:
        if s >= raw_scale: return f'1:{s}'
    return f'1:{int(raw_scale)}'

def _draw_stamp(fig, title: str, scale_str: str):
    ax_stamp = fig.add_axes([0.65, 0.05, 0.3, 0.15])
    ax_stamp.set_xticks([]); ax_stamp.set_yticks([]); ax_stamp.set_facecolor('white')
    for spine in ax_stamp.spines.values(): spine.set_linewidth(1.5)
    ax_stamp.axhline(0.33, color='black', lw=0.5); ax_stamp.axhline(0.66, color='black', lw=0.5); ax_stamp.axvline(0.3, color='black', lw=0.5)
    wrapped_title = '\n'.join(textwrap.wrap(title, width=25))
    font_props = {'fontsize': 7, 'family': 'sans-serif', 'style': 'italic'}
    ax_stamp.text(0.05, 0.8, 'Проект:', **font_props, va='center')
    ax_stamp.text(0.35, 0.8, wrapped_title, fontsize=8, fontweight='bold', va='center')
    ax_stamp.text(0.05, 0.5, 'Стадия:', **font_props, va="center")
    ax_stamp.text(0.35, 0.5, 'Чертеж (П)', fontsize=8, va='center')
    ax_stamp.text(0.05, 0.15, 'Масштаб:', **font_props, va='center')
    ax_stamp.text(0.35, 0.15, scale_str, fontsize=8, va='center')

def _draw_explication(fig, zones: List[Zone], total_area: float):
    ax_leg = fig.add_axes([0.05, 0.05, 0.35, 0.25])
    ax_leg.set_axis_off()
    font_props = {'family': 'sans-serif', 'style': 'italic'}
    y_pos = 0.95
    ax_leg.text(0, y_pos, 'ЭКСПЛИКАЦИЯ ЗОН', fontsize=9, fontweight='bold', **font_props)
    y_pos -= 0.1
    ax_leg.text(0, y_pos, f'Общая площадь: {total_area:.1f} м² ({total_area/100:.2f} сот.)', fontsize=8, fontweight='bold', **font_props)
    y_pos -= 0.1
    ax_leg.text(0, y_pos, '№', fontsize=7, fontweight='bold', **font_props)
    ax_leg.text(0.1, y_pos, 'Наименование', fontsize=7, fontweight='bold', **font_props)
    ax_leg.text(0.7, y_pos, 'S, м²', fontsize=7, fontweight='bold', **font_props)
    y_pos -= 0.08
    for i, zone in enumerate(zones):
        if y_pos < 0.05:
            ax_leg.text(0, y_pos, '... и другие', fontsize=7, fontstyle='italic')
            break
        area = calculate_area(zone.points) or 0
        ax_leg.text(0, y_pos, str(i + 1), fontsize=7, **font_props)
        ax_leg.text(0.1, y_pos, zone.name[:25], fontsize=7, **font_props)
        ax_leg.text(0.7, y_pos, f'{area:.1f}', fontsize=7, **font_props)
        y_pos -= 0.06

def _draw_north_arrow(ax):
    xlim, ylim = ax.get_xlim(), ax.get_ylim()
    x, y = xlim[0] + (xlim[1] - xlim[0]) * 0.05, ylim[1] - (ylim[1] - ylim[0]) * 0.1
    arrow_len = (ylim[1] - ylim[0]) * 0.08
    ax.annotate('', xy=(x, y + arrow_len), xytext=(x, y), arrowprops=dict(arrowstyle='fancy', color='black'))
    ax.text(x, y + arrow_len + arrow_len*0.2, 'С', fontsize=10, fontweight='bold', ha='center')

def render_plot_plan(plan: PlotPlan) -> bytes:
    dpi = plan.dpi if plan.dpi >= 150 else 150
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
    ax.set_xlim(x_min - x_span*0.25, x_max + x_span*0.25)
    ax.set_ylim(y_min - y_span*0.25, y_max + y_span*0.25)
    ax.set_aspect('equal')
    ax.grid(True, which='both', color='#EEEEEE', linestyle='-', linewidth=0.3, zorder=0)
    ax.tick_params(labelsize=7)
    ax.set_xlabel('X (m)', fontsize=7, style='italic'); ax.set_ylabel('Y (m)', fontsize=7, style='italic')
    if plan.zones: _draw_zones(ax, plan.zones)
    _draw_boundary(ax, plan.boundary_points, linewidth=1.5)
    if plan.show_vertex_labels: _draw_vertex_labels(ax, plan.boundary_points)
    if plan.show_distances: _draw_distances(ax, plan.boundary_points)
    _draw_north_arrow(ax)
    total_area = calculate_area(plan.boundary_points) or 0
    _draw_explication(fig, plan.zones, total_area)
    _draw_stamp(fig, plan.title, scale_str)
    buf = io.BytesIO(); fig.savefig(buf, format='png', dpi=dpi, facecolor='white'); buf.seek(0)
    return buf.getvalue()
