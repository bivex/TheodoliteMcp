#!/usr/bin/env python3
"""
Stress test: Very large boundary with many vertices.
"""

import sys, time, math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from theodolite_mcp.domain.models import PlotPlan, Point, Zone
from theodolite_mcp.application.services import SurveyService

svc = SurveyService()

# Generate a high-resolution boundary (200 points)
print("Generating huge boundary (200 vertices)...")
boundary = []
for i in range(200):
    angle = 2 * 3.14159 * i / 200
    x = 1000 + 500 * math.cos(angle) + 50 * math.sin(angle * 7)
    y = 800 + 400 * math.sin(angle) + 40 * math.cos(angle * 5)
    boundary.append(Point(x=x, y=y, name=f"P{i + 1}"))

# Add 50 zones (small irregular polygons)
print("Generating 50 zones...")
zones = []
for i in range(50):
    cx = 200 + (i % 10) * 80
    cy = 200 + (i // 10) * 80
    pts = []
    for j in range(8):
        a = 2 * 3.14159 * j / 8
        pts.append(
            Point(
                x=cx + 30 * math.cos(a),
                y=cy + 30 * math.sin(a),
                name=f"Z{i + 1}_{j + 1}",
            )
        )
    zones.append(Zone(name=f"Sector {i + 1}", points=pts))

plan = PlotPlan(
    title="Huge Atlas Stress Test — 200-vertex boundary + 50 zones",
    boundary_points=boundary,
    zones=zones,
    show_vertex_labels=False,
    coordinate_labels=False,
    dpi=300,
)

print(f"Total points: {len(boundary) + sum(len(z.points) for z in zones)}")

# PNG
print("Rendering PNG...")
t0 = time.time()
png = svc.render_plot(plan, output_format="png")
print(f"  PNG: {len(png):,} bytes in {time.time() - t0:.2f}s")

# SVG
print("Rendering SVG...")
t0 = time.time()
svg = svc.render_plot(plan, output_format="svg")
print(f"  SVG: {len(svg):,} bytes in {time.time() - t0:.2f}s")

# DXF
print("Exporting DXF...")
t0 = time.time()
dxf_path = "output/huge_atlas.dxf"
svc.export_dxf(plan, dxf_path)
print(
    f"  DXF: {Path(dxf_path).stat().st_size / 1024:.1f} KB in {time.time() - t0:.2f}s"
)

# Validation
print("Validating DXF...")
t0 = time.time()
rep = svc.validate_dxf(dxf_path)
print(
    f"  Valid: {rep.is_valid}, Errors: {len(rep.errors)}, Warnings: {len(rep.warnings)} in {time.time() - t0:.3f}s"
)

print("\n✓ Stress test complete.")
