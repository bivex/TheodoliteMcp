#!/usr/bin/env python3
"""
Large demo cadastral plan for Atlas Weekend music festival.
Generates a complex site plan with multiple zones, roads, stages, camping areas, etc.
Tests rendering performance and DXF export quality.
"""

import sys
import math
import time
from pathlib import Path
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from theodolite_mcp.domain.models import PlotPlan, Point, Zone
from theodolite_mcp.application.services import SurveyService
from theodolite_mcp.domain.dxf_validation import validate_dxf_file

svc = SurveyService()

print("Generating large Atlas Weekend festival site plan...")
start = time.time()

# Generate a realistic festival layout (~1km x 800m)
# Coordinate system: origin at southwest corner

boundary_pts = []
# Outer boundary: roughly rectangular but with some irregularity
for i in range(40):
    angle = 2 * math.pi * i / 40
    # Slightly irregular shape
    rx = 500 + 30 * math.sin(angle * 3)  # ~1000m wide
    ry = 400 + 20 * math.cos(angle * 2)  # ~800m tall
    boundary_pts.append(Point(x=rx, y=ry, name=f"B{i + 1}"))

print(f"  Boundary: {len(boundary_pts)} vertices")

# Create zones
zones = []

# 1. Main Stage Area
main_stage = Zone(
    name="Main Stage",
    points=[
        Point(x=450, y=350),
        Point(x=550, y=350),
        Point(x=550, y=400),
        Point(x=450, y=400),
    ],
)
zones.append(main_stage)

# 2. Second Stage
stage2 = Zone(
    name="Second Stage",
    points=[
        Point(x=200, y=350),
        Point(x=300, y=350),
        Point(x=300, y=400),
        Point(x=200, y=400),
    ],
)
zones.append(stage2)

# 3. Main Gate / Entrance
gate = Zone(
    name="Main Gate",
    points=[
        Point(x=480, y=20),
        Point(x=520, y=20),
        Point(x=520, y=60),
        Point(x=480, y=60),
    ],
)
zones.append(gate)

# 4. Camping Area North
camp_n = Zone(
    name="Camping North",
    points=[
        Point(x=100, y=600),
        Point(x=300, y=600),
        Point(x=300, y=780),
        Point(x=100, y=780),
    ],
)
zones.append(camp_n)

# 5. Camping Area South
camp_s = Zone(
    name="Camping South",
    points=[
        Point(x=700, y=600),
        Point(x=900, y=600),
        Point(x=900, y=780),
        Point(x=700, y=780),
    ],
)
zones.append(camp_s)

# 6. VIP Zone (central)
vip = Zone(
    name="VIP Zone",
    points=[
        Point(x=400, y=300),
        Point(x=480, y=300),
        Point(x=480, y=380),
        Point(x=400, y=380),
    ],
)
zones.append(vip)

# 7. Food Court
food = Zone(
    name="Food Court",
    points=[
        Point(x=600, y=250),
        Point(x=700, y=250),
        Point(x=700, y=330),
        Point(x=600, y=330),
    ],
)
zones.append(food)

# 8. Vendor Market
market = Zone(
    name="Vendor Market",
    points=[
        Point(x=300, y=250),
        Point(x=390, y=250),
        Point(x=390, y=330),
        Point(x=300, y=330),
    ],
)
zones.append(market)

# 9. Water Feature (Lake/River)
water = Zone(
    name="Water Feature",
    points=[
        Point(x=50, y=200),
        Point(x=150, y=200),
        Point(x=180, y=280),
        Point(x=120, y=350),
        Point(x=60, y=300),
    ],
)
zones.append(water)

# 10. Chill-out / Art Zone
chill = Zone(
    name="Chill-out Zone",
    points=[
        Point(x=750, y=200),
        Point(x=850, y=200),
        Point(x=850, y=300),
        Point(x=750, y=300),
    ],
)
zones.append(chill)

