import os
from theodolite_mcp.domain.models import Point, Zone, PlotPlan, SecurityItem
from theodolite_mcp.domain.rendering import render_plot_plan

def create_ultra_security_50m2():
    print("🛡️ Generating Best-in-Class 50m² Perimeter Security Design...")

    # 1. Границы участка (5x10 метров = 50м2)
    boundary = [
        Point(x=0, y=0), Point(x=5, y=0), Point(x=5, y=10), Point(x=0, y=10)
    ]

    # 2. Зона объекта (Центральное строение 3х4м)
    zones = [
        Zone(name="Secure Object", points=[Point(x=1, y=3), Point(x=4, y=3), Point(x=4, y=7), Point(x=1, y=7)], fill_color="#455A64")
    ]

    # 3. УЛЬТРА-защита (Cross-Fire Strategy)
    # Исключаем слепые зоны: камеры смотрят ВДОЛЬ стен друг на друга.
    security = [
        # --- Эшелон 1: Камеры на здании (Cross-Fire) ---
        # Каждая камера видит мертвую зону соседней и всю линию стены.
        SecurityItem(
            type="camera", point=Point(x=1, y=7), rotation=270, # NW смотрит на Юг
            fov_angle=110, range=5.0, label="Cross-Fire West"
        ),
        SecurityItem(
            type="camera", point=Point(x=4, y=7), rotation=180, # NE смотрит на Запад
            fov_angle=110, range=5.0, label="Cross-Fire North"
        ),
        SecurityItem(
            type="camera", point=Point(x=4, y=3), rotation=90, # SE смотрит на Север
            fov_angle=110, range=5.0, label="Cross-Fire East"
        ),
        SecurityItem(
            type="camera", point=Point(x=1, y=3), rotation=0, # SW смотрит на Восток
            fov_angle=110, range=5.0, label="Cross-Fire South"
        ),
        
        # --- Эшелон 2: Камеры по углам забора (Inward looking) ---
        # Перекрывают подступы и смотрят на фасад здания.
        SecurityItem(
            type="camera", point=Point(x=0.1, y=0.1), rotation=45, 
            fov_angle=100, range=7.0, label="Fence SW (Inward)"
        ),
        SecurityItem(
            type="camera", point=Point(x=4.9, y=9.9), rotation=225, 
            fov_angle=100, range=7.0, label="Fence NE (Inward)"
        ),
        
        # --- Эшелон 3: Датчики движения (PIR) ---
        # Страхуют узкие проходы (1 метр) между домом и забором.
        SecurityItem(
            type="motion_sensor", point=Point(x=0.1, y=5.0), rotation=0, 
            range=4.0, fov_angle=110, label="PIR Left Corridor"
        ),
        SecurityItem(
            type="motion_sensor", point=Point(x=4.9, y=5.0), rotation=180, 
            range=4.0, fov_angle=110, label="PIR Right Corridor"
        ),
        
        SecurityItem(type="siren", point=Point(x=2.5, y=5.0), label="Alarm 120dB")
    ]

    # 4. Генплан
    plan = PlotPlan(
        title="ULTRA-SECURE 50m² PERIMETER (360 COVERAGE)",
        boundary_points=boundary,
        zones=zones,
        security=security,
        language="en",
        paper_format="A4",
        scale=50 # Крупный масштаб для маленького участка
    )

    output_dir = "output/security_50m2"
    os.makedirs(output_dir, exist_ok=True)
    
    png_bytes = render_plot_plan(plan)
    with open(os.path.join(output_dir, "best_perimeter_50m2.png"), "wb") as f:
        f.write(png_bytes)

    print(f"✅ Best-in-class 50m² security plan generated in {output_dir}")

if __name__ == "__main__":
    create_ultra_security_50m2()
