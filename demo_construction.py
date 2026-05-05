import os
from theodolite_mcp.domain.models import Point, Zone, PlotPlan
from theodolite_mcp.domain.rendering import render_plot_plan

def create_construction_demo():
    print("🏗 Generating Construction Site Plan...")

    # 1. Define Boundary Points (Main Plot)
    boundary = [
        Point(name="1", x=0.0, y=0.0),
        Point(name="2", x=50.0, y=0.0),
        Point(name="3", x=50.0, y=80.0),
        Point(name="4", x=20.0, y=80.0),
        Point(name="5", x=0.0, y=60.0),
        Point(name="1", x=0.0, y=0.0) # Closed loop
    ]

    # 2. Define Zones
    # Zone A: Main Building
    building_points = [
        Point(name="A1", x=10.0, y=20.0),
        Point(name="A2", x=40.0, y=20.0),
        Point(name="A3", x=40.0, y=50.0),
        Point(name="A4", x=10.0, y=50.0),
        Point(name="A1", x=10.0, y=20.0)
    ]
    
    # Zone B: Parking/Driveway
    driveway_points = [
        Point(name="P1", x=5.0, y=0.0),
        Point(name="P2", x=45.0, y=0.0),
        Point(name="P3", x=45.0, y=15.0),
        Point(name="P4", x=5.0, y=15.0),
        Point(name="P1", x=5.0, y=0.0)
    ]

    zones = [
        Zone(name="Building Foundation", points=building_points, fill_color="salmon"),
        Zone(name="Parking Area", points=driveway_points, fill_color="lightgray")
    ]

    # 3. Create PlotPlan object
    plan = PlotPlan(
        title="Industrial Site Layout",
        project_number="CON-2026-004",
        organization="Global Engineering Corp",
        boundary_points=boundary,
        zones=zones,
        language="en",
        standard="construction",
        paper_format="A3",
        orientation="landscape",
        show_vertex_labels=True,
        show_distances=True,
        show_azimuths=True,
        show_areas=True,
        show_north_arrow=True,
        show_scale_bar=True,
        coordinate_labels=True
    )

    # 4. Render to PNG
    png_bytes = render_plot_plan(plan)

    # 5. Save to file
    output_path = "construction_site_plan.png"
    with open(output_path, "wb") as f:
        f.write(png_bytes)

    print(f"✅ Construction plan generated: {output_path}")

if __name__ == "__main__":
    create_construction_demo()
