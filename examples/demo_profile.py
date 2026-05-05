import os
from theodolite_mcp.domain.models import ProfilePoint, ProfilePlan
from theodolite_mcp.domain.rendering import render_profile_plan

def create_pipeline_profile_demo():
    print("📈 Generating Pipeline Longitudinal Profile...")

    # 1. Define Profile Data (Pipeline route)
    # Stations from 0 to 500 meters
    points = [
        ProfilePoint(station=0, ground_z=150.20, design_z=148.50, remark="Start Node"),
        ProfilePoint(station=50, ground_z=151.10, design_z=148.80),
        ProfilePoint(station=120, ground_z=153.50, design_z=149.20, remark="Hill Top"),
        ProfilePoint(station=200, ground_z=152.00, design_z=149.60),
        ProfilePoint(station=300, ground_z=148.50, design_z=150.00, remark="River Crossing"),
        ProfilePoint(station=450, ground_z=149.80, design_z=150.50),
        ProfilePoint(station=500, ground_z=150.50, design_z=150.80, remark="End Node"),
    ]

    # 2. Create ProfilePlan
    plan = ProfilePlan(
        title="MAIN WATER PIPELINE - SECTION A-B",
        project_number="PIPE-2026-001",
        organization="Municipal Water Works",
        points=points,
        language="ru",
        paper_format="A3",
        horiz_scale=1000,
        vert_scale=100
    )

    # 3. Render and Save
    png_bytes = render_profile_plan(plan)
    output_path = os.path.join("output", "pipeline_profile.png")
    
    os.makedirs("output", exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(png_bytes)

    print(f"✅ Pipeline profile generated: {output_path}")

if __name__ == "__main__":
    create_pipeline_profile_demo()
