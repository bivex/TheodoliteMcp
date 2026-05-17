import os
from theodolite_mcp.domain.models import Point, Wall, Opening, Room, InteriorPlan, FurnitureItem, EngineeringItem, DimensionLine
from theodolite_mcp.domain.rendering import render_interior_plan

def create_luxury_bedroom():
    print("✨ Creating a Luxury Master Bedroom Design...")

    # 1. Стены (Комната 5х6 метров)
    walls = [
        Wall(start_pt=Point(x=0, y=0), end_pt=Point(x=6, y=0), thickness=0.3), # Низ
        Wall(start_pt=Point(x=6, y=0), end_pt=Point(x=6, y=5), thickness=0.3), # Право
        Wall(start_pt=Point(x=6, y=5), end_pt=Point(x=0, y=5), thickness=0.3), # Верх
        Wall(start_pt=Point(x=0, y=5), end_pt=Point(x=0, y=0), thickness=0.3), # Лево
    ]
    
    # Огромное панорамное окно
    walls[2].openings = [Opening(type="window", position=1.0, width=4.0)]
    
    # Входная дверь
    walls[0].openings = [Opening(type="door", position=0.5, width=0.9, direction=1, swing_angle=90)]

    # 2. Помещение с текстурой (Паркет елочкой / Planks под 45 град)
    rooms = [
        Room(
            name="Master Bedroom", 
            number="101", 
            wall_finish="Decor plaster & Walnut panels",
            floor_material="Natural Oak Parquet",
            floor_pattern="planks", 
            floor_tile_size=[1.2, 0.15], # Длинные доски
            floor_angle=45, # Укладка по диагонали для стиля
            points=[Point(x=0.3, y=0.3), Point(x=5.7, y=0.3), Point(x=5.7, y=4.7), Point(x=0.3, y=4.7)]
        )
    ]

    # 3. Мебель (Премиальная расстановка)
    furniture = [
        # Кровать King Size в центре
        FurnitureItem(
            type="bed", center_pt=Point(x=3.0, y=2.2), width=2.0, length=2.2, 
            rotation=0, label="King Size Bed (Premium)", ergonomics_padding=0.7 # Нужен проход 70см
        ),
        # Кресло для отдыха у окна
        FurnitureItem(
            type="sofa", center_pt=Point(x=0.8, y=4.0), width=0.8, length=0.8, 
            rotation=-45, label="Reading Chair"
        ),
        # Тумбы
        FurnitureItem(type="table", center_pt=Point(x=1.6, y=2.2), width=0.5, length=0.5, label="Nightstand L"),
        FurnitureItem(type="table", center_pt=Point(x=4.4, y=2.2), width=0.5, length=0.5, label="Nightstand R"),
        
        # Шкаф во всю стену (имитируем через sofa/rect)
        FurnitureItem(type="sofa", center_pt=Point(x=5.6, y=2.5), width=0.6, length=4.0, rotation=90, label="Wardrobe")
    ]

    # 4. Электрика и свет (Атмосфера)
    engineering = [
        # Розетки у кровати
        EngineeringItem(type="socket", point=Point(x=1.3, y=2.2), label="Phone & Lamp"),
        EngineeringItem(type="socket", point=Point(x=4.7, y=2.2), label="Phone & Lamp"),
        # Выключатель у входа
        EngineeringItem(type="switch", point=Point(x=0.1, y=0.8), label="Master Switch"),
        # Освещение
        EngineeringItem(type="lamp", point=Point(x=3.0, y=2.5), label="Designer Chandelier"),
        # Радиатор под окном
        EngineeringItem(type="radiator", point=Point(x=3.0, y=4.9), rotation=0, label="Built-in floor convector")
    ]

    # 5. Размеры
    dimensions = [
        DimensionLine(points=[Point(x=0, y=-0.5), Point(x=3, y=-0.5), Point(x=6, y=-0.5)], offset=0.3),
        DimensionLine(points=[Point(x=-0.5, y=0), Point(x=-0.5, y=5)], offset=0.3)
    ]

    # 6. План
    plan = InteriorPlan(
        title="LUXURY MASTER BEDROOM CONCEPT",
        project_number="INT-BED-01",
        organization="Gemini Design Bureau",
        walls=walls,
        rooms=rooms,
        furniture=furniture,
        engineering=engineering,
        dimensions=dimensions,
        show_ergonomics=True, # Включаем проверку проходов!
        language="en",
        paper_format="A4",
        scale=50
    )

    output_dir = "output/bedroom_design"
    os.makedirs(output_dir, exist_ok=True)
    
    # Рендерим 2 версии: мебель и электрику
    plan.layer = "full"
    with open(os.path.join(output_dir, "bedroom_full_design.png"), "wb") as f:
        f.write(render_interior_plan(plan))
        
    plan.layer = "electrical"
    plan.title = "BEDROOM ELECTRICAL PLAN"
    with open(os.path.join(output_dir, "bedroom_electrical.png"), "wb") as f:
        f.write(render_interior_plan(plan))

    print(f"✅ Luxury Bedroom designs generated in {output_dir}")

if __name__ == "__main__":
    create_luxury_bedroom()
