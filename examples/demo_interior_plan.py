import os
from theodolite_mcp.domain.models import Point, Wall, Opening, Room, InteriorPlan
from theodolite_mcp.domain.rendering import render_interior_plan

def create_interior_plan_demo():
    print("🏠 Generating Architectural Interior Plan...")

    # 1. Define Walls (Centerlines)
    # External walls (300mm)
    w1 = Wall(start_pt=Point(name="W1S", x=0, y=0), end_pt=Point(name="W1E", x=10, y=0), thickness=0.3, material="brick")
    w2 = Wall(start_pt=Point(name="W2S", x=10, y=0), end_pt=Point(name="W2E", x=10, y=8), thickness=0.3, material="brick")
    w3 = Wall(start_pt=Point(name="W3S", x=10, y=8), end_pt=Point(name="W3E", x=0, y=8), thickness=0.3, material="brick")
    w4 = Wall(start_pt=Point(name="W4S", x=0, y=8), end_pt=Point(name="W4E", x=0, y=0), thickness=0.3, material="brick")
    
    # Openings in external walls
    w1.openings = [Opening(type="door", start_distance=4.0, width=1.0, direction=1)]
    w3.openings = [Opening(type="window", start_distance=2.0, width=2.5), 
                   Opening(type="window", start_distance=6.0, width=1.5)]

    # Internal partitions (120mm)
    w5 = Wall(start_pt=Point(name="W5S", x=5, y=0), end_pt=Point(name="W5E", x=5, y=5), thickness=0.12, material="brick")
    w6 = Wall(start_pt=Point(name="W6S", x=5, y=5), end_pt=Point(name="W6E", x=0, y=5), thickness=0.12, material="brick")
    
    w5.openings = [Opening(type="door", start_distance=1.0, width=0.8, direction=-1)]
    
    # Demolition / New Walls
    w_demo = Wall(start_pt=Point(name="D1", x=5, y=5), end_pt=Point(name="D2", x=10, y=5), 
                  thickness=0.12, material="brick", status="demolish")
    w_new = Wall(start_pt=Point(name="N1", x=7, y=8), end_pt=Point(name="N2", x=7, y=5), 
                 thickness=0.1, material="brick", status="new")

    # 2. Rooms
    rooms = [
        Room(name="Living Room", number="1", points=[Point(name="", x=5.5, y=0.5), Point(name="", x=9.5, y=0.5), 
                                                   Point(name="", x=9.5, y=7.5), Point(name="", x=5.5, y=7.5)]),
        Room(name="Kitchen", number="2", points=[Point(name="", x=0.5, y=5.5), Point(name="", x=4.5, y=5.5), 
                                               Point(name="", x=4.5, y=7.5), Point(name="", x=0.5, y=7.5)]),
    ]

    # 3. Create Plan
    plan = InteriorPlan(
        title="APARTMENT RENOVATION - LAYOUT",
        project_number="ARCH-2026-05",
        organization="Creative Space Design",
        walls=[w1, w2, w3, w4, w5, w6, w_demo, w_new],
        rooms=rooms,
        language="en",
        paper_format="A4",
        scale=50 # 1:50
    )

    # 4. Render and Save
    png_bytes = render_interior_plan(plan)
    output_path = os.path.join("output", "interior_floor_plan.png")
    
    os.makedirs("output", exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(png_bytes)

    print(f"✅ Architectural plan generated: {output_path}")

if __name__ == "__main__":
    create_interior_plan_demo()
