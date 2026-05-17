import pytest
import os
from theodolite_mcp.infrastructure.mcp_server import draw_interior_plan, draw_interior_plan_svg

def test_kitchen_bathroom_unit():
    """
    Тест на отрисовку кухни и санузла (типичный узел для водоснабжения).
    Проверяем стены, проемы, комнаты и мебель.
    """
    output_png = "output/test_interior_kitchen_bath.png"
    output_svg = "output/test_interior_kitchen_bath.svg"

    # Стены внешние и перегородка
    walls = [
        # Периметр 5x3 метра
        {"start_pt": {"x": 0, "y": 0}, "end_pt": {"x": 5, "y": 0}, "thickness": 0.3},
        {"start_pt": {"x": 5, "y": 0}, "end_pt": {"x": 5, "y": 3}, "thickness": 0.3, "openings": [{"type": "window", "start_distance": 1.0, "width": 1.2}]},
        {"start_pt": {"x": 5, "y": 3}, "end_pt": {"x": 0, "y": 3}, "thickness": 0.3},
        {"start_pt": {"x": 0, "y": 3}, "end_pt": {"x": 0, "y": 0}, "thickness": 0.3, "openings": [{"type": "door", "start_distance": 0.5, "width": 0.9}]},
        
        # Перегородка между кухней и санузлом (на отметке x=3)
        {"start_pt": {"x": 3, "y": 0}, "end_pt": {"x": 3, "y": 3}, "thickness": 0.15, "openings": [{"type": "door", "start_distance": 1.5, "width": 0.7}]},
    ]

    # Комнаты
    rooms = [
        {"name": "Кухня", "number": "1", "points": [{"x": 0, "y": 0}, {"x": 3, "y": 0}, {"x": 3, "y": 3}, {"x": 0, "y": 3}]},
        {"name": "Санузел", "number": "2", "points": [{"x": 3, "y": 0}, {"x": 5, "y": 0}, {"x": 5, "y": 3}, {"x": 3, "y": 3}]},
    ]

    # Мебель и сантехника
    furniture = [
        # Кухня
        {"type": "sink", "center_pt": {"x": 0.4, "y": 0.4}, "width": 0.6, "length": 0.6},
        {"type": "stove", "center_pt": {"x": 1.2, "y": 0.4}, "width": 0.6, "length": 0.6},
        
        # Санузел
        {"type": "wc", "center_pt": {"x": 4.6, "y": 0.4}, "width": 0.4, "length": 0.6, "rotation": 180},
        {"type": "bath", "center_pt": {"x": 4.0, "y": 2.2}, "width": 1.6, "length": 0.75, "rotation": 90},
    ]

    try:
        # 1. PNG Тест
        res_png = draw_interior_plan(
            title="Тест: Кухня + Санузел",
            walls_json=walls,
            rooms_json=rooms,
            furniture_json=furniture,
            language="ru",
            output_path=output_png
        )
        assert os.path.exists(output_png)
        print(f"\n[OK] Interior PNG created at {output_png}")

        # 2. SVG Тест
        res_svg = draw_interior_plan_svg(
            title="Тест: Кухня + Санузел (SVG)",
            walls_json=walls,
            rooms_json=rooms,
            furniture_json=furniture,
            language="ru"
        )
        assert "svg" in res_svg.lower()
        with open(output_svg, "w") as f:
            f.write(res_svg)
        print(f"[OK] Interior SVG created at {output_svg}")

    except Exception as e:
        pytest.fail(f"Interior rendering failed: {e}")

if __name__ == "__main__":
    test_kitchen_bathroom_unit()
