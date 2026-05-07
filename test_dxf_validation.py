#!/usr/bin/env python3
"""Test the DXF validator on a sample file."""

import sys
from pathlib import Path
import ezdxf

# Create a sample DXF with intentional issues
doc = ezdxf.new("R2010")
msp = doc.modelspace()

# Add layers
doc.layers.add(name="0_BOUNDARY", color=7)
doc.layers.add(name="0_POINTS", color=1)
doc.layers.add(name="ZONE_BUILDINGS", color=4)
doc.layers.add(name="UNKNOWN_LAYER", color=2)  # Should trigger warning

# Add a valid polyline (boundary)
msp.add_lwpolyline(
    [(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)],
    close=True,
    dxfattribs={"layer": "0_BOUNDARY"},
)

# Add a zero-length line (should trigger warning)
msp.add_line((20, 20), (20, 20), dxfattribs={"layer": "0_POINTS"})

# Add a POINT with no explicit layer — should become default "0" layer, which is unexpected in our context (warning)
msp.add_point((5, 5))  # no layer specified (will use layer "0")

# Add overlapping polylines (self-intersection-ish)
msp.add_lwpolyline(
    [(30, 0), (40, 10), (30, 20), (40, 30)], dxfattribs={"layer": "ZONE_BUILDINGS"}
)
# Share vertex with above
msp.add_lwpolyline([(30, 0), (40, 30), (50, 0)], dxfattribs={"layer": "ZONE_BUILDINGS"})

# Add text with empty content (should trigger warning)
msp.add_text("", dxfattribs={"layer": "0_BOUNDARY", "height": 1.0}).set_placement(
    (50, 50)
)

# Add text with NaN
msp.add_text("NaN", dxfattribs={"layer": "0_POINTS", "height": 1.0}).set_placement(
    (60, 60)
)

# Add text with infinity
msp.add_text("Inf", dxfattribs={"layer": "0_POINTS", "height": 1.0}).set_placement(
    (70, 70)
)

# Add text far away
msp.add_text("Far label", dxfattribs={"layer": "0_TEXT", "height": 1.0}).set_placement(
    (1e10, 1e10)
)

# Save
test_path = Path("test_validation.dxf")
doc.saveas(test_path)
print(f"Created test DXF: {test_path.absolute()}")

# Now validate it
sys.path.insert(0, str(Path(__file__).parent / "src"))
from theodolite_mcp.domain.dxf_validation import validate_dxf_file

report = validate_dxf_file(str(test_path), check_geometry=True)
print("\n" + report.summary())
print("\nDetailed issues:")
for issue in report.issues:
    loc = (
        f" ({issue.location[0]:.1f}, {issue.location[1]:.1f})" if issue.location else ""
    )
    print(
        f"  [{issue.severity.value}] {issue.entity_type}/{issue.layer or 'no-layer'}: {issue.message}{loc}"
    )

# Cleanup
test_path.unlink(missing_ok=True)
print("\nTest complete.")
