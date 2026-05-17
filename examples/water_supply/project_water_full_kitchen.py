import json
from theodolite_mcp.infrastructure.mcp_server import draw_pipeline_schematic

# --- ПРОЄКТ: ВОДОПОСТАЧАННЯ З ЗИМІВЛЕЮ ТА КУХНЕЮ (~11,000 грн) ---
# Свердловина -> Автозлив -> Ввід (ізоляція) -> ГА -> Фільтр -> Бойлер -> Змішувач -> Мийка

pipes = [
    # ГРУПА А: СВЕРДЛОВИНА ТА МАГІСТРАЛЬ (ПНД 25)
    {"start_pt": {"x": 0, "y": -15}, "end_pt": {"x": 0, "y": 0}, "medium": "cold_water", "nominal_diameter": 25, "flow_direction": "forward"},
    {"start_pt": {"x": 0, "y": 0}, "end_pt": {"x": 6, "y": 0}, "medium": "cold_water", "nominal_diameter": 25, "flow_direction": "forward"},
    
    # Зимовий злив у свердловині
    {"start_pt": {"x": 0, "y": -2}, "end_pt": {"x": 2, "y": -2}, "medium": "cold_water", "nominal_diameter": 15},
    
    # Ввід у будинок (ІЗОЛЯЦІЯ + ГРІЮЧИЙ КАБЕЛЬ)
    {"start_pt": {"x": 6, "y": 0}, "end_pt": {"x": 6, "y": 8}, "medium": "cold_water", "nominal_diameter": 25, "flow_direction": "forward", "insulated": True},
    
    # Злив магістралі в будинку (нижня точка)
    {"start_pt": {"x": 6, "y": 0}, "end_pt": {"x": 8, "y": 0}, "medium": "cold_water", "nominal_diameter": 15},

    # ГРУПА Б: РОЗВОДКА ПО ДОМУ (ПНД 25 -> ППР 20)
    {"start_pt": {"x": 6, "y": 8}, "end_pt": {"x": 19, "y": 8}, "medium": "cold_water", "nominal_diameter": 25, "flow_direction": "forward"},
    {"start_pt": {"x": 19, "y": 8}, "end_pt": {"x": 28, "y": 8}, "medium": "cold_water", "nominal_diameter": 20, "flow_direction": "forward"}, # Після фільтра
    
    # ГРУПА В: БОЙЛЕР (Опуск ХВП, Підйом ГВП)
    {"start_pt": {"x": 28, "y": 8}, "end_pt": {"x": 28, "y": 3}, "medium": "cold_water", "nominal_diameter": 15, "flow_direction": "forward"},
    {"start_pt": {"x": 28, "y": 4}, "end_pt": {"x": 25, "y": 4}, "medium": "cold_water", "nominal_diameter": 15}, # Злив бойлера (трійник)
    {"start_pt": {"x": 32, "y": 3}, "end_pt": {"x": 32, "y": 10}, "medium": "hot_water", "nominal_diameter": 15, "flow_direction": "forward"},
    
    # ГРУПА Г: КУХНЯ (Магістралі до кутових кранів)
    {"start_pt": {"x": 28, "y": 8}, "end_pt": {"x": 36, "y": 8}, "medium": "cold_water", "nominal_diameter": 20, "flow_direction": "forward"},
    {"start_pt": {"x": 32, "y": 10}, "end_pt": {"x": 40, "y": 10}, "medium": "hot_water", "nominal_diameter": 20, "flow_direction": "forward"},
    
    # Опуски до кутових кранів під мийкою
    {"start_pt": {"x": 36, "y": 8}, "end_pt": {"x": 36, "y": 5}, "medium": "cold_water", "nominal_diameter": 15, "flow_direction": "forward"},
    {"start_pt": {"x": 40, "y": 10}, "end_pt": {"x": 40, "y": 5}, "medium": "hot_water", "nominal_diameter": 15, "flow_direction": "forward"},
    
    # Гнучка підводка (від кранів до змішувача)
    {"start_pt": {"x": 36, "y": 5}, "end_pt": {"x": 38, "y": 3}, "medium": "cold_water", "nominal_diameter": 10, "flow_direction": "forward"},
    {"start_pt": {"x": 40, "y": 5}, "end_pt": {"x": 38, "y": 3}, "medium": "hot_water", "nominal_diameter": 10, "flow_direction": "forward"},
    
    # Злив з мийки (Сифон)
    {"start_pt": {"x": 38, "y": -1}, "end_pt": {"x": 38, "y": -4}, "medium": "drainage", "nominal_diameter": 50, "flow_direction": "forward"},
    {"start_pt": {"x": 38, "y": -4}, "end_pt": {"x": 42, "y": -4}, "medium": "drainage", "nominal_diameter": 50, "flow_direction": "forward"},
]

