import os
from theodolite_mcp.domain.models import Point, Zone, PlotPlan, LandscapeItem, UtilityLine, SecurityItem
from theodolite_mcp.domain.rendering import render_plot_plan

def create_landscaping_demo():
    print("🌿 Generating Professional Landscaping & Utilities Plan...")

    # 1. Границы участка
    boundary = [Point(x=0, y=0), Point(x=30, y=0), Point(x=30, y=40), Point(x=0, y=40)]

    # 2. Зоны
    zones = [
        Zone(name="Luxury Villa", points=[Point(x=10, y=15), Point(x=20, y=15), Point(x=20, y=25), Point(x=10, y=25)], fill_color="#B0BEC5"),
        Zone(name="Swimming Pool", points=[Point(x=22, y=18), Point(x=28, y=18), Point(x=28, y=23), Point(x=22, y=23)], fill_color="#81D4FA"),
        Zone(name="Paved Patio", points=[Point(x=8, y=12), Point(x=22, y=12), Point(x=22, y=28), Point(x=8, y=28)], fill_color="#ECEFF1", fill_alpha=0.5)
    ]

    # 3. Растения и освещение (Landscape)
    landscape = [
        # Группа туй (Conifers) вдоль забора
        LandscapeItem(type="tree_conifer", point=Point(x=2, y=5), size=2.0, label="Thuja Smaragd"),
        LandscapeItem(type="tree_conifer", point=Point(x=5, y=5), size=2.0),
        LandscapeItem(type="tree_conifer", point=Point(x=8, y=5), size=2.0),
        
        # Лиственные деревья (Deciduous)
        LandscapeItem(type="tree_deciduous", point=Point(x=25, y=35), size=4.0, label="Maple Tree"),
        
        # Освещение дорожек
        LandscapeItem(type="lamp_post", point=Point(x=9, y=10), light_range=3.0, label="Path Light"),
        LandscapeItem(type="lamp_post", point=Point(x=21, y=10), light_range=3.0),
        LandscapeItem(type="lamp_post", point=Point(x=9, y=30), light_range=3.0),
        LandscapeItem(type="lamp_post", point=Point(x=21, y=30), light_range=3.0)
    ]

    # 4. Инженерные сети (Utilities)
    utilities = [
        # Водопровод к дому
        UtilityLine(type="water", points=[Point(x=0, y=10), Point(x=10, y=18)], depth=1.5, label="Main Water"),
        # Электричество к воротам и дому
        UtilityLine(type="electricity", points=[Point(x=0, y=2), Point(x=10, y=20)], depth=0.7, label="Power Cable"),
        # Система полива (Irrigation) вокруг бассейна
        UtilityLine(type="irrigation", points=[Point(x=20, y=20), Point(x=25, y=25), Point(x=28, y=20)], label="Auto-water"),
        # Канализация
        UtilityLine(type="sewage", points=[Point(x=15, y=15), Point(x=15, y=0)], depth=2.0, label="Septic Line")
    ]

    # 5. Охрана (Security)
    security = [
        SecurityItem(type="camera", point=Point(x=10, y=25), rotation=135, fov_angle=100, range=10.0, label="Backyard Cam")
    ]

    # 6. Создание плана
    plan = PlotPlan(
        title="LANDSCAPING & UTILITY MASTER PLAN",
        boundary_points=boundary,
        zones=zones,
        landscape=landscape,
        utilities=utilities,
        security=security,
        language="en",
        paper_format="A2", # Большой формат для деталей
        scale=100
    )

    output_dir = "output/landscaping"
    os.makedirs(output_dir, exist_ok=True)
    
    png_bytes = render_plot_plan(plan)
    with open(os.path.join(output_dir, "professional_landscape.png"), "wb") as f:
        f.write(png_bytes)

    print(f"✅ Professional Landscaping plan generated in {output_dir}")

if __name__ == "__main__":
    create_landscaping_demo()
