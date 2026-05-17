import json
from theodolite_mcp.infrastructure.mcp_server import draw_pipeline_schematic

# --- ПРОЄКТ: ІДЕАЛЬНИЙ СЕТАП 10К + ЗИМОВИЙ ПАКЕТ (Бюджет ~8,790 грн) ---
# Насос VMP 70-1 -> ПНД 25 -> Бак 24л -> Фільтр 3/4" -> ППР 20 -> Бойлер 10л
# Зима: Автозлив (-2м), гріючий кабель, злив магістралі, злив бойлера (трійник + повітря)

pipes = [
    # ГРУПА А: СВЕРДЛОВИНА ТА МАГІСТРАЛЬ (ПНД 25)
    {"start_pt": {"x": 0, "y": -15}, "end_pt": {"x": 0, "y": 0}, "medium": "cold_water", "nominal_diameter": 25, "flow_direction": "forward"},
    {"start_pt": {"x": 0, "y": 0}, "end_pt": {"x": 6, "y": 0}, "medium": "cold_water", "nominal_diameter": 25, "flow_direction": "forward"},
    
    # Зимовий злив у свердловині (Автодренаж на глибині -2м)
    {"start_pt": {"x": 0, "y": -2}, "end_pt": {"x": 2, "y": -2}, "medium": "cold_water", "nominal_diameter": 15},
    
    # Підйом та ввід у будинок (З ІЗОЛЯЦІЄЮ ТА ГРІЮЧИМ КАБЕЛЕМ PA-Flex)
    {"start_pt": {"x": 6, "y": 0}, "end_pt": {"x": 6, "y": 5}, "medium": "cold_water", "nominal_diameter": 25, "flow_direction": "forward", "insulated": True},
    
    # Злив магістралі в будинку (нижня точка біля вводу)
    {"start_pt": {"x": 6, "y": 0}, "end_pt": {"x": 8, "y": 0}, "medium": "cold_water", "nominal_diameter": 15},

    # ГРУПА Б: РОЗВОДКА ПО ДОМУ (ПНД 25 до фільтра)
    {"start_pt": {"x": 6, "y": 5}, "end_pt": {"x": 19, "y": 5}, "medium": "cold_water", "nominal_diameter": 25, "flow_direction": "forward"},
    
    # Після фільтра (ППР 20)
    {"start_pt": {"x": 19, "y": 5}, "end_pt": {"x": 28, "y": 5}, "medium": "cold_water", "nominal_diameter": 20, "flow_direction": "forward"},
    
    # Підключення до холодного крана змішувача
    {"start_pt": {"x": 28, "y": 5}, "end_pt": {"x": 36, "y": 5}, "medium": "cold_water", "nominal_diameter": 15, "flow_direction": "forward"},
    
    # Опуск на бойлер (холодна вода)
    {"start_pt": {"x": 28, "y": 5}, "end_pt": {"x": 28, "y": 1.5}, "medium": "cold_water", "nominal_diameter": 15, "flow_direction": "forward"},
    
    # Злив бойлера (Спеціальний трійник для впуску повітря / зливу)
    {"start_pt": {"x": 28, "y": 2.2}, "end_pt": {"x": 26, "y": 2.2}, "medium": "cold_water", "nominal_diameter": 15},
    
    # Підйом з бойлера (гаряча вода)
    {"start_pt": {"x": 32, "y": 1.5}, "end_pt": {"x": 32, "y": 6}, "medium": "hot_water", "nominal_diameter": 15, "flow_direction": "forward"},
    
    # Гаряча вода до змішувача
    {"start_pt": {"x": 32, "y": 6}, "end_pt": {"x": 36, "y": 6}, "medium": "hot_water", "nominal_diameter": 15, "flow_direction": "forward"},
]

equipment = [
    # Насос
    {"center_pt": {"x": 0, "y": -12}, "equipment_type": "centrifugal_pump", "label": "Expert Pump VMP 70", "tag": "P-1", "width": 2.0, "height": 2.0},
    
    # Гідроакумулятор 24л
    {"center_pt": {"x": 13, "y": 5}, "equipment_type": "expansion_vessel", "label": "ГА 24л (Горизонт.)", "tag": "GA-1", "width": 2.5, "height": 2.5, "rotation": 90},
    
    # Очистка (Ecosoft 10")
    {"center_pt": {"x": 20, "y": 5}, "equipment_type": "mesh_filter", "label": "Ecosoft 10\" 3/4\"", "tag": "F-1", "width": 1.5, "height": 2.0},
    
    # Бойлер під мийку (RENS 10л) - чітко підігнаний під опуск (28) та підйом (32)
    {"center_pt": {"x": 30, "y": 0}, "equipment_type": "boiler", "label": "RENS 10л (Під мийку)", "tag": "B-1", "width": 4.0, "height": 3.0},
]

valves = [
    # Зворотний клапан над насосом
    {"center_pt": {"x": 0, "y": -5}, "valve_type": "check", "tag": "CV-1", "rotation": 90, "nominal_diameter": 60},
    
    # Автодренаж (Свердловина)
    {"center_pt": {"x": 1.5, "y": -2}, "valve_type": "safety", "tag": "DV-Автозлив", "nominal_diameter": 40},
    
    # Головний кран 1"
    {"center_pt": {"x": 3, "y": 0}, "valve_type": "ball", "tag": "V-1", "nominal_diameter": 60},
    
    # DV-Магістраль (Кран зливу 1/2")
    {"center_pt": {"x": 7.5, "y": 0}, "valve_type": "ball", "tag": "DV-Магістраль", "nominal_diameter": 40},

    # Група безпеки бойлера (SD FORTE) та кран перед нею
    {"center_pt": {"x": 28, "y": 4.0}, "valve_type": "ball", "tag": "V-2", "rotation": 90, "nominal_diameter": 40},
    {"center_pt": {"x": 28, "y": 3.0}, "valve_type": "safety", "tag": "SV-1", "rotation": 90, "nominal_diameter": 40},
    
    # DV-Бойлер (Трійник + Кран для підсосу повітря)
    {"center_pt": {"x": 26.5, "y": 2.2}, "valve_type": "ball", "tag": "DV-Повітря", "nominal_diameter": 30},
]

instruments = [
    # Реле PM-5 та манометр на п'ятірнику біля бака
    {"center_pt": {"x": 9.5, "y": 5.6}, "measured_variable": "P", "suffix": "I", "tag_number": "01"},
    {"center_pt": {"x": 16.5, "y": 5.6}, "measured_variable": "P", "suffix": "C", "tag_number": "01"},
]

try:
    draw_pipeline_schematic(
        title="СЕТАП 10K + ЗИМОВИЙ ПАКЕТ (~8.8k грн)",
        project_number="UKR-WINTER-BOM",
        organization="DIY Village Pro",
        pipes_json=pipes,
        equipment_json=equipment,
        valves_json=valves,
        instruments_json=instruments,
        language="uk",
        output_path="output/project_voda_winter_bom.png"
    )
    print("Ідеально збалансоване зимове креслення створено: output/project_voda_winter_bom.png")
except Exception as e:
    print(f"Помилка: {e}")
