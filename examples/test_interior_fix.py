import os
from theodolite_mcp.domain.models import Point, Wall, Opening, Room, InteriorPlan
from theodolite_mcp.domain.rendering import render_interior_plan

def verify_apartment_render():
    print("🏠 Verifying Apartment Plan Rendering (Meters)...")
    
    # User's exact case in meters
    w1 = Wall(start_pt=Point(name="P1", x=0, y=0), end_pt=Point(name="P2", x=5, y=0), thickness=0.3, material="кирпич")
    w2 = Wall(start_pt=Point(name="P2", x=5, y=0), end_pt=Point(name="P3", x=5, y=8), thickness=0.3, material="кирпич",
              openings=[Opening(type="window", start_distance=3.25, width=1.5)])
    w3 = Wall(start_pt=Point(name="P3", x=5, y=8), end_pt=Point(name="P4", x=0, y=8), thickness=0.3, material="кирпич")
    w4 = Wall(start_pt=Point(name="P4", x=0, y=8), end_pt=Point(name="P1", x=0, y=0), thickness=0.3, material="кирпич",
              openings=[Opening(type="door", start_distance=0.8, width=0.9)])
    
    # Internal
    w5 = Wall(start_pt=Point(name="P5", x=0, y=5), end_pt=Point(name="P6", x=5, y=5), thickness=0.12, material="гипсоблок",
              openings=[Opening(type="door", start_distance=0.4, width=0.9)])

    rooms = [
        Room(name="Комната", number="1", points=[Point(x=0.15, y=0.15), Point(x=4.85, y=0.15), 
                                                Point(x=4.85, y=4.85), Point(x=0.15, y=4.85)]),
        Room(name="Кухня", number="2", points=[Point(x=0.15, y=5.15), Point(x=4.85, y=5.15), 
                                              Point(x=4.85, y=7.85), Point(x=0.15, y=7.85)]),
    ]

    plan = InteriorPlan(
        title="План однокомнатной квартиры (FIXED)",
        walls=[w1, w2, w3, w4, w5],
        rooms=rooms,
        language="ru",
        paper_format="A3",
        scale=0 # Auto-scale
    )

    png_bytes = render_interior_plan(plan)
    output_path = os.path.join("output", "apartment_fixed_render.png")
    
    os.makedirs("output", exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(png_bytes)

    print(f"✅ Fixed apartment plan generated: {output_path}")

if __name__ == "__main__":
    verify_apartment_render()
