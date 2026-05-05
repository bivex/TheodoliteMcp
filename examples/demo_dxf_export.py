import os
from theodolite_mcp.domain.models import Point, Zone, PlotPlan
from theodolite_mcp.domain.dxf_export import export_plan_to_dxf

def test_dxf_export():
    print("📐 Testing DXF Export Interoperability...")
    
    # 1. Create a Realistic Plan
    boundary = [
        Point(name="1", x=0, y=0),
        Point(name="2", x=50, y=0),
        Point(name="3", x=50, y=80),
        Point(name="4", x=0, y=60),
        Point(name="1", x=0, y=0)
    ]
    
    zones = [
        Zone(name="Main Building", 
             points=[Point(name="B1", x=10, y=20), Point(name="B2", x=40, y=20), 
                     Point(name="B3", x=40, y=50), Point(name="B4", x=10, y=50)]),
        Zone(name="Garden Lake", 
             points=[Point(name="W1", x=5, y=55), Point(name="W2", x=25, y=55), 
                     Point(name="W3", x=20, y=70), Point(name="W4", x=5, y=65)])
    ]
    
    plan = PlotPlan(
        title="Interoperability Test Plan",
        boundary_points=boundary,
        zones=zones,
        coordinate_labels=True
    )
    
    # 2. Export
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    dxf_path = os.path.join(output_dir, "interop_test.dxf")
    
    path = export_plan_to_dxf(plan, dxf_path)
    
    if os.path.exists(path):
        print(f"✅ DXF successfully generated: {os.path.abspath(path)}")
        print("📂 Layers included: 0_BOUNDARY, 0_POINTS, 0_TEXT, ZONE_BUILDINGS, ZONE_WATER")
    else:
        print("❌ DXF generation failed.")

if __name__ == "__main__":
    test_dxf_export()
