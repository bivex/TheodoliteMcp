import os
from theodolite_mcp.domain.models import Point, Zone, PlotPlan
from theodolite_mcp.domain.rendering import render_plot_plan

def create_cadastral_demo():
    print("📜 Generating Cadastral Land Survey Plan...")

    # 1. Define Boundary Points (Land Parcel)
    # Using more "realistic" coordinates for a land parcel
    boundary = [
        Point(name="Corner-1", x=1250.45, y=3420.10),
        Point(name="Corner-2", x=1310.20, y=3415.80),
        Point(name="Corner-3", x=1325.00, y=3480.50),
        Point(name="Corner-4", x=1260.15, y=3495.25),
        Point(name="Corner-1", x=1250.45, y=3420.10) # Closed
    ]

    # 2. Define Zones (e.g., Easements or Restricted Areas)
    # Zone 1: Utility Easement (along the north boundary)
    easement_points = [
        Point(name="E1", x=1260.15, y=3495.25),
        Point(name="E2", x=1325.00, y=3480.50),
        Point(name="E3", x=1320.00, y=3475.00),
        Point(name="E4", x=1265.00, y=3488.00),
        Point(name="E1", x=1260.15, y=3495.25)
    ]

    zones = [
        Zone(name="Utility Easement", points=easement_points, fill_color="lightgreen")
    ]

    # 3. Create PlotPlan object
    # For Cadastral plans, coordinate_labels are often very important
    plan = PlotPlan(
        title="Land Parcel Survey - Lot 42",
        project_number="CAD-SURV-2026-08",
        organization="Municipal Land Registry",
        boundary_points=boundary,
        zones=zones,
        language="en",
        standard="construction", # Using construction styles as baseline for land survey
        paper_format="A3",
        orientation="landscape",
        show_vertex_labels=True,
        show_distances=True,
        show_azimuths=True,
        show_areas=True,
        show_north_arrow=True,
        show_scale_bar=True,
        coordinate_labels=True, # Show X/Y on vertex labels
        width_inches=12.0,
        height_inches=10.0
    )

    # 4. Render to PNG
    png_bytes = render_plot_plan(plan)

    # 5. Save to file
    output_path = "cadastral_survey_plan.png"
    with open(output_path, "wb") as f:
        f.write(png_bytes)

    print(f"✅ Cadastral plan generated: {output_path}")

if __name__ == "__main__":
    create_cadastral_demo()
