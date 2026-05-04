import io
import math
from typing import List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure
from matplotlib.patches import FancyArrowPatch

from .models import PlotPlan, Point, Zone
from .logic import calculate_azimuth_from_points, calculate_area


ZONE_COLORS = [
    "#4CAF50", "#2196F3", "#FF9800", "#9C27B0",
    "#F44336", "#00BCD4", "#795548", "#607D8B",
    "#8BC34A", "#E91E63",
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
    return sum(p.x for p in points) / n, sum(p.y for p in points) / n


def _edge_midpoint(p1: Point, p2: Point) -> Tuple[float, float]:
    return (p1.x + p2.x) / 2, (p1.y + p2.y) / 2


def _perpendicular_offset(p1: Point, p2: Point, distance: float = 1.0) -> Tuple[float, float]:
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    length = math.hypot(dx, dy)
    if length == 0:
        return 0, 0
    nx = -dy / length * distance
    ny = dx / length * distance
    return nx, ny


def _nice_scale_length(total_span: float) -> float:
    candidates = [1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000, 5000]
    target = total_span / 5
    best = candidates[0]
    for c in candidates:
        if c <= target:
            best = c
    return best


def _draw_boundary(ax, points: List[Point], color: str = "#333333", linewidth: float = 2.0):
    xs, ys = _polygon_coords(points)
    ax.plot(xs, ys, color=color, linewidth=linewidth, zorder=3)


def _draw_zones(ax, zones: List[Zone]):
    for i, zone in enumerate(zones):
        color = zone.fill_color or _auto_color(i)
        xs, ys = _polygon_coords(zone.points)
        ax.fill(xs, ys, color=color, alpha=zone.fill_alpha, zorder=1)
        ax.plot(xs, ys, color=color, linewidth=1.0, linestyle="--", alpha=0.7, zorder=2)


def _draw_vertex_labels(ax, points: List[Point], fontsize: float = 9):
    cx, cy = _centroid(points)
    for p in points:
        dx, dy = p.x - cx, p.y - cy
        dist = math.hypot(dx, dy)
        if dist > 0:
            offset_x = dx / dist * 2.5
            offset_y = dy / dist * 2.5
        else:
            offset_x, offset_y = 2.5, 2.5
        ax.annotate(
            p.name, xy=(p.x, p.y), xytext=(p.x + offset_x, p.y + offset_y),
            fontsize=fontsize, fontweight="bold", ha="center", va="center",
            zorder=5,
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="gray", alpha=0.8),
        )


def _draw_distances(ax, points: List[Point], fontsize: float = 8):
    for i in range(len(points)):
        p1 = points[i]
        p2 = points[(i + 1) % len(points)]
        dist = math.hypot(p2.x - p1.x, p2.y - p1.y)
        if dist == 0:
            continue
        mx, my = _edge_midpoint(p1, p2)
        ox, oy = _perpendicular_offset(p1, p2, distance=2.0)
        ax.annotate(
            f"{dist:.1f} м", xy=(mx, my), xytext=(mx + ox, my + oy),
            fontsize=fontsize, color="#1565C0", ha="center", va="center",
            zorder=5,
            bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.7),
        )


def _draw_azimuths(ax, points: List[Point], fontsize: float = 7.5):
    for i in range(len(points)):
        p1 = points[i]
        p2 = points[(i + 1) % len(points)]
        dist = math.hypot(p2.x - p1.x, p2.y - p1.y)
        if dist == 0:
            continue
        az = calculate_azimuth_from_points(p1, p2)
        ox, oy = _perpendicular_offset(p1, p2, distance=-2.5)
        frac = 0.3
        lx = p1.x + (p2.x - p1.x) * frac + ox
        ly = p1.y + (p2.y - p1.y) * frac + oy
        d, m, s = _decimal_to_dms(az)
        az_str = f"{d}°{m:02d}'{s:04.1f}\""
        ax.annotate(
            az_str, xy=(lx, ly), fontsize=fontsize, color="#C62828",
            ha="center", va="center", zorder=5,
            bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.7),
        )


def _decimal_to_dms(decimal: float) -> Tuple[int, int, float]:
    decimal = decimal % 360
    d = int(decimal)
    mf = (decimal - d) * 60
    m = int(mf)
    s = (mf - m) * 60
    return d, m, s


