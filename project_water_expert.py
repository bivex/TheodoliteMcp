import json
from theodolite_mcp.infrastructure.mcp_server import draw_pipeline_schematic

# --- ПРОЄКТ: ЕКСПЕРТНЕ ВОДОПОСТАЧАННЯ (УКРАЇНА) ---
# Свердловина 32м -> Фільтрація -> Бойлер

pipes = [
    # ГРУПА А: СВЕРДЛОВИНА ТА КЕСОН
    {"start_pt": {"x": 0, "y": -15}, "end_pt": {"x": 0, "y": -5}, "medium": "cold_water", "nominal_diameter": 32, "flow_direction": "forward"},
    {"start_pt": {"x": 0, "y": -5}, "end_pt": {"x": 0, "y": 0}, "medium": "cold_water", "nominal_diameter": 32, "flow_direction": "forward"},
    {"start_pt": {"x": 0, "y": 0}, "end_pt": {"x": 8, "y": 0}, "medium": "cold_water", "nominal_diameter": 32, "flow_direction": "forward"},
    
    # ГРУПА Б: ВВІД У БУДИНОК ТА ГІДРОАКУМУЛЯТОР
    {"start_pt": {"x": 8, "y": 0}, "end_pt": {"x": 12, "y": 0}, "medium": "cold_water", "nominal_diameter": 32, "flow_direction": "forward"},
    {"start_pt": {"x": 12, "y": 0}, "end_pt": {"x": 12, "y": 6}, "medium": "cold_water", "nominal_diameter": 32, "flow_direction": "forward"},
    {"start_pt": {"x": 12, "y": 6}, "end_pt": {"x": 18, "y": 6}, "medium": "cold_water", "nominal_diameter": 25, "flow_direction": "forward"},
    
    # ГРУПА В: КАСКАД ОЧИСТКИ
    {"start_pt": {"x": 18, "y": 6}, "end_pt": {"x": 30, "y": 6}, "medium": "cold_water", "nominal_diameter": 25, "flow_direction": "forward"},
    {"start_pt": {"x": 30, "y": 6}, "end_pt": {"x": 30, "y": 14}, "medium": "cold_water", "nominal_diameter": 25, "flow_direction": "forward"},
    
    # ГРУПА Г: БОЙЛЕР
    {"start_pt": {"x": 30, "y": 14}, "end_pt": {"x": 36, "y": 14}, "medium": "cold_water", "nominal_diameter": 20, "flow_direction": "forward"},
    {"start_pt": {"x": 36, "y": 14.5}, "end_pt": {"x": 36, "y": 20}, "medium": "hot_water", "nominal_diameter": 20, "flow_direction": "forward"},
    {"start_pt": {"x": 36, "y": 20}, "end_pt": {"x": 42, "y": 20}, "medium": "hot_water", "nominal_diameter": 20, "flow_direction": "forward"},
]

equipment = [
    # Насос
    {"center_pt": {"x": 0, "y": -12}, "equipment_type": "centrifugal_pump", "label": "Водолій БЦПЕ 0.5-40У", "tag": "P-1", "width": 2.5, "height": 2.5},
    
    # Гідроакумулятор
    {"center_pt": {"x": 12, "y": 6}, "equipment_type": "expansion_vessel", "label": "SantehPlast HT-24L", "tag": "GA-1", "width": 3.0, "height": 4.5},
    
    # Очистка
    {"center_pt": {"x": 22, "y": 6}, "equipment_type": "mesh_filter", "label": "Груба очистка", "tag": "F-1", "width": 2.0, "height": 2.0},
    {"center_pt": {"x": 27, "y": 6}, "equipment_type": "storage_tank", "label": "Тонка очистка", "tag": "F-2", "width": 2.0, "height": 3.0},
    
    # Бойлер
    {"center_pt": {"x": 36, "y": 17.5}, "equipment_type": "boiler", "label": "Atlantic VM 50 S3", "tag": "B-1", "width": 3.0, "height": 4.5},
]

valves = [
    {"center_pt": {"x": 0, "y": -3}, "valve_type": "check", "tag": "CV-1", "rotation": 90, "nominal_diameter": 100},
    {"center_pt": {"x": 4, "y": 0}, "valve_type": "ball", "tag": "V-1", "nominal_diameter": 100},
    
    # Обв'язка бойлера
    {"center_pt": {"x": 33, "y": 14}, "valve_type": "ball", "tag": "V-2", "nominal_diameter": 80},
    {"center_pt": {"x": 36, "y": 21}, "valve_type": "ball", "tag": "V-3", "nominal_diameter": 80, "rotation": 90},
]

instruments = [
    # Автоматика - рознесена
    {"center_pt": {"x": 13, "y": 9}, "measured_variable": "P", "suffix": "I", "tag_number": "01"},
    {"center_pt": {"x": 16, "y": 9}, "measured_variable": "P", "suffix": "C", "tag_number": "01"},
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
    print("Експертне креслення (v5) створено: output/project_voda_expert.png")
except Exception as e:
    print(f"Помилка: {e}")
