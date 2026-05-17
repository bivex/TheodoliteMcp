import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from theodolite_mcp.domain.models.interior import InteriorPlan, Wall, Room, EngineeringItem
from theodolite_mcp.domain.models.base import Point
from theodolite_mcp.application.services import SurveyService
import json

def main():
    service = SurveyService()
    
    # Boilers data from user
    coal_boilers = [
        {"name": "Проскуров 10 кВт", "price": 14700},
        {"name": "Buller (булер'ян)", "price": 16000},
        {"name": "Kronas Стандарт 10-26 кВт", "price": 21200},
        {"name": "ALMAX class B 10-33 кВт", "price": 29900},
        {"name": "Бізон Практик", "price": 31800},
        {"name": "FENIKS К 12 кВт", "price": 39000},
        {"name": "Attack Viadrus 26 кВт", "price": 96456},
    ]
    
    # We select Kronas Standard for this demo
    selected_boiler = coal_boilers[2]
    
    # Create a small boiler room (3x3 meters)
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
            floor_material="Керамограніт",
            floor_pattern="grid"
        )
    ]
    
    engineering = [
        # The coal boiler
        EngineeringItem(
            type="boiler",
            point=Point(x=1, y=2),
            rotation=0,
            label=selected_boiler["name"],
            price=selected_boiler["price"]
        ),
        # A couple of radiators for adjacent rooms (conceptually)
        EngineeringItem(
            type="radiator",
            point=Point(x=3.8, y=1),
            rotation=90,
            label="Радіатор 1",
            price=4500
        ),
        EngineeringItem(
            type="radiator",
            point=Point(x=3.8, y=3),
            rotation=90,
            label="Радіатор 2",
            price=4500
        ),
    ]
    
    plan = InteriorPlan(
        title="План опалення (вугільний котел)",
        organization="ТеплоМонтаж",
        walls=walls,
        rooms=rooms,
        engineering=engineering,
        language="uk",
        paper_format="A4"
    )
    
    # Render PNG
    output_png = "output/heating_coal_plan.png"
    service.render_interior(plan, output_path=output_png)
    print(f"План збережено у {output_png}")
    
    # Generate specification report
    report = service.generate_interior_report(plan)
    
    print("\n--- Специфікація обладнання ---")
    for item in report.engineering_list:
        print(f"- {item['type'].capitalize()}: {item['label']} | Ціна: {item['price']}")
        
    print(f"\nЗагальна вартість обладнання: {report.total_cost:.2f} {report.currency}")
    print(f"Загальна площа котельні: {report.total_area:.2f} м²")

if __name__ == "__main__":
    main()
