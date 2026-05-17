import json
from theodolite_mcp.infrastructure.mcp_server import draw_pipeline_schematic

# --- ПРОЄКТ: ІДЕАЛЬНИЙ СЕТАП НА 10 000 ГРН (ЗИМОВИЙ ВАРІАНТ) ---
# Додано систему зливу на зиму: клапан у свердловині, злив у будинку, злив бойлера.

pipes = [
    # ГРУПА А: СВЕРДЛОВИНА ТА МАГІСТРАЛЬ (ПНД 25)
    {"start_pt": {"x": 0, "y": -12}, "end_pt": {"x": 0, "y": 0}, "medium": "cold_water", "nominal_diameter": 25, "flow_direction": "forward"},
    {"start_pt": {"x": 0, "y": 0}, "end_pt": {"x": 4, "y": 0}, "medium": "cold_water", "nominal_diameter": 25, "flow_direction": "forward"},
    
    # Зимовий злив у свердловині (відгалуження на глибині -2м, нижче промерзання)
    {"start_pt": {"x": 0, "y": -2}, "end_pt": {"x": 1, "y": -2}, "medium": "cold_water", "nominal_diameter": 15},
    
    # Ввід у будинок (З ІЗОЛЯЦІЄЮ)
    {"start_pt": {"x": 4, "y": 0}, "end_pt": {"x": 4, "y": 4}, "medium": "cold_water", "nominal_diameter": 25, "flow_direction": "forward", "insulated": True},
    
    # Злив у будинку (нижня точка біля вводу)
    {"start_pt": {"x": 4, "y": 0}, "end_pt": {"x": 5, "y": 0}, "medium": "cold_water", "nominal_diameter": 15},

    # ГРУПА Б: РОЗВОДКА ПО ДОМУ (ПНД 25 до фільтра)
    {"start_pt": {"x": 4, "y": 4}, "end_pt": {"x": 16, "y": 4}, "medium": "cold_water", "nominal_diameter": 25, "flow_direction": "forward"},
    
    # Після фільтра (ППР 20)
    {"start_pt": {"x": 16, "y": 4}, "end_pt": {"x": 26, "y": 4}, "medium": "cold_water", "nominal_diameter": 20, "flow_direction": "forward"},
    
    # Опуск на бойлер (холодна вода)
    {"start_pt": {"x": 20, "y": 4}, "end_pt": {"x": 20, "y": 1}, "medium": "cold_water", "nominal_diameter": 15, "flow_direction": "forward"},
    
    # Злив бойлера (відгалуження між бойлером і зворотним клапаном)
    {"start_pt": {"x": 20, "y": 1.5}, "end_pt": {"x": 19, "y": 1.5}, "medium": "cold_water", "nominal_diameter": 15},
    
    # Підйом з бойлера (гаряча вода)
    {"start_pt": {"x": 24, "y": 1}, "end_pt": {"x": 24, "y": 6}, "medium": "hot_water", "nominal_diameter": 15, "flow_direction": "forward"},
    
    # Гаряча вода на кухню
    {"start_pt": {"x": 24, "y": 6}, "end_pt": {"x": 28, "y": 6}, "medium": "hot_water", "nominal_diameter": 15, "flow_direction": "forward"},
]

equipment = [
    # Насос
    {"center_pt": {"x": 0, "y": -9}, "equipment_type": "centrifugal_pump", "label": "VMP 70-1", "tag": "P-1", "width": 2.0, "height": 2.0},
    
    # Бак
    {"center_pt": {"x": 10, "y": 4}, "equipment_type": "expansion_vessel", "label": "Euroaqua 50л", "tag": "GA-1", "width": 2.2, "height": 3.2},
    
    # Фільтр
    {"center_pt": {"x": 16, "y": 4}, "equipment_type": "mesh_filter", "label": "Ecosoft 3/4\"", "tag": "F-1", "width": 1.5, "height": 2.0},
    
    # Бойлер
    {"center_pt": {"x": 22, "y": -0.5}, "equipment_type": "boiler", "label": "RENS 15л (Під мийку)", "tag": "B-1", "width": 4.0, "height": 3.0},
]

valves = [
    # Зворотний клапан над насосом
    {"center_pt": {"x": 0, "y": -4}, "valve_type": "check", "tag": "CV-1", "rotation": 90, "nominal_diameter": 60},
    
    # Зимовий автоматичний зливний клапан у свердловині
    {"center_pt": {"x": 1, "y": -2}, "valve_type": "safety", "tag": "DV-Свердловина", "nominal_diameter": 40},
    
    # Головний кран 1"
    {"center_pt": {"x": 2, "y": 0}, "valve_type": "ball", "tag": "V-1", "nominal_diameter": 60},
    
    # Зливний кран магістралі будинку (нижня точка)
    {"center_pt": {"x": 5, "y": 0}, "valve_type": "ball", "tag": "DV-Магістраль", "nominal_diameter": 40},

    # Крани бойлера
    {"center_pt": {"x": 20, "y": 3.0}, "valve_type": "ball", "tag": "V-2", "rotation": 90, "nominal_diameter": 40},
    {"center_pt": {"x": 20, "y": 2.2}, "valve_type": "safety", "tag": "SV-1", "rotation": 90, "nominal_diameter": 40},
    
    # Кран для зливу бойлера
    {"center_pt": {"x": 19, "y": 1.5}, "valve_type": "ball", "tag": "DV-Бойлер", "nominal_diameter": 30},
]

instruments = [
    {"center_pt": {"x": 7.5, "y": 4}, "measured_variable": "P", "suffix": "I", "tag_number": "01"},
    {"center_pt": {"x": 12.5, "y": 4}, "measured_variable": "P", "suffix": "C", "tag_number": "01"},
]

try:
    draw_pipeline_schematic(
        title="ІДЕАЛЬНИЙ СЕТАП 10K (ЗИМОВИЙ ВАРІАНТ)",
        project_number="UKR-SMART-WINTER",
        organization="DIY Village Pro",
        pipes_json=pipes,
        equipment_json=equipment,
        valves_json=valves,
        instruments_json=instruments,
        language="uk",
        output_path="output/project_voda_ideal_10k_winter.png"
    )
    print("Зимове креслення створено: output/project_voda_ideal_10k_winter.png")
except Exception as e:
    print(f"Помилка: {e}")