def _draw_areas(ax, boundary_points: List[Point], zones: List[Zone], fontsize: float = 9):
    area = calculate_area(boundary_points)
    if area and area > 0:
        cx, cy = _centroid(boundary_points)
        sotki = area / 100.0
        ax.annotate(
            f"{area:.1f} м² ({sotki:.2f} сот.)",
            xy=(cx, cy), fontsize=fontsize + 1, fontweight="bold",
            ha="center", va="center", color="#1B5E20", zorder=5,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#E8F5E9", edgecolor="#4CAF50", alpha=0.9),
        )
    for i, zone in enumerate(zones):
        zone_area = calculate_area(zone.points)
        if zone_area and zone_area > 0:
            zx, zy = _centroid(zone.points)
            zs = zone_area / 100.0
            ax.annotate(
                f"{zone.name}\n{zone_area:.1f} м² ({zs:.2f} сот.)",
                xy=(zx, zy), fontsize=fontsize - 1, ha="center", va="center",
                color="#333333", zorder=5,
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="gray", alpha=0.85),
            )


def _draw_north_arrow(ax, xlim, ylim):
    x = xlim[1] - (xlim[1] - xlim[0]) * 0.06
    y_start = ylim[1] - (ylim[1] - ylim[0]) * 0.12
    y_end = ylim[1] - (ylim[1] - ylim[0]) * 0.03
    ax.annotate(
        "N", xy=(x, y_end), xytext=(x, y_start),
        fontsize=11, fontweight="bold", ha="center", va="bottom",
        arrowprops=dict(arrowstyle="->", color="black", lw=1.5),
        zorder=6,
    )


def _draw_scale_bar(ax, xlim, ylim, total_span: float):
    scale_len = _nice_scale_length(total_span)
    x_start = xlim[0] + (xlim[1] - xlim[0]) * 0.03
    y = ylim[0] + (ylim[1] - ylim[0]) * 0.04
    x_end = x_start + scale_len

    ax.plot([x_start, x_end], [y, y], color="black", linewidth=2, zorder=6)
    ax.plot([x_start, x_start], [y - total_span * 0.008, y + total_span * 0.008], color="black", linewidth=2, zorder=6)
    ax.plot([x_end, x_end], [y - total_span * 0.008, y + total_span * 0.008], color="black", linewidth=2, zorder=6)
    ax.text(
        (x_start + x_end) / 2, y + total_span * 0.015,
        f"{scale_len:.0f} м", ha="center", va="bottom", fontsize=8, zorder=6,
    )


def render_plot_plan(plan: PlotPlan) -> bytes:
    fig = Figure(figsize=(plan.width_inches, plan.height_inches), dpi=plan.dpi)
    ax = fig.add_subplot(111)

    all_points = list(plan.boundary_points)
    for zone in plan.zones:
        all_points.extend(zone.points)

    if not all_points:
        fig.savefig(io.BytesIO(), format="png")
        return b""

    xs = [p.x for p in all_points]
    ys = [p.y for p in all_points]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)

    x_span = x_max - x_min or 1
    y_span = y_max - y_min or 1
    margin_x = x_span * 0.15
    margin_y = y_span * 0.15
    ax.set_xlim(x_min - margin_x, x_max + margin_x)
    ax.set_ylim(y_min - margin_y, y_max + margin_y)

    ax.set_aspect("equal")
    ax.set_title(plan.title, fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("X (м)", fontsize=9)
    ax.set_ylabel("Y (м)", fontsize=9)
    ax.grid(True, alpha=0.3, linestyle="--")

    xlim = ax.get_xlim()
    ylim = ax.get_ylim()

    if plan.zones:
        _draw_zones(ax, plan.zones)

    _draw_boundary(ax, plan.boundary_points)

    if plan.show_areas:
        _draw_areas(ax, plan.boundary_points, plan.zones)
    if plan.show_vertex_labels:
        _draw_vertex_labels(ax, plan.boundary_points)
    if plan.show_distances:
        _draw_distances(ax, plan.boundary_points)
    if plan.show_azimuths:
        _draw_azimuths(ax, plan.boundary_points)
    if plan.show_north_arrow:
        _draw_north_arrow(ax, xlim, ylim)
    if plan.show_scale_bar:
        total_span = max(x_span, y_span)
        _draw_scale_bar(ax, xlim, ylim, total_span)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=plan.dpi, bbox_inches="tight")
    buf.seek(0)
    return buf.getvalue()
