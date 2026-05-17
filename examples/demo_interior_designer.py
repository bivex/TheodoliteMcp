import os
from theodolite_mcp.domain.models import Point, Wall, Opening, Room, InteriorPlan, FurnitureItem, EngineeringItem, DimensionLine
from theodolite_mcp.domain.rendering import render_interior_plan

def create_professional_interior_demo():
    """
    Creates a professional-grade interior design demo showing:
    1. Demolition and new construction
    2. Furniture layout with labels
    3. Electrical/Engineering plan (sockets, switches, lamps)
    4. Chained dimensions
    """
    print("🏠 Generating Professional Interior Designer Demo...")

    # --- 1. COORDINATES & WALLS ---
    # We define a 2-room apartment area
    
    # Perimeter (Existing)
    walls = [
        Wall(start_pt=Point(x=0, y=0), end_pt=Point(x=10, y=0), thickness=0.3), # Bottom
        Wall(start_pt=Point(x=10, y=0), end_pt=Point(x=10, y=8), thickness=0.3), # Right
        Wall(start_pt=Point(x=10, y=8), end_pt=Point(x=0, y=8), thickness=0.3), # Top
        Wall(start_pt=Point(x=0, y=8), end_pt=Point(x=0, y=0), thickness=0.3), # Left
    ]
    
    # External Windows
    walls[0].openings = [Opening(type="window", position=4.0, width=2.0)]
    walls[2].openings = [Opening(type="window", position=3.0, width=1.5), 
                         Opening(type="window", position=7.0, width=1.2)]

    # Internal Wall to DEMOLISH (Red dashed)
    walls.append(Wall(
        start_pt=Point(x=5, y=0), end_pt=Point(x=5, y=5), 
        thickness=0.12, material="brick", status="demolish"
    ))

    # NEW Internal Wall (Green solid)
    new_partition = Wall(
        start_pt=Point(x=6, y=0), end_pt=Point(x=6, y=5), 
        thickness=0.1, material="brick", status="new"
    )
    # New door with swing arc
    new_partition.openings = [
        Opening(type="door", position=1.0, width=0.8, direction=1, status="new", swing_angle=90)
    ]
    walls.append(new_partition)

    # --- 2. ROOMS ---
    rooms = [
        Room(name="Living Room", number="1", wall_finish="Washable Paint", 
             points=[Point(x=0.3, y=0.3), Point(x=5.7, y=0.3), Point(x=5.7, y=7.7), Point(x=0.3, y=7.7)]),
        Room(name="Bedroom", number="2", wall_finish="Acoustic Panels",
             points=[Point(x=6.3, y=0.3), Point(x=9.7, y=0.3), Point(x=9.7, y=4.7), Point(x=6.3, y=4.7)]),
    ]

    # --- 3. FURNITURE ---
    furniture = [
        # Bedroom
        FurnitureItem(type="bed", center_pt=Point(x=8.0, y=2.5), width=1.8, length=2.1, rotation=90, label="King Size"),
        # Living Room
        FurnitureItem(type="sofa", center_pt=Point(x=2.0, y=6.0), width=2.4, length=1.0, rotation=0, label="Corner Sofa"),
        FurnitureItem(type="stove", center_pt=Point(x=1.0, y=1.0), width=0.6, length=0.6, label="Induction"),
        FurnitureItem(type="fridge", center_pt=Point(x=1.8, y=1.0), width=0.6, length=0.6, label="Side-by-Side"),
        FurnitureItem(type="washer", center_pt=Point(x=0.8, y=3.0), width=0.6, length=0.6, rotation=90, label="Laundry"),
    ]

    # --- 4. ENGINEERING (Electrical) ---
    engineering = [
        # Near Sofa
        EngineeringItem(type="socket", point=Point(x=0.2, y=6.0), label="USB Socket"),
        EngineeringItem(type="socket", point=Point(x=3.8, y=6.0), label="TV Power"),
        # Bedroom
        EngineeringItem(type="socket", point=Point(x=6.2, y=1.5), label="Bedside L"),
        EngineeringItem(type="socket", point=Point(x=6.2, y=3.5), label="Bedside R"),
        EngineeringItem(type="switch", point=Point(x=6.1, y=0.8), label="Master Light"),
        # Ceiling
        EngineeringItem(type="lamp", point=Point(x=3.0, y=4.0), label="Chandelier 1"),
        EngineeringItem(type="lamp", point=Point(x=8.0, y=2.5), label="Bedroom Lamp"),
        # HVAC
        EngineeringItem(type="radiator", point=Point(x=5.0, y=7.8), rotation=0, label="1200mm"),
    ]

    # --- 5. DIMENSIONS ---
    dimensions = [
        # Horizontal chain at the bottom
        DimensionLine(points=[Point(x=0, y=-0.8), Point(x=6, y=-0.8), Point(x=10, y=-0.8)], offset=0.4),
        # Vertical chain on the left
        DimensionLine(points=[Point(x=-0.8, y=0), Point(x=-0.8, y=5), Point(x=-0.8, y=8)], offset=0.4),
    ]

    # --- 6. RENDER ALL LAYERS ---
    output_dir = "output/designer_demo"
    os.makedirs(output_dir, exist_ok=True)

    # Base Plan settings
    plan_config = {
        "title": "DESIGNER APARTMENT - FULL LAYOUT",
        "project_number": "INT-2026-001",
        "organization": "Modern Space Studio",
        "walls": walls,
        "rooms": rooms,
        "furniture": furniture,
        "engineering": engineering,
        "dimensions": dimensions,
        "language": "en",
        "paper_format": "A3",
        "scale": 50
    }

    # Generate 3 variations
    layers = [
        ("full", "Full Architectural & Design Plan"),
        ("construction", "Demolition & Construction Plan"),
        ("electrical", "Electrical & Engineering Layout")
    ]

    for layer_id, layer_title in layers:
        plan = InteriorPlan(**plan_config)
        plan.layer = layer_id
        plan.title = f"{layer_title.upper()}"
        
        png_bytes = render_interior_plan(plan)
        filename = f"designer_{layer_id}.png"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, "wb") as f:
            f.write(png_bytes)
        print(f"✅ Generated: {filepath}")

if __name__ == "__main__":
    create_professional_interior_demo()
