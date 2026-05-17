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
        # 1. Main Hub / Entrance (Охранная панель и геркон)
        SecurityItem(type="keypad", point=Point(x=0.2, y=5.5), rotation=0, label="Ajax Hub"),
        SecurityItem(type="door_sensor", point=Point(x=0.0, y=5.0), label="Door Protect"),
        
        # 2. Cameras (Видеонаблюдение - Топ выбор)
        # EZVIZ C6N (PTZ 360°, Smart Tracking) - Гостиная/Кухня. 
        # Установлена в верхнем левом углу, покрывает 90% центральной зоны и вход в коридор.
        SecurityItem(
            type="camera", point=Point(x=4.2, y=9.8), rotation=315, # Смотрит на Юго-Восток
            fov_angle=110, range=8.5, label="EZVIZ C6N 1080p (PTZ)"
        ),
        
        # Xiaomi YI Home 2K Pro (Fixed, High Res) - Коридор.
        # Установлена над входной дверью, смотрит вглубь коридора. Идеально для идентификации лиц.
        SecurityItem(
            type="camera", point=Point(x=0.2, y=5.8), rotation=340, # Смотрит на Восток
            fov_angle=110, range=6.0, label="Xiaomi YI 2K Pro (Entrance)"
        ),
        
        # Вторая Xiaomi YI Home 2K Pro - Мастер спальня.
        # Установлена в дальнем углу, контролирует окно и подходы к кровати.
        SecurityItem(
            type="camera", point=Point(x=11.8, y=9.8), rotation=225, # Смотрит на Юго-Запад
            fov_angle=110, range=7.0, label="Xiaomi YI 2K Pro (Bedroom)"
        ),

        # 3. Motion Sensors (Датчики движения PIR для перекрестного покрытия)
        # Если камеру ослепят или закроют, PIR в другом углу поймает движение.
        SecurityItem(
            type="motion_sensor", point=Point(x=7.8, y=0.2), rotation=135, # Смотрит на Северо-Запад
            range=6.0, fov_angle=100, label="MotionCam (Kitchen)"
        ),
        SecurityItem(
            type="motion_sensor", point=Point(x=11.8, y=0.2), rotation=135, 
            range=6.0, fov_angle=100, label="Motion Protect (Bed)"
        ),

        # 4. Siren (Сирена)
        # В центре квартиры для максимального звукового давления во все комнаты.
        SecurityItem(type="siren", point=Point(x=6.0, y=5.0), label="HomeSiren 105dB")
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
