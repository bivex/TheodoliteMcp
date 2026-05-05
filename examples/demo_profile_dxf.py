import os
from theodolite_mcp.domain.models import ProfilePoint, ProfilePlan
from theodolite_mcp.domain.dxf_export import export_profile_to_dxf

def test_profile_dxf_export():
    print("📈 Testing Profile DXF Export...")
    
    points = [
        ProfilePoint(station=0, ground_z=150.20, design_z=148.50),
        ProfilePoint(station=100, ground_z=152.00, design_z=149.00),
        ProfilePoint(station=250, ground_z=148.50, design_z=149.50),
        ProfilePoint(station=400, ground_z=150.00, design_z=150.00),
    ]
    
    plan = ProfilePlan(
        title="DXF Export Test Profile",
        points=points,
        horiz_scale=1000,
        vert_scale=100
    )
    
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    dxf_path = os.path.join(output_dir, "profile_interop_test.dxf")
    
    path = export_profile_to_dxf(plan, dxf_path)
    
    if os.path.exists(path):
        print(f"✅ Profile DXF successfully generated: {os.path.abspath(path)}")
        print("📂 Layers included: V-PROF-GROUND, V-PROF-DESIGN, V-PROF-ORDINATES, V-PROF-TABLE")
    else:
        print("❌ Profile DXF generation failed.")

if __name__ == "__main__":
    test_profile_dxf_export()
