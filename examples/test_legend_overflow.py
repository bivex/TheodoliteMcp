import os
from theodolite_mcp.domain.models import Point, Zone, PlotPlan
from theodolite_mcp.domain.rendering import render_plot_plan

def test_legend_overflow():
    print("🧪 Testing Dynamic Legend Scaling (50 Zones)...")
    
    # 1. Create a large boundary
    boundary = [Point(x=0, y=0), Point(x=200, y=0), Point(x=200, y=200), Point(x=0, y=200)]
    
    # 2. Generate 50 zones
    zones = []
    for i in range(50):
        x = (i % 10) * 15 + 5
        y = (i // 10) * 15 + 5
        pts = [Point(x=x, y=y), Point(x=x+10, y=y), Point(x=x+10, y=y+10), Point(x=x, y=y+10)]
        zones.append(Zone(name=f"Unit Room {i+1}", points=pts))
        
    plan = PlotPlan(
        title="LEGEND EXTREME SCALING TEST (50 ITEMS)",
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
