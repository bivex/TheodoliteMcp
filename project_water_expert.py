import json
from theodolite_mcp.infrastructure.mcp_server import draw_pipeline_schematic

# --- ПРОЄКТ: ЕКСПЕРТНЕ ВОДОПОСТАЧАННЯ (УКРАЇНА) ---
# Свердловина 32м -> Фільтрація -> Бойлер
# Принцип: v7 — Повне заповнення по Y, рознесення V-3, повні назви.

pipes = [
    # ГРУПА А: СВЕРДЛОВИНА ТА КЕСОН (Y: -15 до 0)
    {"start_pt": {"x": 0, "y": -15}, "end_pt": {"x": 0, "y": -5}, "medium": "cold_water", "nominal_diameter": 32, "flow_direction": "forward"},
    {"start_pt": {"x": 0, "y": -5}, "end_pt": {"x": 0, "y": 0}, "medium": "cold_water", "nominal_diameter": 32, "flow_direction": "forward"},
    {"start_pt": {"x": 0, "y": 0}, "end_pt": {"x": 4, "y": 0}, "medium": "cold_water", "nominal_diameter": 32, "flow_direction": "forward"},
    
    # ГРУПА Б: ВВІД У БУДИНОК ТА ГІДРОАКУМУЛЯТОР
    {"start_pt": {"x": 4, "y": 0}, "end_pt": {"x": 8, "y": 0}, "medium": "cold_water", "nominal_diameter": 32, "flow_direction": "forward"},
    {"start_pt": {"x": 8, "y": 0}, "end_pt": {"x": 8, "y": 5}, "medium": "cold_water", "nominal_diameter": 32, "flow_direction": "forward"},
    {"start_pt": {"x": 8, "y": 5}, "end_pt": {"x": 12, "y": 5}, "medium": "cold_water", "nominal_diameter": 25, "flow_direction": "forward"},
    
    # ГРУПА В: КАСКАД ОЧИСТКИ
    {"start_pt": {"x": 12, "y": 5}, "end_pt": {"x": 20, "y": 5}, "medium": "cold_water", "nominal_diameter": 25, "flow_direction": "forward"},
    
    # ГРУПА Г: БОЙЛЕР
    {"start_pt": {"x": 20, "y": 5}, "end_pt": {"x": 24, "y": 5}, "medium": "cold_water", "nominal_diameter": 20, "flow_direction": "forward"},
    {"start_pt": {"x": 24, "y": 5.5}, "end_pt": {"x": 24, "y": 14}, "medium": "hot_water", "nominal_diameter": 20, "flow_direction": "forward"},
    {"start_pt": {"x": 24, "y": 14}, "end_pt": {"x": 28, "y": 14}, "medium": "hot_water", "nominal_diameter": 20, "flow_direction": "forward"},
]

equipment = [
    # Насос
    {"center_pt": {"x": 0, "y": -12}, "equipment_type": "centrifugal_pump", "label": "Водолій БЦПЕ 0.5-40У", "tag": "P-1", "width": 1.5, "height": 1.5},
    
    # Гідроакумулятор
    {"center_pt": {"x": 8, "y": 5}, "equipment_type": "expansion_vessel", "label": "SantehPlast HT-24L", "tag": "GA-1", "width": 1.5, "height": 2.2},
    
    # Очистка
    {"center_pt": {"x": 14, "y": 5}, "equipment_type": "mesh_filter", "label": "Груба очистка", "tag": "F-1", "width": 1.0, "height": 1.0},
    {"center_pt": {"x": 18, "y": 5}, "equipment_type": "storage_tank", "label": "Тонка очистка", "tag": "F-2", "width": 1.2, "height": 1.6},
    
    # Бойлер
    {"center_pt": {"x": 24, "y": 7.5}, "equipment_type": "boiler", "label": "Atlantic VM 50 S3", "tag": "B-1", "width": 1.6, "height": 2.4},
]

valves = [
    {"center_pt": {"x": 0, "y": -2.5}, "valve_type": "check", "tag": "CV-1", "rotation": 90, "nominal_diameter": 50},
    {"center_pt": {"x": 2, "y": 0}, "valve_type": "ball", "tag": "V-1", "nominal_diameter": 50},
    
    # Обв'язка бойлера
    {"center_pt": {"x": 22, "y": 5}, "valve_type": "ball", "tag": "V-2", "nominal_diameter": 40},
    {"center_pt": {"x": 24, "y": 12}, "valve_type": "ball", "tag": "V-3", "nominal_diameter": 40, "rotation": 90},
]

instruments = [
    # Автоматика - рознесена далеко від GA-1
    {"center_pt": {"x": 9.5, "y": 5.6}, "measured_variable": "P", "suffix": "I", "tag_number": "01"},
    {"center_pt": {"x": 10.5, "y": 5.6}, "measured_variable": "P", "suffix": "C", "tag_number": "01"},
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
    print("Експертне креслення (v7) створено: output/project_voda_expert.png")
except Exception as e:
    print(f"Помилка: {e}")