# 11. Medical Center (doesn't share vertices with gate — slight gap to avoid warning)
medical = Zone(
    name="Medical Center",
    points=[
        Point(x=525, y=60),
        Point(x=565, y=60),
        Point(x=565, y=100),
        Point(x=525, y=100),
    ],
)
zones.append(medical)

# 12. Parking Lot East
park_e = Zone(
    name="Parking East",
    points=[
        Point(x=920, y=350),
        Point(x=980, y=350),
        Point(x=980, y=750),
        Point(x=920, y=750),
    ],
)
zones.append(park_e)

# 13. Parking Lot West
park_w = Zone(
    name="Parking West",
    points=[
        Point(x=20, y=350),
        Point(x=80, y=350),
        Point(x=80, y=750),
        Point(x=20, y=750),
    ],
)
zones.append(park_w)

# 14. Service Area (behind stages)
service = Zone(
    name="Service Area",
    points=[
        Point(x=420, y=400),
        Point(x=580, y=400),
        Point(x=580, y=500),
        Point(x=420, y=500),
    ],
)
zones.append(service)

# 15. Green Park
green = Zone(
    name="Green Park",
    points=[
        Point(x=200, y=100),
        Point(x=380, y=100),
        Point(x=380, y=200),
        Point(x=200, y=200),
    ],
)
zones.append(green)

print(f"  Zones: {len(zones)}")

# Create the plan
plan = PlotPlan(
    title="Atlas Weekend 2026 — Festival Site Plan",
    boundary_points=boundary_pts,
    zones=zones,
    show_vertex_labels=False,
    show_distances=True,
    show_azimuths=True,
    show_areas=True,
    show_north_arrow=True,
    show_scale_bar=True,
    coordinate_labels=False,
    dpi=200,  # High resolution for large plan
)

# --- Render to PNG ---
print("Rendering to PNG...")
png_start = time.time()
png_bytes = svc.render_plot(plan, output_format="png")
png_time = time.time() - png_start
print(f"  PNG size: {len(png_bytes):,} bytes, time: {png_time:.2f}s")

out_dir = Path("output")
out_dir.mkdir(exist_ok=True)
png_path = out_dir / "atlas_weekend_plan.png"
with open(png_path, "wb") as f:
    f.write(png_bytes)
print(f"  Saved: {png_path}")

# --- Export to DXF ---
print("Exporting to DXF...")
dxf_start = time.time()
dxf_path = out_dir / "atlas_weekend_plan.dxf"
svc.export_dxf(plan, str(dxf_path))
dxf_time = time.time() - dxf_start
print(f"  DXF export time: {dxf_time:.2f}s")

# --- Validate DXF ---
print("Validating DXF...")
val_start = time.time()
report = svc.validate_dxf(str(dxf_path), check_geometry=True)
val_time = time.time() - val_start
print(f"  Validation time: {val_time:.2f}s")
print(
    f"  Valid: {report.is_valid} | Errors: {len(report.errors)} | Warnings: {len(report.warnings)}"
)
if report.issues:
    print("  Issues:")
    for iss in report.issues[:10]:  # Show first 10
        print(f"    [{iss.severity.value}] {iss.entity_type}: {iss.message}")
    if len(report.issues) > 10:
        print(f"    ... and {len(report.issues) - 10} more")

# --- Render to SVG ---
print("Rendering to SVG...")
svg_start = time.time()
svg_bytes = svc.render_plot(plan, output_format="svg")
svg_time = time.time() - svg_start
svg_len = len(svg_bytes)
print(f"  SVG size: {svg_len:,} bytes, time: {svg_time:.2f}s")

svg_path = out_dir / "atlas_weekend_plan.svg"
with open(svg_path, "wb") as f:
    f.write(svg_bytes)
print(f"  Saved: {svg_path}")

total = time.time() - start
print(f"\nTotal time: {total:.2f}s")
print(
    f"  PNG: {png_time:.2f}s | DXF: {dxf_time:.2f}s | VAL: {val_time:.2f}s | SVG: {svg_time:.2f}s"
)
print("\nDone. Large Atlas Weekend demo plan generated successfully.")
