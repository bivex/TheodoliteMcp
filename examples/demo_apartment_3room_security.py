import os
from theodolite_mcp.domain.models import Point, Wall, Opening, Room, InteriorPlan, FurnitureItem, SecurityItem, DimensionLine
from theodolite_mcp.domain.rendering import render_interior_plan

def create_3room_security_demo():
    print("🛡️ Integrating Premium Security System into 3-Room Apartment...")

    # 1. Perimeter Walls (12m x 10m) - Same as previous 3-room layout
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
    walls.append(Wall(start_pt=Point(x=4, y=0), end_pt=Point(x=4, y=6), thickness=0.12))
    walls.append(Wall(start_pt=Point(x=0, y=6), end_pt=Point(x=4, y=6), thickness=0.12))
    walls.append(Wall(start_pt=Point(x=8, y=0), end_pt=Point(x=8, y=10), thickness=0.12))
    walls.append(Wall(start_pt=Point(x=4, y=4), end_pt=Point(x=8, y=4), thickness=0.12))

    # Internal Doors
    walls[4].openings = [Opening(type="door", position=1.0, width=0.9, direction=1, swing_angle=90)] # Main Entrance Door
    walls[6].openings = [Opening(type="door", position=1.0, width=0.8, direction=-1, swing_angle=90), # Bedroom
                         Opening(type="door", position=5.0, width=0.8, direction=-1, swing_angle=90)] # Small room
    walls[7].openings = [Opening(type="door", position=1.5, width=0.7, direction=1, swing_angle=90)] # Bathroom

    # 3. Furniture (Context)
    furniture = [
        FurnitureItem(type="sofa", center_pt=Point(x=6.0, y=8.0), width=3.0, length=1.0, label="Family Sofa"),
        FurnitureItem(type="bed", center_pt=Point(x=10.0, y=5.0), width=1.8, length=2.0, rotation=90, label="Master Bed"),
    ]

    # --- 🛡️ PREMIUM SECURITY SYSTEM LAYER 🛡️ ---
    security = [
        # 1. Main Hub / Entrance
        SecurityItem(type="keypad", point=Point(x=3.8, y=0.5), rotation=0, label="Alarm Panel"),
        SecurityItem(type="door_sensor", point=Point(x=4.0, y=1.0), label="Entry Door Sensor"),
        
        # 2. Cameras (Based on recommendations)
        # Using EZVIZ C6N (PTZ, Smart Tracking) for the main living area - high traffic
        SecurityItem(
            type="camera", point=Point(x=4.2, y=9.8), rotation=315, 
            fov_angle=120, range=8.0, label="EZVIZ C6N (360° Living Rm)"
        ),
        
        # Using Xiaomi YI Home 2K Pro (Fixed, High Res) for the hallway and entrance monitoring
        SecurityItem(
            type="camera", point=Point(x=3.8, y=5.8), rotation=225, 
            fov_angle=110, range=5.0, label="Xiaomi 2K Pro (Hallway)"
        ),
        
        # Second Xiaomi YI Home 2K Pro for the small room/office window
        SecurityItem(
            type="camera", point=Point(x=7.8, y=3.8), rotation=135, 
            fov_angle=110, range=5.0, label="Xiaomi 2K Pro (Office/Kids)"
        ),

        # 3. Motion Sensors (PIR) for cross-coverage
        SecurityItem(
            type="motion_sensor", point=Point(x=0.2, y=0.2), rotation=45, 
            range=5.0, fov_angle=90, label="PIR - Living Room"
        ),
        SecurityItem(
            type="motion_sensor", point=Point(x=11.8, y=9.8), rotation=225, 
            range=5.0, fov_angle=90, label="PIR - Master Bedroom"
        ),

        # 4. Siren
        SecurityItem(type="siren", point=Point(x=6.0, y=5.0), label="Main Siren 120dB")
    ]

    # 4. Render
    plan = InteriorPlan(
        title="3-ROOM APARTMENT - SECURITY CONCEPT",
        walls=walls,
        furniture=furniture,
        security=security,
        layer="security",
        language="en",
        paper_format="A3",
        scale=100
    )

    output_dir = "output/apartment_3r_security"
    os.makedirs(output_dir, exist_ok=True)

    # Version 1: Security Focus
    plan.layer = "security"
    with open(os.path.join(output_dir, "apt_3r_security_zones.png"), "wb") as f:
        f.write(render_interior_plan(plan))

    # Version 2: Integrated Plan
    plan.layer = "full"
    plan.title = "INTEGRATED DESIGN & SECURITY PLAN"
    with open(os.path.join(output_dir, "apt_3r_integrated.png"), "wb") as f:
        f.write(render_interior_plan(plan))

    print(f"✅ Security plans generated in {output_dir}")

if __name__ == "__main__":
    create_3room_security_demo()
