#!/usr/bin/env python3
"""
Comprehensive Geodetic Rendering Stress Test
Tests font rendering, coordinate formatting, collision avoidance
with large coordinate systems, many zones, and crowded layouts.
"""

import os
from theodolite_mcp.domain.models import Point, PlotPlan, Zone
from theodolite_mcp.domain.rendering import render_plot_plan, _format_coord_value

print("=" * 60)
print("GEODETIC RENDERING STRESS TEST")
print("=" * 60)

# Test 1: Large coordinate values (UTM / military grid)
print("\n[1] Testing large coordinate formatting...")
test_coords = [
    (500000.0, 500000.0, "UTM zone 37N"),
    (2500000.0, 1500000.0, "Mega-coordinates"),
    (10000000.0, 10000000.0, "10-million scale"),
    (-500000.0, -500000.0, "Negative large"),
    (0.0, 0.0, "Origin"),
    (999.9, 999.9, "Sub-kilometer"),
]
for x, y, desc in test_coords:
    formatted = _format_coord_value(x)
    print(f"  {desc}: ({x:.1f}, {y:.1f}) -> ({formatted}, ...)")
    assert isinstance(formatted, str)
    assert len(formatted) < 20  # Should be compact

print("  ✓ Coordinate formatting OK")

# Test 2: Many zones (legend overflow / crowded labels)
print("\n[2] Testing 50 zones with legend overflow...")
boundary_large = [
    Point(x=0, y=0),
    Point(x=2000, y=0),
    Point(x=2000, y=2000),
    Point(x=0, y=2000),
]

zones_many = []
names = [
    "Жил╡я зона",
    "Общественная зона",
    "Специальная зона",
    "Зеленые насаждения",
    "Автомобильные стоянки",
    "Транспортные развязки",
    "Инженерная инфраструктура",
    "Рекреационная зона",
    "Коммерческая зона",
    "Производственная зона",
    "Таможенная зона",
    "Сельскохозяйственная зона",
    "Защитная зона",
    "Санкционированная зона",
    "Экстренная зона",
]
for i in range(50):
    x = i * 30
    y = i * 30
    zones_many.append(
        Zone(
            name=f"Zone_{i:02d}_{names[i % len(names)]}",
            points=[
                Point(x=x, y=y),
                Point(x=x + 25, y=y),
                Point(x=x + 25, y=y + 25),
                Point(x=x, y=y + 25),
            ],
        )
    )

plan_many = PlotPlan(
    title="Масштабное геодезическое исследование (50 зон)",
    boundary_points=boundary_large,
    zones=zones_many,
    show_areas=True,
    show_legend=True,
    paper_format="A2",
    orientation="landscape",
)

png = render_plot_plan(plan_many)
with open("output/stress_test_50_zones.png", "wb") as f:
    f.write(png)
print(f"  ✓ 50-zone legend: {len(png):,} bytes")

