import os
from theodolite_mcp.domain.models import Point, Wall, Opening, Room, InteriorPlan, FurnitureItem, SecurityItem, DimensionLine
from theodolite_mcp.domain.rendering import render_interior_plan

def create_security_demo():
    print("🛡️ Generating Security System Layout Concept...")

    # 1. Стены (Квартира с длинным коридором)
    walls = [
        Wall(start_pt=Point(x=0, y=0), end_pt=Point(x=10, y=0), thickness=0.3),
        Wall(start_pt=Point(x=10, y=0), end_pt=Point(x=10, y=8), thickness=0.3),
        Wall(start_pt=Point(x=10, y=8), end_pt=Point(x=0, y=8), thickness=0.3),
        Wall(start_pt=Point(x=0, y=8), end_pt=Point(x=0, y=0), thickness=0.3),
        # Коридор
        Wall(start_pt=Point(x=3, y=0), end_pt=Point(x=3, y=6), thickness=0.12),
        Wall(start_pt=Point(x=0, y=6), end_pt=Point(x=3, y=6), thickness=0.12),
    ]
    
    # Входная дверь
    walls[0].openings = [Opening(type="door", position=0.5, width=1.0, direction=1)]

    # 2. Охранные системы (Security Layer)
    security = [
        # Камеры наблюдения с углами обзора
        SecurityItem(
            type="camera", point=Point(x=0.1, y=0.1), rotation=45, 
            fov_angle=110, range=8.0, label="Entrance Camera (4K)"
        ),
        SecurityItem(
            type="camera", point=Point(x=9.9, y=7.9), rotation=225, 
            fov_angle=90, range=6.0, label="Living Room Cam"
        ),
        
        # Датчики движения (PIR)
        SecurityItem(
            type="motion_sensor", point=Point(x=3.1, y=5.9), rotation=135, 
            range=4.0, fov_angle=120, label="Hallway PIR"
        ),
        
        # Датчики открытия (Герконы)
        SecurityItem(type="door_sensor", point=Point(x=0.5, y=0.0)),
        
        # Управление и оповещение
        SecurityItem(type="keypad", point=Point(x=2.8, y=1.0), rotation=180, label="Alarm Panel"),
        SecurityItem(type="siren", point=Point(x=1.5, y=7.8), label="Internal Siren")
    ]

    # 3. Мебель для контекста
    furniture = [
        FurnitureItem(type="sofa", center_pt=Point(x=7.0, y=6.0), width=3.0, length=1.0, label="Sofa"),
        FurnitureItem(type="bed", center_pt=Point(x=1.5, y=3.0), width=1.4, length=2.0, rotation=0, label="Guest Bed")
    ]

    # 4. План
    plan = InteriorPlan(
        title="SECURITY & SURVEILLANCE LAYOUT",
        walls=walls,
        furniture=furniture,
        security=security,
        layer="security", # Специальный слой безопасности!
        language="en",
        paper_format="A4",
        scale=50
    )

    output_dir = "output/security_concept"
    os.makedirs(output_dir, exist_ok=True)
    
    # Генерируем 2 версии: только безопасность и совмещенный план
    # 1. Security Analysis (фокус на камерах)
    png_sec = render_interior_plan(plan)
    with open(os.path.join(output_dir, "security_zones.png"), "wb") as f:
        f.write(png_sec)
        
    # 2. Full combined plan
    plan.layer = "full"
    plan.title = "INTEGRATED HOME SECURITY PLAN"
    png_full = render_interior_plan(plan)
    with open(os.path.join(output_dir, "integrated_security.png"), "wb") as f:
        f.write(png_full)

    print(f"✅ Security concepts generated in {output_dir}")

if __name__ == "__main__":
    create_security_demo()
