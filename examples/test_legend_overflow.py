import os
from theodolite_mcp.domain.models import Point, Zone, PlotPlan
from theodolite_mcp.domain.rendering import render_plot_plan

def test_legend_overflow():
    print("🧪 Testing Legend Overflow (20 Zones)...")
    
    # 1. Create a large boundary
    boundary = [Point(x=0, y=0), Point(x=100, y=0), Point(x=100, y=100), Point(x=0, y=100)]
    
    # 2. Generate 20 zones
    zones = []
    for i in range(20):
        # Small squares
        x = (i % 5) * 10 + 5
        y = (i // 5) * 10 + 5
        pts = [Point(x=x, y=y), Point(x=x+5, y=y), Point(x=x+5, y=y+5), Point(x=x, y=y+5)]
        zones.append(Zone(name=f"Test Zone {i+1}", points=pts))
        
    plan = PlotPlan(
        title="LEGEND OVERFLOW STRESS TEST",
        boundary_points=boundary,
        zones=zones,
        language="en",
        paper_format="A3"
    )
    
    # 3. Render
    png_bytes = render_plot_plan(plan)
    output_path = os.path.join("output", "test_legend_overflow.png")
    
    os.makedirs("output", exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(png_bytes)
        
    print(f"✅ Overflow test generated: {output_path}")
    print("🔍 Please verify that the legend shows exactly 14 items + '... and others'.")

if __name__ == "__main__":
    test_legend_overflow()
