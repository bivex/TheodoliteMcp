import os
from theodolite_mcp.domain.models import Point, Zone, PlotPlan, SecurityItem
from theodolite_mcp.domain.rendering import render_plot_plan

def create_perimeter_security_demo():
    print("🏠 Designing Perimeter Security for a Country House...")

    # 1. Границы участка (20x30 метров)
    boundary = [
        Point(x=0, y=0), Point(x=20, y=0), Point(x=20, y=30), Point(x=0, y=30)
    ]

    # 2. Зоны (Дом, Гараж, Сад)
    zones = [
        Zone(name="Main House", points=[Point(x=5, y=10), Point(x=15, y=10), Point(x=15, y=20), Point(x=5, y=20)], fill_color="#E0E0E0"),
        Zone(name="Garage", points=[Point(x=2, y=2), Point(x=7, y=2), Point(x=7, y=7), Point(x=2, y=7)], fill_color="#BDBDBD"),
        Zone(name="Backyard Garden", points=[Point(x=2, y=22), Point(x=18, y=22), Point(x=18, y=28), Point(x=2, y=28)], fill_color="#A5D6A7")
    ]

    # 3. Периметральная охрана (Security Layer for Site Plan)
    security = [
        # Уличные поворотные камеры (PTZ) по углам дома
        SecurityItem(
            type="camera", point=Point(x=5, y=20), rotation=135, 
            fov_angle=120, range=15.0, label="CCTV NW (Garden Control)"
        ),
        SecurityItem(
            type="camera", point=Point(x=15, y=10), rotation=315, 
            fov_angle=120, range=15.0, label="CCTV SE (Entrance Control)"
        ),
        
        # Датчики движения (PIR) вдоль забора
        SecurityItem(
            type="motion_sensor", point=Point(x=10, y=0.5), rotation=90, 
            range=10.0, fov_angle=140, label="Front Perimeter Sensor"
        ),
        
        # Уличная сирена на фасаде гаража
        SecurityItem(type="siren", point=Point(x=7.2, y=5.0), label="Outdoor Siren 120dB")
    ]

    # 4. Генплан
    plan = PlotPlan(
        title="PERIMETER SECURITY & SITE PLAN",
        boundary_points=boundary,
        zones=zones,
        security=security,
        language="en",
        paper_format="A3"
    )

    output_dir = "output/perimeter_security"
    os.makedirs(output_dir, exist_ok=True)
    
    png_bytes = render_plot_plan(plan)
    with open(os.path.join(output_dir, "house_perimeter_security.png"), "wb") as f:
        f.write(png_bytes)

    print(f"✅ Perimeter Security plan generated in {output_dir}")

if __name__ == "__main__":
    create_perimeter_security_demo()