# Test 3: Dense point cloud (vertex label collision)
print("\n[3] Testing dense point cloud (200 vertices)...")
dense_points = []
for i in range(200):
    # Create a spiral pattern
    t = i * 0.1
    x = 50 + t * 2 * (i % 20) * 0.5
    y = 50 + t * 2 + (i // 20) * 2
    dense_points.append(Point(name=f"P{i}", x=x, y=y))

plan_dense = PlotPlan(
    title="Густое облако точек (200 вершин)",
    boundary_points=dense_points[:50],
    show_vertex_labels=True,
    coordinate_labels=True,
    paper_format="A1",
)

png2 = render_plot_plan(plan_dense)
with open("output/stress_test_dense_points.png", "wb") as f:
    f.write(png2)
print(f"  ✓ Dense vertex labels: {len(png2):,} bytes")

# Test 4: Mixed coordinate magnitudes in one drawing
print("\n[4] Testing mixed coordinate magnitudes...")
mixed_boundary = [
    Point(x=0, y=0),
    Point(x=500000.0, y=0),  # Large X
    Point(x=500000.0, y=1000.0),  # Large X, small Y delta
    Point(x=0, y=1000.0),  # back to zero
]
plan_mixed = PlotPlan(
    title="Смешанные масштабы координат",
    boundary_points=mixed_boundary,
    coordinate_labels=True,
    paper_format="A3",
)

png3 = render_plot_plan(plan_mixed)
with open("output/stress_test_mixed_scales.png", "wb") as f:
    f.write(png3)
print(f"  ✓ Mixed scales: {len(png3):,} bytes")

# Test 5: Very small distances (short segment leaders)
print("\n[5] Testing very short segments (leader lines)...")
short_segments = []
for i in range(50):
    short_segments.append(Point(name=f"S{i}", x=i * 0.1, y=i * 0.1))
plan_short = PlotPlan(
    title="Короткие отрезки (лидеры)",
    boundary_points=short_segments,
    show_vertex_labels=True,
    paper_format="A4",
)
png4 = render_plot_plan(plan_short)
with open("output/stress_test_short_segments.png", "wb") as f:
    f.write(png4)
print(f"  ✓ Short segment leaders: {len(png4):,} bytes")

# Test 6: Shipbuilding standard (crowded annotations)
print("\n[6] Testing shipbuilding standard (max label density)...")
ship_zones = []
for i in range(30):
    ship_zones.append(
        Zone(
            name=f"ПАЛУБА_{i}",
            points=[
                Point(x=i * 10, y=i * 10),
                Point(x=i * 10 + 9, y=i * 10),
                Point(x=i * 10 + 9, y=i * 10 + 9),
                Point(x=i * 10, y=i * 10 + 9),
            ],
        )
    )

plan_ship = PlotPlan(
    title="Судостроительная схема (30 палуб)",
    boundary_points=[
        Point(x=0, y=0),
        Point(x=500, y=0),
        Point(x=500, y=500),
        Point(x=0, y=500),
    ],
    zones=ship_zones,
    standard="shipbuilding",
    show_areas=True,
    show_vertex_labels=True,
)

png5 = render_plot_plan(plan_ship)
with open("output/stress_test_shipbuilding.png", "wb") as f:
    f.write(png5)
print(f"  ✓ Shipbuilding dense: {len(png5):,} bytes")

# Test 7: Interior plan with many rooms
print("\n[7] Testing interior plan with many rooms...")
from theodolite_mcp.domain.models import InteriorPlan, Wall, Opening, Room

walls = []
# Create grid of walls
grid_size = 8
wall_len = 50.0
for i in range(grid_size + 1):
    # Horizontal walls
    walls.append(
        Wall(
            start_pt=Point(x=i * wall_len, y=0),
            end_pt=Point(x=i * wall_len, y=grid_size * wall_len),
            thickness=0.3,
        )
    )
    # Vertical walls
    walls.append(
        Wall(
            start_pt=Point(x=0, y=i * wall_len),
            end_pt=Point(x=grid_size * wall_len, y=i * wall_len),
            thickness=0.3,
        )
    )

rooms = []
room_count = 0
for i in range(grid_size):
    for j in range(grid_size):
        room_count += 1
        rooms.append(
            Room(
                name=f"Room_{room_count}",
                number=str(room_count),
                points=[
                    Point(x=i * wall_len + 0.15, y=j * wall_len + 0.15),
                    Point(x=(i + 1) * wall_len - 0.15, y=j * wall_len + 0.15),
                    Point(x=(i + 1) * wall_len - 0.15, y=(j + 1) * wall_len - 0.15),
                    Point(x=i * wall_len + 0.15, y=(j + 1) * wall_len - 0.15),
                ],
            )
        )

plan_interior = InteriorPlan(
    title=f"Интерьер: {room_count} помещений",
    walls=walls,
    rooms=rooms,
    paper_format="A0",
    orientation="landscape",
)

from theodolite_mcp.domain.rendering import render_interior_plan

png6 = render_interior_plan(plan_interior)
with open("output/stress_test_interior_64rooms.png", "wb") as f:
    f.write(png6)
print(f"  ✓ Interior {room_count} rooms: {len(png6):,} bytes")

# Test 8: Very long profile (thousands of stations)
print("\n[8] Testing long profile (500 stations)...")
from theodolite_mcp.domain.models import ProfilePlan, ProfilePoint
import numpy as np

stations = np.linspace(0, 5000, 500)
ground_z = (
    100 + 0.001 * stations + 5 * np.sin(stations / 200) + np.random.normal(0, 0.1, 500)
)
design_z = 100 + 0.001 * stations

points = [
    ProfilePoint(
        station=float(s),
        ground_z=float(g),
        design_z=float(d),
        segment_type="cut" if g > d else "fill",
    )
    for s, g, d in zip(stations, ground_z, design_z)
]

plan_profile = ProfilePlan(
    title="Длинный профиль (500 станций)",
    points=points,
    paper_format="A2",
    orientation="landscape",
)

from theodolite_mcp.domain.rendering import render_profile_plan

png7 = render_profile_plan(plan_profile)
with open("output/stress_test_long_profile.png", "wb") as f:
    f.write(png7)
print(f"  ✓ Profile 500 stations: {len(png7):,} bytes")

# Summary
print("\n" + "=" * 60)
print("STRESS TEST COMPLETE")
print("=" * 60)
print("\nGenerated files:")
test_files = [
    "output/stress_test_50_zones.png",
    "output/stress_test_dense_points.png",
    "output/stress_test_mixed_scales.png",
    "output/stress_test_short_segments.png",
    "output/stress_test_shipbuilding.png",
    "output/stress_test_interior_64rooms.png",
    "output/stress_test_long_profile.png",
]
for f in test_files:
    size = os.path.getsize(f)
    print(f"  {f:60s}  {size:>10,} bytes")

print("\n✅ All rendering stress tests passed!")
print("Check output/ directory for generated images.")
