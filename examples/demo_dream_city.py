import os
from theodolite_mcp.domain.models import Point, Zone, PlotPlan
from theodolite_mcp.domain.rendering import render_plot_plan

def create_dream_city_showcase():
    print("🏙 Generating 'Dream City' Material Showcase Plan...")

    # 1. Main City Boundary (A2 Format scale)
    boundary = [
        Point(name="N1", x=0, y=0),
        Point(name="N2", x=200, y=0),
        Point(name="N3", x=200, y=150),
        Point(name="N4", x=0, y=150),
        Point(name="N1", x=0, y=0)
    ]

    # 2. Zones representing different materials per ISO 128-50
    zones = [
        # Residential Area
        Zone(name="Brick Residential Block", 
             points=[Point(name="B1", x=10, y=100), Point(name="B2", x=40, y=100), 
                     Point(name="B3", x=40, y=130), Point(name="B4", x=10, y=130)],
             fill_color="#FFCCBC"),
        
        # Industrial Area
        Zone(name="Steel Metal Factory", 
             points=[Point(name="M1", x=150, y=100), Point(name="M2", x=190, y=100), 
                     Point(name="M3", x=190, y=140), Point(name="M4", x=150, y=140)],
             fill_color="#B0BEC5"),
             
        # Construction Site
        Zone(name="Concrete Foundation Site", 
             points=[Point(name="C1", x=150, y=10), Point(name="C2", x=190, y=10), 
                     Point(name="C3", x=190, y=40), Point(name="C4", x=150, y=40)],
             fill_color="#ECEFF1"),

        # Recreation & Nature
        Zone(name="City Central Lake (Water)", 
             points=[Point(name="W1", x=70, y=60), Point(name="W2", x=130, y=60), 
                     Point(name="W3", x=130, y=90), Point(name="W4", x=70, y=90)],
             fill_color="#B3E5FC"),
             
        Zone(name="Sandy Beach Area", 
             points=[Point(name="S1", x=70, y=50), Point(name="S2", x=130, y=50), 
                     Point(name="S3", x=130, y=60), Point(name="S4", x=70, y=60)],
             fill_color="#FFF9C4"),
             
        Zone(name="Main City Park (Trees)", 
             points=[Point(name="T1", x=10, y=10), Point(name="T2", x=60, y=10), 
                     Point(name="T3", x=60, y=60), Point(name="T4", x=10, y=60)],
             fill_color="#C8E6C9"),
             
        Zone(name="Grass Lawn & Garden", 
             points=[Point(name="G1", x=10, y=60), Point(name="G2", x=60, y=60), 
                     Point(name="G3", x=60, y=80), Point(name="G4", x=10, y=80)],
             fill_color="#DCEDC8"),

        # Infrastructure
        Zone(name="Asphalt Paving / Parking", 
             points=[Point(name="P1", x=80, y=100), Point(name="P2", x=120, y=100), 
                     Point(name="P3", x=120, y=140), Point(name="P4", x=80, y=140)],
             fill_color="#F5F5F5"),
             
        Zone(name="Wooden Pier (Timber)", 
             points=[Point(name="WD1", x=130, y=70), Point(name="WD2", x=145, y=70), 
                     Point(name="WD3", x=145, y=80), Point(name="WD4", x=130, y=80)],
             fill_color="#D7CCC8"),
             
        # Modern Architecture
        Zone(name="Glass Greenhouse", 
             points=[Point(name="GL1", x=70, y=10), Point(name="GL2", x=100, y=10), 
                     Point(name="GL3", x=100, y=30), Point(name="GL4", x=70, y=30)],
             fill_color="#E1F5FE"),
             
        Zone(name="Plastic Polymer Lab", 
             points=[Point(name="PL1", x=110, y=10), Point(name="PL2", x=140, y=10), 
                     Point(name="PL3", x=140, y=30), Point(name="PL4", x=110, y=30)],
             fill_color="#F3E5F5"),
             
        Zone(name="Deep Soil / Earth excavation", 
             points=[Point(name="ER1", x=10, y=85), Point(name="ER2", x=40, y=85), 
                     Point(name="ER3", x=40, y=95), Point(name="ER4", x=10, y=95)],
             fill_color="#EFEBE9"),
    ]

    # 3. Create PlotPlan (A2 Landscape for maximum detail)
    plan = PlotPlan(
        title="DREAM CITY - ISO 128-50 MATERIAL SHOWCASE",
        project_number="ISO-SHOW-2026",
        organization="Gemini Engineering Labs",
        boundary_points=boundary,
        zones=zones,
        language="en",
        standard="construction",
        paper_format="A2",
        orientation="landscape",
        show_vertex_labels=False, # Focus on materials
        show_distances=True,
        show_azimuths=False,
        show_areas=True,
        show_north_arrow=True,
        show_scale_bar=True,
        coordinate_labels=False
    )

    # 4. Render and Save
    png_bytes = render_plot_plan(plan)
    output_path = os.path.join("output", "dream_city_plan.png")
    with open(output_path, "wb") as f:
        f.write(png_bytes)

    print(f"✅ 'Dream City' generated: {output_path}")

if __name__ == "__main__":
    create_dream_city_showcase()
