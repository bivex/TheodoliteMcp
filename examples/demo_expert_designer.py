import os
import json
from theodolite_mcp.domain.models import Point, Wall, Opening, Room, InteriorPlan, FurnitureItem, EngineeringItem, DimensionLine
from theodolite_mcp.domain.rendering import render_interior_plan
from theodolite_mcp.application.services import SurveyService

def create_expert_designer_demo():
    print("🚀 Generating Expert Interior Designer Demo...")
    service = SurveyService()

    # 1. Walls
    walls = [
        Wall(start_pt=Point(x=0, y=0), end_pt=Point(x=6, y=0), thickness=0.3),
        Wall(start_pt=Point(x=6, y=0), end_pt=Point(x=6, y=5), thickness=0.3),
        Wall(start_pt=Point(x=6, y=5), end_pt=Point(x=0, y=5), thickness=0.3),
        Wall(start_pt=Point(x=0, y=5), end_pt=Point(x=0, y=0), thickness=0.3),
    ]

    # 2. Rooms with FLOOR TEXTURES
    rooms = [
        Room(
            name="Bathroom", number="1", floor_material="Ceramic Tile",
            floor_pattern="tiles", floor_tile_size=[0.6, 0.6], floor_angle=45,
            points=[Point(x=0.3, y=0.3), Point(x=2.5, y=0.3), Point(x=2.5, y=4.7), Point(x=0.3, y=4.7)]
        ),
        Room(
            name="Living Room", number="2", floor_material="Oak Parquet",
            floor_pattern="planks", floor_tile_size=[1.2, 0.2], floor_angle=0,
            points=[Point(x=2.7, y=0.3), Point(x=5.7, y=0.3), Point(x=5.7, y=4.7), Point(x=2.7, y=4.7)]
        ),
    ]

    # 3. Furniture with ERGONOMICS checks
    furniture = [
        # Bed with 0.6m required clearance (padding)
        FurnitureItem(
            type="bed", center_pt=Point(x=4.2, y=2.5), width=1.6, length=2.0, 
            rotation=90, label="Master Bed", ergonomics_padding=0.6
        ),
        # WC with 0.4m clearance
        FurnitureItem(
            type="wc", center_pt=Point(x=1.0, y=4.0), width=0.4, length=0.6, 
            rotation=0, ergonomics_padding=0.4
        ),
    ]

    # 4. Plan with show_ergonomics=True
    plan = InteriorPlan(
        title="EXPERT DESIGNER PLAN",
        walls=walls,
        rooms=rooms,
        furniture=furniture,
        show_ergonomics=True,
        paper_format="A4",
        scale=50
    )

    output_dir = "output/expert_demo"
    os.makedirs(output_dir, exist_ok=True)

    # Render Image
    png_bytes = render_interior_plan(plan)
    with open(os.path.join(output_dir, "expert_plan_textures.png"), "wb") as f:
        f.write(png_bytes)
    print("✅ Expert Plan with Textures generated: output/expert_demo/expert_plan_textures.png")

    # Generate Specifications (BOM)
    report = service.generate_interior_report(plan)
    with open(os.path.join(output_dir, "specifications.json"), "w") as f:
        json.dump(report.model_dump(), f, indent=2)
    print("✅ Specifications JSON generated: output/expert_demo/specifications.json")
    
    # Print some highlights from the report
    print("\n--- MATERIAL ESTIMATES ---")
    for room, tiles in report.tile_counts.items():
        print(f"Room: {room}")
        print(f"  Total Tiles (600x600) needed: {tiles['total']} (includes 15% waste)")
        print(f"  Estimated cut tiles: {tiles['cut']}")

if __name__ == "__main__":
    create_expert_designer_demo()
