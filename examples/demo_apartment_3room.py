import os
from theodolite_mcp.domain.models import Point, Wall, Opening, Room, InteriorPlan, FurnitureItem, EngineeringItem, DimensionLine
from theodolite_mcp.domain.rendering import render_interior_plan

def create_3room_apartment():
    print("🏢 Creating a 3-Room Family Apartment Layout (approx 120 sqm)...")

    # 1. Perimeter Walls (12m x 10m)
    walls = [
        Wall(start_pt=Point(x=0, y=0), end_pt=Point(x=12, y=0), thickness=0.3), # Bottom
        Wall(start_pt=Point(x=12, y=0), end_pt=Point(x=12, y=10), thickness=0.3), # Right
        Wall(start_pt=Point(x=12, y=10), end_pt=Point(x=0, y=10), thickness=0.3), # Top
        Wall(start_pt=Point(x=0, y=10), end_pt=Point(x=0, y=0), thickness=0.3), # Left
    ]
    
    # Windows
    walls[2].openings = [
        Opening(type="window", position=1.0, width=2.5), 
        Opening(type="window", position=5.0, width=2.5),
        Opening(type="window", position=9.0, width=2.0)
    ]
    walls[1].openings = [Opening(type="window", position=4.0, width=2.0)]

    # 2. Internal Partitions
    # Hallway and Living room divide
    walls.append(Wall(start_pt=Point(x=4, y=0), end_pt=Point(x=4, y=6), thickness=0.12))
    walls.append(Wall(start_pt=Point(x=0, y=6), end_pt=Point(x=4, y=6), thickness=0.12))
    
    # Master Bedroom divide
    walls.append(Wall(start_pt=Point(x=8, y=0), end_pt=Point(x=8, y=10), thickness=0.12))
    
    # Bathroom and Small Room
    walls.append(Wall(start_pt=Point(x=4, y=4), end_pt=Point(x=8, y=4), thickness=0.12))

    # Internal Doors
    walls[4].openings = [Opening(type="door", position=1.0, width=0.9, direction=1)] # Living room door
    walls[6].openings = [Opening(type="door", position=1.0, width=0.8, direction=-1), # Bedroom door
                         Opening(type="door", position=5.0, width=0.8, direction=-1)] # Small room door
    walls[7].openings = [Opening(type="door", position=1.5, width=0.7, direction=1)] # Bathroom door

    # 3. Rooms with Textures
    rooms = [
        Room(
            name="Living Room & Kitchen", number="1", floor_material="Oak Planks",
            floor_pattern="planks", floor_tile_size=[1.2, 0.2], floor_angle=0,
            points=[Point(x=4.2, y=0.2), Point(x=7.8, y=0.2), Point(x=7.8, y=9.8), Point(x=4.2, y=9.8)]
        ),
        Room(
            name="Master Bedroom", number="2", floor_material="Carpet",
            points=[Point(x=8.2, y=0.2), Point(x=11.8, y=0.2), Point(x=11.8, y=9.8), Point(x=8.2, y=9.8)]
        ),
        Room(
            name="Bathroom", number="3", floor_material="Ceramic Tiles",
            floor_pattern="tiles", floor_tile_size=[0.6, 0.6],
            points=[Point(x=0.2, y=0.2), Point(x=3.8, y=0.2), Point(x=3.8, y=3.8), Point(x=0.2, y=3.8)]
        ),
        Room(
            name="Hallway & Storage", number="4", floor_material="Stone Tiles",
            floor_pattern="grid", floor_tile_size=[0.8, 0.8],
            points=[Point(x=0.2, y=4.2), Point(x=3.8, y=4.2), Point(x=3.8, y=5.8), Point(x=0.2, y=5.8)]
        ),
    ]

    # 4. Furniture
    furniture = [
        # Living Room
        FurnitureItem(type="sofa", center_pt=Point(x=6.0, y=8.0), width=3.0, length=1.0, label="Family Sofa"),
        FurnitureItem(type="stove", center_pt=Point(x=4.5, y=1.0), width=0.6, length=0.6, label="Kitchen Zone"),
        FurnitureItem(type="fridge", center_pt=Point(x=5.2, y=1.0), width=0.6, length=0.6, label="LG Fridge"),
        
        # Bedroom
        FurnitureItem(type="bed", center_pt=Point(x=10.0, y=5.0), width=1.8, length=2.0, rotation=90, label="Master Bed"),
        
        # Bathroom
        FurnitureItem(type="bath", center_pt=Point(x=1.0, y=1.0), width=1.7, length=0.7, rotation=90),
        FurnitureItem(type="wc", center_pt=Point(x=3.0, y=0.5), width=0.4, length=0.6),
        FurnitureItem(type="sink", center_pt=Point(x=3.5, y=2.0), width=0.6, length=0.5, rotation=-90)
    ]

    # 5. Engineering
    engineering = [
        EngineeringItem(type="socket", point=Point(x=4.1, y=8.0), label="TV"),
        EngineeringItem(type="socket", point=Point(x=11.9, y=5.0), label="Bed Power"),
        EngineeringItem(type="lamp", point=Point(x=6.0, y=5.0), label="Main Light"),
        EngineeringItem(type="radiator", point=Point(x=11.9, y=4.0), rotation=90, label="RAD-1")
    ]

    # 6. Dimensions
    dimensions = [
        DimensionLine(points=[Point(x=0, y=-1), Point(x=4, y=-1), Point(x=8, y=-1), Point(x=12, y=-1)], offset=0.5)
    ]

    # 7. Render
    plan = InteriorPlan(
        title="FAMILY APARTMENT - 3 ROOMS",
        walls=walls,
        rooms=rooms,
        furniture=furniture,
        engineering=engineering,
        dimensions=dimensions,
        language="en",
        paper_format="A3",
        scale=100
    )

    output_dir = "output/apartment_3r"
    os.makedirs(output_dir, exist_ok=True)

    # Version 1: Full
    plan.layer = "full"
    with open(os.path.join(output_dir, "apt_3r_full.png"), "wb") as f:
        f.write(render_interior_plan(plan))

    # Version 2: Construction
    plan.layer = "construction"
    plan.title = "CONSTRUCTION PLAN"
    with open(os.path.join(output_dir, "apt_3r_walls.png"), "wb") as f:
        f.write(render_interior_plan(plan))

    print(f"✅ 3-Room Apartment plans generated in {output_dir}")

if __name__ == "__main__":
    create_3room_apartment()
