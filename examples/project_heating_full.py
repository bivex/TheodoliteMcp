import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from theodolite_mcp.domain.models.interior import InteriorPlan, Wall, Room, EngineeringItem
from theodolite_mcp.domain.models.base import Point
from theodolite_mcp.application.services import SurveyService
import json

def main():
    service = SurveyService()
    
    # 1. FINAL BILL OF MATERIALS (BOM) based on research
    # Prices in UAH
    bom_data = [
        {"type": "boiler", "label": "Котел Kronas Standard 10 кВт", "price": 21200},
        {"type": "automation", "label": "Комплект IE-24n + SP-60", "price": 3132},
        {"type": "automation", "label": "Регулятор тяги EP.5101", "price": 1017},
        {"type": "safety", "label": "Група безпеки Europroduct 3 бар", "price": 750},
        {"type": "pump", "label": "Насос Wilo 25-40 180", "price": 1658},
        {"type": "expansion_tank", "label": "Бак KOER 12л", "price": 1033},
        {"type": "valve", "label": "3-ходовий Herz Calis-TS DN20", "price": 910},
        {"type": "bypass", "label": "Байпас 40 1 1/2\"", "price": 1240},
        {"type": "manifold", "label": "Колектор Koer 3 виходи", "price": 609},
        {"type": "radiator", "label": "Радіатор Engel 500x1000 (x3)", "price": 9000},
        {"type": "radiator_kit", "label": "Комплект SD Plus (x3)", "price": 1563},
        {"type": "chimney", "label": "Димохід Сендвіч 160мм (комплект)", "price": 3501},
        {"type": "piping", "label": "Труби PPR 32мм + фітинги", "price": 2530},
    ]
    
    # 2. GENERATE SCHEMATIC
    # We use the new automated tool through the service logic
    print("Генерація технічної схеми (ISO 14617)...")
    from theodolite_mcp.infrastructure.mcp_server import draw_heating_system
    
    output_schematic = "output/project_heating_final_schematic.png"
    draw_heating_system(
        boiler_label="Kronas Standard 10kW",
        radiator_count=3,
        title="Проект системи опалення (вугільний котел)",
        language="uk",
        output_path=output_schematic
    )
    print(f"Схему збережено: {output_schematic}")

    # 3. GENERATE INTERIOR PLAN (Layout)
    # Simple 4x4m Boiler Room
    walls = [
        Wall(start_pt=Point(x=0, y=0), end_pt=Point(x=4, y=0)),
        Wall(start_pt=Point(x=4, y=0), end_pt=Point(x=4, y=4)),
        Wall(start_pt=Point(x=4, y=4), end_pt=Point(x=0, y=4)),
        Wall(start_pt=Point(x=0, y=4), end_pt=Point(x=0, y=0)),
    ]
    
    rooms = [
        Room(
            name="Котельня",
            number="1",
            points=[Point(x=0, y=0), Point(x=4, y=0), Point(x=4, y=4), Point(x=0, y=4)],
            floor_material="Керамограніт"
        )
    ]
    
    engineering = [
        EngineeringItem(
            type="boiler",
            point=Point(x=1, y=2),
            label="Kronas Standard",
            price=21200
        ),
        EngineeringItem(
            type="radiator",
            point=Point(x=3.8, y=1),
            label="Радіатор 1",
            price=3000
        )
    ]
    
    plan = InteriorPlan(
        title="Монтажна схема котельні",
        walls=walls,
        rooms=rooms,
        engineering=engineering,
        language="uk"
    )
    
    output_layout = "output/project_heating_final_layout.png"
    service.render_interior(plan, output_path=output_layout)
    print(f"План розстановки збережено: {output_layout}")

    # 4. PRINT SUMMARY REPORT
    total_cost = sum(item["price"] for item in bom_data)
    
    print("\n" + "="*60)
    print("ПОВНИЙ КОШТОРИС СИСТЕМИ ОПАЛЕННЯ")
    print("="*60)
    print(f"{'#':<3} | {'Назва компонента':<35} | {'Ціна (грн)':>10}")
    print("-" * 60)
    for i, item in enumerate(bom_data, 1):
        print(f"{i:<3} | {item['label']:<35} | {item['price']:>10.2f}")
    print("-" * 60)
    print(f"{'ЗАГАЛЬНА ВАРТІСТЬ ОБЛАДНАННЯ':<38} | {total_cost:>10.2f} грн")
    print("="*60)
    
    print("\nРекомендації по монтажу:")
    print("1. Насос PU1 встановлювати на зворотній лінії перед котлом.")
    print("2. Розширювальний бак GA1 підключати паралельно через трійник.")
    print("3. Дренаж від клапана PRV1 вивести вниз до каналізації.")
    print("4. Трьохходовий клапан обов'язковий для захисту котла від конденсату.")

if __name__ == "__main__":
    main()
