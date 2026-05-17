import json
from theodolite_mcp.infrastructure.mcp_server import draw_pipeline_schematic

# --- ПРОЄКТ: ІДЕАЛЬНИЙ СЕТАП НА 10 000 ГРН (УКРАЇНА) ---
# Насос VMP 70-1 -> ПНД 25 -> Бак 50л -> Фільтр 3/4" -> ППР 20 -> Бойлер 15л

pipes = [
    # ГРУПА А: СВЕРДЛОВИНА ТА МАГІСТРАЛЬ (ПНД 25)
    {"start_pt": {"x": 0, "y": -12}, "end_pt": {"x": 0, "y": 0}, "medium": "cold_water", "nominal_diameter": 25, "flow_direction": "forward"},
    {"start_pt": {"x": 0, "y": 0}, "end_pt": {"x": 4, "y": 0}, "medium": "cold_water", "nominal_diameter": 25, "flow_direction": "forward"},
    
    # Підйом та ввід у будинок
    {"start_pt": {"x": 4, "y": 0}, "end_pt": {"x": 4, "y": 4}, "medium": "cold_water", "nominal_diameter": 25, "flow_direction": "forward"},
    
    # ГРУПА Б: РОЗВОДКА ПО ДОМУ (ПНД 25 до фільтра)
    {"start_pt": {"x": 4, "y": 4}, "end_pt": {"x": 16, "y": 4}, "medium": "cold_water", "nominal_diameter": 25, "flow_direction": "forward"},
    
    # Після фільтра (ППР 20)
    {"start_pt": {"x": 16, "y": 4}, "end_pt": {"x": 26, "y": 4}, "medium": "cold_water", "nominal_diameter": 20, "flow_direction": "forward"},
    
    # Опуск на бойлер (холодна вода)
    {"start_pt": {"x": 20, "y": 4}, "end_pt": {"x": 20, "y": 1}, "medium": "cold_water", "nominal_diameter": 15, "flow_direction": "forward"},
    
    # Підйом з бойлера (гаряча вода)
    {"start_pt": {"x": 24, "y": 1}, "end_pt": {"x": 24, "y": 6}, "medium": "hot_water", "nominal_diameter": 15, "flow_direction": "forward"},
    
    # Гаряча вода на кухню
    {"start_pt": {"x": 24, "y": 6}, "end_pt": {"x": 28, "y": 6}, "medium": "hot_water", "nominal_diameter": 15, "flow_direction": "forward"},
]

equipment = [
    # Насос
    {"center_pt": {"x": 0, "y": -9}, "equipment_type": "centrifugal_pump", "label": "VMP 70-1", "tag": "P-1", "width": 2.0, "height": 2.0},
    
    # Бак (Вертикальний)
    {"center_pt": {"x": 10, "y": 4}, "equipment_type": "expansion_vessel", "label": "Euroaqua 50л", "tag": "GA-1", "width": 2.2, "height": 3.2},
    
    # Фільтр
    {"center_pt": {"x": 16, "y": 4}, "equipment_type": "mesh_filter", "label": "Ecosoft 3/4\"", "tag": "F-1", "width": 1.5, "height": 2.0},
    
    # Бойлер (Ідеально підігнаний під труби x=20 та x=24. Топ на y=1.0)
    {"center_pt": {"x": 22, "y": -0.5}, "equipment_type": "boiler", "label": "RENS 15л (Під мийку)", "tag": "B-1", "width": 4.0, "height": 3.0},
]

valves = [
    # Клапан і ввідний кран
    {"center_pt": {"x": 0, "y": -3}, "valve_type": "check", "tag": "CV-1", "rotation": 90, "nominal_diameter": 60},
    {"center_pt": {"x": 2, "y": 0}, "valve_type": "ball", "tag": "V-1", "nominal_diameter": 60},
    
    # Крани бойлера (На вертикальній трубі холодної води x=20)
    {"center_pt": {"x": 20, "y": 3.0}, "valve_type": "ball", "tag": "V-2", "rotation": 90, "nominal_diameter": 40},
    {"center_pt": {"x": 20, "y": 2.0}, "valve_type": "safety", "tag": "SV-1", "rotation": 90, "nominal_diameter": 40},
]

instruments = [
    # Реле та манометр по боках від бака
    {"center_pt": {"x": 7.5, "y": 4}, "measured_variable": "P", "suffix": "I", "tag_number": "01"},
    {"center_pt": {"x": 12.5, "y": 4}, "measured_variable": "P", "suffix": "C", "tag_number": "01"},
]

try:
    draw_pipeline_schematic(
        title="ІДЕАЛЬНИЙ СЕТАП НА 10 000 ГРН",
        project_number="UKR-SMART-10K",
        organization="DIY Village Pro",
        pipes_json=pipes,
        equipment_json=equipment,
        valves_json=valves,
        instruments_json=instruments,
        language="uk",
        output_path="output/project_voda_ideal_10k.png"
    )
    print("Ідеальне креслення на 10к створено: output/project_voda_ideal_10k.png")
except Exception as e:
    print(f"Помилка: {e}")