equipment = [
    # Насос
    {"center_pt": {"x": 0, "y": -12}, "equipment_type": "centrifugal_pump", "label": "Expert Pump VMP 70-1", "tag": "P-1", "width": 2.0, "height": 2.0},
    
    # Автоматика
    {"center_pt": {"x": 13, "y": 8}, "equipment_type": "expansion_vessel", "label": "Euroaqua 24л (Верт.)", "tag": "GA-1", "width": 2.0, "height": 3.0},
    
    # Очистка
    {"center_pt": {"x": 20, "y": 8}, "equipment_type": "mesh_filter", "label": "Ecosoft 10\" (PP-20)", "tag": "F-1", "width": 1.5, "height": 2.0},
    
    # Бойлер (Під мийку)
    {"center_pt": {"x": 30, "y": 1}, "equipment_type": "boiler", "label": "RENS 10л (Під мийку)", "tag": "B-1", "width": 4.0, "height": 4.0},
    
    # Кухня: Змішувач
    {"center_pt": {"x": 38, "y": 2.5}, "equipment_type": "flow_meter", "label": "Змішувач VENTA", "tag": "MIX-1", "width": 1.5, "height": 1.5},
    
    # Кухня: Мийка (зобразимо як відкритий резервуар)
    {"center_pt": {"x": 38, "y": 0.5}, "equipment_type": "storage_tank", "label": "Мийка Platinum", "tag": "SINK-1", "width": 4.0, "height": 2.0},
]

valves = [
    # CV-1 (Свердловина)
    {"center_pt": {"x": 0, "y": -5}, "valve_type": "check", "tag": "CV-1", "rotation": 90, "nominal_diameter": 60},
    
    # Автодренаж (Свердловина)
    {"center_pt": {"x": 1.5, "y": -2}, "valve_type": "safety", "tag": "DV-Свердловина", "nominal_diameter": 40},
    
    # Головний кран
    {"center_pt": {"x": 3, "y": 0}, "valve_type": "ball", "tag": "V-1", "nominal_diameter": 60},
    
    # DV-Магістраль
    {"center_pt": {"x": 7.5, "y": 0}, "valve_type": "ball", "tag": "DV-Магістраль", "nominal_diameter": 40},

    # Обв'язка бойлера (Група безпеки SD FORTE)
    {"center_pt": {"x": 28, "y": 6}, "valve_type": "ball", "tag": "V-2", "rotation": 90, "nominal_diameter": 40},
    {"center_pt": {"x": 28, "y": 5}, "valve_type": "safety", "tag": "SV-1", "rotation": 90, "nominal_diameter": 40},
    
    # Злив бойлера (Трійник + Кран для підсосу повітря)
    {"center_pt": {"x": 26, "y": 4}, "valve_type": "ball", "tag": "DV-Бойлер", "nominal_diameter": 30},
    
    # Кутові крани на кухні (SD FORTE / ORSO)
    {"center_pt": {"x": 36, "y": 5}, "valve_type": "globe", "tag": "V-Cold", "rotation": 90, "nominal_diameter": 30},
    {"center_pt": {"x": 40, "y": 5}, "valve_type": "globe", "tag": "V-Hot", "rotation": 90, "nominal_diameter": 30},
]

instruments = [
    # Реле та манометр
    {"center_pt": {"x": 9.5, "y": 8.6}, "measured_variable": "P", "suffix": "I", "tag_number": "01"},
    {"center_pt": {"x": 16.5, "y": 8.6}, "measured_variable": "P", "suffix": "C", "tag_number": "01"},
]

try:
    draw_pipeline_schematic(
        title="ПОВНИЙ СЕТАП З КУХНЕЮ ТА ЗИМІВЛЕЮ (~11.0k грн)",
        project_number="UKR-FULL-KITCHEN",
        organization="DIY Village Pro",
        pipes_json=pipes,
        equipment_json=equipment,
        valves_json=valves,
        instruments_json=instruments,
        language="uk",
        output_path="output/project_voda_full_kitchen.png"
    )
    print("Повне креслення з кухнею створено: output/project_voda_full_kitchen.png")
except Exception as e:
    print(f"Помилка: {e}")
