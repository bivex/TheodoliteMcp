import os
from theodolite_mcp.domain.models import Point, Wall, Opening, Room, InteriorPlan, FurnitureItem
from theodolite_mcp.domain.rendering import render_interior_plan

def create_full_apartment_demo():
    print("🛋 Generating Full Professional Apartment Plan...")

    # 1. Walls
    walls = [
        Wall(start_pt=Point(x=0, y=0), end_pt=Point(x=6, y=0), thickness=0.3),
        Wall(start_pt=Point(x=6, y=0), end_pt=Point(x=6, y=5), thickness=0.3, openings=[Opening(type="window", start_distance=1.5, width=2.0)]),
        Wall(start_pt=Point(x=6, y=5), end_pt=Point(x=0, y=5), thickness=0.3),
        Wall(start_pt=Point(x=0, y=5), end_pt=Point(x=0, y=0), thickness=0.3, openings=[Opening(type="door", start_distance=0.5, width=0.9)]),
        # Partition
        Wall(start_pt=Point(x=3, y=0), end_pt=Point(x=3, y=3), thickness=0.12, openings=[Opening(type="door", start_distance=0.5, width=0.8)]),
        Wall(start_pt=Point(x=3, y=3), end_pt=Point(x=0, y=3), thickness=0.12),
    ]

    # 2. Furniture & Sanitary
    furniture = [
        FurnitureItem(type="bed", center_pt=Point(x=4.5, y=1.2), width=1.6, length=2.0, rotation=0),
        FurnitureItem(type="sofa", center_pt=Point(x=4.5, y=3.8), width=2.2, length=0.9, rotation=180),
        FurnitureItem(type="wc", center_pt=Point(x=0.5, y=3.5), width=0.4, length=0.6, rotation=90),
        FurnitureItem(type="bath", center_pt=Point(x=2.0, y=4.5), width=1.7, length=0.75, rotation=0),
        FurnitureItem(type="stove", center_pt=Point(x=0.5, y=0.5), width=0.6, length=0.6, rotation=0),
    ]

    # 3. Rooms
    rooms = [
        Room(name="Bathroom", number="1", points=[Point(x=0.15, y=3.15), Point(x=2.85, y=3.15), Point(x=2.85, y=4.85), Point(x=0.15, y=4.85)]),
        Room(name="Bedroom", number="2", points=[Point(x=3.15, y=0.15), Point(x=5.85, y=0.15), Point(x=5.85, y=4.85), Point(x=3.15, y=4.85)]),
        Room(name="Kitchen/Hall", number="3", points=[Point(x=0.15, y=0.15), Point(x=2.85, y=0.15), Point(x=2.85, y=2.85), Point(x=0.15, y=2.85)]),
    ]

    plan = InteriorPlan(
        title="PROFESSIONAL INTERIOR LAYOUT",
        walls=walls,
        furniture=furniture,
        rooms=rooms,
        language="en",
        paper_format="A4",
        scale=50
    )

    png_bytes = render_interior_plan(plan)
    output_path = os.path.join("output", "professional_interior_full.png")
    
    os.makedirs("output", exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(png_bytes)

    print(f"✅ Professional interior plan generated: {output_path}")

if __name__ == "__main__":
    create_full_apartment_demo()
