import json
from theodolite_mcp.infrastructure.mcp_server import draw_pipeline_schematic

# --- ПРОЄКТ: ЕКСПЕРТНЕ ВОДОПОСТАЧАННЯ (УКРАЇНА) ---
# Свердловина 32м -> Фільтрація -> Бойлер
# Принцип: Компактні координати, відсутність перекриттів з легендою.

pipes = [
    # ГРУПА А: СВЕРДЛОВИНА ТА КЕСОН (x: 0-2)
    {"start_pt": {"x": 0, "y": -6}, "end_pt": {"x": 0, "y": -3}, "medium": "cold_water", "nominal_diameter": 32, "flow_direction": "forward"},
    {"start_pt": {"x": 0, "y": -3}, "end_pt": {"x": 0, "y": 0}, "medium": "cold_water", "nominal_diameter": 32, "flow_direction": "forward"},
    {"start_pt": {"x": 0, "y": 0}, "end_pt": {"x": 2, "y": 0}, "medium": "cold_water", "nominal_diameter": 32, "flow_direction": "forward"},
    
    # ГРУПА Б: ВВІД У БУДИНОК ТА ГІДРОАКУМУЛЯТОР (x: 2-6)
    {"start_pt": {"x": 2, "y": 0}, "end_pt": {"x": 6, "y": 0}, "medium": "cold_water", "nominal_diameter": 32, "flow_direction": "forward"},
    {"start_pt": {"x": 6, "y": 0}, "end_pt": {"x": 6, "y": 2}, "medium": "cold_water", "nominal_diameter": 32, "flow_direction": "forward"},
    {"start_pt": {"x": 6, "y": 2}, "end_pt": {"x": 9, "y": 2}, "medium": "cold_water", "nominal_diameter": 25, "flow_direction": "forward"},
    
    # ГРУПА В: КАСКАД ОЧИСТКИ (x: 9-14)
    {"start_pt": {"x": 9, "y": 2}, "end_pt": {"x": 14, "y": 2}, "medium": "cold_water", "nominal_diameter": 25, "flow_direction": "forward"},
    
    # ГРУПА Г: БОЙЛЕР (x: 14-19)
    {"start_pt": {"x": 14, "y": 2}, "end_pt": {"x": 17, "y": 2}, "medium": "cold_water", "nominal_diameter": 20, "flow_direction": "forward"},
    {"start_pt": {"x": 17, "y": 2.5}, "end_pt": {"x": 17, "y": 5}, "medium": "hot_water", "nominal_diameter": 20, "flow_direction": "forward"},
    {"start_pt": {"x": 17, "y": 5}, "end_pt": {"x": 19, "y": 5}, "medium": "hot_water", "nominal_diameter": 20, "flow_direction": "forward"},
]

equipment = [
    # Насос
    {"center_pt": {"x": 0, "y": -4.5}, "equipment_type": "centrifugal_pump", "label": "Водолій БЦПЕ", "tag": "P-1", "width": 1.0, "height": 1.0},
    
    # Гідроакумулятор
    {"center_pt": {"x": 6, "y": 2}, "equipment_type": "expansion_vessel", "label": "SantehPlast", "tag": "GA-1", "width": 1.2, "height": 1.8},
    
    # Очистка
    {"center_pt": {"x": 10.5, "y": 2}, "equipment_type": "mesh_filter", "label": "Груба очистка", "tag": "F-1", "width": 0.8, "height": 0.8},
    {"center_pt": {"x": 12.5, "y": 2}, "equipment_type": "storage_tank", "label": "Тонка очистка", "tag": "F-2", "width": 0.8, "height": 1.2},
    
    # Бойлер
    {"center_pt": {"x": 17, "y": 3.75}, "equipment_type": "boiler", "label": "Atlantic VM 50", "tag": "B-1", "width": 1.2, "height": 1.8},
]

valves = [
    # CV-1 (більший діаметр для видимості символу)
    {"center_pt": {"x": 0, "y": -1.5}, "valve_type": "check", "tag": "CV-1", "rotation": 90, "nominal_diameter": 50},
    {"center_pt": {"x": 1, "y": 0}, "valve_type": "ball", "tag": "V-1", "nominal_diameter": 50},
    
    # Обв'язка бойлера
    {"center_pt": {"x": 15.5, "y": 2}, "valve_type": "ball", "tag": "V-2", "nominal_diameter": 40},
    {"center_pt": {"x": 17, "y": 5.5}, "valve_type": "ball", "tag": "V-3", "nominal_diameter": 40, "rotation": 90},
]

instruments = [
    # Автоматика
    {"center_pt": {"x": 6.5, "y": 3.5}, "measured_variable": "P", "suffix": "I", "tag_number": "01"},
    {"center_pt": {"x": 8.0, "y": 3.5}, "measured_variable": "P", "suffix": "C", "tag_number": "01"},
]

try:
    draw_pipeline_schematic(
        title="ПРОЄКТ ВОДОПОСТАЧАННЯ (ЕКСПЕРТНИЙ РІВЕНЬ)",
        project_number="UKR-WATER-2026",
        organization="Solo Developer Project",
        pipes_json=pipes,
        equipment_json=equipment,
        valves_json=valves,
        instruments_json=instruments,
        language="uk",
        output_path="output/project_voda_expert.png"
    )
    print("Експертне креслення (v6) створено: output/project_voda_expert.png")
except Exception as e:
    print(f"Помилка: {e}")
